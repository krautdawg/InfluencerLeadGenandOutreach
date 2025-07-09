import os
import asyncio
import logging
import json
import base64
import hashlib
from datetime import datetime
from email.mime.text import MIMEText
from concurrent.futures import ThreadPoolExecutor
import httpx
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from openai import OpenAI
from apify_client import ApifyClient
import csv
import io

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET",
                                "dev-secret-key-change-in-production")

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize database
from models import db, Lead, ProcessingSession, HashtagUsernamePair
db.init_app(app)

# Initialize OpenAI client
# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Create database tables
with app.app_context():
    db.create_all()

# Global storage for processing status (only for status, data is in DB)
app_data = {'processing_status': None}


# Global temporary storage for usernames during processing
temp_username_storage = []

def save_usernames_to_temp_storage(usernames):
    """Save usernames to temporary storage to avoid memory accumulation"""
    global temp_username_storage
    saved = []
    for username in usernames:
        if username not in temp_username_storage:
            temp_username_storage.append(username)
            saved.append(username)
    return saved

def get_usernames_from_temp_storage():
    """Get usernames from temporary storage and clear it"""
    global temp_username_storage
    result = [{'ownerUsername': username} for username in temp_username_storage]
    temp_username_storage = []  # Clear after retrieval
    return result

def deduplicate_profiles(profiles):
    """Remove duplicate profiles based on hashtag|username key"""
    seen = set()
    unique_profiles = []
    duplicates = set()

    for profile in profiles:
        key = f"{profile.get('hashtag', '')}|{profile.get('username', '')}"
        if key in seen:
            duplicates.add(profile.get('username', ''))
        else:
            seen.add(key)
            unique_profiles.append(profile)

    return unique_profiles, duplicates


def save_hashtag_username_pairs(profiles, duplicates):
    """Save deduplicated hashtag-username pairs to database"""
    saved_pairs = []
    batch_size = 50  # Process in batches for better performance
    
    with app.app_context():
        try:
            for i, profile in enumerate(profiles):
                hashtag = profile.get('hashtag', '')
                username = profile.get('username', '')
                
                if not hashtag or not username:
                    continue
                
                # Check if pair already exists
                existing_pair = HashtagUsernamePair.query.filter_by(
                    hashtag=hashtag,
                    username=username
                ).first()
                
                if existing_pair:
                    # Update existing pair
                    existing_pair.is_duplicate = username in duplicates
                    saved_pairs.append(existing_pair)
                else:
                    # Create new pair
                    new_pair = HashtagUsernamePair(
                        hashtag=hashtag,
                        username=username,
                        is_duplicate=username in duplicates
                    )
                    db.session.add(new_pair)
                    saved_pairs.append(new_pair)
                
                # Commit in batches
                if (i + 1) % batch_size == 0:
                    db.session.commit()
                    logger.info(f"Committed batch {i + 1} hashtag-username pairs to database")
            
            # Final commit for remaining items
            db.session.commit()
            logger.info(f"Successfully saved {len(saved_pairs)} hashtag-username pairs to database")
            
            return saved_pairs
            
        except Exception as e:
            logger.error(f"Failed to save hashtag-username pairs: {e}")
            db.session.rollback()
            raise


def call_apify_actor_sync(actor_id, input_data, token):
    """Call Apify actor using official client - extreme memory optimization with true streaming"""
    client = ApifyClient(token)
    
    try:
        # Run the Actor and wait for it to finish
        run = client.actor(actor_id).call(run_input=input_data)
        
        # Ultra memory optimization settings
        max_items = 30   # Further reduced to prevent memory issues
        save_batch_size = 5  # Save to DB every 5 usernames
        processing_delay = 1.0  # Increased delay
        
        dataset = client.dataset(run["defaultDatasetId"])
        
        # Process and save usernames in micro-batches
        username_batch = []
        total_saved = 0
        total_processed = 0
        
        # Use smaller chunks and more frequent garbage collection
        import gc
        import time
        
        logger.info(f"Starting ultra-streaming extraction with max_items={max_items}")
        
        # Don't accumulate all usernames - process in micro batches
        for item in dataset.iterate_items():
            if total_processed >= max_items:
                logger.info(f"Reached maximum item limit of {max_items} for memory safety")
                break
            
            # Extract usernames from this single item
            item_usernames = set()
            
            if isinstance(item, dict):
                # Extract from latestPosts
                if 'latestPosts' in item and isinstance(item['latestPosts'], list):
                    for post in item['latestPosts'][:5]:  # Limit posts per item
                        if isinstance(post, dict) and 'ownerUsername' in post:
                            username = post['ownerUsername']
                            if username and isinstance(username, str):
                                item_usernames.add(username)
                
                # Extract from topPosts
                if 'topPosts' in item and isinstance(item['topPosts'], list):
                    for post in item['topPosts'][:5]:  # Limit posts per item
                        if isinstance(post, dict) and 'ownerUsername' in post:
                            username = post['ownerUsername']
                            if username and isinstance(username, str):
                                item_usernames.add(username)
            
            # Add to batch
            username_batch.extend(item_usernames)
            
            # Clear the item from memory immediately
            item = None
            item_usernames = None
            
            total_processed += 1
            
            # Save batch to database when it reaches threshold
            if len(username_batch) >= save_batch_size:
                # Save this micro-batch immediately
                saved_usernames = save_usernames_to_temp_storage(username_batch[:save_batch_size])
                total_saved += len(saved_usernames)
                
                # Keep only unprocessed usernames
                username_batch = username_batch[save_batch_size:]
                
                # Aggressive cleanup
                gc.collect()
                time.sleep(processing_delay)
                logger.debug(f"Saved micro-batch: {len(saved_usernames)} usernames. Total saved: {total_saved}")
        
        # Save any remaining usernames
        if username_batch:
            saved_usernames = save_usernames_to_temp_storage(username_batch)
            total_saved += len(saved_usernames)
            gc.collect()
        
        logger.info(f"Ultra-streaming completed: {total_saved} usernames saved from {total_processed} items")
        
        # Return usernames from temp storage
        return {"items": get_usernames_from_temp_storage()}
        
    except Exception as e:
        logger.error(f"Apify actor call failed: {e}")
        return {"items": []}


async def call_perplexity_api(username, api_key):
    """Call Perplexity API to find contact information"""
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model":
        "llama-3.1-sonar-small-128k-online",
        "messages": [{
            "role":
            "system",
            "content":
            "Du bist ein hilfreicher Recherche-Assistent, finde öffentlich verfügbare Kontaktinfos."
        }, {
            "role":
            "user",
            "content":
            f"Suche nach E-Mail-Adresse, Telefonnummer oder Website des Instagram-Profils https://www.instagram.com/{username}/ Antworte nur als JSON: {{ \"email\": \"...\", \"phone\": \"...\", \"website\": \"...\" }}"
        }],
        "temperature":
        0.2,
        "stream":
        False
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()

        try:
            content = result['choices'][0]['message']['content']
            # Try to parse JSON from the response
            contact_info = json.loads(content)
            return contact_info
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(
                f"Failed to parse Perplexity response for {username}: {e}")
            return {"email": "", "phone": "", "website": ""}


def save_single_lead_to_db(username, profile_info, keyword=None):
    """Save a single lead directly to database - used for extreme memory optimization"""
    try:
        with app.app_context():
            # Get keyword from global context if not provided
            if not keyword:
                keyword = getattr(save_single_lead_to_db, 'current_keyword', 'unknown')
            
            # Check if lead already exists
            existing_lead = Lead.query.filter_by(
                username=username,
                hashtag=keyword
            ).first()
            
            if existing_lead:
                # Update existing lead
                existing_lead.full_name = profile_info.get('full_name', '')
                existing_lead.bio = profile_info.get('biography', '')
                existing_lead.email = profile_info.get('public_email', '')
                existing_lead.phone = profile_info.get('contact_phone_number', '')
                existing_lead.website = profile_info.get('external_url', '')
                existing_lead.followers_count = profile_info.get('follower_count', 0)
                existing_lead.following_count = profile_info.get('following_count', 0)
                existing_lead.posts_count = profile_info.get('media_count', 0)
                existing_lead.is_verified = profile_info.get('is_verified', False)
                existing_lead.profile_pic_url = profile_info.get('profile_pic_url', '')
                existing_lead.address_street = profile_info.get('address_street', '')
                existing_lead.city_name = profile_info.get('city_name', '')
                existing_lead.zip = profile_info.get('zip', '')
                existing_lead.latitude = profile_info.get('latitude')
                existing_lead.longitude = profile_info.get('longitude')
                existing_lead.is_duplicate = profile_info.get('is_duplicate', False)
                existing_lead.updated_at = datetime.utcnow()
            else:
                # Create new lead
                new_lead = Lead(
                    username=username,
                    hashtag=keyword,
                    full_name=profile_info.get('full_name', ''),
                    bio=profile_info.get('biography', ''),
                    email=profile_info.get('public_email', ''),
                    phone=profile_info.get('contact_phone_number', ''),
                    website=profile_info.get('external_url', ''),
                    followers_count=profile_info.get('follower_count', 0),
                    following_count=profile_info.get('following_count', 0),
                    posts_count=profile_info.get('media_count', 0),
                    is_verified=profile_info.get('is_verified', False),
                    profile_pic_url=profile_info.get('profile_pic_url', ''),
                    address_street=profile_info.get('address_street', ''),
                    city_name=profile_info.get('city_name', ''),
                    zip=profile_info.get('zip', ''),
                    latitude=profile_info.get('latitude'),
                    longitude=profile_info.get('longitude'),
                    is_duplicate=profile_info.get('is_duplicate', False)
                )
                db.session.add(new_lead)
            
            # Commit immediately
            db.session.commit()
            return True
            
    except Exception as e:
        logger.error(f"Failed to save single lead {username}: {e}")
        db.session.rollback()
        return False

def save_leads_incrementally(enriched_leads, keyword):
    """Save leads to database incrementally to prevent data loss"""
    saved_count = 0
    try:
        with app.app_context():
            for lead_data in enriched_leads:
                try:
                    # Check if lead already exists
                    existing_lead = Lead.query.filter_by(
                        username=lead_data['username'],
                        hashtag=keyword
                    ).first()
                    
                    if existing_lead:
                        # Update existing lead
                        existing_lead.full_name = lead_data.get('full_name', '')
                        existing_lead.bio = lead_data.get('biography', '')
                        existing_lead.email = lead_data.get('public_email', '')
                        existing_lead.phone = lead_data.get('contact_phone_number', '')
                        existing_lead.website = lead_data.get('external_url', '')
                        existing_lead.followers_count = lead_data.get('follower_count', 0)
                        existing_lead.following_count = lead_data.get('following_count', 0)
                        existing_lead.posts_count = lead_data.get('media_count', 0)
                        existing_lead.is_verified = lead_data.get('is_verified', False)
                        existing_lead.profile_pic_url = lead_data.get('profile_pic_url', '')
                        existing_lead.address_street = lead_data.get('address_street', '')
                        existing_lead.city_name = lead_data.get('city_name', '')
                        existing_lead.zip = lead_data.get('zip', '')
                        existing_lead.latitude = lead_data.get('latitude')
                        existing_lead.longitude = lead_data.get('longitude')
                        existing_lead.is_duplicate = lead_data.get('is_duplicate', False)
                        existing_lead.updated_at = datetime.utcnow()
                    else:
                        # Create new lead
                        new_lead = Lead(
                            username=lead_data['username'],
                            hashtag=keyword,
                            full_name=lead_data.get('full_name', ''),
                            bio=lead_data.get('biography', ''),
                            email=lead_data.get('public_email', ''),
                            phone=lead_data.get('contact_phone_number', ''),
                            website=lead_data.get('external_url', ''),
                            followers_count=lead_data.get('follower_count', 0),
                            following_count=lead_data.get('following_count', 0),
                            posts_count=lead_data.get('media_count', 0),
                            is_verified=lead_data.get('is_verified', False),
                            profile_pic_url=lead_data.get('profile_pic_url', ''),
                            address_street=lead_data.get('address_street', ''),
                            city_name=lead_data.get('city_name', ''),
                            zip=lead_data.get('zip', ''),
                            latitude=lead_data.get('latitude'),
                            longitude=lead_data.get('longitude'),
                            is_duplicate=lead_data.get('is_duplicate', False)
                        )
                        db.session.add(new_lead)
                    
                    # Commit each lead immediately
                    db.session.commit()
                    saved_count += 1
                    logger.info(f"Saved lead {lead_data['username']} to database")
                    
                except Exception as e:
                    logger.error(f"Failed to save lead {lead_data.get('username', 'unknown')}: {e}")
                    db.session.rollback()
                    continue
            
            logger.info(f"Incremental save completed: {saved_count} leads saved")
            
    except Exception as e:
        logger.error(f"Error during incremental save: {e}")
    
    return saved_count


async def enrich_profile_batch(usernames, ig_sessionid, apify_token,
                               perplexity_key, semaphore):
    """Enrich a batch of profiles with direct database saving - extreme memory optimization"""
    async with semaphore:
        saved_count = 0
        keyword = None  # Will be set from context
        
        try:
            # Process one username at a time to minimize memory
            for username in usernames:
                try:
                    # Call Apify for single profile
                    instagram_url = f"https://www.instagram.com/{username}"
                    input_data = {
                        "instagram_ids": [instagram_url],  # Only one URL
                        "SessionID": ig_sessionid,
                        "proxy": {
                            "useApifyProxy": True,
                            "groups": ["RESIDENTIAL"],
                        }
                    }
                    
                    # Call profile enrichment for single profile
                    client = ApifyClient(apify_token)
                    profile_info = {}
                    
                    try:
                        run = client.actor("8WEn9FvZnhE7lM3oA").call(run_input=input_data)
                        dataset = client.dataset(run["defaultDatasetId"])
                        
                        # Get first item only
                        for item in dataset.iterate_items():
                            if isinstance(item, dict):
                                # Extract only essential fields
                                profile_info = {
                                    'username': item.get('username', username),
                                    'full_name': item.get('full_name', ''),
                                    'biography': item.get('biography', ''),
                                    'public_email': item.get('public_email', ''),
                                    'contact_phone_number': item.get('contact_phone_number', ''),
                                    'external_url': item.get('external_url', ''),
                                    'follower_count': item.get('follower_count', 0),
                                    'following_count': item.get('following_count', 0),
                                    'media_count': item.get('media_count', 0),
                                    'is_verified': item.get('is_verified', False),
                                    'profile_pic_url': item.get('profile_pic_url', ''),
                                    'address_street': item.get('address_street', ''),
                                    'city_name': item.get('city_name', ''),
                                    'zip': item.get('zip', ''),
                                    'latitude': item.get('latitude'),
                                    'longitude': item.get('longitude')
                                }
                                break  # Only process first item
                        
                        # Clear dataset from memory
                        dataset = None
                        
                    except Exception as e:
                        logger.error(f"Profile enrichment failed for {username}: {e}")
                    
                    # Check if contact info is missing and use Perplexity fallback
                    if not any([
                            profile_info.get('public_email'),
                            profile_info.get('contact_phone_number'),
                            profile_info.get('external_url')
                    ]):
                        try:
                            contact_info = await call_perplexity_api(username, perplexity_key)
                            if 'email' in contact_info:
                                profile_info['public_email'] = contact_info['email']
                            if 'phone' in contact_info:
                                profile_info['contact_phone_number'] = contact_info['phone']
                            if 'website' in contact_info:
                                profile_info['external_url'] = contact_info['website']
                        except Exception as e:
                            logger.error(f"Perplexity API failed for {username}: {e}")
                    
                    # Save directly to database - one profile at a time
                    if profile_info:
                        saved = save_single_lead_to_db(username, profile_info)
                        if saved:
                            saved_count += 1
                            logger.info(f"Saved profile {username} directly to database")
                    
                    # Force garbage collection after each profile
                    import gc
                    gc.collect()
                    
                    # Small delay to reduce memory pressure
                    import time
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Failed to process profile {username}: {e}")
                    continue
            
            logger.info(f"Enrichment batch complete: {saved_count} profiles saved")
            return saved_count  # Return count instead of list
            
        except Exception as e:
            logger.error(f"Failed to enrich profiles batch: {e}")
            return 0


@app.route('/')
def index():
    """Main page"""
    ig_sessionid = session.get('ig_sessionid') or os.environ.get(
        'IG_SESSIONID')
    
    # Get leads from database
    leads = Lead.query.order_by(Lead.created_at.desc()).all()
    leads_dict = [lead.to_dict() for lead in leads]
    
    return render_template('index.html',
                           ig_sessionid=ig_sessionid,
                           leads=leads_dict,
                           processing_status=app_data['processing_status'])


@app.route('/ping')
def ping():
    """Health check endpoint"""
    return {"status": "OK"}, 200


@app.route('/session', methods=['POST'])
def set_session():
    """Set Instagram session ID"""
    data = request.get_json()
    if not data or not data.get('ig_sessionid'):
        return {"error": "Instagram Session ID is required"}, 400

    session['ig_sessionid'] = data['ig_sessionid']
    return {"success": True}


@app.route('/process', methods=['POST'])
def process_keyword():
    """Process keyword and generate leads"""
    data = request.get_json()
    keyword = data.get('keyword', '').strip()
    search_limit = data.get('searchLimit', 100)

    if not keyword:
        return {"error": "Keyword is required"}, 400
    
    # Validate search limit - further reduced maximum to prevent memory issues
    try:
        search_limit = int(search_limit)
        if search_limit < 1 or search_limit > 50:  # Reduced from 100 to 50 for memory safety
            return {"error": "Search limit must be between 1 and 50"}, 400
    except (ValueError, TypeError):
        return {"error": "Invalid search limit value"}, 400

    ig_sessionid = session.get('ig_sessionid') or os.environ.get(
        'IG_SESSIONID')
    if not ig_sessionid:
        return {"error": "Instagram Session ID not found. Please provide your Instagram session ID first."}, 400

    # Start processing in background using ThreadPoolExecutor
    app_data['processing_status'] = 'Processing...'

    try:
        # Run the async processing in a thread pool with memory optimization
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_async_process, keyword, ig_sessionid, search_limit)
            try:
                result = future.result(timeout=180)  # Reduced to 3 minutes
            except TimeoutError:
                logger.error("Processing timed out after 3 minutes")
                app_data['processing_status'] = None
                return {"error": "Processing timed out. Please try with a smaller search limit."}, 408

        app_data['processing_status'] = None
        return {"success": True, "leads": result}

    except Exception as e:
        logger.error(f"Processing failed: {e}")
        app_data['processing_status'] = None
        return {"error": str(e)}, 500


def run_async_process(keyword, ig_sessionid, search_limit):
    """Run async processing in a separate thread"""
    try:
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                process_keyword_async(keyword, ig_sessionid, search_limit))
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"Async processing failed: {e}")
        raise


async def process_keyword_async(keyword, ig_sessionid, search_limit):
    """Async processing of keyword"""
    apify_token = os.environ.get('APIFY_TOKEN')
    perplexity_key = os.environ.get('PERPLEXITY_API_KEY')

    if not all([apify_token, perplexity_key
                ]) or not apify_token.strip() or not perplexity_key.strip():
        missing_keys = []
        if not apify_token or not apify_token.strip():
            missing_keys.append('APIFY_TOKEN')
        if not perplexity_key or not perplexity_key.strip():
            missing_keys.append('PERPLEXITY_API_KEY')
        raise ValueError(
            f"Missing or empty API tokens: {', '.join(missing_keys)}")

    # Step 1: Hashtag crawl - Using correct Apify API format with user-defined limit
    hashtag_input = {
        "search": keyword,
        "searchType": "hashtag",
        "searchLimit": search_limit
    }

    try:
        hashtag_data = call_apify_actor_sync("DrF9mzPPEuVizVF4l", hashtag_input,
                                             apify_token)
        if not hashtag_data or not hashtag_data.get('items'):
            logger.error(f"No hashtag data returned for keyword: {keyword}")
            return []
    except Exception as e:
        logger.error(f"Hashtag crawl failed for keyword '{keyword}': {e}")
        return []

    # Step 2: Extract usernames from the processed data
    # The call_apify_actor_sync function already processed and extracted usernames
    hashtag_items = hashtag_data.get('items', [])
    logger.info(f"Processing {len(hashtag_items)} hashtag items")
    
    # Debug: Log the structure of the first item
    if hashtag_items:
        logger.debug(f"First item structure: {list(hashtag_items[0].keys()) if isinstance(hashtag_items[0], dict) else type(hashtag_items[0])}")
        logger.debug(f"First item sample: {str(hashtag_items[0])[:200]}")
    
    usernames_set = set()  # Use set for deduplication
    
    # Extract usernames from the processed items (these already contain ownerUsername)
    try:
        for item in hashtag_items:
            if not isinstance(item, dict):
                logger.warning(f"Skipping non-dict item: {type(item)}")
                continue
                
            # The streaming process already extracted usernames and stored them as ownerUsername
            username = item.get('ownerUsername')
            if username and isinstance(username, str):
                usernames_set.add(username)
            else:
                logger.debug(f"Item without ownerUsername: {list(item.keys()) if isinstance(item, dict) else 'not a dict'}")
    
    except Exception as e:
        logger.error(f"Error during username extraction: {e}")
        # Continue with whatever usernames we have
    
    # Clear hashtag_data from memory to help with garbage collection
    hashtag_data = None
    hashtag_items = None
    
    logger.info(f"Found {len(usernames_set)} unique usernames from posts")

    # Convert to profiles list using search keyword as hashtag
    profiles = [{'hashtag': keyword, 'username': username} for username in usernames_set]
    
    # Store count before clearing for logging
    usernames_count = len(usernames_set)
    
    # Clear usernames_set from memory
    usernames_set = None

    logger.info(f"Found {len(profiles)} profiles")
    
    # If no profiles found, return empty result
    if not profiles:
        logger.warning(f"No profiles found in hashtag data for keyword: {keyword}")
        logger.info(f"Extracted {usernames_count} unique usernames from hashtag data")
        return []

    unique_profiles, duplicates = deduplicate_profiles(profiles)
    logger.info(f"After deduplication: {len(unique_profiles)} unique profiles")

    # Save deduplicated hashtag-username pairs to database
    try:
        saved_pairs = save_hashtag_username_pairs(unique_profiles, duplicates)
        logger.info(f"Saved {len(saved_pairs)} hashtag-username pairs to database")
    except Exception as e:
        logger.error(f"Failed to save hashtag-username pairs: {e}")
        # Continue processing even if saving pairs fails

    # Step 3: Profile enrichment with extreme memory optimization
    # Set keyword context for database saving
    save_single_lead_to_db.current_keyword = keyword
    
    semaphore = asyncio.Semaphore(1)  # Only 1 concurrent call to minimize memory
    
    # Extract usernames and process one at a time
    usernames = [p['username'] for p in unique_profiles]
    
    # Ultra-reduced limit to prevent memory overflow
    max_usernames = 5  # Extremely reduced for memory safety
    if len(usernames) > max_usernames:
        logger.info(f"Limiting usernames from {len(usernames)} to {max_usernames} for extreme memory safety")
        usernames = usernames[:max_usernames]
    
    # Clear unique_profiles from memory
    unique_profiles = None
    duplicates_set = duplicates  # Keep for checking
    duplicates = None
    
    # Process one username at a time with direct database saving
    total_saved_leads = 0
    import gc
    import time
    
    logger.info(f"Starting ultra-memory-optimized enrichment for {len(usernames)} usernames")
    
    # Process each username individually
    for i, username in enumerate(usernames):
        try:
            logger.info(f"Processing username {i+1}/{len(usernames)}: {username}")
            
            # Process single username with direct DB save
            saved_count = await enrich_profile_batch([username], ig_sessionid, apify_token,
                                                   perplexity_key, semaphore)
            
            # Update duplicate status if needed
            if username in duplicates_set:
                try:
                    with app.app_context():
                        lead = Lead.query.filter_by(username=username, hashtag=keyword).first()
                        if lead:
                            lead.is_duplicate = True
                            db.session.commit()
                except Exception as e:
                    logger.error(f"Failed to update duplicate status for {username}: {e}")
            
            total_saved_leads += saved_count
            logger.info(f"Username {i+1}: Saved {saved_count} lead(s)")
            
            # Aggressive cleanup after each profile
            gc.collect()
            time.sleep(1.5)  # Longer delay between profiles
            
        except Exception as e:
            logger.error(f"Username {i+1} processing error: {e}")
            # Continue with next username
            continue

    logger.info(f"Ultra-memory-optimized enrichment complete: {total_saved_leads} leads saved to database")
    
    # Return dictionary format for API response
    # Query fresh leads from database to avoid session issues
    try:
        with app.app_context():
            fresh_leads = Lead.query.filter_by(hashtag=keyword).order_by(Lead.created_at.desc()).all()
            return [lead.to_dict() for lead in fresh_leads]
    except Exception as e:
        logger.error(f"Failed to query leads from database: {e}")
        return []


@app.route('/draft/<username>', methods=['POST'])
def draft_email(username):
    """Generate email draft using OpenAI"""
    data = request.get_json()
    subject_prompt = data.get(
        'subject_prompt',
        'Generate a compelling subject line for an outreach email')
    body_prompt = data.get('body_prompt',
                           'Generate a personalized outreach email')

    # Find the lead in database
    lead = Lead.query.filter_by(username=username).first()
    if not lead:
        return {"error": "Lead not found"}, 404

    try:
        # Generate subject
        subject_response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "system",
                "content": subject_prompt
            }, {
                "role":
                "user",
                "content":
                f"Profile: @{lead.username}, Name: {lead.full_name}, Bio: {lead.bio}"
            }],
            response_format={"type": "json_object"},
            max_tokens=100)

        # Generate body
        body_response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role":
                "system",
                "content":
                f"{body_prompt} Respond with JSON format: {{\"body\": \"email content\"}}"
            }, {
                "role":
                "user",
                "content":
                f"Profile: @{lead.username}, Name: {lead.full_name}, Bio: {lead.bio}, Email: {lead.email}"
            }],
            response_format={"type": "json_object"},
            max_tokens=500)

        subject_data = json.loads(subject_response.choices[0].message.content)
        body_data = json.loads(body_response.choices[0].message.content)

        # Update lead with generated content
        lead.subject = subject_data.get('subject',
                                       'Collaboration Opportunity')
        lead.email_body = body_data.get(
            'body',
            'Hello, I would like to discuss a collaboration opportunity.')
        
        # Save to database
        db.session.commit()

        return {"subject": lead.subject, "body": lead.email_body}

    except Exception as e:
        logger.error(f"Email drafting failed: {e}")
        return {"error": "Failed to generate email"}, 500


@app.route('/send/<username>', methods=['POST'])
def send_email(username):
    """Send email using Gmail API"""
    data = request.get_json()
    subject = data.get('subject', '')
    body = data.get('body', '')

    # Find the lead in database
    lead = Lead.query.filter_by(username=username).first()
    if not lead:
        return {"error": "Lead not found"}, 404

    if not lead.email:
        return {"error": "No email address available"}, 400

    try:
        # Setup Gmail API credentials
        creds = Credentials(
            token=None,
            refresh_token=os.environ.get('GMAIL_REFRESH_TOKEN'),
            token_uri='https://oauth2.googleapis.com/token',
            client_id=os.environ.get('GMAIL_CLIENT_ID'),
            client_secret=os.environ.get('GMAIL_CLIENT_SECRET'))

        # Refresh token if needed
        if creds.expired:
            creds.refresh(Request())

        # Build Gmail service
        service = build('gmail', 'v1', credentials=creds)

        # Create email message
        message = MIMEText(body)
        message['to'] = lead.email
        message['subject'] = subject

        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Send email
        send_result = service.users().messages().send(userId='me',
                                                      body={
                                                          'raw': raw_message
                                                      }).execute()

        # Update lead status
        lead.sent = True
        lead.sent_at = datetime.now()
        lead.subject = subject
        lead.email_body = body
        
        # Save to database
        db.session.commit()

        return {"success": True, "messageId": send_result['id']}

    except Exception as e:
        logger.error(f"Email sending failed: {e}")
        return {"error": f"Failed to send email: {str(e)}"}, 500


@app.route('/export/<format>')
def export_data(format):
    """Export data in different formats"""
    # Get leads from database
    leads = Lead.query.all()
    if not leads:
        return {"error": "No data to export"}, 400

    try:
        if format == 'csv':
            output = io.StringIO()
            writer = csv.DictWriter(output,
                                    fieldnames=[
                                        'username', 'fullName', 'bio', 'email',
                                        'phone', 'website', 'followersCount',
                                        'followingCount', 'postsCount',
                                        'isVerified'
                                    ])
            writer.writeheader()
            for lead in leads:
                lead_dict = lead.to_dict()
                writer.writerow(
                    {k: lead_dict.get(k, '')
                     for k in writer.fieldnames})

            return {
                "data":
                output.getvalue(),
                "filename":
                f"leads_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }

        elif format == 'json':
            leads_data = [lead.to_dict() for lead in leads]
            return {
                "data":
                json.dumps(leads_data, indent=2),
                "filename":
                f"leads_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            }

        else:
            return {"error": "Unsupported format"}, 400

    except Exception as e:
        logger.error(f"Export failed: {e}")
        return {"error": "Export failed"}, 500


@app.route('/clear')
def clear_data():
    """Clear all stored data"""
    try:
        # Clear all data from database
        Lead.query.delete()
        ProcessingSession.query.delete()
        HashtagUsernamePair.query.delete()
        db.session.commit()
        
        app_data['processing_status'] = None
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to clear data: {e}")
        db.session.rollback()
        return {"error": "Failed to clear data"}, 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

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
    """Call Apify actor using official client - memory optimized streaming version"""
    client = ApifyClient(token)
    
    try:
        # Run the Actor and wait for it to finish
        run = client.actor(actor_id).call(run_input=input_data)
        
        # Extreme memory optimization to prevent SIGKILL
        max_items = 50   # Drastically reduced from 100 to 50
        batch_size = 10  # Reduced batch size from 20 to 10
        processing_delay = 0.8  # Increased delay to reduce memory pressure
        
        dataset = client.dataset(run["defaultDatasetId"])
        
        # Stream process with immediate username extraction - no item storage
        all_usernames = set()  # Use set for automatic deduplication
        total_processed = 0
        
        # Use smaller chunks and more frequent garbage collection
        import gc
        
        logger.info(f"Starting streaming extraction with max_items={max_items}")
        
        for item in dataset.iterate_items():
            if total_processed >= max_items:
                logger.info(f"Reached maximum item limit of {max_items} for memory safety")
                break
            
            # Extract usernames immediately without storing the item
            if isinstance(item, dict):
                # Extract from latestPosts
                if 'latestPosts' in item and isinstance(item['latestPosts'], list):
                    for post in item['latestPosts']:
                        if isinstance(post, dict) and 'ownerUsername' in post:
                            username = post['ownerUsername']
                            if username and isinstance(username, str):
                                all_usernames.add(username)
                
                # Extract from topPosts
                if 'topPosts' in item and isinstance(item['topPosts'], list):
                    for post in item['topPosts']:
                        if isinstance(post, dict) and 'ownerUsername' in post:
                            username = post['ownerUsername']
                            if username and isinstance(username, str):
                                all_usernames.add(username)
            
            total_processed += 1
            
            # Aggressive memory cleanup
            if total_processed % batch_size == 0:
                gc.collect()  # Force garbage collection
                import time
                time.sleep(processing_delay)
                logger.debug(f"Processed {total_processed} items, found {len(all_usernames)} unique usernames")
        
        # Convert set to list of profile objects
        processed_items = [{'ownerUsername': username} for username in all_usernames]
        
        # Final cleanup
        gc.collect()
        logger.info(f"Streaming extraction completed: {len(all_usernames)} unique usernames from {total_processed} items")
        
        return {"items": processed_items}
        
    except Exception as e:
        logger.error(f"Apify actor call failed: {e}")
        return {"items": []}


async def call_perplexity_api(profile_info, api_key):
    """Call Perplexity API to find contact information using full profile data"""
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Build comprehensive profile information for better search results
    username = profile_info.get('username', '')
    full_name = profile_info.get('full_name', '')
    biography = profile_info.get('biography', '')
    followers = profile_info.get('follower_count', 0)
    following = profile_info.get('following_count', 0)
    posts = profile_info.get('media_count', 0)
    is_verified = profile_info.get('is_verified', False)
    
    # Create detailed profile description
    profile_description = f"""
    Instagram Profile Information:
    - Username: {username}
    - Full Name: {full_name}
    - Biography: {biography}
    - Followers: {followers}
    - Following: {following}
    - Posts: {posts}
    - Verified: {is_verified}
    """

    data = {
        "model": "sonar",
        "messages": [
            {
                "role": "system",
                "content": "Du bist ein hilfreicher Recherche-Assistent, finde öffentlich verfügbare Kontaktinfos. Verwende die bereitgestellten Profilinformationen um bessere Suchergebnisse zu erzielen."
            },
            {
                "role": "user",
                "content": f"Basierend auf diesen Instagram-Profilinformationen, suche nach E-Mail-Adresse, Telefonnummer oder Website:\n\n{profile_description}\n\nSuche nach öffentlich verfügbaren Kontaktinformationen für diese Person/dieses Unternehmen. Antworte nur als JSON: {{ \"email\": \"...\", \"phone\": \"...\", \"website\": \"...\" }}"
            }
        ],
        "temperature": 0.2,
        "stream": False
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()

            try:
                content = result['choices'][0]['message']['content']
                logger.info(f"Perplexity API raw response for {username}: {content}")
                print(f"=== PERPLEXITY API RESPONSE FOR {username} ===")
                print(f"Full result: {json.dumps(result, indent=2)}")
                print(f"Content: {content}")
                print("=" * 50)
                
                # Try to parse JSON from the response
                contact_info = json.loads(content)
                logger.info(f"Perplexity API parsed contact info for {username}: {contact_info}")
                print(f"Parsed contact info: {contact_info}")
                return contact_info
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(
                    f"Failed to parse Perplexity response for {username}: {e}")
                logger.error(f"Raw response content: {content if 'content' in locals() else 'No content'}")
                print(f"=== PERPLEXITY PARSING ERROR FOR {username} ===")
                print(f"Error: {e}")
                print(f"Raw content: {content if 'content' in locals() else 'No content'}")
                print("=" * 50)
                return {"email": "", "phone": "", "website": ""}
        except httpx.HTTPStatusError as e:
            logger.error(f"Perplexity API HTTP error for {username}: {e.response.status_code} - {e.response.text}")
            return {"email": "", "phone": "", "website": ""}
        except Exception as e:
            logger.error(f"Perplexity API error for {username}: {e}")
            return {"email": "", "phone": "", "website": ""}


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


def call_apify_profile_enrichment(actor_id, input_data, token):
    """Call Apify profile enrichment actor - returns profile data directly"""
    client = ApifyClient(token)
    
    try:
        # Run the Actor and wait for it to finish
        run = client.actor(actor_id).call(run_input=input_data)
        
        # Get the dataset
        dataset = client.dataset(run["defaultDatasetId"])
        
        # The profile enrichment API returns profiles directly
        profiles = []
        for item in dataset.iterate_items():
            if isinstance(item, dict):
                profiles.append(item)
        
        logger.info(f"Profile enrichment API returned {len(profiles)} profiles")
        return profiles
        
    except Exception as e:
        logger.error(f"Apify profile enrichment call failed: {e}")
        return []


async def enrich_profile_batch(usernames, ig_sessionid, apify_token,
                               perplexity_key, semaphore):
    """Enrich a batch of profiles with concurrent processing"""
    async with semaphore:
        try:
            # Call Apify profile enrichment actor with correct format
            instagram_urls = [f"https://www.instagram.com/{username}" for username in usernames]
            input_data = {
                "instagram_ids": instagram_urls,
                "SessionID": ig_sessionid,
                "proxy": {
                    "useApifyProxy": True,
                    "groups": ["RESIDENTIAL"],
                }
            }

            # Use dedicated profile enrichment function
            profile_items = call_apify_profile_enrichment("8WEn9FvZnhE7lM3oA",
                                                          input_data, apify_token)
            enriched_profiles = []

            # Create a mapping of username to profile data
            profile_map = {}
            for item in profile_items:
                # The API returns username field directly
                if 'username' in item:
                    profile_map[item['username']] = item
                # Also check URL field as fallback
                elif 'URL' in item:
                    url = item['URL']
                    username_from_url = url.rstrip('/').split('/')[-1]
                    profile_map[username_from_url] = item

            for username in usernames:
                profile_info = profile_map.get(username, {})

                # Always try to enrich contact info with Perplexity for missing data
                perplexity_contact = {}
                if not any([
                        profile_info.get('public_email'),
                        profile_info.get('contact_phone_number'),
                        profile_info.get('external_url')
                ]):
                    try:
                        # Pass full profile info instead of just username
                        profile_with_username = dict(profile_info)
                        profile_with_username['username'] = username
                        perplexity_contact = await call_perplexity_api(
                            profile_with_username, perplexity_key)
                        logger.info(f"Perplexity enrichment for {username}: {perplexity_contact}")
                    except Exception as e:
                        logger.error(f"Perplexity API failed for {username}: {e}")

                # Log the profile info we got from Apify for debugging
                if profile_info:
                    logger.info(f"Apify profile data for {username}: found with {profile_info.get('follower_count', 0)} followers")
                else:
                    logger.info(f"Apify profile data for {username}: not found in response")

                enriched_profiles.append({
                    'username':
                    username,
                    'full_name':
                    profile_info.get('full_name', ''),
                    'biography':
                    profile_info.get('biography', ''),
                    'public_email':
                    profile_info.get('public_email', '') or perplexity_contact.get('email', ''),
                    'contact_phone_number':
                    profile_info.get('contact_phone_number', '') or perplexity_contact.get('phone', ''),
                    'external_url':
                    profile_info.get('external_url', '') or perplexity_contact.get('website', ''),
                    'follower_count':
                    profile_info.get('follower_count', 0),
                    'following_count':
                    profile_info.get('following_count', 0),
                    'media_count':
                    profile_info.get('media_count', 0),
                    'is_verified':
                    profile_info.get('is_verified', False),
                    'profile_pic_url':
                    profile_info.get('profile_pic_url', ''),
                    'address_street':
                    profile_info.get('address_street', ''),
                    'city_name':
                    profile_info.get('city_name', ''),
                    'zip':
                    profile_info.get('zip', ''),
                    'latitude':
                    profile_info.get('latitude'),
                    'longitude':
                    profile_info.get('longitude'),
                    'subject':
                    '',
                    'emailBody':
                    '',
                    'sent':
                    False,
                    'sentAt':
                    None
                })

            return enriched_profiles

        except Exception as e:
            logger.error(f"Failed to enrich profiles {usernames}: {e}")
            return []


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
    enrich_limit = data.get('enrichLimit', 25)  # New parameter for testing

    if not keyword:
        return {"error": "Keyword is required"}, 400
    
    # Validate search limit - further reduced maximum to prevent memory issues
    try:
        search_limit = int(search_limit)
        if search_limit < 1 or search_limit > 50:  # Reduced from 100 to 50 for memory safety
            return {"error": "Search limit must be between 1 and 50"}, 400
    except (ValueError, TypeError):
        return {"error": "Invalid search limit value"}, 400
    
    # Validate enrich limit for testing purposes
    try:
        enrich_limit = int(enrich_limit)
        if enrich_limit < 1 or enrich_limit > 25:
            return {"error": "Enrich limit must be between 1 and 25"}, 400
    except (ValueError, TypeError):
        return {"error": "Invalid enrich limit value"}, 400

    ig_sessionid = session.get('ig_sessionid') or os.environ.get(
        'IG_SESSIONID')
    if not ig_sessionid:
        return {"error": "Instagram Session ID not found. Please provide your Instagram session ID first."}, 400

    # Start processing in background using ThreadPoolExecutor
    app_data['processing_status'] = 'Processing...'

    try:
        # Run the async processing in a thread pool with memory optimization
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_async_process, keyword, ig_sessionid, search_limit, enrich_limit)
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


def run_async_process(keyword, ig_sessionid, search_limit, enrich_limit):
    """Run async processing in a separate thread"""
    try:
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                process_keyword_async(keyword, ig_sessionid, search_limit, enrich_limit))
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"Async processing failed: {e}")
        raise


async def process_keyword_async(keyword, ig_sessionid, search_limit, enrich_limit):
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

    # Step 3: Profile enrichment with aggressive memory optimization
    semaphore = asyncio.Semaphore(20)  # Further reduced to 2 concurrent calls
    perplexity_semaphore = asyncio.Semaphore(1)  # Reduced to 1 concurrent Perplexity call

    # Extreme memory safety measures to prevent SIGKILL
    usernames = [p['username'] for p in unique_profiles]
    batch_size = 2  # Further reduced batch size from 3 to 2 for memory safety
    
    # Use enrich_limit parameter to control how many profiles to enrich (for testing)
    if len(usernames) > enrich_limit:
        logger.info(f"Limiting usernames from {len(usernames)} to {enrich_limit} for testing (enrich_limit)")
        usernames = usernames[:enrich_limit]
    
    batches = [
        usernames[i:i + batch_size]
        for i in range(0, len(usernames), batch_size)
    ]

    # Process batches sequentially to minimize memory usage
    total_saved_leads = 0
    import gc
    
    for i, batch in enumerate(batches):
        try:
            logger.info(f"Processing batch {i+1}/{len(batches)} with {len(batch)} usernames")
            
            # Process one batch at a time
            result = await enrich_profile_batch(batch, ig_sessionid, apify_token,
                                              perplexity_key, semaphore)
            
            if isinstance(result, list) and result:
                # Mark duplicates and add hashtag information for this batch
                for lead in result:
                    if lead['username'] in duplicates:
                        lead['is_duplicate'] = True
                    else:
                        lead['is_duplicate'] = False
                    # Use search keyword as hashtag
                    lead['hashtag'] = keyword
                
                # Save this batch immediately to prevent data loss
                saved_count = save_leads_incrementally(result, keyword)
                total_saved_leads += saved_count
                logger.info(f"Batch {i+1}: Saved {saved_count} leads incrementally")
            else:
                logger.warning(f"Batch {i+1}: No results or unexpected type: {type(result)}")
            
            # Force garbage collection after each batch
            gc.collect()
            
            # Add delay between batches to reduce memory pressure
            import time
            time.sleep(1.0)  # Increased delay to reduce memory pressure
            
        except Exception as e:
            logger.error(f"Batch {i+1} processing error: {e}")
            # Continue processing other batches even if one fails
            continue

    logger.info(f"Total enrichment complete: {total_saved_leads} leads saved to database")
    
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
        # Generate subject in German
        subject_response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "system",
                "content": "Erstelle eine ansprechende deutsche Betreffzeile für eine professionelle Outreach-E-Mail von Kasimir vom Store KasimirLieselotte. Die Betreffzeile sollte persönlich sein. Antworte im JSON-Format: {\"subject\": \"betreff text\"}"
            }, {
                "role":
                "user",
                "content":
                f"Profil: @{lead.username}, Name: {lead.full_name}, Bio: {lead.bio}"
            }],
            response_format={"type": "json_object"},
            max_tokens=100)

        # Generate body in German with KasimirLieselotte branding
        body_response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role":
                "system",
                "content": "Erstelle eine personalisierte, professionelle deutsche E-Mail, ohne die Betreffzeile, für potenzielle Kooperationen. Die E-Mail kommt von Kasimir vom Store KasimirLieselotte. Verwende einen höflichen, professionellen Ton auf Deutsch aber in DU-Form um es casual im Instagram feel zu bleiben. Füge am Ende die Signatur mit der Website https://www.kasimirlieselotte.de/ hinzu. Antworte im JSON-Format: {\"body\": \"email inhalt\"}"
            }, {
                "role":
                "user",
                "content":
                f"Profil: @{lead.username}, Name: {lead.full_name}, Bio: {lead.bio}, Email: {lead.email}"
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

import os
import asyncio
import logging
import json
import hashlib
import random
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import httpx
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
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
from models import db, Lead, ProcessingSession, HashtagUsernamePair, LeadBackup, EmailTemplate, Product
db.init_app(app)

# Initialize OpenAI client
# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Create database tables
with app.app_context():
    db.create_all()

    # Initialize default email templates if they don't exist
    def initialize_default_templates():
        """Initialize default email templates if they don't exist"""
        default_subject_template = 'Schreibe in DU-Form eine persönliche Betreffzeile mit freundlichen Hook für eine Influencer Kooperation mit Kasimir + Liselotte. Nutze persönliche Infos (z.B. Username, BIO, Interessen), sprich sie direkt in DU-Form. Falls ein Produkt ausgewählt ist, erwähne es subtil in der Betreffzeile. Antworte im JSON-Format: {"subject": "betreff text"}'
        default_body_template = 'Erstelle eine personalisierte, professionelle deutsche E-Mail, ohne die Betreffzeile, für potenzielle Instagram Influencer Kooperationen. Die E-Mail kommt von Kasimir vom Store KasimirLieselotte. Verwende einen höflichen, professionellen Ton auf Deutsch aber in DU-Form um es casual im Instagram feel zu bleiben. WICHTIG: Falls ein Produkt ausgewählt ist, integriere unbedingt folgende Elemente in die E-Mail: 1) Erwähne das Produkt namentlich, 2) Füge den direkten Link zum Produkt ein (Produkt-URL), 3) Erkläre kurz die Produkteigenschaften basierend auf der Beschreibung, 4) Beziehe das Produkt auf die Bio/Interessen des Influencers. Die E-Mail sollte den Produktlink natürlich in den Text einbetten. Füge am Ende die Signatur mit der Website https://www.kasimirlieselotte.de/ hinzu. Antworte im JSON-Format: {"body": "email inhalt"}'

        # Check if subject template exists
        subject_template = EmailTemplate.query.filter_by(name='subject').first()
        if not subject_template:
            subject_template = EmailTemplate(name='subject', template=default_subject_template)
            db.session.add(subject_template)

        # Check if body template exists
        body_template = EmailTemplate.query.filter_by(name='body').first()
        if not body_template:
            body_template = EmailTemplate(name='body', template=default_body_template)
            db.session.add(body_template)

        db.session.commit()

    initialize_default_templates()

    # Initialize default products if they don't exist
    def initialize_default_products():
        """Initialize default product catalog if it doesn't exist"""
        default_products = [
            {
                'name': 'Zeck Zack',
                'url': 'https://www.kasimirlieselotte.de/shop/Zeck-Zack-Spray-50-ml-kaufen',
                'image_url': '/static/product-zeck-zack.jpg',
                'description': 'Zeck Zack Spray 50ml - 100% rein ohne Zusatzstoffe - Hergestellt in Deutschland',
                'price': '50 ml'
            },
            {
                'name': 'Funghi Funk',
                'url': 'https://www.kasimirlieselotte.de/shop/Funghi-Funk-Spray-50-ml-kaufen',
                'image_url': '/static/product-funghi-funk.jpg',
                'description': 'Funghi Funk Spray 50ml - 100% rein - Hergestellt in Deutschland',
                'price': '50 ml'
            }
        ]

        for product_data in default_products:
            existing_product = Product.query.filter_by(name=product_data['name']).first()
            if not existing_product:
                product = Product(
                    name=product_data['name'],
                    url=product_data['url'],
                    image_url=product_data['image_url'],
                    description=product_data['description'],
                    price=product_data['price']
                )
                db.session.add(product)

        db.session.commit()

    initialize_default_products()

# Global storage for processing status (only for status, data is in DB)
app_data = {
    'processing_status': None,
    'processing_progress': {
        'current_step': '',
        'total_steps': 0,
        'completed_steps': 0,
        'estimated_time_remaining': 0
    },
    'start_time': time.time(),  # Track application startup time
    'stop_requested': False  # Flag to request processing stop
}


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
    # Start tracking this API call
    call_id = None

    start_time = time.time()
    client = ApifyClient(token)
    
    # Extract keyword from input_data for fallback hashtag
    keyword = input_data.get('search', 'unknown')

    # Add random delay before Apify call to avoid anti-spam measures
    delay = random.uniform(1, 10)
    logger.info(f"Anti-spam delay: {delay:.1f}s before Apify hashtag search")
    time.sleep(delay)

    try:
        # Run the Actor and wait for it to finish
        run = client.actor(actor_id).call(run_input=input_data)

        # Extreme memory optimization to prevent SIGKILL
        max_items = 50   # Drastically reduced from 100 to 50
        batch_size = 10  # Reduced batch size from 20 to 10
        processing_delay = 0.8  # Increased delay to reduce memory pressure

        dataset = client.dataset(run["defaultDatasetId"])

        # Stream process with immediate username and hashtag extraction
        username_hashtag_map = {}  # Map username to hashtag for deduplication
        total_processed = 0

        # Use smaller chunks and more frequent garbage collection
        import gc

        logger.info(f"Starting streaming extraction with max_items={max_items}")

        for item in dataset.iterate_items():
            if total_processed >= max_items:
                logger.info(f"Reached maximum item limit of {max_items} for memory safety")
                break

            # Extract usernames and hashtags from posts
            if isinstance(item, dict):
                # Get the hashtag ID from the item
                hashtag_id = item.get('id') or item.get('ID') or item.get('hashtag') or item.get('name') or keyword
                
                # Debug log to see what fields are available
                if total_processed == 0:
                    logger.info(f"First item keys: {list(item.keys())}")
                    logger.info(f"Hashtag ID extracted: {hashtag_id}")
                
                # Extract from latestPosts
                if 'latestPosts' in item and isinstance(item['latestPosts'], list):
                    for post in item['latestPosts']:
                        if isinstance(post, dict) and 'ownerUsername' in post:
                            username = post['ownerUsername']
                            if username and isinstance(username, str):
                                # Store with hashtag ID
                                username_hashtag_map[username] = hashtag_id

                # Extract from topPosts
                if 'topPosts' in item and isinstance(item['topPosts'], list):
                    for post in item['topPosts']:
                        if isinstance(post, dict) and 'ownerUsername' in post:
                            username = post['ownerUsername']
                            if username and isinstance(username, str):
                                # Store with hashtag ID
                                username_hashtag_map[username] = hashtag_id

            total_processed += 1

            # Aggressive memory cleanup
            if total_processed % batch_size == 0:
                gc.collect()  # Force garbage collection
                time.sleep(processing_delay)
                logger.debug(f"Processed {total_processed} items, found {len(username_hashtag_map)} unique usernames")

        # Convert map to list of profile objects with hashtag
        processed_items = [{'username': username, 'hashtag': hashtag} 
                          for username, hashtag in username_hashtag_map.items()]

        # Final cleanup
        gc.collect()

        # Log successful completion
        logger.info(f"Streaming extraction completed: {len(username_hashtag_map)} unique usernames from {total_processed} items")
        return {"items": processed_items}

    except Exception as e:
        # Log the failure with detailed error information
        logger.error(f"Apify hashtag search failed: {e}")
        return {"items": []}


async def call_perplexity_api(profile_info, api_key):
    """Call Perplexity API to find contact information using full profile data"""
    username = profile_info.get('username', '')

    # Start tracking this API call
    call_id = None

    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Build comprehensive profile information for better search results
    full_name = profile_info.get('full_name', '')
    biography = profile_info.get('biography', '')
    followers = profile_info.get('follower_count', 0)
    following = profile_info.get('following_count', 0)
    posts = profile_info.get('media_count', 0)
    is_verified = profile_info.get('is_verified', False)

    # Extract existing contact information from the lead database
    existing_email = profile_info.get('email', '') or profile_info.get('public_email', '')
    existing_phone = profile_info.get('phone', '') or profile_info.get('contact_phone_number', '')
    existing_website = profile_info.get('website', '') or profile_info.get('external_url', '')

    # Create detailed profile description including existing contact info
    profile_description = f"""
    Instagram Profile Information:
    - Username: {username}
    - Full Name: {full_name}
    - Biography: {biography}
    - Followers: {followers}
    - Following: {following}
    - Posts: {posts}
    - Verified: {is_verified}

    Existing Contact Information:
    - Email: {existing_email if existing_email else 'Not found'}
    - Phone: {existing_phone if existing_phone else 'Not found'}
    - Website: {existing_website if existing_website else 'Not found'}
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
                "content": f"Basierend auf diesen Instagram-Profilinformationen, suche nach E-Mail-Adresse, Telefonnummer oder Website:\n\n{profile_description}\n\nWICHTIG: Falls eine Webseite vorhanden ist, durchsuche sie nach telefon und email Kontaktdaten.. Suche nur nach fehlenden Informationen. Wenn eine Website, Email oder Telefonnummer bereits bekannt ist, gib diese zurück und suche nach den fehlenden Daten. Antworte nur als JSON: {{\"full_name\": \"...\", \"email\": \"...\", \"phone\": \"...\", \"website\": \"...\" }}"
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

                # Try to extract JSON from the response (may contain additional text)
                # Find the first { and matching } to extract just the JSON part
                json_start = content.find('{')
                if json_start != -1:
                    # Find the matching closing brace
                    brace_count = 0
                    json_end = json_start
                    for i, char in enumerate(content[json_start:], json_start):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                json_end = i + 1
                                break

                    json_content = content[json_start:json_end]
                    contact_info = json.loads(json_content)

                    # Merge existing contact info with new findings
                    # Prioritize existing data from the lead database
                    merged_contact = {
                        "email": existing_email or contact_info.get("email", ""),
                        "phone": existing_phone or contact_info.get("phone", ""),
                        "website": existing_website or contact_info.get("website", "")
                    }

                    # Log successful completion
                    logger.info(f"Perplexity API enrichment for {username}: found {sum(1 for v in contact_info.values() if v)} new fields")
                    return merged_contact
                else:
                    # No JSON found, return existing contact info if available
                    logger.warning(f"No JSON found in Perplexity response for {username}")
                    return {
                        "email": existing_email or "",
                        "phone": existing_phone or "",
                        "website": existing_website or ""
                    }
            except (json.JSONDecodeError, KeyError) as e:
                # Log parsing failure
                logger.error(f"Failed to parse Perplexity response for {username}: {e}")
                return {
                    "email": existing_email or "",
                    "phone": existing_phone or "",
                    "website": existing_website or ""
                }
        except httpx.HTTPStatusError as e:
            # Log HTTP error
            
            return {
                "email": existing_email or "",
                "phone": existing_phone or "",
                "website": existing_website or ""
            }
        except Exception as e:
            # Log general error
            logger.error(f"Perplexity API error for {username}: {e}")
            return {
                "email": existing_email or "",
                "phone": existing_phone or "",
                "website": existing_website or ""
            }


def backup_lead_to_backup_table(lead):
    """Create a backup copy of a lead in the LeadBackup table"""
    try:
        backup_lead = LeadBackup(
            original_lead_id=lead.id,
            username=lead.username,
            hashtag=lead.hashtag,
            full_name=lead.full_name,
            bio=lead.bio,
            email=lead.email,
            phone=lead.phone,
            website=lead.website,
            followers_count=lead.followers_count,
            following_count=lead.following_count,
            posts_count=lead.posts_count,
            is_verified=lead.is_verified,
            profile_pic_url=lead.profile_pic_url,
            is_duplicate=lead.is_duplicate,
            address_street=lead.address_street,
            city_name=lead.city_name,
            zip=lead.zip,
            latitude=lead.latitude,
            longitude=lead.longitude,
            subject=lead.subject,
            email_body=lead.email_body,
            sent=lead.sent,
            sent_at=lead.sent_at,
            original_created_at=lead.created_at,
            original_updated_at=lead.updated_at
        )
        db.session.add(backup_lead)
        db.session.commit()
        logger.info(f"Backed up lead {lead.username} to backup table")
        return True
    except Exception as e:
        logger.error(f"Failed to backup lead {lead.username}: {e}")
        db.session.rollback()
        return False


def save_leads_incrementally(enriched_leads, keyword, default_product_id=None):
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

                        # Create backup before updating
                        backup_lead_to_backup_table(existing_lead)

                        current_lead = existing_lead
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
                            is_duplicate=lead_data.get('is_duplicate', False),
                            selected_product_id=default_product_id  # Apply default product from session
                        )
                        db.session.add(new_lead)
                        current_lead = new_lead

                    # Commit each lead immediately
                    db.session.commit()

                    # Create backup after successful save
                    backup_lead_to_backup_table(current_lead)

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
    # Start tracking this API call
    usernames = input_data.get('instagram_ids', [])
    username_count = len(usernames) if isinstance(usernames, list) else 1

    call_id = None

    client = ApifyClient(token)

    # Add random delay before Apify call to avoid anti-spam measures
    delay = random.uniform(1, 10)
    logger.info(f"Anti-spam delay: {delay:.1f}s before Apify profile enrichment...")
    time.sleep(delay)

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

        # Log successful completion

        logger.info(f"Profile enrichment API returned {len(profiles)} profiles for {username_count} requested usernames")
        return profiles

    except Exception as e:
        # Log the failure
        logger.error(f"Profile enrichment API error: {e}")
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
                # Check if any contact info is missing (not all fields need to be empty)
                missing_email = not profile_info.get('public_email')
                missing_phone = not profile_info.get('contact_phone_number') 
                missing_website = not profile_info.get('external_url')

                if missing_email or missing_phone or missing_website:
                    try:
                        # Update progress to show Perplexity enrichment in progress
                        current_progress = app_data.get('processing_progress', {})
                        if 'current_batch' in current_progress:
                            batch_num = current_progress['current_batch']
                            total_batches = current_progress.get('total_batches', 1)
                            current_progress['current_step'] = f'2.1 Erweitere Kontaktdaten mit Perplexity für @{username} (Batch {batch_num}/{total_batches})'

                        # Pass full profile info instead of just username
                        profile_with_username = dict(profile_info)
                        profile_with_username['username'] = username
                        # Add existing contact info to the profile for API context
                        profile_with_username['email'] = profile_info.get('public_email', '')
                        profile_with_username['phone'] = profile_info.get('contact_phone_number', '')
                        profile_with_username['website'] = profile_info.get('external_url', '')

                        perplexity_contact = await call_perplexity_api(
                            profile_with_username, perplexity_key)
                        logger.info(f"Perplexity enrichment for {username}: {perplexity_contact}")
                        logger.info(f"Missing fields for {username}: email={missing_email}, phone={missing_phone}, website={missing_website}")
                    except Exception as e:
                        logger.error(f"Perplexity API failed for {username}: {e}")

                # Log the profile info we got from Apify for debugging
                if profile_info:
                    logger.info(f"Apify profile data for {username}: found with {profile_info.get('follower_count', 0)} followers")
                else:
                    logger.info(f"Apify profile data for {username}: not found in response")

                # Try multiple possible field names for follower count
                follower_count = (
                    profile_info.get('follower_count', 0) or 
                    profile_info.get('followers_count', 0) or 
                    profile_info.get('followers', 0) or 
                    profile_info.get('followerCount', 0) or 0
                )

                following_count = (
                    profile_info.get('following_count', 0) or 
                    profile_info.get('followings_count', 0) or 
                    profile_info.get('following', 0) or 
                    profile_info.get('followingCount', 0) or 0
                )

                media_count = (
                    profile_info.get('media_count', 0) or 
                    profile_info.get('posts_count', 0) or 
                    profile_info.get('posts', 0) or 
                    profile_info.get('postsCount', 0) or 0
                )

                # Log what we found for debugging
                logger.info(f"Follower count mapping for {username}: follower_count={follower_count}, following_count={following_count}, media_count={media_count}")

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
                    follower_count,
                    'following_count':
                    following_count,
                    'media_count':
                    media_count,
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

    # Get email templates
    subject_template = EmailTemplate.query.filter_by(name='subject').first()
    body_template = EmailTemplate.query.filter_by(name='body').first()

    templates = {
        'subject': subject_template.template if subject_template else '',
        'body': body_template.template if body_template else ''
    }

    # Get products
    products = Product.query.all()
    products_dict = [product.to_dict() for product in products]

    return render_template('index.html',
                           ig_sessionid=ig_sessionid,
                           leads=leads_dict,
                           processing_status=app_data['processing_status'],
                           email_templates=templates,
                           products=products_dict,
                           default_product_id=session.get('default_product_id'))


@app.route('/ping')
def ping():
    """Health check endpoint"""
    return {"status": "OK"}, 200


@app.route('/progress')
def get_progress():
    """Get current processing progress"""
    return jsonify(app_data['processing_progress'])


@app.route('/api/leads')
def get_leads_by_keyword():
    """Get leads filtered by keyword for real-time table updates"""
    keyword = request.args.get('keyword', '').strip()

    if not keyword:
        return {"error": "Keyword parameter is required"}, 400

    try:
        leads = Lead.query.filter_by(hashtag=keyword).order_by(Lead.created_at.desc()).all()
        return {"leads": [lead.to_dict() for lead in leads]}
    except Exception as e:
        logger.error(f"Failed to query leads by keyword: {e}")
        return {"error": "Failed to retrieve leads"}, 500


@app.route('/api-metrics')
def get_api_metrics():
    """Get comprehensive API call metrics and performance data"""
    time_window = request.args.get('time_window', 60, type=int)  # Default 60 minutes

    try:
        metrics_summary = {'total_calls': 0, 'success_calls': 0, 'failed_calls': 0, 'success_rate': 100.0, 'avg_response_time': 0.0}

        # Add additional system information
        metrics_summary.update({
            "system_info": {
                "log_file_exists": os.path.exists('api_debug.log'),
                "current_time": datetime.utcnow().isoformat(),
                "uptime_minutes": int((time.time() - app_data.get('start_time', time.time())) / 60)
            }
        })

        return jsonify(metrics_summary)
    except Exception as e:
        return jsonify({"error": "Failed to retrieve API metrics", "details": str(e)}), 500


@app.route('/api-health')
def get_api_health():
    """Get API health status and recent error trends"""
    try:
        # Get recent metrics
        recent_metrics = {'total_calls': 0, 'success_calls': 0, 'failed_calls': 0, 'success_rate': 100.0, 'avg_response_time': 0.0}

        # Determine health status
        if recent_metrics.get('total_calls', 0) == 0:
            health_status = "IDLE"
        elif recent_metrics.get('success_rate', 0) >= 90:
            health_status = "HEALTHY"
        elif recent_metrics.get('success_rate', 0) >= 70:
            health_status = "WARNING"
        else:
            health_status = "CRITICAL"

        # Get database status
        db_healthy = True
        try:
            db.session.execute(db.text('SELECT 1'))
            db.session.commit()
        except Exception as e:
            db_healthy = False
            logger.error(f"Database health check failed: {e}")

        health_info = {
            "status": health_status,
            "timestamp": datetime.utcnow().isoformat(),
            "api_metrics": recent_metrics,
            "database_healthy": db_healthy,
            "services": {
                "apify": "available" if os.environ.get("APIFY_TOKEN") else "no_token",
                "perplexity": "available" if os.environ.get("PERPLEXITY_API_KEY") else "no_token", 
                "openai": "available" if os.environ.get("OPENAI_API_KEY") else "no_token",
                "instagram_session": "configured" if session.get('ig_sessionid') else "not_configured"
            }
        }
        return jsonify(health_info)
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500


@app.route('/debug-logs')
def get_debug_logs():
    """Get recent debug logs from the log file"""
    try:
        lines = request.args.get('lines', 100, type=int)
        log_file = 'api_debug.log'

        if not os.path.exists(log_file):
            return jsonify({"logs": [], "message": "Log file not found"})

        # Read last N lines from log file
        with open(log_file, 'r') as f:
            log_lines = f.readlines()

        # Get the last N lines
        recent_logs = log_lines[-lines:] if len(log_lines) > lines else log_lines

        # Parse JSON logs
        parsed_logs = []
        for line in recent_logs:
            try:
                log_entry = json.loads(line.strip())
                parsed_logs.append(log_entry)
            except json.JSONDecodeError:
                # If not JSON, treat as plain text
                parsed_logs.append({"raw_log": line.strip()})

        return jsonify({
            "logs": parsed_logs,
            "total_lines": len(log_lines),
            "returned_lines": len(parsed_logs)
        })
    except Exception as e:
        return jsonify({"error": "Failed to retrieve logs", "details": str(e)}), 500


@app.route('/debug')
def debug_dashboard():
    """Render the debug dashboard for API monitoring"""
    return render_template('debug_dashboard.html')


@app.route('/set-session', methods=['POST'])
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

    # Get default product ID from session before starting background processing
    default_product_id = session.get('default_product_id')

    # Start processing in background using ThreadPoolExecutor
    app_data['processing_status'] = 'Processing...'
    app_data['stop_requested'] = False  # Reset stop flag

    try:
        # Run hashtag discovery only - no enrichment yet
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(discover_hashtags_sync, keyword, ig_sessionid, search_limit)
            try:
                hashtag_variants = future.result(timeout=180)  # Reduced to 3 minutes
            except TimeoutError:
                logger.error("Hashtag discovery timed out after 3 minutes")
                app_data['processing_status'] = None
                return {"error": "Hashtag discovery timed out. Please try with a smaller search limit."}, 408

        # Store hashtag variants in app_data for later enrichment
        app_data['hashtag_variants'] = hashtag_variants
        app_data['keyword'] = keyword
        app_data['ig_sessionid'] = ig_sessionid
        app_data['search_limit'] = search_limit
        app_data['default_product_id'] = default_product_id
        app_data['processing_status'] = 'hashtag_selection'  # New status
        
        return {"success": True, "phase": "hashtag_selection", "hashtag_variants": hashtag_variants}

    except Exception as e:
        logger.error(f"Processing failed: {e}")
        app_data['processing_status'] = None

        # Get any partial results from database before failing
        try:
            with app.app_context():
                partial_leads = Lead.query.filter_by(hashtag=keyword).order_by(Lead.created_at.desc()).all()
                partial_count = len(partial_leads)
                if partial_count > 0:
                    # Return partial results with error information
                    return {
                        "error": str(e), 
                        "partial_success": True,
                        "leads": [lead.to_dict() for lead in partial_leads],
                        "partial_count": partial_count
                    }, 206  # Partial Content status
                else:
                    return {"error": str(e)}, 500
        except Exception as db_error:
            logger.error(f"Failed to query partial leads: {db_error}")
            return {"error": str(e)}, 500


@app.route('/stop-processing', methods=['POST'])
def stop_processing():
    """Stop current processing"""
    try:
        app_data['stop_requested'] = True
        app_data['processing_status'] = 'Stopping...'
        
        # Update progress to show stopping
        app_data['processing_progress']['current_step'] = 'Stoppe Verarbeitung...'
        app_data['processing_progress']['final_status'] = 'stopped'
        
        logger.info("Stop requested by user")
        return jsonify({"success": True, "message": "Stopp-Anfrage gesendet"})
    except Exception as e:
        logger.error(f"Failed to stop processing: {e}")
        return jsonify({"error": "Fehler beim Stoppen"}), 500


@app.route('/api/hashtag-variants', methods=['GET'])
def get_hashtag_variants():
    """Get discovered hashtag variants"""
    try:
        variants = app_data.get('hashtag_variants', [])
        if not variants:
            return jsonify({"error": "No hashtag variants found"}), 404
        
        # Don't send full username lists to frontend, just counts
        simplified_variants = []
        for variant in variants:
            simplified_variants.append({
                'hashtag': variant['hashtag'],
                'user_count': variant['user_count']
            })
        
        return jsonify({
            'success': True,
            'hashtag_variants': simplified_variants,
            'keyword': app_data.get('keyword', '')
        })
    except Exception as e:
        logger.error(f"Failed to get hashtag variants: {e}")
        return jsonify({"error": "Failed to get hashtag variants"}), 500


@app.route('/continue-enrichment', methods=['POST'])
def continue_enrichment():
    """Continue with enrichment for selected hashtags"""
    try:
        data = request.get_json()
        selected_hashtags = data.get('selected_hashtags', [])
        
        if not selected_hashtags:
            return jsonify({"error": "No hashtags selected"}), 400
        
        # Get stored data
        hashtag_variants = app_data.get('hashtag_variants', [])
        keyword = app_data.get('keyword', '')
        ig_sessionid = app_data.get('ig_sessionid', '')
        search_limit = app_data.get('search_limit', 100)
        default_product_id = app_data.get('default_product_id')
        
        if not hashtag_variants:
            return jsonify({"error": "No hashtag data found. Please run hashtag search first."}), 400
        
        # Filter to only selected hashtags
        selected_profiles = []
        for variant in hashtag_variants:
            if variant['hashtag'] in selected_hashtags:
                # Add all usernames from this hashtag variant
                for username in variant['usernames']:
                    selected_profiles.append({
                        'username': username,
                        'hashtag': variant['hashtag']
                    })
        
        logger.info(f"Selected {len(selected_profiles)} profiles from {len(selected_hashtags)} hashtags")
        
        # Reset processing status
        app_data['processing_status'] = 'Processing...'
        app_data['stop_requested'] = False
        
        # Start enrichment in background
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_enrichment_process, selected_profiles, ig_sessionid, default_product_id)
            try:
                result = future.result(timeout=7200)  # 2 hours for enrichment
            except TimeoutError:
                logger.error("Enrichment timed out after 2 hours")
                app_data['processing_status'] = None
                return {"error": "Enrichment timed out."}, 408
        
        app_data['processing_status'] = None
        return {"success": True, "leads": result}
        
    except Exception as e:
        logger.error(f"Failed to continue enrichment: {e}")
        app_data['processing_status'] = None
        return jsonify({"error": str(e)}), 500


def discover_hashtags_sync(keyword, ig_sessionid, search_limit):
    """Discover hashtags only - no enrichment"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                discover_hashtags_async(keyword, ig_sessionid, search_limit))
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"Hashtag discovery failed: {e}")
        raise


def run_enrichment_process(selected_profiles, ig_sessionid, default_product_id=None):
    """Run enrichment process for selected profiles"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                enrich_selected_profiles_async(selected_profiles, ig_sessionid, default_product_id))
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"Enrichment process failed: {e}")
        raise


def run_async_process(keyword, ig_sessionid, search_limit, default_product_id=None):
    """Run async processing in a separate thread"""
    try:
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                process_keyword_async(keyword, ig_sessionid, search_limit, default_product_id))
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"Async processing failed: {e}")
        raise


async def enrich_selected_profiles_async(selected_profiles, ig_sessionid, default_product_id=None):
    """Enrich selected profiles only"""
    apify_token = os.environ.get('APIFY_TOKEN')
    perplexity_key = os.environ.get('PERPLEXITY_API_KEY')
    
    if not all([apify_token, perplexity_key]) or not apify_token.strip() or not perplexity_key.strip():
        missing_keys = []
        if not apify_token or not apify_token.strip():
            missing_keys.append('APIFY_TOKEN')
        if not perplexity_key or not perplexity_key.strip():
            missing_keys.append('PERPLEXITY_API_KEY')
        raise ValueError(f"Missing or empty API tokens: {', '.join(missing_keys)}")
    
    # Initialize progress tracking
    start_time = time.time()
    batch_size = 3
    
    # Filter out existing usernames from database
    usernames = [p['username'] for p in selected_profiles]
    username_to_hashtag = {p['username']: p['hashtag'] for p in selected_profiles}
    
    with app.app_context():
        existing_usernames = set()
        existing_leads = Lead.query.filter(Lead.username.in_(usernames)).all()
        for lead in existing_leads:
            existing_usernames.add(lead.username)
        
        usernames_to_enrich = [u for u in usernames if u not in existing_usernames]
        
        logger.info(f"Selected {len(usernames)} profiles")
        logger.info(f"Filtered out {len(existing_usernames)} existing usernames")
        logger.info(f"Will enrich {len(usernames_to_enrich)} new usernames")
        
        # Create batches
        batches = [usernames_to_enrich[i:i + batch_size] for i in range(0, len(usernames_to_enrich), batch_size)]
        
        # Update progress
        app_data['processing_progress'] = {
            'current_step': f'2. Erweitere {len(usernames_to_enrich)} neue Profile...',
            'phase': 'profile_enrichment',
            'total_steps': len(batches),
            'completed_steps': 0,
            'estimated_time_remaining': len(batches) * 105,  # 15s processing + 90s pause
            'total_usernames': len(usernames),
            'existing_usernames': len(existing_usernames),
            'usernames_to_enrich': len(usernames_to_enrich)
        }
    
    # Process batches
    semaphore = asyncio.Semaphore(3)
    perplexity_semaphore = asyncio.Semaphore(2)
    total_saved_leads = 0
    
    for i, batch in enumerate(batches):
        if app_data.get('stop_requested', False):
            logger.info(f"Processing stopped by user during batch {i+1}")
            break
            
        try:
            app_data['processing_progress']['current_step'] = f'2. Erweitere Profile - Batch {i+1}/{len(batches)}'
            app_data['processing_progress']['current_batch'] = i + 1
            app_data['processing_progress']['total_batches'] = len(batches)
            
            # Fix the function call to pass correct parameters
            perplexity_semaphore_unused = perplexity_semaphore  # Keep for consistency even though not used in function
            result = await enrich_profile_batch(batch, ig_sessionid, apify_token, perplexity_key, semaphore)
            
            if isinstance(result, list) and result:
                # Add hashtag information
                for lead in result:
                    lead['hashtag'] = username_to_hashtag.get(lead['username'], 'unknown')
                    lead['is_duplicate'] = False
                
                # Save batch
                saved_count = save_leads_incrementally(result, app_data.get('keyword', ''), default_product_id)
                total_saved_leads += saved_count
                logger.info(f"Batch {i+1}: Saved {saved_count} leads")
                
                app_data['processing_progress']['incremental_leads'] = total_saved_leads
            
            app_data['processing_progress']['completed_steps'] = i + 1
            
            # Anti-spam pause
            if i < len(batches) - 1:
                logger.info(f"Anti-spam pause: 90s before batch {i+2}")
                for remaining in range(90, 0, -15):
                    app_data['processing_progress']['current_step'] = f'⏸ Anti-Spam Pause: {remaining}s bis Batch {i+2}/{len(batches)}'
                    await asyncio.sleep(15)
                    
        except Exception as e:
            logger.error(f"Batch {i+1} error: {e}")
            continue
    
    # Final status
    app_data['processing_progress'] = {
        'current_step': f'3. Fertig! {total_saved_leads} Leads erfolgreich generiert ✓',
        'phase': 'completed',
        'total_steps': 0,
        'completed_steps': 0,
        'estimated_time_remaining': 0,
        'total_leads_generated': total_saved_leads
    }
    
    logger.info(f"Enrichment complete: {total_saved_leads} leads saved")
    
    # Get all leads for the selected hashtags
    with app.app_context():
        # Extract unique hashtags from selected_profiles
        hashtags = list(set([p['hashtag'] for p in selected_profiles]))
        leads = Lead.query.filter(Lead.hashtag.in_(hashtags)).all()
        return [lead.to_dict() for lead in leads]


async def discover_hashtags_async(keyword, ig_sessionid, search_limit):
    """Discover hashtags only - returns hashtag variants with user counts"""
    apify_token = os.environ.get('APIFY_TOKEN')
    
    if not apify_token or not apify_token.strip():
        raise ValueError("Missing or empty APIFY_TOKEN")
    
    # Update progress tracking
    app_data['processing_progress'] = {
        'current_step': f'1. Suche Instagram-Profile für Hashtag #{keyword}...',
        'phase': 'hashtag_search',
        'total_steps': 1,
        'completed_steps': 0,
        'estimated_time_remaining': 30,
        'keyword': keyword
    }
    
    # Call Apify to get hashtag data
    hashtag_input = {
        "search": keyword,
        "searchType": "hashtag",
        "searchLimit": search_limit
    }
    
    try:
        hashtag_data = call_apify_actor_sync("DrF9mzPPEuVizVF4l", hashtag_input, apify_token)
        
        if not hashtag_data or not hashtag_data.get('items'):
            logger.error(f"No hashtag data returned for keyword: {keyword}")
            return []
            
        hashtag_items = hashtag_data.get('items', [])
        logger.info(f"Processing {len(hashtag_items)} hashtag items")
        
        # Count users per hashtag variant
        hashtag_counts = {}
        hashtag_usernames = {}  # Store usernames per hashtag
        
        for item in hashtag_items:
            username = item.get('username')
            hashtag = item.get('hashtag', keyword)
            
            if username:
                if hashtag not in hashtag_counts:
                    hashtag_counts[hashtag] = 0
                    hashtag_usernames[hashtag] = []
                
                hashtag_counts[hashtag] += 1
                hashtag_usernames[hashtag].append(username)
        
        # Create hashtag variants list with counts
        variants = []
        for hashtag, count in hashtag_counts.items():
            variants.append({
                'hashtag': hashtag,
                'user_count': count,
                'usernames': hashtag_usernames[hashtag]
            })
        
        # Sort by user count descending
        variants.sort(key=lambda x: x['user_count'], reverse=True)
        
        # Update progress
        app_data['processing_progress']['completed_steps'] = 1
        app_data['processing_progress']['current_step'] = f'Hashtag-Suche abgeschlossen - {len(variants)} Varianten gefunden'
        app_data['processing_progress']['phase'] = 'hashtag_selection'
        
        return variants
        
    except Exception as e:
        logger.error(f"Hashtag discovery failed: {e}")
        app_data['processing_progress']['current_step'] = f'Fehler: {str(e)}'
        return []


async def process_keyword_async(keyword, ig_sessionid, search_limit, default_product_id=None):
    """Async processing of keyword"""
    apify_token = os.environ.get('APIFY_TOKEN')
    perplexity_key = os.environ.get('PERPLEXITY_API_KEY')

    # Initialize progress tracking
    start_time = time.time()

    if not all([apify_token, perplexity_key
                ]) or not apify_token.strip() or not perplexity_key.strip():
        missing_keys = []
        if not apify_token or not apify_token.strip():
            missing_keys.append('APIFY_TOKEN')
        if not perplexity_key or not perplexity_key.strip():
            missing_keys.append('PERPLEXITY_API_KEY')
        raise ValueError(
            f"Missing or empty API tokens: {', '.join(missing_keys)}")

    # Calculate total estimated time including 5-minute anti-spam pauses between batches
    avg_delay_time = 5.5  # Average of 1-10 seconds
    hashtag_crawl_time = avg_delay_time + 30  # Hashtag search takes longer
    profile_batch_time = avg_delay_time + 15  # Per batch (slightly longer for 3 profiles)
    estimated_batches = search_limit // 3  # 3 profiles per batch
    pause_time_per_batch = 90  # 90 seconds = 1.5 minutes between batches

    # Total time = hashtag search + (batch processing time + pause time) * (batches - 1) + final batch processing
    total_batch_and_pause_time = (profile_batch_time + pause_time_per_batch) * max(0, estimated_batches - 1)
    final_batch_time = profile_batch_time if estimated_batches > 0 else 0
    total_estimated_time = hashtag_crawl_time + total_batch_and_pause_time + final_batch_time

    # Initialize progress with detailed step tracking
    app_data['processing_progress'] = {
        'current_step': '1. Suche Instagram-Profile für Hashtag...',
        'phase': 'hashtag_search',
        'total_steps': 1 + estimated_batches,  # 1 hashtag search + N profile batches
        'completed_steps': 0,
        'estimated_time_remaining': int(total_estimated_time),
        'incremental_leads': 0,
        'keyword': keyword,
        'final_status': 'processing',
        'current_batch': 0,
        'total_batches': estimated_batches,
        'phase_start_time': time.time()
    }

    # Step 1: Hashtag crawl - Using correct Apify API format with user-defined limit
    hashtag_input = {
        "search": keyword,
        "searchType": "hashtag",
        "searchLimit": search_limit
    }
    
    try:
        # Check if stop was requested before starting
        if app_data.get('stop_requested', False):
            logger.info("Processing stopped by user before hashtag search")
            app_data['processing_progress']['final_status'] = 'stopped'
            app_data['processing_status'] = None
            return []
            
        app_data['processing_progress']['current_step'] = f'1. Suche Instagram-Profile für Hashtag #{keyword} (ca. {hashtag_crawl_time/60:.1f}min)...'
        hashtag_data = call_apify_actor_sync("DrF9mzPPEuVizVF4l", hashtag_input,
                                             apify_token)
        # Don't increment completed_steps here - will do it after hashtag processing is fully done
        logger.info(f"Hashtag search completed successfully for #{keyword}")

        # Update time remaining
        elapsed_time = time.time() - start_time
        remaining_steps = app_data['processing_progress']['total_steps'] - app_data['processing_progress']['completed_steps']
        avg_time_per_step = elapsed_time / max(1, app_data['processing_progress']['completed_steps'] + 1)
        app_data['processing_progress']['estimated_time_remaining'] = int(avg_time_per_step * remaining_steps)

        if not hashtag_data or not hashtag_data.get('items'):
            logger.error(f"No hashtag data returned for keyword: {keyword}")
            return []
    except Exception as e:
        logger.error(f"Hashtag crawl failed for keyword '{keyword}': {e}")
        return []

    # The call_apify_actor_sync function already processed and extracted username-hashtag pairs
    hashtag_items = hashtag_data.get('items', [])
    logger.info(f"Processing {len(hashtag_items)} hashtag items")

    # Debug: Log the structure of the first item
    if hashtag_items:
        logger.debug(f"First item structure: {list(hashtag_items[0].keys()) if isinstance(hashtag_items[0], dict) else type(hashtag_items[0])}")
        logger.debug(f"First item sample: {str(hashtag_items[0])[:200]}")

    # Use the extracted username-hashtag pairs directly from Apify result
    profiles = hashtag_items

    # Store count before clearing for logging
    usernames_count = len(profiles)

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

    # Update progress to show hashtag search completed with counts
    app_data['processing_progress']['completed_steps'] = 1
    app_data['processing_progress']['current_step'] = f'1. Hashtag-Suche abgeschlossen - {len(unique_profiles)} Profile gefunden ✓'
    app_data['processing_progress']['phase'] = 'hashtag_search_complete'
    app_data['processing_progress']['total_usernames'] = len(unique_profiles)
    logger.info(f"Progress updated: Step 1 complete, found {len(unique_profiles)} profiles")

    # Brief pause to make transition visible
    await asyncio.sleep(1)

    # Step 3: Profile enrichment with Instagram anti-spam optimization
    semaphore = asyncio.Semaphore(3)  # Match batch size for controlled processing
    perplexity_semaphore = asyncio.Semaphore(2)  # Limit concurrent Perplexity API calls

    # Advanced anti-spam optimization: batch 3 profiles with strategic pauses
    usernames = [p['username'] for p in unique_profiles]
    
    # Create username to hashtag mapping for later use
    username_to_hashtag = {p['username']: p['hashtag'] for p in unique_profiles}
    
    # Filter out usernames that already exist in database
    with app.app_context():
        existing_usernames = set()
        existing_leads = Lead.query.filter(Lead.username.in_(usernames)).all()
        for lead in existing_leads:
            existing_usernames.add(lead.username)
        
        # Filter out usernames that already exist in database
        usernames_to_enrich = [u for u in usernames if u not in existing_usernames]
        
        logger.info(f"Found {len(usernames)} unique usernames from hashtag search")
        logger.info(f"Filtered out {len(existing_usernames)} existing usernames from database")
        logger.info(f"Will enrich {len(usernames_to_enrich)} new usernames")
        
        # Update progress with de-duplication info
        app_data['processing_progress']['total_usernames'] = len(usernames)
        app_data['processing_progress']['existing_usernames'] = len(existing_usernames)
        app_data['processing_progress']['usernames_to_enrich'] = len(usernames_to_enrich)
        
        # Update progress display to show de-duplication stats
        app_data['processing_progress']['current_step'] = f'1. Hashtag-Suche abgeschlossen - {len(usernames)} Profile gefunden ({len(existing_usernames)} bereits in Datenbank, {len(usernames_to_enrich)} werden angereichert) ✓'
        
        usernames = usernames_to_enrich  # Use filtered list
    
    batch_size = 3  # Process 3 profiles at a time with extended pauses between groups

    batches = [
        usernames[i:i + batch_size]
        for i in range(0, len(usernames), batch_size)
    ]

    # Update progress total steps based on actual batches
    app_data['processing_progress']['total_steps'] = 1 + len(batches)

    # Process batches sequentially to minimize memory usage
    total_saved_leads = 0
    import gc

    for i, batch in enumerate(batches):
        # Check if stop was requested before processing each batch
        if app_data.get('stop_requested', False):
            logger.info(f"Processing stopped by user during batch {i+1}")
            app_data['processing_progress']['final_status'] = 'stopped'
            app_data['processing_status'] = None
            # Return any leads saved so far
            return total_saved_leads
            
        try:
            # Update progress with detailed step information
            batch_time_estimate = (profile_batch_time + (90 if i < len(batches) - 1 else 0)) / 60  # Convert to minutes
            profiles_processed = i * batch_size
            profiles_current_batch = min(len(batch), batch_size)
            total_profiles_after_batch = profiles_processed + profiles_current_batch
            app_data['processing_progress']['current_step'] = f'2. Erweitere Profil-Informationen - {profiles_processed}/{len(usernames)} Profile angereichert - Batch {i+1}/{len(batches)} (ca. {batch_time_estimate:.1f}min)'
            app_data['processing_progress']['phase'] = 'profile_enrichment'
            app_data['processing_progress']['current_batch'] = i + 1
            app_data['processing_progress']['total_batches'] = len(batches)
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
                    # Ensure hashtag is present from unique profiles or extracted IDs.
                    hashtag = next((p['hashtag'] for p in unique_profiles if p['username'] == lead['username']), keyword)
                    lead['hashtag'] = hashtag

                # Save this batch immediately to prevent data loss
                saved_count = save_leads_incrementally(result, keyword, default_product_id=default_product_id)
                total_saved_leads += saved_count
                logger.info(f"Batch {i+1}: Saved {saved_count} leads incrementally")

                # Update progress with incremental lead count for frontend - force immediate update
                app_data['processing_progress']['incremental_leads'] = total_saved_leads
                app_data['processing_progress']['keyword'] = keyword
                app_data['processing_progress']['current_step'] = f'2. Batch {i+1}/{len(batches)} abgeschlossen - {total_saved_leads} Leads generiert'

                # Force immediate progress update for UI refresh
                logger.info(f"UI Refresh Trigger: {total_saved_leads} leads saved for keyword '{keyword}'")
            else:
                logger.warning(f"Batch {i+1}: No results or unexpected type: {type(result)}")

            # Update progress after batch completion
            app_data['processing_progress']['completed_steps'] += 1

            # Recalculate time remaining (including pause time for remaining batches)
            elapsed_time = time.time() - start_time
            remaining_batches = len(batches) - (i + 1)  # How many batches still need processing
            # Calculate pause time with new pattern: 3 batches with 90s pauses, then 180s pause
            if remaining_batches > 0:
                remaining_groups = remaining_batches // 3
                remaining_in_current_group = remaining_batches % 3

                # Calculate total pause time
                pause_time_remaining = 0
                # Full groups have 2x90s + 1x180s = 360s
                pause_time_remaining += remaining_groups * 360
                # Partial group has only 90s pauses
                if remaining_in_current_group > 0:
                    pause_time_remaining += (remaining_in_current_group - 1) * 90
            else:
                pause_time_remaining = 0

            if app_data['processing_progress']['completed_steps'] > 0:
                avg_processing_time_per_step = elapsed_time / app_data['processing_progress']['completed_steps']
                processing_time_remaining = remaining_batches * avg_processing_time_per_step
                app_data['processing_progress']['estimated_time_remaining'] = int(processing_time_remaining + pause_time_remaining)
            else:
                app_data['processing_progress']['estimated_time_remaining'] = int(total_estimated_time - elapsed_time + pause_time_remaining)

            # Force garbage collection after each batch
            gc.collect()

            # Advanced Instagram anti-spam protection: 90s pause between batches, 3min pause after 3 batches
            if i < len(batches) - 1:  # Don't pause after the last batch
                # Determine pause duration based on batch group position
                batch_position_in_group = i % 3  # 0, 1, or 2
                is_end_of_group = (batch_position_in_group == 2) or (i == len(batches) - 2)

                if is_end_of_group and i < len(batches) - 2:  # End of group but not last batch
                    pause_duration = 180  # 3 minutes between groups
                    pause_reason = "Extended anti-spam pause between batch groups"
                else:
                    pause_duration = 90  # 90 seconds within group
                    pause_reason = "Standard anti-spam pause"

                logger.info(f"{pause_reason}: Taking {pause_duration}s pause after batch {i+1}. Next batch will start in {pause_duration} seconds...")

                # Update progress to show pause status with next batch info
                minutes_left = pause_duration // 60
                seconds_left = pause_duration % 60

                if pause_duration == 180:
                    app_data['processing_progress']['current_step'] = f'⏸ Erweiterte Anti-Spam Pause (3min): {minutes_left}m {seconds_left}s bis Batch-Gruppe {(i+2)//3 + 1}'
                else:
                    app_data['processing_progress']['current_step'] = f'⏸ Anti-Spam Pause: {minutes_left}m {seconds_left}s bis Batch {i+2}/{len(batches)}'

                # Count down the pause time with progress updates
                for remaining_seconds in range(pause_duration, 0, -15):  # Update every 15 seconds
                    minutes_remaining = remaining_seconds // 60
                    seconds_remaining = remaining_seconds % 60

                    if minutes_remaining > 0:
                        time_display = f"{minutes_remaining}m {seconds_remaining}s"
                    else:
                        time_display = f"{seconds_remaining}s"

                    if pause_duration == 180:
                        app_data['processing_progress']['current_step'] = f'⏸ Erweiterte Anti-Spam Pause (3min): {time_display} bis Batch-Gruppe {(i+2)//3 + 1}'
                    else:
                        app_data['processing_progress']['current_step'] = f'⏸ Anti-Spam Pause: {time_display} bis Batch {i+2}/{len(batches)}'
                    logger.info(f"Pause countdown: {time_display} remaining until next batch")

                    await asyncio.sleep(15)  # Use async sleep to not block the event loop

                # Final sleep for any remaining seconds
                remaining_final = pause_duration % 15
                if remaining_final > 0:
                    await asyncio.sleep(remaining_final)

                logger.info(f"90s pause completed. Resuming with batch {i+2}/{len(batches)}")
            else:
                logger.info(f"All batches completed. No pause needed after final batch {i+1}")

        except Exception as e:
            logger.error(f"Batch {i+1} processing error: {e}")
            # Update progress with current saved count even on error
            app_data['processing_progress']['incremental_leads'] = total_saved_leads
            app_data['processing_progress']['current_step'] = f'Batch {i+1} failed - {total_saved_leads} leads saved so far'
            # Continue processing other batches even if one fails
            continue

    logger.info(f"Total enrichment complete: {total_saved_leads} leads saved to database")

    # Show final completion status
    app_data['processing_progress'] = {
        'current_step': f'3. Fertig! {total_saved_leads} Leads erfolgreich generiert und gespeichert ✓',
        'phase': 'completed',
        'total_steps': 0,
        'completed_steps': 0,
        'estimated_time_remaining': 0,
        'total_leads_generated': total_saved_leads,
        'final_status': 'success'
    }

    # Return dictionary format for API response
    # Query fresh leads from database to avoid session issues
    try:
        with app.app_context():
            fresh_leads = Lead.query.filter_by(hashtag=keyword).order_by(Lead.created_at.desc()).all()
            return [lead.to_dict() for lead in fresh_leads]
    except Exception as e:
        logger.error(f"Failed to query leads from database: {e}")
        return []


@app.route('/draft-email/<username>', methods=['GET'])
def draft_email(username):
    """Generate email draft using OpenAI"""
    # Get templates from database
    subject_template = EmailTemplate.query.filter_by(name='subject').first()
    body_template = EmailTemplate.query.filter_by(name='body').first()

    # Use stored templates or fallback to defaults
    subject_prompt = subject_template.template if subject_template else 'Schreibe in DU-Form eine persönliche Betreffzeile mit freundlichen Hook für eine Influencer Kooperation mit Kasimir + Liselotte. Nutze persönliche Infos (z.B. Username, BIO, Interessen), sprich sie direkt in DU-Form. Falls ein Produkt ausgewählt ist, erwähne es subtil in der Betreffzeile. Antworte im JSON-Format: {"subject": "betreff text"}'
    body_prompt = body_template.template if body_template else 'Erstelle eine personalisierte, professionelle deutsche E-Mail, ohne die Betreffzeile, für potenzielle Instagram Influencer Kooperationen. Die E-Mail kommt von Kasimir vom Store KasimirLieselotte. Verwende einen höflichen, professionellen Ton auf Deutsch aber in DU-Form um es casual im Instagram feel zu bleiben. WICHTIG: Falls ein Produkt ausgewählt ist, integriere unbedingt folgende Elemente in die E-Mail: 1) Erwähne das Produkt namentlich, 2) Füge den direkten Link zum Produkt ein (Produkt-URL), 3) Erkläre kurz die Produkteigenschaften basierend auf der Beschreibung, 4) Beziehe das Produkt auf die Bio/Interessen des Influencers. Die E-Mail sollte den Produktlink natürlich in den Text einbetten. Füge am Ende die Signatur mit der Website https://www.kasimirlieselotte.de/ hinzu. Antworte im JSON-Format: {"body": "email inhalt"}'

    # Find the lead in database
    lead = Lead.query.filter_by(username=username).first()
    if not lead:
        return {"error": "Lead not found"}, 404

    try:
        # Build user content with profile and product information
        profile_content = f"Profil: @{lead.username}, Name: {lead.full_name}, Bio: {lead.bio}, Hashtag: {lead.hashtag}"

        # Create different prompts based on whether product is selected
        if lead.selected_product:
            # WITH PRODUCT: Use current prompts with product instructions
            product_info = f"\n\nAusgewähltes Produkt: {lead.selected_product.name}\nProdukt-URL: {lead.selected_product.url}\nBeschreibung: {lead.selected_product.description}"
            profile_content += product_info
            profile_content_with_email = f"Profil: @{lead.username}, Name: {lead.full_name}, Bio: {lead.bio}, Email: {lead.email}, Hashtag: {lead.hashtag}" + product_info

            # Use current prompts with product instructions
            final_subject_prompt = subject_prompt
            final_body_prompt = body_prompt
        else:
            # WITHOUT PRODUCT: Use alternative prompts without product references
            profile_content_with_email = f"Profil: @{lead.username}, Name: {lead.full_name}, Bio: {lead.bio}, Email: {lead.email}, Hashtag: {lead.hashtag}"

            # Create clean alternative prompts without any product mentions
            final_subject_prompt = 'Schreibe in DU-Form eine persönliche Betreffzeile mit freundlichen Hook für eine Influencer Kooperation mit Kasimir + Liselotte. Nutze persönliche Infos (z.B. Username, BIO, Interessen), sprich sie direkt in DU-Form. Fokussiere dich auf die Interessen und den Content des Influencers. Antworte im JSON-Format: {"subject": "betreff text"}'

            final_body_prompt = 'Erstelle eine personalisierte, professionelle deutsche E-Mail, ohne die Betreffzeile, für potenzielle Instagram Influencer Kooperationen. Die E-Mail kommt von Kasimir vom Store KasimirLieselotte. Verwende einen höflichen, professionellen Ton auf Deutsch aber in DU-Form um es casual im Instagram feel zu bleiben. Fokussiere dich auf eine allgemeine Kooperationsanfrage, die auf die Interessen und den Content des Influencers eingeht. Erwähne deine Begeisterung für ihren Content und schlage eine mögliche Zusammenarbeit vor, ohne spezifische Produkte zu erwähnen. Füge am Ende die Signatur mit der Website https://www.kasimirlieselotte.de/ hinzu. Antworte im JSON-Format: {"body": "email inhalt"}'

        # Generate subject using appropriate prompt
        subject_response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "system",
                "content": final_subject_prompt
            }, {
                "role": "user",
                "content": profile_content
            }],
            response_format={"type": "json_object"},
            max_tokens=100)

        # Generate body using appropriate prompt
        body_response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "system",
                "content": final_body_prompt
            }, {
                "role": "user",
                "content": profile_content_with_email
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


@app.route('/get-email/<username>')
def get_email(username):
    """Get email address for a lead"""
    # Find the lead in database
    lead = Lead.query.filter_by(username=username).first()
    if not lead:
        return {"error": "Lead not found"}, 404

    if not lead.email:
        return {"error": "No email address available for this lead"}, 400

    return {"email": lead.email}


@app.route('/update-lead/<username>', methods=['POST'])
def update_lead(username):
    """Update lead information"""
    data = request.get_json()

    # Find the lead in database
    lead = Lead.query.filter_by(username=username).first()
    if not lead:
        return {"error": "Lead not found"}, 404

    try:
        # Update any fields that were provided
        if 'email' in data:
            lead.email = data['email']
        if 'subject' in data:
            lead.subject = data['subject']
        if 'email_body' in data:
            lead.email_body = data['email_body']
        if 'phone' in data:
            lead.phone = data['phone']
        if 'website' in data:
            lead.website = data['website']

        lead.updated_at = datetime.now()

        # Save to database
        db.session.commit()

        return {"success": True, "message": "Lead updated successfully"}

    except Exception as e:
        logger.error(f"Failed to update lead: {e}")
        return {"error": f"Failed to update lead: {str(e)}"}, 500


@app.route('/send-email/<username>', methods=['POST'])
def send_email(username):
    """Mark email as sent (used with Gmail integration)"""
    # Find the lead in database
    lead = Lead.query.filter_by(username=username).first()
    if not lead:
        return {"error": "Lead not found"}, 404

    if not lead.email:
        return {"error": "No email address available"}, 400

    if not lead.subject or not lead.email_body:
        return {"error": "Email draft not ready"}, 400

    try:
        # Mark as sent since Gmail will handle the actual sending
        lead.sent = True
        lead.sent_at = datetime.now()

        # Save to database
        db.session.commit()

        return {"success": True, "message": "Email marked as sent"}

    except Exception as e:
        logger.error(f"Failed to mark email as sent: {e}")
        return {"error": f"Failed to mark email as sent: {str(e)}"}, 500


@app.route('/mark-sent/<username>', methods=['POST'])
def mark_sent(username):
    """Mark email as sent and update database"""
    data = request.get_json()
    subject = data.get('subject', '')
    body = data.get('body', '')

    # Find the lead in database
    lead = Lead.query.filter_by(username=username).first()
    if not lead:
        return {"error": "Lead not found"}, 404

    try:
        # Update lead status
        lead.sent = True
        lead.sent_at = datetime.now()
        lead.subject = subject
        lead.email_body = body

        # Save to database
        db.session.commit()

        return {"success": True}

    except Exception as e:
        logger.error(f"Failed to mark email as sent: {e}")
        return {"error": f"Failed to update send status: {str(e)}"}, 500


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
                "data": json.dumps(leads_data, indent=2),
                "filename": f"leads_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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


@app.route('/api/email-templates', methods=['GET'])
def get_email_templates():
    """Get current email templates"""
    try:
        subject_template = EmailTemplate.query.filter_by(name='subject').first()
        body_template = EmailTemplate.query.filter_by(name='body').first()

        return jsonify({
            'subject': subject_template.template if subject_template else '',
            'body': body_template.template if body_template else ''
        })
    except Exception as e:
        logger.error(f"Failed to get email templates: {e}")
        return {"error": "Failed to get email templates"}, 500


@app.route('/api/email-templates', methods=['POST'])
def save_email_templates():
    """Save email templates"""
    try:
        data = request.get_json()

        if 'subject' in data:
            subject_template = EmailTemplate.query.filter_by(name='subject').first()
            if subject_template:
                subject_template.template = data['subject']
                subject_template.updated_at = datetime.utcnow()
            else:
                subject_template = EmailTemplate(name='subject', template=data['subject'])
                db.session.add(subject_template)

        if 'body' in data:
            body_template = EmailTemplate.query.filter_by(name='body').first()
            if body_template:
                body_template.template = data['body']
                body_template.updated_at = datetime.utcnow()
            else:
                body_template = EmailTemplate(name='body', template=data['body'])
                db.session.add(body_template)

        db.session.commit()

        return jsonify({"success": True, "message": "Email templates saved successfully"})
    except Exception as e:
        logger.error(f"Failed to save email templates: {e}")
        db.session.rollback()
        return {"error": "Failed to save email templates"}, 500


@app.route('/api/products', methods=['GET'])
def get_products():
    """Get all available products for email generation"""
    try:
        products = Product.query.all()
        return jsonify({
            'products': [product.to_dict() for product in products]
        })
    except Exception as e:
        logger.error(f"Failed to get products: {e}")
        return {"error": "Failed to get products"}, 500


@app.route('/api/leads/<username>/product', methods=['POST'])
def update_lead_product(username):
    """Update the selected product for a lead"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')

        lead = Lead.query.filter_by(username=username).first()
        if not lead:
            return {"error": "Lead not found"}, 404

        if product_id:
            product = Product.query.get(product_id)
            if not product:
                return {"error": "Product not found"}, 404
            lead.selected_product_id = product_id
        else:
            lead.selected_product_id = None

        lead.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({"success": True, "message": "Product updated successfully"})
    except Exception as e:
        logger.error(f"Failed to update lead product: {e}")
        db.session.rollback()
        return {"error": "Failed to update product selection"}, 500


@app.route('/api/set-default-product', methods=['POST'])
def set_default_product():
    """Set the default product in session"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')

        if product_id:
            # Validate product exists
            product = Product.query.get(product_id)
            if not product:
                return {"error": "Product not found"}, 404
            session['default_product_id'] = int(product_id)
        else:
            # Clear default product
            session.pop('default_product_id', None)

        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Failed to set default product: {e}")
        return {"error": "Failed to set default product"}, 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
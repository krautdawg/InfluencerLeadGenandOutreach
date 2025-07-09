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
from models import db, Lead, ProcessingSession
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


def call_apify_actor_sync(actor_id, input_data, token):
    """Call Apify actor using official client - synchronous version"""
    client = ApifyClient(token)
    
    # Run the Actor and wait for it to finish
    run = client.actor(actor_id).call(run_input=input_data)
    
    # Fetch results from the run's dataset
    dataset_items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    
    # Return in format compatible with existing code
    return {"items": dataset_items}


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

            profile_data = call_apify_actor_sync("8WEn9FvZnhE7lM3oA",
                                                 input_data, apify_token)
            enriched_profiles = []

            # Process each profile from the returned data
            profile_items = profile_data.get('items', [])
            
            # Create a mapping of username to profile data
            profile_map = {}
            for item in profile_items:
                # Extract username from URL or directly from item
                if 'url' in item:
                    username_from_url = item['url'].split('/')[-2] if item['url'].endswith('/') else item['url'].split('/')[-1]
                    profile_map[username_from_url] = item
                elif 'username' in item:
                    profile_map[item['username']] = item

            for username in usernames:
                profile_info = profile_map.get(username, {})

                # Check if contact info is missing and use Perplexity fallback
                if not any([
                        profile_info.get('email'),
                        profile_info.get('phone'),
                        profile_info.get('website')
                ]):
                    try:
                        contact_info = await call_perplexity_api(
                            username, perplexity_key)
                        profile_info.update(contact_info)
                    except Exception as e:
                        logger.error(
                            f"Perplexity API failed for {username}: {e}")

                enriched_profiles.append({
                    'username':
                    username,
                    'fullName':
                    profile_info.get('fullName', ''),
                    'bio':
                    profile_info.get('bio', ''),
                    'email':
                    profile_info.get('email', ''),
                    'phone':
                    profile_info.get('phone', ''),
                    'website':
                    profile_info.get('website', ''),
                    'followersCount':
                    profile_info.get('followersCount', 0),
                    'followingCount':
                    profile_info.get('followingCount', 0),
                    'postsCount':
                    profile_info.get('postsCount', 0),
                    'isVerified':
                    profile_info.get('isVerified', False),
                    'profilePicUrl':
                    profile_info.get('profilePicUrl', ''),
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

    if not keyword:
        return {"error": "Keyword is required"}, 400
    
    # Validate search limit - reduced maximum to prevent memory issues
    try:
        search_limit = int(search_limit)
        if search_limit < 1 or search_limit > 100:
            return {"error": "Search limit must be between 1 and 100"}, 400
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

    hashtag_data = call_apify_actor_sync("DrF9mzPPEuVizVF4l", hashtag_input,
                                         apify_token)

    # Step 2: Memory-efficient processing - extract usernames without storing all posts
    usernames_set = set()  # Use set for deduplication
    logger.info(f"Processing {len(hashtag_data.get('items', []))} hashtag items")
    
    for item in hashtag_data.get('items', []):
        # Process posts directly without storing them all in memory
        for post in item.get('latestPosts', []):
            if post.get('ownerUsername'):
                usernames_set.add(post['ownerUsername'])
        for post in item.get('topPosts', []):
            if post.get('ownerUsername'):
                usernames_set.add(post['ownerUsername'])
    
    logger.info(f"Found {len(usernames_set)} unique usernames from posts")

    # Convert to profiles list
    profiles = [{'hashtag': keyword, 'username': username} for username in usernames_set]

    logger.info(f"Found {len(profiles)} profiles")
    
    # If no profiles found, return empty result
    if not profiles:
        logger.warning("No profiles found in hashtag data")
        return []

    unique_profiles, duplicates = deduplicate_profiles(profiles)
    logger.info(f"After deduplication: {len(unique_profiles)} unique profiles")

    # Step 3: Profile enrichment with reduced memory footprint
    semaphore = asyncio.Semaphore(3)  # Reduced to 3 concurrent calls to save memory
    perplexity_semaphore = asyncio.Semaphore(
        2)  # Reduced to 2 concurrent Perplexity calls

    # Batch usernames for processing with smaller batches
    usernames = [p['username'] for p in unique_profiles]
    batch_size = 3  # Reduced batch size to lower memory usage
    batches = [
        usernames[i:i + batch_size]
        for i in range(0, len(usernames), batch_size)
    ]

    # Process batches concurrently
    tasks = []
    for batch in batches:
        task = enrich_profile_batch(batch, ig_sessionid, apify_token,
                                    perplexity_key, semaphore)
        tasks.append(task)

    logger.info(f"Processing {len(tasks)} batches concurrently")
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Flatten results
    enriched_leads = []
    for result in results:
        if isinstance(result, list):
            enriched_leads.extend(result)
        elif isinstance(result, Exception):
            logger.error(f"Batch processing error: {result}")
        else:
            logger.warning(f"Unexpected result type: {type(result)}")

    logger.info(f"Successfully enriched {len(enriched_leads)} leads")

    # Mark duplicates
    for lead in enriched_leads:
        if lead['username'] in duplicates:
            lead['is_duplicate'] = True
        else:
            lead['is_duplicate'] = False

    # Store results in database with memory optimization
    saved_leads = []
    batch_commit_size = 20  # Commit in smaller batches to reduce memory usage
    
    try:
        for i, lead_data in enumerate(enriched_leads):
            try:
                # Check if lead already exists
                existing_lead = Lead.query.filter_by(
                    username=lead_data['username'],
                    hashtag=keyword
                ).first()
                
                if existing_lead:
                    # Update existing lead
                    existing_lead.full_name = lead_data.get('fullName', '')
                    existing_lead.bio = lead_data.get('bio', '')
                    existing_lead.email = lead_data.get('email', '')
                    existing_lead.phone = lead_data.get('phone', '')
                    existing_lead.website = lead_data.get('website', '')
                    existing_lead.followers_count = lead_data.get('followersCount', 0)
                    existing_lead.following_count = lead_data.get('followingCount', 0)
                    existing_lead.posts_count = lead_data.get('postsCount', 0)
                    existing_lead.is_verified = lead_data.get('isVerified', False)
                    existing_lead.profile_pic_url = lead_data.get('profilePicUrl', '')
                    existing_lead.is_duplicate = lead_data.get('is_duplicate', False)
                    existing_lead.updated_at = datetime.utcnow()
                    saved_leads.append(existing_lead)
                else:
                    # Create new lead
                    new_lead = Lead(
                        username=lead_data['username'],
                        hashtag=keyword,
                        full_name=lead_data.get('fullName', ''),
                        bio=lead_data.get('bio', ''),
                        email=lead_data.get('email', ''),
                        phone=lead_data.get('phone', ''),
                        website=lead_data.get('website', ''),
                        followers_count=lead_data.get('followersCount', 0),
                        following_count=lead_data.get('followingCount', 0),
                        posts_count=lead_data.get('postsCount', 0),
                        is_verified=lead_data.get('isVerified', False),
                        profile_pic_url=lead_data.get('profilePicUrl', ''),
                        is_duplicate=lead_data.get('is_duplicate', False)
                    )
                    db.session.add(new_lead)
                    saved_leads.append(new_lead)
                
                # Commit in batches to manage memory
                if (i + 1) % batch_commit_size == 0:
                    db.session.commit()
                    logger.info(f"Committed batch {i + 1} leads to database")
                    
            except Exception as e:
                logger.error(f"Failed to save lead {lead_data.get('username', 'unknown')}: {e}")
                continue
        
        # Final commit for remaining items
        db.session.commit()
        logger.info(f"Successfully saved {len(saved_leads)} leads to database")
        
    except Exception as e:
        logger.error(f"Failed to commit leads to database: {e}")
        db.session.rollback()
        raise
    finally:
        # Ensure session cleanup
        db.session.close()
    
    # Return dictionary format for API response (create new session for reading)
    with app.app_context():
        fresh_leads = Lead.query.filter_by(hashtag=keyword).order_by(Lead.created_at.desc()).all()
        return [lead.to_dict() for lead in fresh_leads]


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
        # Clear leads from database
        Lead.query.delete()
        ProcessingSession.query.delete()
        db.session.commit()
        
        app_data['processing_status'] = None
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to clear data: {e}")
        db.session.rollback()
        return {"error": "Failed to clear data"}, 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

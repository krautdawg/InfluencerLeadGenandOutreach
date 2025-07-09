import os
import asyncio
import logging
import json
import base64
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

# Initialize OpenAI client
# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Global storage for results (in production, use a proper database)
app_data = {'leads': [], 'processing_status': None}


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
            # Call Apify profile enrichment actor
            input_data = {"usernames": usernames, "sessionid": ig_sessionid}

            profile_data = await call_apify_actor("8WEn9FvZnhE7lM3oA",
                                                  input_data, apify_token)
            enriched_profiles = []

            # Process each profile
            for username in usernames:
                profile_info = profile_data.get(
                    'items', [{}])[0] if profile_data.get('items') else {}

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
    return render_template('index.html',
                           ig_sessionid=ig_sessionid,
                           leads=app_data['leads'],
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

    if not keyword:
        return {"error": "Keyword is required"}, 400

    ig_sessionid = session.get('ig_sessionid') or os.environ.get(
        'IG_SESSIONID')
    if not ig_sessionid:
        return {"error": "Instagram Session ID not found"}, 400

    # Start processing in background using ThreadPoolExecutor
    app_data['processing_status'] = 'Processing...'

    try:
        # Run the async processing in a thread pool
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_async_process, keyword, ig_sessionid)
            result = future.result(timeout=300)  # 5 minute timeout

        app_data['processing_status'] = None
        return {"success": True, "leads": result}

    except Exception as e:
        logger.error(f"Processing failed: {e}")
        app_data['processing_status'] = None
        return {"error": str(e)}, 500


def run_async_process(keyword, ig_sessionid):
    """Run async processing in a separate thread"""
    try:
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                process_keyword_async(keyword, ig_sessionid))
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"Async processing failed: {e}")
        raise


async def process_keyword_async(keyword, ig_sessionid):
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

    # Step 1: Hashtag crawl - Using correct Apify API format
    hashtag_input = {
        "search": keyword,
        "searchType": "hashtag",
        "searchLimit": 100
    }

    hashtag_data = call_apify_actor_sync("DrF9mzPPEuVizVF4l", hashtag_input,
                                         apify_token)

    # Step 2: Flatten and deduplicate
    all_posts = []
    for item in hashtag_data.get('items', []):
        all_posts.extend(item.get('latestPosts', []))
        all_posts.extend(item.get('topPosts', []))

    # Extract unique usernames
    profiles = []
    for post in all_posts:
        if post.get('ownerUsername'):
            profiles.append({
                'hashtag': keyword,
                'username': post['ownerUsername']
            })

    unique_profiles, duplicates = deduplicate_profiles(profiles)

    # Step 3: Profile enrichment with concurrency
    semaphore = asyncio.Semaphore(10)  # Limit to 10 concurrent calls
    perplexity_semaphore = asyncio.Semaphore(
        5)  # Limit to 5 concurrent Perplexity calls

    # Batch usernames for processing
    usernames = [p['username'] for p in unique_profiles]
    batch_size = 5
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

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Flatten results
    enriched_leads = []
    for result in results:
        if isinstance(result, list):
            enriched_leads.extend(result)
        else:
            logger.error(f"Batch processing error: {result}")

    # Mark duplicates
    for lead in enriched_leads:
        if lead['username'] in duplicates:
            lead['is_duplicate'] = True
        else:
            lead['is_duplicate'] = False

    # Store results
    app_data['leads'].extend(enriched_leads)

    return enriched_leads


@app.route('/draft/<username>', methods=['POST'])
def draft_email(username):
    """Generate email draft using OpenAI"""
    data = request.get_json()
    subject_prompt = data.get(
        'subject_prompt',
        'Generate a compelling subject line for an outreach email')
    body_prompt = data.get('body_prompt',
                           'Generate a personalized outreach email')

    # Find the lead
    lead = next((l for l in app_data['leads'] if l['username'] == username),
                None)
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
                f"Profile: @{lead['username']}, Name: {lead['fullName']}, Bio: {lead['bio']}"
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
                f"Profile: @{lead['username']}, Name: {lead['fullName']}, Bio: {lead['bio']}, Email: {lead['email']}"
            }],
            response_format={"type": "json_object"},
            max_tokens=500)

        subject_data = json.loads(subject_response.choices[0].message.content)
        body_data = json.loads(body_response.choices[0].message.content)

        # Update lead with generated content
        lead['subject'] = subject_data.get('subject',
                                           'Collaboration Opportunity')
        lead['emailBody'] = body_data.get(
            'body',
            'Hello, I would like to discuss a collaboration opportunity.')

        return {"subject": lead['subject'], "body": lead['emailBody']}

    except Exception as e:
        logger.error(f"Email drafting failed: {e}")
        return {"error": "Failed to generate email"}, 500


@app.route('/send/<username>', methods=['POST'])
def send_email(username):
    """Send email using Gmail API"""
    data = request.get_json()
    subject = data.get('subject', '')
    body = data.get('body', '')

    # Find the lead
    lead = next((l for l in app_data['leads'] if l['username'] == username),
                None)
    if not lead:
        return {"error": "Lead not found"}, 404

    if not lead.get('email'):
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
        message['to'] = lead['email']
        message['subject'] = subject

        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Send email
        send_result = service.users().messages().send(userId='me',
                                                      body={
                                                          'raw': raw_message
                                                      }).execute()

        # Update lead status
        lead['sent'] = True
        lead['sentAt'] = datetime.now().isoformat()
        lead['subject'] = subject
        lead['emailBody'] = body

        return {"success": True, "messageId": send_result['id']}

    except Exception as e:
        logger.error(f"Email sending failed: {e}")
        return {"error": f"Failed to send email: {str(e)}"}, 500


@app.route('/export/<format>')
def export_data(format):
    """Export data in different formats"""
    if not app_data['leads']:
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
            for lead in app_data['leads']:
                writer.writerow(
                    {k: lead.get(k, '')
                     for k in writer.fieldnames})

            return {
                "data":
                output.getvalue(),
                "filename":
                f"leads_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }

        elif format == 'json':
            return {
                "data":
                json.dumps(app_data['leads'], indent=2),
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
    app_data['leads'] = []
    app_data['processing_status'] = None
    return {"success": True}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

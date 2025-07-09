#!/usr/bin/env python3
"""
Test script for the first Apify API call (hashtag crawling)
This tests the DrF9mzPPEuVizVF4l actor with hashtag data collection
"""

import os
import json
import asyncio
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def call_apify_actor(actor_id, input_data, token):
    """Call Apify actor with run-sync"""
    url = f"https://api.apify.com/v2/acts/{actor_id}/run-sync"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"📡 Making API call to: {url}")
    print(f"🔑 Using actor: {actor_id}")
    print(f"📤 Input data: {json.dumps(input_data, indent=2)}")
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(url, headers=headers, json=input_data)
        print(f"📊 Response status: {response.status_code}")
        
        response.raise_for_status()
        return response.json()

async def test_hashtag_crawl():
    """Test the hashtag crawling functionality"""
    print("🚀 Testing Apify Hashtag Crawl (DrF9mzPPEuVizVF4l)")
    print("=" * 60)
    
    # Get required environment variables
    apify_token = os.environ.get('APIFY_TOKEN')
    ig_sessionid = os.environ.get('IG_SESSIONID') or os.environ.get('SESSION_SECRET')
    
    if not apify_token:
        print("❌ Error: APIFY_TOKEN not found in environment variables")
        return False
        
    if not ig_sessionid:
        print("❌ Error: IG_SESSIONID or SESSION_SECRET not found in environment variables")
        return False
    
    print(f"✅ APIFY_TOKEN: {'*' * (len(apify_token) - 4)}{apify_token[-4:]}")
    print(f"✅ IG_SESSIONID: {'*' * (len(ig_sessionid) - 4)}{ig_sessionid[-4:]}")
    print()
    
    # Test with a popular hashtag
    test_keyword = "fitness"
    
    # Prepare input data (same as in the main app)
    hashtag_input = {
        "hashtags": [test_keyword],
        "sessionid": ig_sessionid,
        "resultsLimit": 10  # Using smaller limit for testing
    }
    
    try:
        print(f"🔍 Testing hashtag: #{test_keyword}")
        hashtag_data = await call_apify_actor("DrF9mzPPEuVizVF4l", hashtag_input, apify_token)
        
        print("\n📋 Response Analysis:")
        print(f"   Response type: {type(hashtag_data)}")
        
        if isinstance(hashtag_data, dict):
            print(f"   Response keys: {list(hashtag_data.keys())}")
            
            items = hashtag_data.get('items', [])
            print(f"   Items count: {len(items)}")
            
            if items:
                print("\n📄 First item analysis:")
                first_item = items[0]
                print(f"   Item keys: {list(first_item.keys())}")
                
                latest_posts = first_item.get('latestPosts', [])
                top_posts = first_item.get('topPosts', [])
                
                print(f"   Latest posts: {len(latest_posts)}")
                print(f"   Top posts: {len(top_posts)}")
                
                # Analyze post structure
                all_posts = latest_posts + top_posts
                if all_posts:
                    print(f"\n📝 Sample post structure:")
                    sample_post = all_posts[0]
                    print(f"   Post keys: {list(sample_post.keys())}")
                    
                    if 'ownerUsername' in sample_post:
                        print(f"   Sample username: @{sample_post['ownerUsername']}")
                    
                    # Count unique usernames
                    usernames = set()
                    for post in all_posts:
                        if post.get('ownerUsername'):
                            usernames.add(post['ownerUsername'])
                    
                    print(f"   Unique usernames found: {len(usernames)}")
                    print(f"   First 5 usernames: {list(usernames)[:5]}")
                    
        print("\n✅ Hashtag crawl test completed successfully!")
        return True
        
    except httpx.HTTPStatusError as e:
        print(f"\n❌ HTTP Error: {e.response.status_code}")
        print(f"   Response: {e.response.text}")
        return False
        
    except Exception as e:
        print(f"\n❌ Error during hashtag crawl: {e}")
        return False

async def main():
    """Main test function"""
    print("🧪 Apify Hashtag Crawl API Test")
    print("Testing the first API call in the lead generation pipeline")
    print("=" * 60)
    
    success = await test_hashtag_crawl()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Test completed successfully!")
        print("The first Apify API call is working correctly.")
    else:
        print("💥 Test failed!")
        print("Please check your API credentials and try again.")

if __name__ == "__main__":
    asyncio.run(main())
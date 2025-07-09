#!/usr/bin/env python3
"""
Simple test for Apify API call with timeout handling
"""

import os
import json
import asyncio
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_apify_call():
    """Test Apify API call with proper timeout"""
    apify_token = os.environ.get('APIFY_TOKEN')
    ig_sessionid = os.environ.get('IG_SESSIONID') or os.environ.get('SESSION_SECRET')
    
    print(f"APIFY_TOKEN available: {bool(apify_token)}")
    print(f"IG_SESSIONID available: {bool(ig_sessionid)}")
    
    if not apify_token:
        print("❌ Missing APIFY_TOKEN")
        return
        
    if not ig_sessionid:
        print("❌ Missing IG_SESSIONID")
        return
    
    # Check if SESSION_SECRET looks like a proper Instagram session ID
    print(f"Session ID length: {len(ig_sessionid)}")
    print(f"Session ID starts with: {ig_sessionid[:10]}...")
    print(f"Session ID ends with: ...{ig_sessionid[-10:]}")
    
    # Test data
    hashtag_input = {
        "hashtags": ["test"],
        "sessionid": ig_sessionid,
        "resultsLimit": 5
    }
    
    url = "https://api.apify.com/v2/acts/DrF9mzPPEuVizVF4l/run-sync"
    headers = {
        "Authorization": f"Bearer {apify_token}",
        "Content-Type": "application/json"
    }
    
    print("Making API call...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:  # Shorter timeout
            response = await client.post(url, headers=headers, json=hashtag_input)
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 201:
                data = response.json()
                print("✅ API call successful!")
                print(f"Response keys: {list(data.keys())}")
                return True
            else:
                print(f"❌ API call failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except asyncio.TimeoutError:
        print("⏱️ API call timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_apify_call())
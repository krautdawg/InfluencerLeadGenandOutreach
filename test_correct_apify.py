#!/usr/bin/env python3
"""
Test Apify API call with correct input format based on official documentation
"""

import os
import json
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

async def test_correct_apify_format():
    """Test with the correct input format from Apify documentation"""
    apify_token = os.environ.get('APIFY_TOKEN')
    
    if not apify_token:
        print("❌ Missing APIFY_TOKEN")
        return False
    
    print("🧪 Testing Apify API with correct input format")
    print("=" * 50)
    
    # Correct input format based on official documentation
    run_input = {
        "search": "fitness",
        "searchType": "hashtag", 
        "searchLimit": 5
    }
    
    url = "https://api.apify.com/v2/acts/DrF9mzPPEuVizVF4l/run-sync"
    headers = {
        "Authorization": f"Bearer {apify_token}",
        "Content-Type": "application/json"
    }
    
    print(f"📤 Correct input format:")
    print(json.dumps(run_input, indent=2))
    print()
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print("🚀 Making API call...")
            response = await client.post(url, headers=headers, json=run_input)
            
            print(f"📊 Status: {response.status_code}")
            
            if response.status_code == 201:
                data = response.json()
                print("✅ API call successful!")
                print(f"Response keys: {list(data.keys())}")
                
                # Check if we have data
                if 'items' in data:
                    items = data['items']
                    print(f"Items found: {len(items)}")
                    
                    if items:
                        print("📋 Sample item structure:")
                        sample = items[0]
                        print(f"Keys: {list(sample.keys())}")
                        
                return True
            else:
                print(f"❌ Failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_correct_apify_format())
#!/usr/bin/env python3
"""
Quick test for Apify API to check immediate response
"""

import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

async def quick_test():
    apify_token = os.environ.get('APIFY_TOKEN')
    ig_sessionid = os.environ.get('IG_SESSIONID')
    
    print(f"Testing with IG session: {ig_sessionid[:20]}...")
    
    # Minimal test data
    data = {
        "hashtags": ["test"],
        "sessionid": ig_sessionid,
        "resultsLimit": 1
    }
    
    url = "https://api.apify.com/v2/acts/DrF9mzPPEuVizVF4l/run-sync"
    headers = {
        "Authorization": f"Bearer {apify_token}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, headers=headers, json=data)
            print(f"Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Error response: {response.text[:500]}")
            else:
                result = response.json()
                print(f"Success! Keys: {list(result.keys())}")
                
    except asyncio.TimeoutError:
        print("Still timing out after 10 seconds")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(quick_test())
#!/usr/bin/env python3
"""
Test using the official Apify client library
"""

import os
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

def test_apify_client():
    """Test with official Apify client"""
    apify_token = os.environ.get('APIFY_TOKEN')
    
    if not apify_token:
        print("❌ Missing APIFY_TOKEN")
        return False
    
    print("🧪 Testing with official Apify client")
    print("=" * 40)
    
    # Initialize the ApifyClient with API token
    client = ApifyClient(apify_token)
    
    # Prepare the Actor input (same as documentation)
    run_input = {
        "search": "fitness",
        "searchType": "hashtag",
        "searchLimit": 5
    }
    
    print(f"📤 Input: {run_input}")
    print("🚀 Starting Actor run...")
    
    try:
        # Run the Actor and wait for it to finish
        run = client.actor("DrF9mzPPEuVizVF4l").call(run_input=run_input)
        
        print("✅ Actor run completed!")
        print(f"Run info: {run}")
        
        # Fetch and print Actor results from the run's dataset
        dataset_items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        
        print(f"📊 Found {len(dataset_items)} items")
        
        if dataset_items:
            print("📋 Sample item:")
            sample = dataset_items[0]
            print(f"Keys: {list(sample.keys())}")
            
            # Look for username or profile data
            if 'username' in sample:
                print(f"Username: {sample['username']}")
            if 'displayName' in sample:
                print(f"Display name: {sample['displayName']}")
                
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_apify_client()
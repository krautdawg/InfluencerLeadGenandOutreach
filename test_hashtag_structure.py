#!/usr/bin/env python3
"""
Test to see the actual response structure from the hashtag actor
"""

import os
import json
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

def test_hashtag_structure():
    """Test hashtag actor response structure"""
    apify_token = os.environ.get('APIFY_TOKEN')
    
    if not apify_token:
        print("❌ Missing APIFY_TOKEN")
        return False
    
    print("🧪 Testing hashtag actor response structure")
    print("=" * 50)
    
    # Initialize the ApifyClient with API token
    client = ApifyClient(apify_token)
    
    # Prepare the Actor input
    run_input = {
        "search": "fitness",
        "searchType": "hashtag",
        "searchLimit": 3  # Small limit for testing
    }
    
    print(f"📤 Input: {run_input}")
    print("🚀 Starting Actor run...")
    
    try:
        # Run the Actor and wait for it to finish
        run = client.actor("DrF9mzPPEuVizVF4l").call(run_input=run_input)
        
        print("✅ Actor run completed!")
        
        # Fetch and analyze results
        dataset = client.dataset(run["defaultDatasetId"])
        items = list(dataset.iterate_items())
        
        print(f"\n📊 Found {len(items)} items in dataset")
        
        for i, item in enumerate(items[:3]):  # Analyze first 3 items
            print(f"\n🔍 Item {i+1} structure:")
            print(f"  Type: {type(item)}")
            print(f"  Keys: {list(item.keys()) if isinstance(item, dict) else 'Not a dict'}")
            
            if isinstance(item, dict):
                # Check for common fields
                for key in ['username', 'displayName', 'ownerUsername', 'owner', 'posts', 'latestPosts', 'topPosts', 'hashtag']:
                    if key in item:
                        value = item[key]
                        if isinstance(value, list):
                            print(f"  {key}: List with {len(value)} items")
                            if value and isinstance(value[0], dict):
                                print(f"    First item keys: {list(value[0].keys())}")
                        elif isinstance(value, dict):
                            print(f"  {key}: Dict with keys: {list(value.keys())}")
                        else:
                            print(f"  {key}: {value}")
                
                # If the item itself contains username/profile info
                if 'username' in item:
                    print(f"\n  ✅ Direct username found: {item['username']}")
                
                # Pretty print a sample of the full item (truncated)
                print(f"\n  Full item sample (truncated):")
                json_str = json.dumps(item, indent=2)
                print(json_str[:1000] + "..." if len(json_str) > 1000 else json_str)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_hashtag_structure()
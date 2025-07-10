#!/usr/bin/env python3
"""
Debug script to test Apify profile enrichment API and understand data structure
"""
import os
import json
from apify_client import ApifyClient

def test_profile_enrichment():
    """Test the profile enrichment API with a known Instagram profile"""
    apify_token = os.environ.get('APIFY_TOKEN')
    if not apify_token:
        print("APIFY_TOKEN not found in environment variables")
        return
    
    # Initialize the ApifyClient
    client = ApifyClient(apify_token)
    
    # Test data - a known Instagram profile
    test_urls = ["https://www.instagram.com/truenaturegermany"]
    ig_sessionid = os.environ.get('IG_SESSIONID', 'dummy_session')
    
    input_data = {
        "instagram_ids": test_urls,
        "SessionID": ig_sessionid,
        "proxy": {
            "useApifyProxy": True,
            "groups": ["RESIDENTIAL"],
        }
    }
    
    print("Testing Apify profile enrichment API...")
    print(f"Input data: {json.dumps(input_data, indent=2)}")
    
    try:
        # Run the actor and wait for it to finish
        run = client.actor("8WEn9FvZnhE7lM3oA").call(run_input=input_data)
        
        # Fetch the actor results from the run's dataset
        dataset = client.dataset(run["defaultDatasetId"])
        
        # Get all items from the dataset
        items = list(dataset.iterate_items())
        
        print(f"\nAPI Response - Number of items: {len(items)}")
        
        if items:
            print(f"\nFirst item structure:")
            print(json.dumps(items[0], indent=2, default=str))
            
            # Check specific fields we're interested in
            first_item = items[0]
            print(f"\nKey field values:")
            print(f"username: {first_item.get('username', 'NOT FOUND')}")
            print(f"full_name: {first_item.get('full_name', 'NOT FOUND')}")
            print(f"biography: {first_item.get('biography', 'NOT FOUND')}")
            print(f"follower_count: {first_item.get('follower_count', 'NOT FOUND')}")
            print(f"public_email: {first_item.get('public_email', 'NOT FOUND')}")
        else:
            print("No items returned from API")
            
    except Exception as e:
        print(f"Error calling Apify API: {e}")

if __name__ == "__main__":
    test_profile_enrichment()
#!/usr/bin/env python3
"""
Test both Apify API calls with correct formats
"""

import os
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

def test_hashtag_search():
    """Test the hashtag search API"""
    apify_token = os.environ.get('APIFY_TOKEN')
    client = ApifyClient(apify_token)
    
    print("🧪 Testing Hashtag Search API")
    print("=" * 40)
    
    # Test hashtag search
    run_input = {
        "search": "fitness",
        "searchType": "hashtag",
        "searchLimit": 3
    }
    
    print(f"📤 Input: {run_input}")
    
    try:
        run = client.actor("DrF9mzPPEuVizVF4l").call(run_input=run_input)
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        
        print(f"✅ Found {len(items)} hashtag results")
        
        if items:
            sample = items[0]
            print(f"📋 Sample keys: {list(sample.keys())}")
            
            # Look for usernames in the data
            usernames = []
            if 'username' in sample:
                usernames.append(sample['username'])
            elif 'ownerUsername' in sample:
                usernames.append(sample['ownerUsername'])
                
            print(f"🎯 Sample username: {usernames[0] if usernames else 'Not found'}")
            return usernames[:2] if usernames else []
        
        return []
        
    except Exception as e:
        print(f"❌ Hashtag search failed: {e}")
        return []

def test_profile_enrichment(usernames):
    """Test the profile enrichment API"""
    if not usernames:
        print("⚠️ No usernames to test profile enrichment")
        return
        
    apify_token = os.environ.get('APIFY_TOKEN')
    ig_sessionid = os.environ.get('IG_SESSIONID')
    client = ApifyClient(apify_token)
    
    print("\n🧪 Testing Profile Enrichment API")
    print("=" * 40)
    
    # Test profile enrichment
    instagram_urls = [f"https://www.instagram.com/{username}" for username in usernames]
    run_input = {
        "instagram_ids": instagram_urls,
        "SessionID": ig_sessionid,
        "proxy": {
            "useApifyProxy": True,
            "groups": ["RESIDENTIAL"],
        }
    }
    
    print(f"📤 Testing with usernames: {usernames}")
    
    try:
        run = client.actor("8WEn9FvZnhE7lM3oA").call(run_input=run_input)
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        
        print(f"✅ Found {len(items)} profile results")
        
        if items:
            sample = items[0]
            print(f"📋 Profile keys: {list(sample.keys())}")
            
            # Look for profile data
            fields = ['username', 'fullName', 'bio', 'email', 'followersCount']
            for field in fields:
                if field in sample:
                    print(f"   {field}: {sample[field]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Profile enrichment failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing both Apify APIs with correct formats")
    print("=" * 50)
    
    # Test hashtag search first
    usernames = test_hashtag_search()
    
    # Test profile enrichment with found usernames
    if usernames:
        test_profile_enrichment(usernames)
    
    print("\n🎯 API testing completed!")
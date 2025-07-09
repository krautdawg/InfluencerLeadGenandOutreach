#!/usr/bin/env python3
"""
Complete workflow test for the Instagram LeadGen application
"""

import requests
import json
import time

def test_workflow():
    """Test the complete workflow"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Full Instagram LeadGen Workflow")
    print("=" * 50)
    
    # Test 1: Health check
    print("1. Testing health check...")
    response = requests.get(f"{base_url}/ping")
    if response.status_code == 200:
        print("✅ Health check passed")
    else:
        print("❌ Health check failed")
        return False
    
    # Test 2: Set session ID
    print("\n2. Testing session ID setting...")
    session_data = {"ig_sessionid": "test_session_123"}
    response = requests.post(f"{base_url}/session", json=session_data)
    if response.status_code == 200:
        print("✅ Session ID set successfully")
        session_cookie = response.cookies
    else:
        print("❌ Session ID setting failed")
        return False
    
    # Test 3: Process keyword with session
    print("\n3. Testing keyword processing with session...")
    keyword_data = {"keyword": "fitness", "searchLimit": 3}
    
    # Use the same session
    response = requests.post(f"{base_url}/process", json=keyword_data, cookies=session_cookie, timeout=30)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Keyword processing successful")
        print(f"   Found {len(result.get('leads', []))} leads")
        return True
    else:
        print(f"❌ Keyword processing failed: {response.status_code}")
        try:
            error = response.json()
            print(f"   Error: {error}")
        except:
            print(f"   Response: {response.text}")
        return False

if __name__ == "__main__":
    success = test_workflow()
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n💥 Some tests failed!")
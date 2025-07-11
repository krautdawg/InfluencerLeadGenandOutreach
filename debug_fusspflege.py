#!/usr/bin/env python3
"""
Debug script to test Perplexity API with the fusspflege.neu.ulm profile
"""
import asyncio
import os
import sys
sys.path.append('.')
from main import call_perplexity_api

async def debug_fusspflege():
    """Test Perplexity API with the exact fusspflege profile data"""
    
    # Check if we have the API key
    api_key = os.environ.get('PERPLEXITY_API_KEY')
    if not api_key:
        print("❌ PERPLEXITY_API_KEY not found in environment")
        return
    
    # Exact profile data from database
    profile_data = {
        'username': 'fusspflege.neu.ulm',
        'full_name': 'I L S A⚜️W I N K L E R',
        'biography': '''I L S A⚜️W I N K L E R 
4500+ Behandlungen
Hunderte zufriedene Kunden
LOCATION // Elsa-Brandström-Straße 19, 
89231 Neu-Ulm
TERMINE // 01525 248 7666''',
        'email': '',  # Currently empty in database
        'phone': '',  # Currently empty in database  
        'website': 'http://www.winkler-fusspflege.de',  # Known website
        'follower_count': 0,
        'following_count': 0,
        'media_count': 0,
        'is_verified': False
    }
    
    print("🔍 Testing Perplexity API with fusspflege.neu.ulm profile...")
    print(f"📋 Profile data:")
    print(f"   Username: {profile_data['username']}")
    print(f"   Name: {profile_data['full_name']}")
    print(f"   Bio: {profile_data['biography']}")
    print(f"   Website: {profile_data['website']}")
    print(f"   Current email: '{profile_data['email']}'")
    print(f"   Current phone: '{profile_data['phone']}'")
    print()
    
    # Call the Perplexity API
    try:
        result = await call_perplexity_api(profile_data, api_key)
        print("✅ Perplexity API Response:")
        print(f"   Email: '{result.get('email', '')}'")
        print(f"   Phone: '{result.get('phone', '')}'")
        print(f"   Website: '{result.get('website', '')}'")
        print()
        
        # Expected findings
        expected_phone = "01525 248 7666"
        found_phone = result.get('phone', '')
        
        if expected_phone in found_phone or found_phone == expected_phone:
            print("✅ Phone number correctly extracted from bio!")
        else:
            print(f"❌ Phone number not found. Expected: {expected_phone}, Got: {found_phone}")
        
        if result.get('email'):
            print(f"✅ Email found: {result.get('email')}")
        else:
            print("ℹ️  No email found (this might be expected if website doesn't have contact email)")
            
    except Exception as e:
        print(f"❌ Error calling Perplexity API: {e}")

if __name__ == "__main__":
    asyncio.run(debug_fusspflege())
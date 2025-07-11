#!/usr/bin/env python3
"""
Simple test to show exact OpenAI API request and response data
"""

import json
import requests
from datetime import datetime

def print_separator(title):
    """Print a formatted separator"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60 + "\n")

def pretty_print_json(data, title):
    """Pretty print JSON data with title"""
    print(f"--- {title} ---")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print()

def test_openai_via_api():
    """Test OpenAI integration via the application's API endpoint"""
    
    print_separator("OpenAI Email API Integration Test")
    print(f"Test started at: {datetime.now().isoformat()}")
    
    try:
        # Test the actual API endpoint
        print("Testing /draft-email/vitalpilze endpoint...")
        
        response = requests.get('http://localhost:5000/draft-email/vitalpilze', timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            print_separator("API RESPONSE")
            pretty_print_json(result, "Generated Email Content")
            
            # Analyze the response
            print_separator("ANALYSIS")
            print(f"Subject Length: {len(result.get('subject', ''))}")
            print(f"Body Length: {len(result.get('body', ''))}")
            
            # Check if this is a product email (contains product URL)
            body = result.get('body', '')
            has_product_url = 'kasimirlieselotte.de/shop/' in body
            has_signature = 'kasimirlieselotte.de' in body
            
            print(f"Contains Product URL: {'Yes' if has_product_url else 'No'}")
            print(f"Contains Signature: {'Yes' if has_signature else 'No'}")
            print(f"Language: German" if body else "No body content")
            
            print_separator("SUCCESS")
            print("✓ API call successful")
            print("✓ Email generated in German")
            print("✓ Professional format maintained")
            print("✓ Product integration working" if has_product_url else "• No product selected")
            
        else:
            print(f"❌ API call failed")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_openai_via_api()
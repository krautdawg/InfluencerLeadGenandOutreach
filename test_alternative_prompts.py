"""
Test script to verify alternative prompts work correctly
- WITH product: Should use product-specific prompts and include product details
- WITHOUT product: Should use alternative prompts without product mentions
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def print_separator(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)

def test_without_product():
    """Test email generation WITHOUT product selected"""
    print_separator("TEST 1: WITHOUT PRODUCT SELECTED")
    
    # Remove product assignment
    response = requests.post(f"{BASE_URL}/api/leads/vitalpilze/product", 
                           json={"product_id": None})
    print("✅ Product removed:", response.json())
    
    # Generate email
    response = requests.get(f"{BASE_URL}/draft-email/vitalpilze")
    if response.status_code == 200:
        email_data = response.json()
        
        print("\n📧 Generated Email (WITHOUT Product):")
        print(f"Subject: {email_data['subject']}")
        print(f"Body: {email_data['body'][:200]}...")
        
        # Check for product mentions
        body = email_data['body']
        has_zeck_zack = 'Zeck Zack' in body
        has_funghi_funk = 'Funghi Funk' in body
        has_product_url = 'kasimirlieselotte.de/shop/' in body
        
        print(f"\n🔍 Analysis:")
        print(f"Contains 'Zeck Zack': {has_zeck_zack}")
        print(f"Contains 'Funghi Funk': {has_funghi_funk}")
        print(f"Contains product URL: {has_product_url}")
        
        if not has_zeck_zack and not has_funghi_funk and not has_product_url:
            print("✅ SUCCESS: No specific product mentions found (as expected)")
        else:
            print("❌ ISSUE: Alternative prompt may not be working")
            
    else:
        print(f"❌ Error: {response.status_code}")

def test_with_product():
    """Test email generation WITH product selected"""
    print_separator("TEST 2: WITH PRODUCT SELECTED (Zeck Zack)")
    
    # Assign Zeck Zack product
    response = requests.post(f"{BASE_URL}/api/leads/vitalpilze/product", 
                           json={"product_id": 1})
    print("✅ Product assigned:", response.json())
    
    # Generate email
    response = requests.get(f"{BASE_URL}/draft-email/vitalpilze")
    if response.status_code == 200:
        email_data = response.json()
        
        print("\n📧 Generated Email (WITH Product):")
        print(f"Subject: {email_data['subject']}")
        print(f"Body: {email_data['body'][:200]}...")
        
        # Check for product mentions
        body = email_data['body']
        has_zeck_zack = 'Zeck Zack' in body
        has_product_url = 'kasimirlieselotte.de/shop/Zeck-Zack' in body
        has_product_description = '100% rein' in body or 'ohne Zusatzstoffe' in body
        
        print(f"\n🔍 Analysis:")
        print(f"Contains 'Zeck Zack': {has_zeck_zack}")
        print(f"Contains product URL: {has_product_url}")
        print(f"Contains product description: {has_product_description}")
        
        if has_zeck_zack and has_product_url:
            print("✅ SUCCESS: Product information properly included")
        else:
            print("❌ ISSUE: Product information missing")
            
    else:
        print(f"❌ Error: {response.status_code}")

def test_with_funghi_funk():
    """Test email generation WITH Funghi Funk product"""
    print_separator("TEST 3: WITH PRODUCT SELECTED (Funghi Funk)")
    
    # Assign Funghi Funk product
    response = requests.post(f"{BASE_URL}/api/leads/vitalpilze/product", 
                           json={"product_id": 2})
    print("✅ Product assigned:", response.json())
    
    # Generate email
    response = requests.get(f"{BASE_URL}/draft-email/vitalpilze")
    if response.status_code == 200:
        email_data = response.json()
        
        print("\n📧 Generated Email (WITH Funghi Funk):")
        print(f"Subject: {email_data['subject']}")
        print(f"Body: {email_data['body'][:200]}...")
        
        # Check for product mentions
        body = email_data['body']
        has_funghi_funk = 'Funghi Funk' in body
        has_product_url = 'kasimirlieselotte.de/shop/Funghi-Funk' in body
        
        print(f"\n🔍 Analysis:")
        print(f"Contains 'Funghi Funk': {has_funghi_funk}")
        print(f"Contains product URL: {has_product_url}")
        
        if has_funghi_funk and has_product_url:
            print("✅ SUCCESS: Funghi Funk product information properly included")
        else:
            print("❌ ISSUE: Funghi Funk product information missing")
            
    else:
        print(f"❌ Error: {response.status_code}")

if __name__ == "__main__":
    print("🧪 ALTERNATIVE PROMPTS TEST SUITE")
    print("Testing both scenarios: with and without product selection")
    
    try:
        test_without_product()
        test_with_product() 
        test_with_funghi_funk()
        
        print_separator("TEST SUMMARY")
        print("✅ All tests completed!")
        print("Check the analysis results above to verify:")
        print("  - WITHOUT product: No specific product mentions")
        print("  - WITH product: Proper product integration")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
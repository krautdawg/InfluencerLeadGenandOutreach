#!/usr/bin/env python3
"""
Detailed test to capture exact OpenAI API requests and responses
Shows the precise data being sent to OpenAI including product information
"""

import json
import requests
from datetime import datetime

def print_separator(title):
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)

def test_openai_detailed():
    """Test with detailed request/response logging"""
    
    print_separator("DETAILED OpenAI API Integration Test")
    print(f"Test started at: {datetime.now().isoformat()}")
    
    # Step 1: Check current lead state
    print("\n1. Checking current lead state...")
    try:
        response = requests.get('http://localhost:5000/api/leads')
        if response.status_code == 200:
            leads_data = response.json()
            vitalpilze_leads = [lead for lead in leads_data.get('leads', []) if lead['username'] == 'vitalpilze']
            print(f"Found {len(vitalpilze_leads)} vitalpilze leads:")
            for i, lead in enumerate(vitalpilze_leads):
                print(f"  Lead {i+1}: product_id={lead.get('selected_product_id')}, id={lead.get('id')}")
                print(f"    Selected Product: {lead.get('selected_product')}")
        else:
            print(f"Failed to get leads: {response.status_code}")
    except Exception as e:
        print(f"Error getting leads: {e}")
    
    # Step 2: Check available products
    print("\n2. Checking available products...")
    try:
        response = requests.get('http://localhost:5000/api/products')
        if response.status_code == 200:
            products_data = response.json()
            print("Available products:")
            for product in products_data.get('products', []):
                print(f"  ID {product['id']}: {product['name']}")
                print(f"    URL: {product['url']}")
                print(f"    Description: {product['description']}")
        else:
            print(f"Failed to get products: {response.status_code}")
    except Exception as e:
        print(f"Error getting products: {e}")
    
    # Step 3: Ensure product is assigned
    print("\n3. Assigning product to vitalpilze lead...")
    try:
        response = requests.post(
            'http://localhost:5000/api/leads/vitalpilze/product',
            headers={'Content-Type': 'application/json'},
            json={'product_id': 1}
        )
        if response.status_code == 200:
            print("✓ Product assigned successfully")
        else:
            print(f"Failed to assign product: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error assigning product: {e}")
    
    # Step 4: Generate email and capture request
    print("\n4. Generating email with detailed logging...")
    
    # Enable debug logging by setting environment variable
    import os
    os.environ['OPENAI_LOG_LEVEL'] = 'DEBUG'
    
    try:
        print("Making request to /draft-email/vitalpilze...")
        response = requests.get('http://localhost:5000/draft-email/vitalpilze')
        
        if response.status_code == 200:
            result = response.json()
            
            print_separator("EMAIL GENERATION RESULT")
            print("Subject:")
            print(f"  {result.get('subject', 'N/A')}")
            print("\nBody:")
            print(f"  {result.get('body', 'N/A')[:200]}...")
            
            # Check for product integration
            body = result.get('body', '')
            subject = result.get('subject', '')
            
            print_separator("PRODUCT INTEGRATION ANALYSIS")
            
            # Check for Zeck Zack product
            zeck_zack_mentioned = 'zeck zack' in body.lower()
            product_url_included = 'kasimirlieselotte.de/shop/Zeck-Zack-Spray' in body
            product_description_included = '100% rein ohne Zusatzstoffe' in body
            made_in_germany = 'Deutschland' in body
            
            print(f"✓ Product name 'Zeck Zack' mentioned: {zeck_zack_mentioned}")
            print(f"✓ Product URL included: {product_url_included}")
            print(f"✓ Product description included: {product_description_included}")
            print(f"✓ 'Made in Germany' mentioned: {made_in_germany}")
            
            if product_url_included:
                print("✅ PRODUCT INTEGRATION WORKING CORRECTLY")
            else:
                print("❌ PRODUCT INTEGRATION NOT WORKING")
                print("Expected URL: https://www.kasimirlieselotte.de/shop/Zeck-Zack-Spray-50-ml-kaufen")
                print("Searching for URL in body...")
                if 'kasimirlieselotte.de' in body:
                    # Extract the URL part
                    start = body.find('kasimirlieselotte.de')
                    end = body.find(' ', start)
                    if end == -1:
                        end = body.find(')', start)
                    if end == -1:
                        end = start + 50
                    found_url = body[start:end]
                    print(f"Found URL fragment: {found_url}")
                else:
                    print("No kasimirlieselotte.de URL found in body")
            
            print_separator("FULL EMAIL CONTENT")
            print("SUBJECT:")
            print(subject)
            print("\nBODY:")
            print(body)
            
        else:
            print(f"❌ Email generation failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Email generation error: {e}")
    
    print_separator("TEST COMPLETED")

if __name__ == "__main__":
    test_openai_detailed()
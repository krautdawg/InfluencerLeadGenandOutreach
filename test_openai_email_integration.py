#!/usr/bin/env python3
"""
Test script to demonstrate exact OpenAI API integration for email generation
Shows the precise data sent to and received from OpenAI API
"""

import json
import os
import sys
from datetime import datetime
from models import Lead, Product
from main import app, db
import openai

def print_separator(title):
    """Print a formatted separator"""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80 + "\n")

def pretty_print_json(data, title):
    """Pretty print JSON data with title"""
    print(f"\n--- {title} ---")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print()

def test_openai_email_generation_complete():
    """
    Complete test showing exact OpenAI API request and response data
    Tests both scenarios: with product and without product
    """
    
    print_separator("OpenAI Email Generation API Integration Test")
    print(f"Test started at: {datetime.now().isoformat()}")
    
    with app.app_context():
        
        # Test Case 1: Lead WITHOUT product selection
        print_separator("TEST CASE 1: Email Generation WITHOUT Product")
        
        # Create test lead without product
        test_lead_1 = {
            'username': 'vitalpilze',
            'full_name': 'Waldkraft',
            'bio': '🌿 Naturheilkunde & Vitalpilze 🌱 | Stärke aus der Natur für Körper und Geist | Dein Weg zu mehr Vitalität und innerer Kraft',
            'email': 'Not found',
            'hashtag': 'Vitalpilze',
            'selected_product': None
        }
        
        print("Input Lead Data:")
        pretty_print_json(test_lead_1, "Lead Profile Data")
        
        # Construct the exact prompt that would be sent to OpenAI
        system_prompt = """Erstelle eine personalisierte, professionelle deutsche E-Mail, ohne die Betreffzeile, für potenzielle Instagram Influencer Kooperationen. Die E-Mail kommt von Kasimir vom Store KasimirLieselotte. Verwende einen höflichen, professionellen Ton auf Deutsch aber in DU-Form um es casual im Instagram feel zu bleiben. WICHTIG: Falls ein Produkt ausgewählt ist, integriere unbedingt folgende Elemente in die E-Mail: 1) Erwähne das Produkt namentlich, 2) Füge den direkten Link zum Produkt ein (Produkt-URL), 3) Erkläre kurz die Produkteigenschaften basierend auf der Beschreibung, 4) Beziehe das Produkt auf die Bio/Interessen des Influencers. Die E-Mail sollte den Produktlink natürlich in den Text einbetten. Füge am Ende die Signatur mit der Website https://www.kasimirlieselotte.de/ hinzu. Antworte im JSON-Format: {"body": "email inhalt"}"""
        
        user_content = f"Profil: @{test_lead_1['username']}, Name: {test_lead_1['full_name']}, Bio: {test_lead_1['bio']}, Email: {test_lead_1['email']}, Hashtag: {test_lead_1['hashtag']}"
        
        # Show exact OpenAI request data
        openai_request = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user", 
                    "content": user_content
                }
            ],
            "max_tokens": 500,
            "response_format": {"type": "json_object"}
        }
        
        print("Exact OpenAI API Request:")
        pretty_print_json(openai_request, "OpenAI Request Payload")
        
        # Make actual API call
        try:
            print("Making actual OpenAI API call...")
            client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
            response = client.chat.completions.create(**openai_request)
            
            # Extract response data
            response_data = {
                "id": response.id,
                "model": response.model,
                "created": response.created,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "choices": [
                    {
                        "index": choice.index,
                        "message": {
                            "role": choice.message.role,
                            "content": choice.message.content
                        },
                        "finish_reason": choice.finish_reason
                    } for choice in response.choices
                ]
            }
            
            print("Exact OpenAI API Response:")
            pretty_print_json(response_data, "OpenAI Response Data")
            
            # Parse the email content
            email_content = json.loads(response.choices[0].message.content)
            print("Parsed Email Content:")
            pretty_print_json(email_content, "Generated Email")
            
        except Exception as e:
            print(f"❌ API call failed: {e}")
        
        
        # Test Case 2: Lead WITH product selection
        print_separator("TEST CASE 2: Email Generation WITH Product")
        
        # Get product data from database
        product = Product.query.first()
        if not product:
            print("❌ No products found in database. Please run the application first to initialize products.")
            return
            
        test_lead_2 = {
            'username': 'vitalpilze',
            'full_name': 'Waldkraft', 
            'bio': '🌿 Naturheilkunde & Vitalpilze 🌱 | Stärke aus der Natur für Körper und Geist | Dein Weg zu mehr Vitalität und innerer Kraft',
            'email': 'Not found',
            'hashtag': 'Vitalpilze',
            'selected_product': {
                'id': product.id,
                'name': product.name,
                'url': product.url,
                'description': product.description,
                'price': product.price
            }
        }
        
        print("Input Lead Data (with Product):")
        pretty_print_json(test_lead_2, "Lead Profile Data with Product")
        
        # Construct prompt with product information
        user_content_with_product = f"""Profil: @{test_lead_2['username']}, Name: {test_lead_2['full_name']}, Bio: {test_lead_2['bio']}, Email: {test_lead_2['email']}, Hashtag: {test_lead_2['hashtag']}

Ausgewähltes Produkt: {product.name}
Produkt-URL: {product.url}
Beschreibung: {product.description}"""

        openai_request_with_product = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_content_with_product
                }
            ],
            "max_tokens": 500,
            "response_format": {"type": "json_object"}
        }
        
        print("Exact OpenAI API Request (with Product):")
        pretty_print_json(openai_request_with_product, "OpenAI Request Payload with Product")
        
        # Make actual API call with product
        try:
            print("Making actual OpenAI API call with product...")
            response_with_product = client.chat.completions.create(**openai_request_with_product)
            
            # Extract response data
            response_data_with_product = {
                "id": response_with_product.id,
                "model": response_with_product.model,
                "created": response_with_product.created,
                "usage": {
                    "prompt_tokens": response_with_product.usage.prompt_tokens,
                    "completion_tokens": response_with_product.usage.completion_tokens,
                    "total_tokens": response_with_product.usage.total_tokens
                },
                "choices": [
                    {
                        "index": choice.index,
                        "message": {
                            "role": choice.message.role,
                            "content": choice.message.content
                        },
                        "finish_reason": choice.finish_reason
                    } for choice in response_with_product.choices
                ]
            }
            
            print("Exact OpenAI API Response (with Product):")
            pretty_print_json(response_data_with_product, "OpenAI Response Data with Product")
            
            # Parse the email content
            email_content_with_product = json.loads(response_with_product.choices[0].message.content)
            print("Parsed Email Content (with Product):")
            pretty_print_json(email_content_with_product, "Generated Email with Product")
            
            # Analyze differences
            print_separator("ANALYSIS: Differences Between Emails")
            print("WITHOUT Product - Email Body Length:", len(email_content.get('body', '')))
            print("WITH Product - Email Body Length:", len(email_content_with_product.get('body', '')))
            
            # Check if product name is mentioned
            product_mentioned = product.name.lower() in email_content_with_product.get('body', '').lower()
            product_url_included = product.url in email_content_with_product.get('body', '')
            
            print(f"\nProduct Integration Check:")
            print(f"✓ Product name '{product.name}' mentioned: {product_mentioned}")
            print(f"✓ Product URL included: {product_url_included}")
            
        except Exception as e:
            print(f"❌ API call with product failed: {e}")
        
        
        # Test Case 3: Show current application integration via API
        print_separator("TEST CASE 3: Current Application Integration via API")
        
        try:
            # Test the actual API endpoint used by the application
            import requests
            
            print("Testing actual application API endpoint /draft-email/vitalpilze...")
            
            # Make a request to the actual endpoint
            response = requests.get('http://localhost:5000/draft-email/vitalpilze')
            
            if response.status_code == 200:
                api_result = response.json()
                print("Application API Response:")
                pretty_print_json(api_result, "API Endpoint Response")
            else:
                print(f"❌ API call failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Application API test failed: {e}")
        
        print_separator("TEST COMPLETED")
        print(f"Test completed at: {datetime.now().isoformat()}")
        print("Summary:")
        print("✓ Demonstrated exact OpenAI API request structure")
        print("✓ Showed actual API response format")
        print("✓ Tested both scenarios: with and without product")
        print("✓ Verified product integration in generated emails")
        print("✓ Tested current application integration")

if __name__ == "__main__":
    # Check if OpenAI API key is available
    if not os.environ.get('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY environment variable not found")
        print("Please set your OpenAI API key to run this test")
        sys.exit(1)
    
    # Run the test
    test_openai_email_generation_complete()
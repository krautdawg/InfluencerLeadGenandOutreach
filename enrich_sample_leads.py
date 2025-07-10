#!/usr/bin/env python3
"""
Sample enrichment script to demonstrate the process on a few leads
"""

import asyncio
import os
from main import app, db, Lead, call_perplexity_api

async def enrich_sample_leads():
    """Enrich a few sample leads to show the process"""
    
    api_key = os.environ.get('PERPLEXITY_API_KEY')
    if not api_key:
        print("No PERPLEXITY_API_KEY found")
        return
    
    print("🔍 PERPLEXITY API ENRICHMENT DEMONSTRATION")
    print("=" * 60)
    
    with app.app_context():
        # Get leads that don't have complete contact info
        leads = Lead.query.filter(
            (Lead.email.is_(None) | (Lead.email == '')) |
            (Lead.phone.is_(None) | (Lead.phone == '')) |
            (Lead.website.is_(None) | (Lead.website == ''))
        ).limit(3).all()
        
        if not leads:
            print("No leads found needing enrichment")
            return
        
        for i, lead in enumerate(leads, 1):
            print(f"\n[{i}] PROCESSING: {lead.username}")
            print("-" * 40)
            
            # Show BEFORE state
            before = {
                'email': lead.email or '',
                'phone': lead.phone or '',
                'website': lead.website or ''
            }
            print(f"BEFORE: Email='{before['email']}', Phone='{before['phone']}', Website='{before['website']}'")
            
            # Prepare profile data
            profile_data = {
                'username': lead.username,
                'full_name': lead.full_name or '',
                'biography': lead.bio or '',
                'email': lead.email or '',
                'phone': lead.phone or '',
                'website': lead.website or '',
                'follower_count': lead.followers_count or 0,
                'following_count': lead.following_count or 0,
                'media_count': lead.posts_count or 0,
                'is_verified': lead.is_verified or False
            }
            
            try:
                # Call Perplexity API
                enriched_data = await call_perplexity_api(profile_data, api_key)
                print(f"API RESULT: {enriched_data}")
                
                # Track changes
                changes = []
                
                # Update only empty fields
                if enriched_data.get('email') and not before['email']:
                    lead.email = enriched_data['email']
                    changes.append(f"Email: '{enriched_data['email']}'")
                
                if enriched_data.get('phone') and not before['phone']:
                    lead.phone = enriched_data['phone']
                    changes.append(f"Phone: '{enriched_data['phone']}'")
                
                if enriched_data.get('website') and not before['website']:
                    lead.website = enriched_data['website']
                    changes.append(f"Website: '{enriched_data['website']}'")
                
                # Show AFTER state
                after = {
                    'email': lead.email or '',
                    'phone': lead.phone or '',
                    'website': lead.website or ''
                }
                print(f"AFTER:  Email='{after['email']}', Phone='{after['phone']}', Website='{after['website']}'")
                
                if changes:
                    db.session.commit()
                    print(f"✅ CHANGES MADE: {', '.join(changes)}")
                else:
                    print("ℹ️  NO NEW DATA FOUND")
                
                # Small delay
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"❌ ERROR: {str(e)}")
        
        print("\n" + "=" * 60)
        print("ENRICHMENT DEMONSTRATION COMPLETE")

if __name__ == "__main__":
    asyncio.run(enrich_sample_leads())
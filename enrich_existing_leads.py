#!/usr/bin/env python3
"""
Script to enrich existing leads with Perplexity API
This will add missing contact information to existing database records
"""

import asyncio
import os
import sys
from datetime import datetime
from main import app, db, Lead, call_perplexity_api

async def enrich_existing_leads():
    """Enrich all existing leads with Perplexity API"""
    
    # Check for API key
    api_key = os.environ.get('PERPLEXITY_API_KEY')
    if not api_key:
        print("❌ PERPLEXITY_API_KEY not found in environment variables")
        return
    
    print("🔍 Starting enrichment of existing leads...")
    print("=" * 60)
    
    with app.app_context():
        # Get all leads from database
        leads = Lead.query.all()
        
        if not leads:
            print("No leads found in database")
            return
        
        print(f"Found {len(leads)} leads to process")
        print()
        
        enriched_count = 0
        updated_count = 0
        
        for i, lead in enumerate(leads, 1):
            print(f"[{i}/{len(leads)}] Processing: {lead.username}")
            
            # Show current contact data
            current_data = {
                'email': lead.email or '',
                'phone': lead.phone or '',
                'website': lead.website or ''
            }
            
            print(f"  Current: Email={current_data['email'] or 'None'}, "
                  f"Phone={current_data['phone'] or 'None'}, "
                  f"Website={current_data['website'] or 'None'}")
            
            # Prepare profile data for API
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
                enriched_count += 1
                
                # Check what's new
                changes_made = False
                changes = []
                
                # Check email
                if enriched_data.get('email') and enriched_data['email'] != current_data['email']:
                    if not current_data['email']:  # Only update if empty
                        lead.email = enriched_data['email']
                        changes.append(f"Email: {enriched_data['email']}")
                        changes_made = True
                
                # Check phone
                if enriched_data.get('phone') and enriched_data['phone'] != current_data['phone']:
                    if not current_data['phone']:  # Only update if empty
                        lead.phone = enriched_data['phone']
                        changes.append(f"Phone: {enriched_data['phone']}")
                        changes_made = True
                
                # Check website
                if enriched_data.get('website') and enriched_data['website'] != current_data['website']:
                    if not current_data['website']:  # Only update if empty
                        lead.website = enriched_data['website']
                        changes.append(f"Website: {enriched_data['website']}")
                        changes_made = True
                
                if changes_made:
                    lead.updated_at = datetime.utcnow()
                    db.session.commit()
                    updated_count += 1
                    print(f"  ✅ Updated: {', '.join(changes)}")
                else:
                    print(f"  ℹ️  No new data found or all fields already populated")
                
                # Add delay to avoid rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"  ❌ Error processing {lead.username}: {str(e)}")
            
            print()
        
        print("=" * 60)
        print(f"📊 ENRICHMENT SUMMARY:")
        print(f"   Total leads processed: {len(leads)}")
        print(f"   API calls made: {enriched_count}")
        print(f"   Leads updated: {updated_count}")
        print(f"   Leads unchanged: {len(leads) - updated_count}")

if __name__ == "__main__":
    asyncio.run(enrich_existing_leads())
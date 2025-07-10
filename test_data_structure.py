#!/usr/bin/env python3
"""
Create test data to understand the UI layout and verify the data flow
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from main import app
from models import db, Lead
from datetime import datetime

def create_test_data():
    """Create some test data to verify the UI and data flow"""
    with app.app_context():
        # Clear existing test data
        Lead.query.filter_by(hashtag='test_data').delete()
        
        # Create test leads with various data scenarios
        test_leads = [
            {
                'username': 'test_user_1',
                'hashtag': 'test_data',
                'full_name': 'Test User One',
                'bio': 'This is a test bio for user 1',
                'email': 'test1@example.com',
                'phone': '+49 123 456 7890',
                'website': 'https://example.com',
                'followers_count': 12500,
                'following_count': 850,
                'posts_count': 234,
                'is_verified': True,
                'profile_pic_url': 'https://via.placeholder.com/150',
                'is_duplicate': False
            },
            {
                'username': 'test_user_2',
                'hashtag': 'test_data',
                'full_name': 'Test User Two',
                'bio': 'Another test bio with German text: Hallo Welt! Ich bin ein Test-Benutzer.',
                'email': 'test2@example.de',
                'followers_count': 5420,
                'following_count': 1200,
                'posts_count': 89,
                'is_verified': False,
                'is_duplicate': False
            },
            {
                'username': 'test_duplicate',
                'hashtag': 'test_data',
                'full_name': '',  # Empty name to test missing data
                'bio': '',
                'email': '',
                'followers_count': 0,
                'following_count': 0,
                'posts_count': 0,
                'is_verified': False,
                'is_duplicate': True
            }
        ]
        
        for lead_data in test_leads:
            new_lead = Lead(
                username=lead_data['username'],
                hashtag=lead_data['hashtag'],
                full_name=lead_data['full_name'],
                bio=lead_data['bio'],
                email=lead_data['email'],
                phone=lead_data.get('phone', ''),
                website=lead_data.get('website', ''),
                followers_count=lead_data['followers_count'],
                following_count=lead_data['following_count'],
                posts_count=lead_data['posts_count'],
                is_verified=lead_data['is_verified'],
                profile_pic_url=lead_data.get('profile_pic_url', ''),
                is_duplicate=lead_data['is_duplicate'],
                created_at=datetime.utcnow()
            )
            db.session.add(new_lead)
        
        db.session.commit()
        print(f"Created {len(test_leads)} test leads")
        
        # Query and display the test data to verify
        test_leads_query = Lead.query.filter_by(hashtag='test_data').all()
        print("\nTest data verification:")
        for lead in test_leads_query:
            print(f"- {lead.username}: {lead.full_name}, {lead.followers_count} followers, email: {lead.email}")

if __name__ == "__main__":
    create_test_data()
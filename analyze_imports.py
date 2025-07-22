#!/usr/bin/env python3
import json
import psycopg2
import os

def analyze_import_conflicts():
    """Analyze conflicts between new JSON data and existing database records"""
    
    # Connect to database
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    cur = conn.cursor()
    
    # Load new data
    with open('attached_assets/v2_hashtag_username_pair_1753225076256.json', 'r') as f:
        new_hashtag_data = json.load(f)
    
    with open('attached_assets/v2_lead_1753225076257.json', 'r') as f:
        new_lead_data = json.load(f)
    
    # Get existing usernames from database
    cur.execute("SELECT DISTINCT username FROM hashtag_username_pair")
    existing_hashtag_usernames = set([row[0] for row in cur.fetchall()])
    
    cur.execute("SELECT DISTINCT username FROM lead") 
    existing_lead_usernames = set([row[0] for row in cur.fetchall()])
    
    # Analyze new data
    new_hashtag_usernames = set([record['username'] for record in new_hashtag_data])
    new_lead_usernames = set([record['username'] for record in new_lead_data])
    
    # Find conflicts (duplicates by username)
    hashtag_conflicts = new_hashtag_usernames.intersection(existing_hashtag_usernames)
    lead_conflicts = new_lead_usernames.intersection(existing_lead_usernames)
    
    print("=== IMPORT ANALYSIS REPORT ===\n")
    
    print("HASHTAG_USERNAME_PAIR TABLE:")
    print(f"  • Current records in DB: {len(existing_hashtag_usernames)} unique usernames")
    print(f"  • New records to import: {len(new_hashtag_data)} records")
    print(f"  • Unique usernames in new data: {len(new_hashtag_usernames)}")
    print(f"  • Username conflicts (will be skipped): {len(hashtag_conflicts)}")
    print(f"  • Records that will be ADDED: {len(new_hashtag_usernames) - len(hashtag_conflicts)}")
    
    print(f"\nLEAD TABLE:")
    print(f"  • Current records in DB: {len(existing_lead_usernames)} unique usernames")
    print(f"  • New records to import: {len(new_lead_data)} records")
    print(f"  • Unique usernames in new data: {len(new_lead_usernames)}")
    print(f"  • Username conflicts (will be skipped): {len(lead_conflicts)}")
    print(f"  • Records that will be ADDED: {len(new_lead_usernames) - len(lead_conflicts)}")
    
    print(f"\nSUMMARY:")
    total_to_add = (len(new_hashtag_usernames) - len(hashtag_conflicts)) + (len(new_lead_usernames) - len(lead_conflicts))
    total_conflicts = len(hashtag_conflicts) + len(lead_conflicts)
    print(f"  • Total new records to be added: {total_to_add}")
    print(f"  • Total conflicts (duplicates skipped): {total_conflicts}")
    
    # Show some sample conflicts
    if hashtag_conflicts:
        print(f"\nSample hashtag_username_pair conflicts: {list(hashtag_conflicts)[:5]}")
    if lead_conflicts:
        print(f"Sample lead conflicts: {list(lead_conflicts)[:5]}")
    
    cur.close()
    conn.close()
    
    return {
        'hashtag_to_add': len(new_hashtag_usernames) - len(hashtag_conflicts),
        'lead_to_add': len(new_lead_usernames) - len(lead_conflicts),
        'hashtag_conflicts': len(hashtag_conflicts),
        'lead_conflicts': len(lead_conflicts)
    }

if __name__ == "__main__":
    results = analyze_import_conflicts()
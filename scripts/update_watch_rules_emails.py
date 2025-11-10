#!/usr/bin/env python3
"""
Update watch rules to have proper user_email addresses

This script updates existing watch rules that have user_email='N/A'
to use the FROM_EMAIL environment variable.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.firestore_client import FirestoreClient
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()

    print("=" * 80)
    print("Updating Watch Rules Email Addresses")
    print("=" * 80)
    print()

    # Get FROM_EMAIL from environment
    from_email = os.environ.get('FROM_EMAIL', 'gkartik.extraneous@gmail.com')
    print(f"Default email address: {from_email}")
    print()

    client = FirestoreClient()

    # Get all watch rules
    rules_ref = client.db.collection('watch_rules')
    rules_to_update = []

    for doc in rules_ref.stream():
        rule_data = doc.to_dict()
        rule_data['id'] = doc.id

        if rule_data.get('user_email') == 'N/A' or not rule_data.get('user_email'):
            rules_to_update.append(rule_data)

    print(f"Found {len(rules_to_update)} rules with user_email='N/A'")
    print()

    if not rules_to_update:
        print("No rules to update!")
        return

    # Update each rule
    for i, rule in enumerate(rules_to_update, 1):
        rule_id = rule['id']
        rule_name = rule.get('name', 'unnamed')
        rule_type = rule.get('rule_type', 'unknown')

        print(f"[{i}/{len(rules_to_update)}] Updating rule: {rule_name}")
        print(f"  ID: {rule_id}")
        print(f"  Type: {rule_type}")
        print(f"  Old email: {rule.get('user_email', 'N/A')}")
        print(f"  New email: {from_email}")

        try:
            # Update in Firestore
            client.db.collection('watch_rules').document(rule_id).update({
                'user_email': from_email,
                'user_name': 'Researcher'  # Add default user name
            })

            print(f"  ✓ Updated rule {rule_id}")
            print()

        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            print()

    print("=" * 80)
    print("Update complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()

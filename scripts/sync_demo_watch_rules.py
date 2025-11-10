#!/usr/bin/env python3
"""
Sync watch rules with demo.html/index.html
Replaces existing test rules with the 4 meaningful demo rules
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
    print("Syncing Watch Rules with Demo")
    print("=" * 80)
    print()

    # Get FROM_EMAIL from environment
    from_email = os.environ.get('FROM_EMAIL', 'gkartik.extraneous@gmail.com')
    print(f"Using email address: {from_email}")
    print()

    client = FirestoreClient()

    # Delete ALL existing watch rules
    print("Step 1: Deleting all existing watch rules...")
    rules_ref = client.db.collection('watch_rules')
    deleted_count = 0
    for doc in rules_ref.stream():
        doc.reference.delete()
        deleted_count += 1
        print(f"  Deleted: {doc.id}")

    print(f"✓ Deleted {deleted_count} existing rules")
    print()

    # Create the 4 demo watch rules
    print("Step 2: Creating demo watch rules...")

    demo_rules = [
        {
            "name": "Multimodal Learning Research",
            "rule_type": "claim",
            "claim_description": "Research advancing multimodal learning that combines vision, language, or other modalities to achieve new capabilities",
            "user_email": from_email,
            "user_name": "Researcher",
            "active": True
        },
        {
            "name": "Language Model Reasoning & Planning",
            "rule_type": "claim",
            "claim_description": "Methods that enhance language model reasoning, planning, or problem-solving through novel prompting or inference strategies",
            "user_email": from_email,
            "user_name": "Researcher",
            "active": True
        },
        {
            "name": "Open-Source Foundation Models",
            "rule_type": "claim",
            "claim_description": "Release of open-source foundation models that achieve competitive performance with closed-source alternatives",
            "user_email": from_email,
            "user_name": "Researcher",
            "active": True
        },
        {
            "name": "Hugo Touvron & Shunyu Yao Publications",
            "rule_type": "author",
            "authors": ["Hugo Touvron", "Shunyu Yao"],
            "user_email": from_email,
            "user_name": "Researcher",
            "active": True
        }
    ]

    created_ids = []
    for i, rule in enumerate(demo_rules, 1):
        rule_ref = client.db.collection('watch_rules').document()
        rule_ref.set(rule)
        created_ids.append(rule_ref.id)

        print(f"  [{i}/4] Created: {rule['name']}")
        print(f"         Type: {rule['rule_type']}")
        print(f"         ID: {rule_ref.id}")
        print()

    print("=" * 80)
    print("✅ Demo watch rules synced successfully!")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  - Deleted: {deleted_count} old rules")
    print(f"  - Created: {len(created_ids)} new demo rules")
    print()
    print("These rules match the demo and should trigger real alerts!")

if __name__ == "__main__":
    main()

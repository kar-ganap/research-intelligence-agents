#!/usr/bin/env python3
"""
Backup current relationships from Firestore to JSON file.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage.firestore_client import FirestoreClient

def main():
    """Backup relationships to JSON file."""
    firestore_client = FirestoreClient()

    # Fetch all relationships
    print("Fetching relationships from Firestore...")
    relationships_ref = firestore_client.db.collection('relationships')
    all_rels = []

    for doc in relationships_ref.stream():
        rel_data = doc.to_dict()
        rel_data['_doc_id'] = doc.id  # Store document ID for restoration

        # Convert any datetime objects to ISO strings for JSON serialization
        for key, value in rel_data.items():
            if hasattr(value, 'isoformat'):  # datetime-like object
                rel_data[key] = value.isoformat()

        all_rels.append(rel_data)

    print(f"Found {len(all_rels)} relationships")

    # Create backup file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(__file__).parent.parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    backup_file = backup_dir / f"relationships_backup_{timestamp}.json"

    # Save to file
    with open(backup_file, 'w') as f:
        json.dump(all_rels, f, indent=2)

    print(f"Backed up {len(all_rels)} relationships to {backup_file}")

    # Print summary
    type_counts = {}
    for rel in all_rels:
        rel_type = rel.get('relationship_type', 'unknown')
        type_counts[rel_type] = type_counts.get(rel_type, 0) + 1

    print("\nRelationship type breakdown:")
    for rel_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {rel_type}: {count}")

if __name__ == "__main__":
    main()

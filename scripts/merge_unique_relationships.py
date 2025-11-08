#!/usr/bin/env python3
"""
Merge unique relationships from Options 1+5+6 backup into current Firestore.

This adds the 7 relationships that were unique to Options 1+5+6 to the
current set of 143 relationships from Options 5+6, giving us a union of
150 total relationships.
"""

import sys
import os
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage.firestore_client import FirestoreClient


def get_relationship_key(rel):
    """Create a unique key for a relationship."""
    return (
        rel['source_paper_id'],
        rel['target_paper_id'],
        rel['relationship_type']
    )


def main():
    """Merge unique relationships from backup into Firestore."""
    firestore_client = FirestoreClient()

    # Load backup from Options 1+5+6
    backup_dir = Path(__file__).parent.parent / "backups"
    backup_file = backup_dir / "relationships_backup_20251107_144206.json"

    print(f"Loading Options 1+5+6 relationships from backup...")
    with open(backup_file, 'r') as f:
        backup_rels = json.load(f)
    print(f"Loaded {len(backup_rels)} relationships from backup")

    # Load current relationships from Firestore (Options 5+6)
    print(f"\nLoading current relationships from Firestore...")
    relationships_ref = firestore_client.db.collection('relationships')
    current_rels = []
    for doc in relationships_ref.stream():
        rel_data = doc.to_dict()
        current_rels.append(rel_data)
    print(f"Loaded {len(current_rels)} current relationships")

    # Find relationships unique to backup
    current_keys = {get_relationship_key(rel) for rel in current_rels}
    backup_keys = {get_relationship_key(rel) for rel in backup_rels}

    unique_to_backup = backup_keys - current_keys
    print(f"\nFound {len(unique_to_backup)} relationships unique to Options 1+5+6")

    # Get the full relationship data for unique ones
    unique_rels = []
    for rel in backup_rels:
        if get_relationship_key(rel) in unique_to_backup:
            # Remove backup metadata
            rel_clean = {k: v for k, v in rel.items() if k != '_doc_id'}
            unique_rels.append(rel_clean)

    # Add unique relationships to Firestore
    print(f"\nAdding {len(unique_rels)} unique relationships to Firestore...")
    for i, rel in enumerate(unique_rels, 1):
        firestore_client.store_relationship(rel)
        print(f"  [{i}/{len(unique_rels)}] Added {rel['relationship_type']} relationship")

    # Verify final count
    print(f"\nVerifying final count...")
    final_count = len(list(firestore_client.db.collection('relationships').stream()))
    print(f"Final relationship count: {final_count}")
    print(f"Expected: {len(current_rels) + len(unique_rels)}")

    # Show breakdown
    all_rels = list(firestore_client.db.collection('relationships').stream())
    type_counts = {}
    for rel_doc in all_rels:
        rel = rel_doc.to_dict()
        rel_type = rel.get('relationship_type', 'unknown')
        type_counts[rel_type] = type_counts.get(rel_type, 0) + 1

    print(f"\nFinal relationship type breakdown:")
    for rel_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {rel_type}: {count}")

    max_possible = 49 * 48 // 2  # 1,176
    density = (final_count / max_possible) * 100
    print(f"\nGraph density: {density:.1f}%")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Restore relationships from a JSON backup file to Firestore.
"""

import sys
import os
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage.firestore_client import FirestoreClient

def main(backup_file: str):
    """Restore relationships from JSON file."""
    firestore_client = FirestoreClient()

    # Load backup file
    backup_path = Path(backup_file)
    if not backup_path.exists():
        print(f"Error: Backup file not found: {backup_file}")
        sys.exit(1)

    print(f"Loading relationships from {backup_file}...")
    with open(backup_path, 'r') as f:
        relationships = json.load(f)

    print(f"Found {len(relationships)} relationships in backup")

    # Delete existing relationships
    print("Deleting existing relationships...")
    relationships_ref = firestore_client.db.collection('relationships')
    deleted = 0
    for doc in relationships_ref.stream():
        doc.reference.delete()
        deleted += 1
    print(f"Deleted {deleted} existing relationships")

    # Restore relationships
    print("Restoring relationships...")
    for rel in relationships:
        # Remove the _doc_id field before storing
        doc_id = rel.pop('_doc_id', None)
        firestore_client.store_relationship(rel)

    print(f"Restored {len(relationships)} relationships")

    # Print summary
    type_counts = {}
    for rel in relationships:
        rel_type = rel.get('relationship_type', 'unknown')
        type_counts[rel_type] = type_counts.get(rel_type, 0) + 1

    print("\nRestored relationship type breakdown:")
    for rel_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {rel_type}: {count}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python restore_relationships.py <backup_file>")
        sys.exit(1)

    main(sys.argv[1])

#!/usr/bin/env python3
"""
Compare two relationship sets to analyze overlap and differences.

This script compares the relationships from two different approaches:
- Options 1+5+6 (with embedding filtering): 94 relationships
- Options 5+6 (without embedding filtering): ~97-100 relationships

The goal is to determine if the embedding filter is:
1. Simply reducing the set (Options 1+5+6 is a subset of Options 5+6)
2. Finding different relationships (some unique to each approach)
"""

import sys
import os
import json
from pathlib import Path
from collections import defaultdict

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


def load_relationships_from_backup(backup_file):
    """Load relationships from a backup JSON file."""
    with open(backup_file, 'r') as f:
        relationships = json.load(f)
    return relationships


def get_current_relationships():
    """Get relationships currently in Firestore."""
    firestore_client = FirestoreClient()
    relationships_ref = firestore_client.db.collection('relationships')

    all_rels = []
    for doc in relationships_ref.stream():
        rel_data = doc.to_dict()
        all_rels.append(rel_data)

    return all_rels


def analyze_relationship_sets(set1_name, set1_rels, set2_name, set2_rels):
    """Compare two sets of relationships and analyze differences."""

    # Convert to sets of keys
    set1_keys = {get_relationship_key(rel) for rel in set1_rels}
    set2_keys = {get_relationship_key(rel) for rel in set2_rels}

    # Find overlaps and differences
    common = set1_keys & set2_keys
    only_in_set1 = set1_keys - set2_keys
    only_in_set2 = set2_keys - set1_keys

    print("=" * 80)
    print("RELATIONSHIP SET COMPARISON")
    print("=" * 80)
    print(f"{set1_name}: {len(set1_rels)} relationships")
    print(f"{set2_name}: {len(set2_rels)} relationships")
    print()

    print("=" * 80)
    print("OVERLAP ANALYSIS")
    print("=" * 80)
    print(f"Common relationships: {len(common)}")
    print(f"Only in {set1_name}: {len(only_in_set1)}")
    print(f"Only in {set2_name}: {len(only_in_set2)}")
    print()

    # Calculate overlap percentage
    total_unique = len(set1_keys | set2_keys)
    overlap_pct = (len(common) / total_unique * 100) if total_unique > 0 else 0
    print(f"Overlap: {len(common)}/{total_unique} ({overlap_pct:.1f}%)")
    print()

    # Check subset relationship
    is_set1_subset = set1_keys.issubset(set2_keys)
    is_set2_subset = set2_keys.issubset(set1_keys)

    print("=" * 80)
    print("SUBSET ANALYSIS")
    print("=" * 80)
    if is_set1_subset:
        print(f"✓ {set1_name} is a COMPLETE SUBSET of {set2_name}")
        print(f"  → The embedding filter simply reduced the set")
        print(f"  → All {len(set1_rels)} relationships from {set1_name} are in {set2_name}")
    elif is_set2_subset:
        print(f"✓ {set2_name} is a COMPLETE SUBSET of {set1_name}")
        print(f"  → All {len(set2_rels)} relationships from {set2_name} are in {set1_name}")
    else:
        print(f"✗ Neither is a complete subset of the other")
        print(f"  → Both approaches found unique relationships")
        print(f"  → The embedding filter affects WHICH relationships are found")
    print()

    # Analyze relationship types
    print("=" * 80)
    print("RELATIONSHIP TYPE BREAKDOWN")
    print("=" * 80)

    set1_types = defaultdict(int)
    set2_types = defaultdict(int)

    for rel in set1_rels:
        set1_types[rel['relationship_type']] += 1

    for rel in set2_rels:
        set2_types[rel['relationship_type']] += 1

    print(f"\n{set1_name}:")
    for rel_type, count in sorted(set1_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {rel_type}: {count}")

    print(f"\n{set2_name}:")
    for rel_type, count in sorted(set2_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {rel_type}: {count}")
    print()

    # Show unique relationships
    if only_in_set1:
        print("=" * 80)
        print(f"RELATIONSHIPS ONLY IN {set1_name} ({len(only_in_set1)})")
        print("=" * 80)
        for key in list(only_in_set1)[:10]:  # Show first 10
            print(f"  {key[0][:30]}... → {key[1][:30]}... ({key[2]})")
        if len(only_in_set1) > 10:
            print(f"  ... and {len(only_in_set1) - 10} more")
        print()

    if only_in_set2:
        print("=" * 80)
        print(f"RELATIONSHIPS ONLY IN {set2_name} ({len(only_in_set2)})")
        print("=" * 80)
        for key in list(only_in_set2)[:10]:  # Show first 10
            print(f"  {key[0][:30]}... → {key[1][:30]}... ({key[2]})")
        if len(only_in_set2) > 10:
            print(f"  ... and {len(only_in_set2) - 10} more")
        print()

    print("=" * 80)
    print("INTERPRETATION")
    print("=" * 80)
    if is_set1_subset and not is_set2_subset:
        print("The embedding pre-filter (Option 1) appears to be filtering out some")
        print("valid relationships. Without the filter, more relationships are found.")
        print()
        print("RECOMMENDATION: Skip Option 1 (embedding pre-filter)")
        print("  → Use Options 5+6 only for maximum relationship discovery")
        print(f"  → Trade-off: ~{len(set2_rels)/len(set1_rels):.1f}x more API calls")
    elif is_set2_subset and not is_set1_subset:
        print("The embedding pre-filter (Option 1) is finding additional relationships")
        print("that the full comparison misses (likely due to LLM variation).")
        print()
        print("RECOMMENDATION: Keep Option 1 (embedding pre-filter)")
        print("  → Better signal-to-noise by focusing on semantically similar papers")
        print(f"  → ~{1 - len(set1_rels)/len(set2_rels):.1%} reduction in API calls")
    elif len(only_in_set1) > 0 and len(only_in_set2) > 0:
        print("Each approach finds unique relationships due to:")
        print("  1. LLM variation at temperature=0.7")
        print("  2. Different context (comparing against different sets of papers)")
        print()
        print("RECOMMENDATION: Hybrid approach or lower temperature")
        print("  → Consider running both and taking the union")
        print(f"  → Or reduce temperature to reduce LLM variation")
    else:
        print("The sets are identical - no difference between approaches.")
        print()
        print("RECOMMENDATION: Use Option 1 (embedding pre-filter)")
        print("  → Same results with fewer API calls")

    print("=" * 80)


def main():
    """Main comparison logic."""
    # Path to the backup of Options 1+5+6 results
    backup_dir = Path(__file__).parent.parent / "backups"
    backup_file = backup_dir / "relationships_backup_20251107_144206.json"

    if not backup_file.exists():
        print(f"Error: Backup file not found: {backup_file}")
        print("Please ensure the Options 1+5+6 backup exists.")
        sys.exit(1)

    # Load both sets
    print("Loading Options 1+5+6 relationships from backup...")
    options_156_rels = load_relationships_from_backup(backup_file)

    print("Loading Options 5+6 relationships from Firestore...")
    options_56_rels = get_current_relationships()

    # Compare
    analyze_relationship_sets(
        "Options 1+5+6 (with embedding filter)",
        options_156_rels,
        "Options 5+6 (no embedding filter)",
        options_56_rels
    )


if __name__ == "__main__":
    main()

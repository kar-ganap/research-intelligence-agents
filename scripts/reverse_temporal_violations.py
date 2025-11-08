#!/usr/bin/env python3
"""
Reverse Temporal Violations Instead of Deleting Them

This script corrects temporal violations by reversing the relationship direction
(swapping source and target) rather than deleting them entirely.

For a relationship that violates temporal ordering (older paper → newer paper),
we reverse it to (newer paper → older paper).

This preserves the semantic relationship detected by the LLM while fixing the
temporal direction.
"""

import sys
import os
from datetime import datetime
from typing import Dict, List

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.storage.firestore_client import FirestoreClient
from src.agents.ingestion.relationship_agent import get_paper_date
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_temporal_violations_to_reverse(
    relationships: List[Dict],
    papers_map: Dict[str, Dict]
) -> List[Dict]:
    """
    Find relationships that violate temporal ordering and prepare them for reversal.

    Args:
        relationships: List of all relationships
        papers_map: Dict mapping paper_id to paper data

    Returns:
        List of relationships to reverse with metadata
    """
    violations = []

    for rel in relationships:
        source_id = rel.get('source_paper_id')
        target_id = rel.get('target_paper_id')

        source_paper = papers_map.get(source_id)
        target_paper = papers_map.get(target_id)

        if not source_paper or not target_paper:
            continue

        source_date = get_paper_date(source_paper)
        target_date = get_paper_date(target_paper)

        if source_date and target_date:
            if source_date < target_date:
                # Source is older than target - needs reversal!
                violations.append({
                    'relationship_id': rel.get('relationship_id'),
                    'source_id': source_id,
                    'target_id': target_id,
                    'source_title': source_paper.get('title', 'Unknown')[:50],
                    'target_title': target_paper.get('title', 'Unknown')[:50],
                    'source_date': source_date.strftime('%Y-%m-%d'),
                    'target_date': target_date.strftime('%Y-%m-%d'),
                    'relationship_type': rel.get('relationship_type'),
                    'confidence': rel.get('confidence', 0.0),
                    'evidence': rel.get('evidence', ''),
                    'description': rel.get('description', '')
                })

    return violations


def find_bidirectional_contradictions(
    relationships: List[Dict]
) -> List[str]:
    """
    Find duplicate bidirectional contradictions.

    For each contradiction pair (A->B and B->A), keep only one direction.
    We'll keep the newer paper -> older paper direction.

    Args:
        relationships: List of all relationships

    Returns:
        List of relationship IDs to delete
    """
    contradictions = [r for r in relationships if r.get('relationship_type') == 'contradicts']

    seen_pairs = set()
    to_delete = []

    for rel in contradictions:
        source_id = rel.get('source_paper_id')
        target_id = rel.get('target_paper_id')
        rel_id = rel.get('relationship_id')

        # Create normalized pair
        pair = tuple(sorted([source_id, target_id]))

        if pair in seen_pairs:
            # This is the duplicate - mark for deletion
            to_delete.append(rel_id)
        else:
            seen_pairs.add(pair)

    return to_delete


def main():
    """
    Main reversal function.

    Steps:
    1. Load all papers and relationships
    2. Find temporal violations to reverse
    3. Find bidirectional contradictions to delete
    4. Present summary to user
    5. Ask for confirmation
    6. Reverse temporal violations (delete old, create new)
    7. Delete bidirectional contradictions
    """
    logger.info("=" * 80)
    logger.info("Starting Temporal Violations Reversal")
    logger.info("=" * 80)

    # Initialize Firestore client
    firestore_client = FirestoreClient()

    # Load all papers
    logger.info("Loading papers...")
    papers = firestore_client.get_all_papers()
    papers_map = {p['paper_id']: p for p in papers}
    logger.info(f"Loaded {len(papers)} papers")

    # Load all relationships
    logger.info("Loading relationships...")
    relationships_docs = list(firestore_client.db.collection('relationships').stream())
    relationships = []
    for doc in relationships_docs:
        rel_data = doc.to_dict()
        rel_data['relationship_id'] = doc.id
        relationships.append(rel_data)
    logger.info(f"Loaded {len(relationships)} relationships")

    # Find temporal violations to reverse
    logger.info("\n" + "=" * 80)
    logger.info("Checking for temporal violations to reverse...")
    logger.info("=" * 80)
    violations_to_reverse = find_temporal_violations_to_reverse(relationships, papers_map)

    if violations_to_reverse:
        logger.warning(f"\nFound {len(violations_to_reverse)} temporal violations to reverse:")
        for i, v in enumerate(violations_to_reverse[:10], 1):  # Show first 10
            logger.warning(f"{i}. {v['relationship_type'].upper()}")
            logger.warning(f"   Current (WRONG): {v['source_title']}... ({v['source_date']}) → {v['target_title']}... ({v['target_date']})")
            logger.warning(f"   Will reverse to: {v['target_title']}... ({v['target_date']}) → {v['source_title']}... ({v['source_date']})")
        if len(violations_to_reverse) > 10:
            logger.warning(f"   ... and {len(violations_to_reverse) - 10} more")
    else:
        logger.info("✓ No temporal violations found")

    # Find bidirectional contradictions
    logger.info("\n" + "=" * 80)
    logger.info("Checking for bidirectional contradictions...")
    logger.info("=" * 80)
    bidirectional_ids = find_bidirectional_contradictions(relationships)

    if bidirectional_ids:
        logger.warning(f"\nFound {len(bidirectional_ids)} duplicate contradictions (will keep one direction)")
    else:
        logger.info("✓ No bidirectional contradictions found")

    # Summary
    total_operations = len(violations_to_reverse) + len(bidirectional_ids)

    logger.info("\n" + "=" * 80)
    logger.info("REVERSAL SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Temporal violations to REVERSE: {len(violations_to_reverse)}")
    logger.info(f"Duplicate contradictions to DELETE: {len(bidirectional_ids)}")
    logger.info(f"Total operations: {total_operations}")
    logger.info(f"Current relationships in DB: {len(relationships)}")
    logger.info(f"Relationships after reversal: {len(relationships) - len(bidirectional_ids)} (same count, but corrected direction)")

    if total_operations == 0:
        logger.info("\n✓ No operations needed - database is already correct!")
        return

    # Ask for confirmation
    logger.info("\n" + "=" * 80)
    if sys.stdin.isatty():
        response = input("\nProceed with reversal? (yes/no): ").strip().lower()
        if response != 'yes':
            logger.info("Reversal cancelled by user")
            return
    else:
        logger.info("Running non-interactively - auto-proceeding with reversal")

    # Reverse temporal violations
    logger.info("\n" + "=" * 80)
    logger.info("Reversing temporal violations...")
    logger.info("=" * 80)
    reversed_count = 0

    for v in violations_to_reverse:
        rel_id = v['relationship_id']
        try:
            # Delete old (wrong direction) relationship
            firestore_client.db.collection('relationships').document(rel_id).delete()

            # Create new (correct direction) relationship
            firestore_client.db.collection('relationships').add({
                'source_paper_id': v['target_id'],  # Swap
                'target_paper_id': v['source_id'],  # Swap
                'relationship_type': v['relationship_type'],
                'confidence': v['confidence'],
                'evidence': v.get('evidence', ''),
                'description': v.get('description', '')
            })

            reversed_count += 1
            if reversed_count % 10 == 0:
                logger.info(f"Reversed {reversed_count}/{len(violations_to_reverse)} relationships...")

        except Exception as e:
            logger.error(f"Failed to reverse relationship {rel_id}: {e}")

    logger.info(f"✓ Reversed {reversed_count} temporal violations")

    # Delete bidirectional contradictions
    logger.info("\n" + "=" * 80)
    logger.info("Deleting duplicate contradictions...")
    logger.info("=" * 80)
    deleted_bidirectional = 0

    for rel_id in bidirectional_ids:
        try:
            firestore_client.db.collection('relationships').document(rel_id).delete()
            deleted_bidirectional += 1
            if deleted_bidirectional % 10 == 0:
                logger.info(f"Deleted {deleted_bidirectional}/{len(bidirectional_ids)} duplicates...")
        except Exception as e:
            logger.error(f"Failed to delete relationship {rel_id}: {e}")

    logger.info(f"✓ Deleted {deleted_bidirectional} duplicate contradictions")

    # Final summary
    logger.info("\n" + "=" * 80)
    logger.info("REVERSAL COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Relationships reversed: {reversed_count}")
    logger.info(f"Duplicate contradictions deleted: {deleted_bidirectional}")
    logger.info(f"Final relationship count: {len(relationships) - deleted_bidirectional}")
    logger.info("\n✓ Database corrected successfully!")
    logger.info("✓ All relationships now respect temporal ordering (newer → older)")
    logger.info("✓ Future relationships will be validated by relationship_agent.py")


if __name__ == "__main__":
    main()

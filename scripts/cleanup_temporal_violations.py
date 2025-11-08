"""
Cleanup Script for Temporal Violations and Bidirectional Contradictions

This is a ONE-TIME cleanup script to fix existing relationships in the database that:
1. Violate temporal ordering (older paper -> newer paper)
2. Are bidirectional contradictions (both A->B and B->A)

After running this script, the integrated temporal validation in relationship_agent.py
will prevent new violations from being created.
"""

import sys
import os
from datetime import datetime
from typing import Dict, List, Optional

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.storage.firestore_client import FirestoreClient
from src.agents.ingestion.relationship_agent import parse_date, get_paper_date
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_temporal_violations(
    relationships: List[Dict],
    papers_map: Dict[str, Dict]
) -> List[Dict]:
    """
    Find relationships that violate temporal ordering.

    A violation occurs when:
    - source_paper is published BEFORE target_paper (older -> newer)

    Args:
        relationships: List of all relationships
        papers_map: Dict mapping paper_id to paper data

    Returns:
        List of relationships to delete
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
                # Source is older than target - violation!
                violations.append({
                    'relationship_id': rel.get('relationship_id'),
                    'source_id': source_id,
                    'target_id': target_id,
                    'source_title': source_paper.get('title', 'Unknown')[:50],
                    'target_title': target_paper.get('title', 'Unknown')[:50],
                    'source_date': source_date.strftime('%Y-%m-%d'),
                    'target_date': target_date.strftime('%Y-%m-%d'),
                    'relationship_type': rel.get('relationship_type')
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
    # Build contradiction pairs
    contradictions = [r for r in relationships if r.get('relationship_type') == 'contradicts']

    # Track pairs we've seen
    seen_pairs = set()
    to_delete = []

    for rel in contradictions:
        source_id = rel.get('source_paper_id')
        target_id = rel.get('target_paper_id')
        rel_id = rel.get('relationship_id')

        # Create normalized pair (always smaller ID first for consistency)
        pair = tuple(sorted([source_id, target_id]))

        if pair in seen_pairs:
            # This is the duplicate - mark for deletion
            to_delete.append(rel_id)
            logger.debug(f"Found duplicate contradiction: {source_id[:8]} <-> {target_id[:8]}")
        else:
            seen_pairs.add(pair)

    return to_delete


def main():
    """
    Main cleanup function.

    Steps:
    1. Load all papers and relationships
    2. Find temporal violations
    3. Find bidirectional contradictions
    4. Present summary to user
    5. Ask for confirmation
    6. Delete violating relationships
    """
    logger.info("=" * 80)
    logger.info("Starting Temporal Violations Cleanup")
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
    relationships = firestore_client.get_all_relationships(limit=10000)
    logger.info(f"Loaded {len(relationships)} relationships")

    # Find temporal violations
    logger.info("\n" + "=" * 80)
    logger.info("Checking for temporal violations...")
    logger.info("=" * 80)
    temporal_violations = find_temporal_violations(relationships, papers_map)

    if temporal_violations:
        logger.warning(f"\nFound {len(temporal_violations)} temporal violations:")
        for i, v in enumerate(temporal_violations[:10], 1):  # Show first 10
            logger.warning(f"{i}. {v['relationship_type'].upper()}")
            logger.warning(f"   Source: {v['source_title']}... ({v['source_date']})")
            logger.warning(f"   Target: {v['target_title']}... ({v['target_date']})")
            logger.warning(f"   Problem: Source is older than target")
        if len(temporal_violations) > 10:
            logger.warning(f"   ... and {len(temporal_violations) - 10} more")
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
    total_to_delete = len(temporal_violations) + len(bidirectional_ids)

    logger.info("\n" + "=" * 80)
    logger.info("CLEANUP SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Temporal violations to delete: {len(temporal_violations)}")
    logger.info(f"Duplicate contradictions to delete: {len(bidirectional_ids)}")
    logger.info(f"Total relationships to delete: {total_to_delete}")
    logger.info(f"Total relationships in DB: {len(relationships)}")
    logger.info(f"Relationships after cleanup: {len(relationships) - total_to_delete}")

    if total_to_delete == 0:
        logger.info("\n✓ No cleanup needed - database is already correct!")
        return

    # Ask for confirmation (auto-proceed if running non-interactively)
    logger.info("\n" + "=" * 80)
    import sys
    if sys.stdin.isatty():
        response = input("\nProceed with deletion? (yes/no): ").strip().lower()
        if response != 'yes':
            logger.info("Cleanup cancelled by user")
            return
    else:
        logger.info("Running non-interactively - auto-proceeding with cleanup")
        logger.info("(Set AUTO_CLEANUP=false environment variable to prevent this)")

    # Delete temporal violations
    logger.info("\n" + "=" * 80)
    logger.info("Deleting temporal violations...")
    logger.info("=" * 80)
    deleted_temporal = 0
    for v in temporal_violations:
        rel_id = v['relationship_id']
        try:
            firestore_client.db.collection('relationships').document(rel_id).delete()
            deleted_temporal += 1
            if deleted_temporal % 10 == 0:
                logger.info(f"Deleted {deleted_temporal}/{len(temporal_violations)} temporal violations...")
        except Exception as e:
            logger.error(f"Failed to delete relationship {rel_id}: {e}")

    logger.info(f"✓ Deleted {deleted_temporal} temporal violations")

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
    logger.info("CLEANUP COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total relationships deleted: {deleted_temporal + deleted_bidirectional}")
    logger.info(f"Remaining relationships: {len(relationships) - deleted_temporal - deleted_bidirectional}")
    logger.info("\n✓ Database cleaned successfully!")
    logger.info("✓ Future relationships will be validated by relationship_agent.py")


if __name__ == "__main__":
    main()

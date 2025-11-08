#!/usr/bin/env python3
"""
Regenerate Lost Relationships

After the cleanup script deleted temporal violations, we lost 70 relationships.
This script regenerates relationships by comparing ALL papers in BOTH directions.

This ensures we don't miss any relationships due to temporal ordering issues
in the original comparison.

Strategy:
- For each pair of papers (A, B), we compare both directions:
  - A vs B (source=A, target=B)
  - B vs A (source=B, target=A)
- The RelationshipAgent's temporal validation will automatically enforce
  correct direction (newer → older)
"""

import sys
import os
import time
import logging
from typing import List, Dict
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.ingestion.relationship_agent import RelationshipAgent, get_paper_date
from src.storage.firestore_client import FirestoreClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True
)
logger = logging.getLogger(__name__)


def regenerate_bidirectional():
    """Regenerate relationships by comparing all pairs in BOTH directions."""

    print("=" * 80)
    print("REGENERATE LOST RELATIONSHIPS (BIDIRECTIONAL COMPARISON)")
    print("=" * 80)
    print()

    # Initialize
    firestore_client = FirestoreClient()
    relationship_agent = RelationshipAgent()

    # Get all papers
    print("📚 Fetching all papers from Firestore...")
    papers = firestore_client.get_all_papers()
    print(f"Found {len(papers)} papers in corpus")
    print()

    if len(papers) < 2:
        print("⚠️  Need at least 2 papers to detect relationships")
        return

    # Check existing relationships
    existing_relationships = list(firestore_client.db.collection('relationships').stream())
    print(f"📊 Current relationships in database: {len(existing_relationships)}")

    # Build set of existing pairs
    existing_pairs = set()
    for rel in existing_relationships:
        rel_data = rel.to_dict()
        source_id = rel_data.get('source_paper_id')
        target_id = rel_data.get('target_paper_id')
        # Normalize pair (both orderings)
        existing_pairs.add((source_id, target_id))
        existing_pairs.add((target_id, source_id))  # Also track reverse

    print(f"📊 Existing unique relationships: {len(existing_relationships)}")
    print()

    # Calculate total comparisons
    total_papers = len(papers)
    # We'll compare BOTH directions for each pair
    # Total pairs = n * (n-1) / 2
    # But we check both directions, so comparisons = n * (n-1)
    total_comparisons = total_papers * (total_papers - 1)

    print(f"Will perform {total_comparisons} comparisons ({total_papers} papers, both directions)")
    print("Using temporal validation - only newer → older relationships will be created")
    print()

    # Process all papers against all other papers
    total_detected = 0
    total_stored = 0
    total_skipped_existing = 0
    total_skipped_temporal = 0
    start_time = time.time()

    print("🔍 Starting bidirectional relationship detection...")
    print()

    comparison_count = 0

    for i, paper_a in enumerate(papers):
        paper_a_title = paper_a.get('title', 'Unknown')[:60]
        paper_a_date = get_paper_date(paper_a)
        date_a_str = paper_a_date.strftime('%Y-%m-%d') if paper_a_date else 'no date'

        logger.info(f"Processing paper {i+1}/{total_papers}: {paper_a_title}... ({date_a_str})")
        print(f"\n[{i+1}/{total_papers}] Processing: {paper_a_title}... ({date_a_str})")

        for j, paper_b in enumerate(papers):
            # Skip same paper
            if paper_a.get('paper_id') == paper_b.get('paper_id'):
                continue

            comparison_count += 1

            # Check if this pair already exists in database
            pair = (paper_a.get('paper_id'), paper_b.get('paper_id'))
            if pair in existing_pairs:
                total_skipped_existing += 1
                logger.debug(f"Skipping existing pair: {paper_a_title[:30]}... → {paper_b.get('title', 'Unknown')[:30]}...")
                continue

            # Check temporal constraint BEFORE calling LLM (to save API calls)
            paper_b_date = get_paper_date(paper_b)

            if paper_a_date and paper_b_date:
                if paper_a_date < paper_b_date:
                    # paper_a is older than paper_b - this would be a temporal violation
                    # Skip this comparison to avoid wasting an API call
                    logger.debug(f"Skipping temporal violation: {paper_a_title[:30]}... ({date_a_str}) → {paper_b.get('title', 'Unknown')[:30]}... ({paper_b_date.strftime('%Y-%m-%d')})")
                    continue

            # Detect relationship (only for temporally valid pairs)
            try:
                result = relationship_agent.detect_relationship(paper_a, paper_b)

                # Only store if confidence meets threshold and not "none"
                if result['confidence'] >= 0.6 and result['relationship_type'] != 'none':
                    # Store relationship
                    firestore_client.store_relationship({
                        'source_paper_id': paper_a.get('paper_id'),
                        'target_paper_id': paper_b.get('paper_id'),
                        'relationship_type': result['relationship_type'],
                        'confidence': result['confidence'],
                        'evidence': result['evidence']
                    })

                    total_detected += 1
                    total_stored += 1

                    paper_b_title = paper_b.get('title', 'Unknown')[:50]
                    print(f"  ✅ Found {result['relationship_type']}: {paper_b_title}... (conf: {result['confidence']:.2f})")

            except Exception as e:
                logger.error(f"Error processing pair {paper_a_title} → {paper_b.get('title', 'Unknown')}: {e}")
                continue

        # Progress summary
        elapsed = time.time() - start_time
        avg_time_per_paper = elapsed / (i + 1)
        eta = avg_time_per_paper * (total_papers - i - 1)
        print(f"  Progress: {i+1}/{total_papers}, New: {total_detected}, Skipped existing: {total_skipped_existing}, ETA: {eta/60:.1f} min")

    # Summary
    elapsed_total = time.time() - start_time

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total papers processed: {total_papers}")
    print(f"Total comparisons performed: {comparison_count}")
    print(f"Relationships skipped (already exist): {total_skipped_existing}")
    print(f"NEW relationships detected (conf >= 0.6): {total_detected}")
    print(f"NEW relationships stored in Firestore: {total_stored}")
    print(f"Total time: {elapsed_total/60:.1f} minutes")
    print()

    # Final count
    print("Final relationship breakdown:")
    relationships_final = list(firestore_client.db.collection('relationships').stream())
    print(f"Total relationships: {len(relationships_final)}")

    types = {}
    for rel in relationships_final:
        rel_data = rel.to_dict()
        rel_type = rel_data.get('relationship_type', 'unknown')
        types[rel_type] = types.get(rel_type, 0) + 1

    for rel_type, count in sorted(types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {rel_type}: {count}")

    print()
    print("=" * 80)
    print("✅ Relationship regeneration complete!")
    print("=" * 80)
    print()


if __name__ == "__main__":
    regenerate_bidirectional()

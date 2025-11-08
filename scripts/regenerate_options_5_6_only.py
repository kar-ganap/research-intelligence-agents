#!/usr/bin/env python3
"""
Regenerate All Relationships - Options 5+6 Only (Ablation Study)

This script tests Options 5 and 6 WITHOUT embedding filtering (Option 1):
- Option 5: Selective confidence thresholds by relationship type
- Option 6: Refined prompt that encourages finding meaningful relationships

This is an ablation study to understand:
1. How much does the embedding filter help/hurt?
2. What's the maximum improvement from prompt + thresholds alone?

Process:
1. Delete ALL existing relationships from the database
2. For each paper, detect relationships against ALL other papers (no embedding filter)
3. Apply selective thresholds: contradicts=0.7, extends/supports=0.5
4. Use the refined prompt from Option 6

Expected results:
- Higher API call count (~1,176 comparisons)
- Potentially more relationships found (if embedding filter was too aggressive)
- Helps us understand if we're losing relationships due to premature filtering
"""

import sys
import os
import time
import logging
from pathlib import Path

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


def main():
    """Main regeneration process."""
    start_time = time.time()

    logger.info("=" * 80)
    logger.info("REGENERATING RELATIONSHIPS WITH OPTIONS 5+6 ONLY (ABLATION STUDY)")
    logger.info("=" * 80)
    logger.info("Improvements:")
    logger.info("  - Option 5: Selective thresholds (contradicts=0.7, extends/supports=0.5)")
    logger.info("  - Option 6: Refined prompt (encourages finding relationships)")
    logger.info("  - NO embedding filtering (compare against ALL papers)")
    logger.info("=" * 80)
    logger.info("")

    # Initialize clients
    firestore_client = FirestoreClient()
    relationship_agent = RelationshipAgent()

    # Fetch all papers
    logger.info("Fetching papers from Firestore...")
    all_papers = firestore_client.get_all_papers()
    logger.info(f"Found {len(all_papers)} papers in corpus")

    # Sort papers by publication date (oldest first)
    all_papers.sort(key=lambda p: p.get('published', ''), reverse=False)

    # Delete existing relationships
    logger.info("Deleting existing relationships...")
    relationships_ref = firestore_client.db.collection('relationships')
    deleted = 0
    for doc in relationships_ref.stream():
        doc.reference.delete()
        deleted += 1

    logger.info(f"Deleted {deleted} existing relationships")
    logger.info("")

    # Regenerate relationships WITHOUT embedding filtering
    logger.info("Starting relationship detection WITHOUT embedding pre-filtering...")
    logger.info(f"Will process {len(all_papers)} papers")
    logger.info("Each paper will be compared against ALL other papers")
    logger.info("")

    total_relationships = 0
    total_comparisons = 0
    max_possible_comparisons = len(all_papers) * (len(all_papers) - 1) // 2

    # Selective thresholds (Option 5)
    thresholds = {
        'contradicts': 0.7,
        'extends': 0.5,
        'supports': 0.5,
    }

    for i, paper in enumerate(all_papers):
        paper_num = i + 1
        logger.info(f"\n[{paper_num}/{len(all_papers)}] Processing: {paper.get('title', 'Unknown')[:60]}...")

        relationships = []
        new_paper_date = get_paper_date(paper)
        temporal_violations = 0

        for existing_paper in all_papers:
            # Skip if same paper
            if paper.get('paper_id') == existing_paper.get('paper_id'):
                continue

            # Check temporal constraint
            existing_paper_date = get_paper_date(existing_paper)
            if new_paper_date and existing_paper_date:
                if new_paper_date < existing_paper_date:
                    temporal_violations += 1
                    continue

            # Detect relationship
            total_comparisons += 1
            result = relationship_agent.detect_relationship(paper, existing_paper)

            rel_type = result['relationship_type']

            # Skip "none" relationships
            if rel_type == 'none':
                continue

            # Apply selective threshold based on relationship type
            min_conf = thresholds.get(rel_type, 0.6)

            if result['confidence'] >= min_conf:
                relationships.append({
                    'source_paper_id': paper.get('paper_id'),
                    'target_paper_id': existing_paper.get('paper_id'),
                    'relationship_type': rel_type,
                    'confidence': result['confidence'],
                    'evidence': result['evidence']
                })

                logger.info(f"Found relationship: {rel_type} (confidence: {result['confidence']:.2f})")

        # Store relationships
        for rel in relationships:
            firestore_client.store_relationship(rel)
            total_relationships += 1

        logger.info(f"  Found {len(relationships)} relationships")
        logger.info(f"  Skipped {temporal_violations} papers due to temporal constraints")
        logger.info(f"  Total relationships so far: {total_relationships}")
        logger.info(f"  Total comparisons: {total_comparisons} (vs {max_possible_comparisons} maximum)")

    # Final statistics
    elapsed = time.time() - start_time
    logger.info("")
    logger.info("=" * 80)
    logger.info("REGENERATION COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total papers processed: {len(all_papers)}")
    logger.info(f"Total relationships created: {total_relationships}")
    logger.info(f"Total comparisons made: {total_comparisons}")
    logger.info(f"Maximum possible comparisons: {max_possible_comparisons}")
    logger.info(f"Graph density: {total_relationships/max_possible_comparisons*100:.1f}%")
    logger.info(f"Time elapsed: {elapsed/60:.1f} minutes")
    logger.info("")

    # Relationship type breakdown
    logger.info("Fetching relationship type breakdown...")
    all_rels = list(firestore_client.db.collection('relationships').stream())
    type_counts = {}
    for rel_doc in all_rels:
        rel = rel_doc.to_dict()
        rel_type = rel.get('relationship_type', 'unknown')
        type_counts[rel_type] = type_counts.get(rel_type, 0) + 1

    logger.info("Relationship types:")
    for rel_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  {rel_type}: {count}")

    logger.info("=" * 80)


if __name__ == "__main__":
    main()

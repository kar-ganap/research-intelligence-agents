#!/usr/bin/env python3
"""
Regenerate All Relationships - Clean Slate

This script:
1. Deletes ALL existing relationships from the database
2. Regenerates relationships from scratch with proper temporal validation
3. Compares each unique paper pair exactly ONCE in the correct temporal direction

Strategy:
- Sort papers by publication date (newest first)
- For each paper, compare it against all OLDER papers
- This ensures we only create relationships in the correct direction (newer → older)
- Each unique pair is compared exactly once, resulting in 1,176 comparisons (49 × 48 / 2)
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

# Also log to file
file_handler = logging.FileHandler('regenerate_all_relationships.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)


def regenerate_all():
    """Delete all relationships and regenerate from scratch with temporal validation."""

    print("=" * 80)
    print("REGENERATE ALL RELATIONSHIPS - CLEAN SLATE")
    print("=" * 80)
    print()

    # Initialize
    firestore_client = FirestoreClient()
    relationship_agent = RelationshipAgent()

    # Get all papers and sort by publication date
    print("📚 Fetching all papers from Firestore...")
    papers = firestore_client.get_all_papers()
    print(f"Found {len(papers)} papers in corpus")
    print()

    if len(papers) < 2:
        print("⚠️  Need at least 2 papers to detect relationships")
        return

    # Sort by publication date (newest first)
    papers_with_dates = [(p, get_paper_date(p)) for p in papers]
    papers_with_dates.sort(key=lambda x: x[1] if x[1] else datetime.min, reverse=True)
    papers_sorted = [p[0] for p in papers_with_dates]

    print("Papers sorted by date (newest → oldest):")
    for i, (paper, date) in enumerate(papers_with_dates[:5]):
        date_str = date.strftime('%Y-%m-%d') if date else 'no date'
        print(f"  {i+1}. {paper.get('title', 'Unknown')[:60]}... ({date_str})")
    print(f"  ... and {len(papers) - 5} more")
    print()

    # Check existing relationships
    existing_relationships = list(firestore_client.db.collection('relationships').stream())
    print(f"📊 Current relationships in database: {len(existing_relationships)}")
    print()

    # Ask for confirmation to delete
    if len(existing_relationships) > 0:
        print("⚠️  WARNING: This will DELETE all existing relationships!")
        if sys.stdin.isatty():
            response = input("Proceed with deletion and regeneration? (yes/no): ").strip().lower()
            if response != 'yes':
                print("Operation cancelled by user")
                return
        else:
            print("Running non-interactively - proceeding with deletion...")

        print()
        print("Deleting existing relationships...")
        deleted_count = 0
        for rel in existing_relationships:
            try:
                firestore_client.db.collection('relationships').document(rel.id).delete()
                deleted_count += 1
                if deleted_count % 20 == 0:
                    print(f"  Deleted {deleted_count}/{len(existing_relationships)}...")
            except Exception as e:
                logger.error(f"Failed to delete relationship {rel.id}: {e}")

        print(f"✅ Deleted {deleted_count} relationships")
        print()

    # Calculate expected comparisons
    total_papers = len(papers_sorted)
    expected_comparisons = total_papers * (total_papers - 1) // 2  # n × (n-1) / 2

    print(f"Will perform {expected_comparisons} comparisons")
    print(f"Strategy: Each paper compared against all OLDER papers")
    print(f"This ensures temporal validity (newer → older) by design")
    print()

    # Process papers
    total_detected = 0
    total_stored = 0
    start_time = time.time()

    print("🔍 Starting relationship detection...")
    print()

    for i, new_paper in enumerate(papers_sorted):
        paper_title = new_paper.get('title', 'Unknown')[:60]
        paper_date = get_paper_date(new_paper)
        date_str = paper_date.strftime('%Y-%m-%d') if paper_date else 'no date'

        logger.info(f"Processing paper {i+1}/{total_papers}: {paper_title}... ({date_str})")
        print(f"\n[{i+1}/{total_papers}] Processing: {paper_title}... ({date_str})")

        # Get all older papers (papers after this index in our sorted list)
        older_papers = papers_sorted[i+1:]

        if not older_papers:
            print(f"  ⏭️  No older papers to compare against")
            continue

        print(f"  Comparing against {len(older_papers)} older papers...")

        # Use the batch detection method
        try:
            relationships = relationship_agent.detect_relationships_batch(
                new_paper=new_paper,
                existing_papers=older_papers,
                min_confidence=0.6
            )

            detected_count = len(relationships)
            total_detected += detected_count

            if detected_count > 0:
                print(f"  ✅ Found {detected_count} relationships:")

                # Store each relationship
                for rel in relationships:
                    try:
                        firestore_client.store_relationship(rel)
                        total_stored += 1

                        # Show details
                        target_paper = next((p for p in older_papers if p.get('paper_id') == rel['target_paper_id']), None)
                        if target_paper:
                            print(f"     - {rel['relationship_type']}: {target_paper.get('title', 'Unknown')[:50]}... (conf: {rel['confidence']:.2f})")

                    except Exception as e:
                        logger.error(f"Error storing relationship: {e}")
            else:
                print(f"  No relationships found")

        except Exception as e:
            logger.error(f"Error processing paper {paper_title}: {e}")
            continue

        # Progress summary
        elapsed = time.time() - start_time
        avg_time_per_paper = elapsed / (i + 1)
        eta = avg_time_per_paper * (total_papers - i - 1)
        print(f"  Progress: {i+1}/{total_papers}, Detected: {total_detected}, Stored: {total_stored}, ETA: {eta/60:.1f} min")

    # Summary
    elapsed_total = time.time() - start_time

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total papers processed: {total_papers}")
    print(f"Relationships detected (conf >= 0.6): {total_detected}")
    print(f"Relationships stored in Firestore: {total_stored}")
    print(f"Total time: {elapsed_total/60:.1f} minutes")
    print()

    # Breakdown by type
    print("Breakdown by relationship type:")
    relationships_final = list(firestore_client.db.collection('relationships').stream())

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
    print("All relationships respect temporal ordering (newer → older)")
    print()


if __name__ == "__main__":
    regenerate_all()

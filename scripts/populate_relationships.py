"""
Populate Relationships for Existing Papers

Runs the RelationshipAgent on all existing paper pairs to detect
relationships (supports, contradicts, extends).

This is a one-time batch job to populate the knowledge graph with
relationship data for papers that were ingested before Phase 2.1.

Usage:
    uv run python scripts/populate_relationships.py

Notes:
    - Processes all papers in Firestore
    - Compares each paper against all others
    - Stores detected relationships in Firestore
    - Uses gemini-2.5-pro (respects .env DEFAULT_MODEL)
    - Rate limit: 60 req/min with backoff
"""

import sys
import os
import time
import logging
from typing import List, Dict
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.ingestion.relationship_agent import RelationshipAgent
from src.storage.firestore_client import FirestoreClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True  # Override any existing config
)
logger = logging.getLogger(__name__)

# Also log to file for debugging
file_handler = logging.FileHandler('relationship_population.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)


def populate_relationships():
    """Populate relationships for all existing papers with temporal validation."""

    print("=" * 80)
    print("BATCH RELATIONSHIP DETECTION (WITH TEMPORAL VALIDATION)")
    print("=" * 80)
    print()

    # Initialize
    firestore_client = FirestoreClient()
    relationship_agent = RelationshipAgent()

    # Get all papers and sort by publication date
    print("📚 Fetching all papers from Firestore...")
    papers = firestore_client.get_all_papers()
    print(f"Found {len(papers)} papers in corpus")

    # Sort by publication date (newest first)
    from src.agents.ingestion.relationship_agent import get_paper_date
    papers_with_dates = [(p, get_paper_date(p)) for p in papers]
    papers_with_dates.sort(key=lambda x: x[1] if x[1] else datetime.min, reverse=True)
    papers_sorted = [p[0] for p in papers_with_dates]

    print()

    if len(papers) < 2:
        print("⚠️  Need at least 2 papers to detect relationships")
        return

    # Check existing relationships
    existing_relationships = list(firestore_client.db.collection('relationships').stream())
    print(f"📊 Current relationships in database: {len(existing_relationships)}")
    print()

    # Strategy: For each paper, compare it against all older papers
    # This ensures temporal validity and avoids bidirectional comparisons
    total_papers = len(papers_sorted)
    print(f"Will process {total_papers} papers (each compared against older papers)")
    print(f"Using temporal validation - only newer → older relationships will be created")
    print()
    print("Starting batch processing...")
    print()

    # Process papers
    total_detected = 0
    total_stored = 0
    total_skipped = 0
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
            print(f"  ⏭️  Skipping - no older papers to compare against")
            continue

        print(f"  Comparing against {len(older_papers)} older papers...")

        # Use the batch detection method (includes temporal validation)
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
                total_skipped += 1

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
    print(f"Papers with no relationships: {total_skipped}")
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
    print("✅ Relationship population complete!")
    print("=" * 80)
    print()
    print("All relationships respect temporal ordering (newer → older)")
    print()
    print("You can now query the knowledge graph:")
    print("  - 'What papers contradict each other?'")
    print("  - 'Which papers support the Transformer architecture?'")
    print("  - 'What papers extend BERT?'")
    print("  - 'Show me the most cited papers'")
    print()


if __name__ == "__main__":
    populate_relationships()

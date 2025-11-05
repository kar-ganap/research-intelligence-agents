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
    """Populate relationships for all existing papers."""

    print("=" * 80)
    print("BATCH RELATIONSHIP DETECTION")
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

    # Calculate total comparisons
    total_comparisons = len(papers) * (len(papers) - 1) // 2
    print(f"Will compare {total_comparisons} paper pairs")
    print(f"Estimated time: ~{total_comparisons * 2 / 60:.1f} minutes (at 60 req/min)")
    print()

    # Check existing relationships
    existing_relationships = list(firestore_client.db.collection('relationships').stream())
    print(f"📊 Current relationships in database: {len(existing_relationships)}")
    print()

    # Confirm before proceeding
    response = input("Continue with batch processing? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Cancelled.")
        return
    print()

    # Process all pairs
    processed = 0
    detected = 0
    stored = 0
    start_time = time.time()

    print("🔍 Starting relationship detection...")
    print()
    logger.info(f"Starting batch processing of {total_comparisons} paper pairs")

    for i, paper_a in enumerate(papers):
        # Log which paper we're currently processing
        logger.info(f"Processing paper {i+1}/{len(papers)}: {paper_a.get('title', 'Unknown')[:60]}...")

        for j, paper_b in enumerate(papers[i+1:], start=i+1):
            processed += 1

            # Progress update every comparison (unbuffered output)
            if processed % 10 == 0 or processed == 1:
                elapsed = time.time() - start_time
                rate = (processed / elapsed * 60) if elapsed > 0 else 0  # comparisons per minute
                eta = (total_comparisons - processed) / (rate / 60) if rate > 0 else 0
                msg = f"[{processed}/{total_comparisons}] Processed: {processed}, Detected: {detected}, Stored: {stored}, Rate: {rate:.1f}/min, ETA: {eta/60:.1f} min"
                print(msg, flush=True)  # Force flush to see output immediately
                logger.info(msg)

            # Detect relationship
            try:
                result = relationship_agent.detect_relationship(paper_a, paper_b)

                # Check if relationship found
                if result['relationship_type'] != 'none' and result['confidence'] >= 0.6:
                    detected += 1

                    print(f"✅ Found relationship ({result['relationship_type']}, {result['confidence']:.2f}):")
                    print(f"   {paper_a.get('title', 'Unknown')[:60]}...")
                    print(f"   {paper_b.get('title', 'Unknown')[:60]}...")
                    print(f"   Evidence: {result['evidence'][:100]}...")
                    print()

                    # Store in Firestore
                    relationship_data = {
                        'source_paper_id': paper_a.get('paper_id'),
                        'target_paper_id': paper_b.get('paper_id'),
                        'relationship_type': result['relationship_type'],
                        'confidence': result['confidence'],
                        'description': result['evidence']
                    }

                    firestore_client.db.collection('relationships').add(relationship_data)
                    stored += 1

                # Rate limiting: 60 req/min = 1 req/sec
                time.sleep(1)

            except Exception as e:
                logger.error(f"Error processing pair: {e}")
                continue

    # Summary
    elapsed_total = time.time() - start_time

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total pairs processed: {processed}/{total_comparisons}")
    print(f"Relationships detected (conf >= 0.6): {detected}")
    print(f"Relationships stored in Firestore: {stored}")
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
    print("✅ Relationship population complete!")
    print()
    print("You can now query contradictions:")
    print("  - 'What papers contradict each other?'")
    print("  - 'Which papers support X?'")
    print("  - 'What papers extend Y?'")
    print()


if __name__ == "__main__":
    populate_relationships()

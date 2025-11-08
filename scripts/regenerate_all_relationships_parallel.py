#!/usr/bin/env python3
"""
Regenerate All Relationships - Parallel with Rate Limiting

This script:
1. Deletes ALL existing relationships from the database
2. Regenerates relationships from scratch with proper temporal validation
3. Uses parallel processing with rate limiting to speed up execution

Rate limiting:
- Gemini API: 60 requests per minute for gemini-2.5-pro
- We'll use 50 req/min to be safe, with batches of 10 concurrent requests
"""

import sys
import os
import time
import logging
import asyncio
from typing import List, Dict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import threading

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
file_handler = logging.FileHandler('regenerate_all_relationships_parallel.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)


class RateLimiter:
    """Rate limiter for API calls."""

    def __init__(self, max_calls_per_minute: int = 50):
        self.max_calls = max_calls_per_minute
        self.calls = []
        self.lock = threading.Lock()

    def wait_if_needed(self):
        """Wait if we've hit the rate limit."""
        with self.lock:
            now = time.time()
            # Remove calls older than 1 minute
            self.calls = [t for t in self.calls if now - t < 60]

            if len(self.calls) >= self.max_calls:
                # Need to wait
                oldest = self.calls[0]
                wait_time = 60 - (now - oldest) + 0.1  # Add small buffer
                if wait_time > 0:
                    logger.info(f"Rate limit reached, waiting {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    # Clean up again after waiting
                    now = time.time()
                    self.calls = [t for t in self.calls if now - t < 60]

            # Record this call
            self.calls.append(time.time())


def detect_relationship_with_rate_limit(
    relationship_agent: RelationshipAgent,
    rate_limiter: RateLimiter,
    paper_a: Dict,
    paper_b: Dict
) -> Dict:
    """Detect relationship with rate limiting."""
    rate_limiter.wait_if_needed()
    return relationship_agent.detect_relationship(paper_a, paper_b)


def process_paper_batch(
    new_paper: Dict,
    older_papers: List[Dict],
    relationship_agent: RelationshipAgent,
    rate_limiter: RateLimiter,
    min_confidence: float = 0.6
) -> List[Dict]:
    """Process a batch of comparisons for a single paper in parallel."""

    relationships = []

    # Use ThreadPoolExecutor for parallel processing
    # Batch size of 10 to avoid overwhelming the system
    batch_size = 10

    for i in range(0, len(older_papers), batch_size):
        batch = older_papers[i:i+batch_size]

        with ThreadPoolExecutor(max_workers=min(batch_size, len(batch))) as executor:
            futures = []
            for older_paper in batch:
                future = executor.submit(
                    detect_relationship_with_rate_limit,
                    relationship_agent,
                    rate_limiter,
                    new_paper,
                    older_paper
                )
                futures.append((future, older_paper))

            # Collect results
            for future, older_paper in futures:
                try:
                    result = future.result(timeout=60)  # 60 second timeout per request

                    if result['confidence'] >= min_confidence and result['relationship_type'] != 'none':
                        relationships.append({
                            'source_paper_id': new_paper.get('paper_id'),
                            'target_paper_id': older_paper.get('paper_id'),
                            'relationship_type': result['relationship_type'],
                            'confidence': result['confidence'],
                            'evidence': result['evidence']
                        })
                except Exception as e:
                    logger.error(f"Error detecting relationship: {e}")
                    continue

    return relationships


def regenerate_all_parallel():
    """Delete all relationships and regenerate from scratch with parallelization."""

    print("=" * 80)
    print("REGENERATE ALL RELATIONSHIPS - PARALLEL MODE")
    print("=" * 80)
    print()

    # Initialize
    firestore_client = FirestoreClient()
    relationship_agent = RelationshipAgent()
    rate_limiter = RateLimiter(max_calls_per_minute=50)

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
    expected_comparisons = total_papers * (total_papers - 1) // 2

    print(f"Will perform {expected_comparisons} comparisons")
    print(f"Using parallel processing with rate limiting (50 req/min)")
    print(f"Batch size: 10 concurrent requests per paper")
    print()

    # Process papers
    total_detected = 0
    total_stored = 0
    start_time = time.time()

    print("🔍 Starting parallel relationship detection...")
    print()

    for i, new_paper in enumerate(papers_sorted):
        paper_title = new_paper.get('title', 'Unknown')[:60]
        paper_date = get_paper_date(new_paper)
        date_str = paper_date.strftime('%Y-%m-%d') if paper_date else 'no date'

        logger.info(f"Processing paper {i+1}/{total_papers}: {paper_title}... ({date_str})")
        print(f"\n[{i+1}/{total_papers}] Processing: {paper_title}... ({date_str})")

        # Get all older papers
        older_papers = papers_sorted[i+1:]

        if not older_papers:
            print(f"  ⏭️  No older papers to compare against")
            continue

        print(f"  Comparing against {len(older_papers)} older papers (in parallel batches of 10)...")

        # Process in parallel with rate limiting
        try:
            relationships = process_paper_batch(
                new_paper=new_paper,
                older_papers=older_papers,
                relationship_agent=relationship_agent,
                rate_limiter=rate_limiter,
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
    print(f"Average time per paper: {elapsed_total/total_papers:.1f}s")
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
    print("✅ Parallel relationship regeneration complete!")
    print("=" * 80)
    print()
    print("All relationships respect temporal ordering (newer → older)")
    print()


if __name__ == "__main__":
    regenerate_all_parallel()

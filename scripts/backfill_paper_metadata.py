#!/usr/bin/env python3
"""
Backfill Paper Metadata Script

Fetches category and published date information from arXiv API
for existing papers in Firestore that are missing these fields.
"""

import os
import sys
import logging
import arxiv
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from google.cloud import firestore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT', 'research-intel-agents')


def fetch_arxiv_metadata(arxiv_id):
    """
    Fetch metadata for a paper from arXiv API.

    Args:
        arxiv_id: arXiv ID (e.g., "1706.03762")

    Returns:
        dict with categories, primary_category, published, updated, abstract
    """
    try:
        search = arxiv.Search(id_list=[arxiv_id])
        result = next(search.results())

        return {
            'categories': result.categories,
            'primary_category': result.primary_category,
            'published': result.published.isoformat(),
            'updated': result.updated.isoformat() if result.updated else None,
            'abstract': result.summary.strip()
        }
    except Exception as e:
        logger.error(f"Failed to fetch metadata for {arxiv_id}: {e}")
        return None


def backfill_metadata():
    """
    Main function to backfill metadata for all papers.
    """
    logger.info(f"Starting metadata backfill for project: {PROJECT_ID}")

    # Initialize Firestore
    db = firestore.Client(project=PROJECT_ID)
    papers_ref = db.collection('papers')

    # Get all papers
    papers = papers_ref.stream()

    updated_count = 0
    skipped_count = 0
    failed_count = 0

    for doc in papers:
        paper = doc.to_dict()
        paper_id = doc.id
        arxiv_id = paper.get('arxiv_id')

        # Check if already has metadata (including abstract)
        if paper.get('primary_category') and paper.get('published') and paper.get('abstract'):
            logger.info(f"Skipping {arxiv_id} - already has metadata")
            skipped_count += 1
            continue

        if not arxiv_id:
            logger.warning(f"Skipping {paper_id} - no arXiv ID")
            skipped_count += 1
            continue

        logger.info(f"Fetching metadata for {arxiv_id}...")

        # Fetch metadata from arXiv
        metadata = fetch_arxiv_metadata(arxiv_id)

        if metadata:
            # Update Firestore document
            papers_ref.document(paper_id).update(metadata)
            logger.info(f"✅ Updated {arxiv_id}: {metadata['primary_category']}, {metadata['published']}")
            updated_count += 1
        else:
            logger.error(f"❌ Failed to update {arxiv_id}")
            failed_count += 1

    # Summary
    logger.info("=" * 60)
    logger.info("Backfill Complete")
    logger.info(f"  Updated: {updated_count}")
    logger.info(f"  Skipped: {skipped_count}")
    logger.info(f"  Failed: {failed_count}")
    logger.info("=" * 60)


if __name__ == '__main__':
    try:
        backfill_metadata()
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)

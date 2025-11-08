#!/usr/bin/env python3
"""
Generate embeddings for all papers in Firestore.

This script:
1. Fetches all papers from Firestore
2. Generates embeddings using text-embedding-004
3. Stores embeddings in a JSON cache file
4. Reports progress and failures
"""

import sys
import os
import json
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.firestore_client import FirestoreClient
from src.utils.embeddings import generate_embeddings_for_papers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cache file location
CACHE_DIR = Path(__file__).parent.parent / "cache"
EMBEDDINGS_CACHE_FILE = CACHE_DIR / "paper_embeddings.json"


def main():
    """Generate and cache embeddings for all papers."""
    logger.info("Starting embedding generation for all papers")

    # Create cache directory if needed
    CACHE_DIR.mkdir(exist_ok=True)

    # Fetch all papers from Firestore
    logger.info("Fetching papers from Firestore...")
    firestore_client = FirestoreClient()
    papers = firestore_client.get_all_papers()

    logger.info(f"Found {len(papers)} papers in corpus")

    # Generate embeddings
    logger.info("Generating embeddings...")
    embeddings = generate_embeddings_for_papers(papers)

    # Save to cache file
    logger.info(f"Saving embeddings to {EMBEDDINGS_CACHE_FILE}...")
    with open(EMBEDDINGS_CACHE_FILE, 'w') as f:
        json.dump(embeddings, f, indent=2)

    # Report statistics
    logger.info("=" * 80)
    logger.info("EMBEDDING GENERATION COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total papers: {len(papers)}")
    logger.info(f"Embeddings generated: {len(embeddings)}")
    logger.info(f"Success rate: {len(embeddings)/len(papers)*100:.1f}%")
    logger.info(f"Cache file: {EMBEDDINGS_CACHE_FILE}")

    if len(embeddings) < len(papers):
        failed_count = len(papers) - len(embeddings)
        logger.warning(f"{failed_count} papers failed to generate embeddings")

    logger.info("=" * 80)


if __name__ == "__main__":
    main()

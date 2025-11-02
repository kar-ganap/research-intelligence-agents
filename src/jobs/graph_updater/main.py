"""
Graph Updater Job

Cloud Run Job that:
1. Fetches all papers from Firestore
2. Detects relationships between papers using RelationshipAgent (ADK)
3. Stores relationships in Firestore
4. Exits when complete

Can run in parallel: Each task processes a subset of paper pairs
Triggered by: Cloud Scheduler (nightly) or manual
"""

import os
import sys
import logging
from typing import List, Dict, Tuple

from src.agents.ingestion.relationship_agent import RelationshipAgent
from src.storage.firestore_client import FirestoreClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT')
CLOUD_RUN_TASK_INDEX = int(os.environ.get('CLOUD_RUN_TASK_INDEX', '0'))
CLOUD_RUN_TASK_COUNT = int(os.environ.get('CLOUD_RUN_TASK_COUNT', '1'))

# Control flags
SKIP_EXISTING = os.environ.get('SKIP_EXISTING', 'true').lower() == 'true'


def get_paper_pairs_for_task(papers: List[Dict], task_index: int, task_count: int) -> List[Tuple[Dict, Dict]]:
    """
    Distribute paper pairs across parallel tasks.

    Each task gets a subset of pairs to process.

    Args:
        papers: List of all papers
        task_index: Current task index (0-based)
        task_count: Total number of tasks

    Returns:
        List of (source_paper, target_paper) tuples for this task
    """
    all_pairs = []

    # Generate all unique pairs (n choose 2)
    for i in range(len(papers)):
        for j in range(i + 1, len(papers)):
            all_pairs.append((papers[i], papers[j]))

    # Distribute pairs across tasks
    pairs_for_task = []
    for idx, pair in enumerate(all_pairs):
        if idx % task_count == task_index:
            pairs_for_task.append(pair)

    logger.info(f"Task {task_index}: Processing {len(pairs_for_task)} pairs out of {len(all_pairs)} total")
    return pairs_for_task


def detect_relationship(
    source_paper: Dict,
    target_paper: Dict,
    relationship_agent: RelationshipAgent,
    firestore_client: FirestoreClient
) -> bool:
    """
    Detect and store relationship between two papers.

    Args:
        source_paper: Source paper data
        target_paper: Target paper data
        relationship_agent: Initialized RelationshipAgent
        firestore_client: Firestore client

    Returns:
        True if relationship found and stored, False otherwise
    """
    source_id = source_paper['paper_id']
    target_id = target_paper['paper_id']

    logger.info(f"Analyzing: {source_paper['title'][:40]}... → {target_paper['title'][:40]}...")

    try:
        # Check if relationship already exists
        if SKIP_EXISTING:
            existing = firestore_client.get_relationship(source_id, target_id)
            if existing:
                logger.info(f"  ⏭️  Relationship already exists, skipping")
                return False

        # Detect relationship using ADK agent
        result = relationship_agent.detect_relationship(
            source_paper=source_paper,
            target_paper=target_paper
        )

        if result.get('relationship_type'):
            # Store relationship
            relationship_data = {
                'source_id': source_id,
                'target_id': target_id,
                'relationship_type': result['relationship_type'],
                'confidence': result.get('confidence', 0.5),
                'evidence': result.get('evidence', ''),
                'created_at': firestore_client._get_timestamp()
            }

            firestore_client.store_relationship(relationship_data)

            logger.info(f"  ✅ Found: {result['relationship_type']} (confidence: {result.get('confidence', 0):.2f})")
            return True
        else:
            logger.info(f"  ⚪ No relationship detected")
            return False

    except Exception as e:
        logger.error(f"  ❌ Error: {str(e)}")
        return False


def main():
    """
    Main job execution.

    Steps:
    1. Fetch all papers
    2. Generate paper pairs for this task
    3. Detect relationships using RelationshipAgent (ADK)
    4. Store results
    5. Exit
    """
    logger.info("=" * 70)
    logger.info("Graph Updater Job Started")
    logger.info("=" * 70)
    logger.info(f"Project ID: {PROJECT_ID}")
    logger.info(f"Task Index: {CLOUD_RUN_TASK_INDEX}")
    logger.info(f"Task Count: {CLOUD_RUN_TASK_COUNT}")
    logger.info(f"Skip Existing: {SKIP_EXISTING}")
    logger.info("=" * 70)

    try:
        # Initialize clients
        logger.info("Initializing RelationshipAgent (ADK)...")
        relationship_agent = RelationshipAgent()
        logger.info("RelationshipAgent initialized")

        logger.info("Initializing Firestore client...")
        firestore_client = FirestoreClient(project_id=PROJECT_ID)
        logger.info("Firestore client initialized")

        # Fetch all papers
        logger.info("Fetching all papers...")
        papers = firestore_client.get_all_papers()
        logger.info(f"Found {len(papers)} papers")

        if len(papers) < 2:
            logger.warning("Need at least 2 papers to detect relationships")
            return 0

        # Get pairs for this task
        pairs = get_paper_pairs_for_task(papers, CLOUD_RUN_TASK_INDEX, CLOUD_RUN_TASK_COUNT)

        if not pairs:
            logger.warning(f"No pairs assigned to task {CLOUD_RUN_TASK_INDEX}")
            return 0

        # Process pairs
        logger.info(f"\nProcessing {len(pairs)} paper pairs...")
        relationships_found = 0

        for i, (source, target) in enumerate(pairs, 1):
            logger.info(f"\n--- Pair {i}/{len(pairs)} ---")

            found = detect_relationship(source, target, relationship_agent, firestore_client)
            if found:
                relationships_found += 1

        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("Graph Updater Job Complete")
        logger.info(f"  Pairs processed: {len(pairs)}")
        logger.info(f"  Relationships found: {relationships_found}")
        logger.info(f"  Task: {CLOUD_RUN_TASK_INDEX + 1}/{CLOUD_RUN_TASK_COUNT}")
        logger.info("=" * 70)

        return 0

    except Exception as e:
        logger.error(f"Job failed: {str(e)}", exc_info=True)
        return 1


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.warning("Job interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        sys.exit(1)

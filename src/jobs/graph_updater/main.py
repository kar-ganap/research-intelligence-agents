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


def get_papers_for_task(papers: List[Dict], task_index: int, task_count: int) -> List[Dict]:
    """
    Distribute papers across parallel tasks.

    Each task gets a subset of papers to process against all other papers.

    Args:
        papers: List of all papers
        task_index: Current task index (0-based)
        task_count: Total number of tasks

    Returns:
        List of papers for this task to process
    """
    # Distribute papers across tasks
    papers_for_task = []
    for idx, paper in enumerate(papers):
        if idx % task_count == task_index:
            papers_for_task.append(paper)

    logger.info(f"Task {task_index}: Processing {len(papers_for_task)} papers out of {len(papers)} total")
    return papers_for_task




def main():
    """
    Main job execution with temporal validation.

    Steps:
    1. Fetch all papers
    2. Distribute papers across parallel tasks
    3. For each paper assigned to this task, detect relationships with all other papers
    4. Use detect_relationships_batch() which includes temporal validation
    5. Store results
    6. Exit
    """
    logger.info("=" * 70)
    logger.info("Graph Updater Job Started (with temporal validation)")
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

        # Get papers for this task
        task_papers = get_papers_for_task(papers, CLOUD_RUN_TASK_INDEX, CLOUD_RUN_TASK_COUNT)

        if not task_papers:
            logger.warning(f"No papers assigned to task {CLOUD_RUN_TASK_INDEX}")
            return 0

        # Process papers with temporal validation
        logger.info(f"\nProcessing {len(task_papers)} papers with temporal validation...")
        relationships_found = 0
        relationships_skipped = 0

        for i, current_paper in enumerate(task_papers, 1):
            # Get all other papers
            other_papers = [p for p in papers if p['paper_id'] != current_paper['paper_id']]

            logger.info(f"\n--- Paper {i}/{len(task_papers)} ---")
            logger.info(f"Title: {current_paper['title'][:50]}...")

            # Use detect_relationships_batch which includes temporal validation
            relationships = relationship_agent.detect_relationships_batch(
                new_paper=current_paper,
                existing_papers=other_papers,
                min_confidence=0.6
            )

            # Store relationships that don't already exist
            for rel in relationships:
                source_id = rel.get('source_paper_id')
                target_id = rel.get('target_paper_id')

                # Check if relationship already exists
                if SKIP_EXISTING:
                    existing = firestore_client.get_relationship_between_papers(source_id, target_id)
                    if existing:
                        relationships_skipped += 1
                        continue

                # Store new relationship
                relationship_data = {
                    'source_id': source_id,
                    'target_id': target_id,
                    'relationship_type': rel['relationship_type'],
                    'confidence': rel.get('confidence', 0.5),
                    'evidence': rel.get('evidence', ''),
                    'created_at': firestore_client._get_timestamp()
                }

                firestore_client.store_relationship(relationship_data)
                relationships_found += 1
                logger.info(f"  ✅ Stored: {rel['relationship_type']} (confidence: {rel.get('confidence', 0):.2f})")

        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("Graph Updater Job Complete")
        logger.info(f"  Papers processed: {len(task_papers)}")
        logger.info(f"  Relationships found: {relationships_found}")
        logger.info(f"  Skipped (existing): {relationships_skipped}")
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

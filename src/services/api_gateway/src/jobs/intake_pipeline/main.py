"""
Intake Pipeline Job

Cloud Run Job that:
1. Receives paper data (from Pub/Sub or direct invocation)
2. Downloads PDF
3. Runs IngestionPipeline (EntityAgent, IndexerAgent, RelationshipAgent)
4. Stores in Firestore
5. Publishes to alert matching (optional)
6. Exits when complete

Can run in parallel: Each task processes a subset of papers
Triggered by: Manual, scheduled, or Pub/Sub
"""

import os
import sys
import logging
import json
import tempfile
import requests
from pathlib import Path
from typing import Dict, List, Optional

from src.pipelines.ingestion_pipeline import IngestionPipeline
from google.cloud import pubsub_v1

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

# Pub/Sub configuration (optional)
PUBSUB_SUBSCRIPTION = os.environ.get('PUBSUB_SUBSCRIPTION', 'arxiv-candidates-sub')


def download_pdf(pdf_url: str, output_dir: Path) -> Optional[Path]:
    """
    Download PDF from arXiv.

    Args:
        pdf_url: URL to PDF
        output_dir: Directory to save PDF

    Returns:
        Path to downloaded PDF, or None if failed
    """
    try:
        logger.info(f"Downloading PDF: {pdf_url}")

        response = requests.get(pdf_url, timeout=60)
        response.raise_for_status()

        # Extract filename from URL or generate one
        arxiv_id = pdf_url.split('/')[-1].replace('.pdf', '')
        pdf_path = output_dir / f"{arxiv_id}.pdf"

        with open(pdf_path, 'wb') as f:
            f.write(response.content)

        logger.info(f"Downloaded PDF to: {pdf_path}")
        return pdf_path

    except Exception as e:
        logger.error(f"Error downloading PDF {pdf_url}: {str(e)}")
        return None


def process_paper(paper_data: Dict, ingestion_pipeline: IngestionPipeline) -> bool:
    """
    Process a single paper through ingestion pipeline.

    Args:
        paper_data: Paper metadata from arXiv
        ingestion_pipeline: Initialized pipeline

    Returns:
        True if successful, False otherwise
    """
    arxiv_id = paper_data.get('arxiv_id', 'unknown')
    title = paper_data.get('title', 'Unknown')

    logger.info(f"Processing paper: {title}")
    logger.info(f"  arXiv ID: {arxiv_id}")

    try:
        # Create temporary directory for PDF
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Download PDF
            pdf_path = download_pdf(paper_data['pdf_url'], temp_path)
            if not pdf_path:
                logger.error(f"Failed to download PDF for {arxiv_id}")
                return False

            # Run ingestion pipeline
            logger.info(f"Running ingestion pipeline for {arxiv_id}...")
            result = ingestion_pipeline.ingest_paper(
                pdf_path=str(pdf_path),
                paper_id=arxiv_id
            )

            if result['status'] == 'success':
                logger.info(f"✅ Successfully ingested: {title}")
                logger.info(f"  Paper ID: {result['paper_id']}")
                logger.info(f"  Relationships detected: {result.get('relationships_detected', 0)}")
                logger.info(f"  Alerts triggered: {result.get('alerts_triggered', 0)}")
                return True
            else:
                logger.error(f"❌ Failed to ingest: {title}")
                logger.error(f"  Error: {result.get('error', 'Unknown')}")
                return False

    except Exception as e:
        logger.error(f"Error processing paper {arxiv_id}: {str(e)}", exc_info=True)
        return False


def pull_from_pubsub(subscription_path: str, max_messages: int = 10) -> List[Dict]:
    """
    Pull messages from Pub/Sub subscription.

    Args:
        subscription_path: Full subscription path
        max_messages: Maximum messages to pull

    Returns:
        List of paper data dictionaries
    """
    logger.info(f"Pulling up to {max_messages} messages from Pub/Sub...")

    subscriber = pubsub_v1.SubscriberClient()

    try:
        response = subscriber.pull(
            request={
                "subscription": subscription_path,
                "max_messages": max_messages,
            },
            timeout=30.0
        )

        papers = []
        ack_ids = []

        for received_message in response.received_messages:
            try:
                # Parse message
                message_data = received_message.message.data.decode('utf-8')
                paper_data = json.loads(message_data)
                papers.append(paper_data)
                ack_ids.append(received_message.ack_id)

                logger.info(f"Received: {paper_data.get('title', 'Unknown')[:50]}...")

            except Exception as e:
                logger.error(f"Error parsing message: {str(e)}")
                continue

        # Acknowledge messages
        if ack_ids:
            subscriber.acknowledge(
                request={
                    "subscription": subscription_path,
                    "ack_ids": ack_ids,
                }
            )
            logger.info(f"Acknowledged {len(ack_ids)} messages")

        return papers

    except Exception as e:
        logger.error(f"Error pulling from Pub/Sub: {str(e)}")
        return []


def main():
    """
    Main job execution.

    Supports two modes:
    1. Pub/Sub mode: Pull papers from subscription
    2. Direct mode: Process papers from environment variable (for testing)
    """
    logger.info("=" * 70)
    logger.info("Intake Pipeline Job Started")
    logger.info("=" * 70)
    logger.info(f"Project ID: {PROJECT_ID}")
    logger.info(f"Task Index: {CLOUD_RUN_TASK_INDEX}")
    logger.info(f"Task Count: {CLOUD_RUN_TASK_COUNT}")
    logger.info("=" * 70)

    try:
        # Initialize ingestion pipeline with all features
        logger.info("Initializing ingestion pipeline...")
        ingestion_pipeline = IngestionPipeline(
            project_id=PROJECT_ID,
            enable_relationships=True,
            enable_alerting=True
        )
        logger.info("Ingestion pipeline initialized")

        # Get papers to process
        papers = []

        # Mode 1: Pull from Pub/Sub
        if PUBSUB_SUBSCRIPTION:
            subscriber = pubsub_v1.SubscriberClient()
            subscription_path = subscriber.subscription_path(PROJECT_ID, PUBSUB_SUBSCRIPTION)

            # Calculate how many messages this task should process
            messages_per_task = 10
            papers = pull_from_pubsub(subscription_path, messages_per_task)

        # Mode 2: Direct invocation (for testing)
        # Can add paper data via environment variable PAPER_DATA='[{...}, {...}]'
        elif os.environ.get('PAPER_DATA'):
            logger.info("Using direct paper data from environment")
            paper_data_str = os.environ.get('PAPER_DATA')
            papers = json.loads(paper_data_str)

        if not papers:
            logger.warning("No papers to process")
            return 0

        # Process papers
        logger.info(f"Processing {len(papers)} papers...")
        success_count = 0

        for i, paper_data in enumerate(papers, 1):
            logger.info(f"\n{'=' * 70}")
            logger.info(f"Paper {i}/{len(papers)}")
            logger.info(f"{'=' * 70}")

            success = process_paper(paper_data, ingestion_pipeline)
            if success:
                success_count += 1

        # Summary
        logger.info("\n" + "=" * 70)
        logger.info(f"Intake Pipeline Job Complete")
        logger.info(f"  Processed: {len(papers)} papers")
        logger.info(f"  Successful: {success_count}")
        logger.info(f"  Failed: {len(papers) - success_count}")
        logger.info("=" * 70)

        return 0 if success_count > 0 else 1

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

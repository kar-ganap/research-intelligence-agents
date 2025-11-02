"""
ArXiv Watcher Job

Cloud Run Job that:
1. Queries arXiv for new papers matching research interests
2. Publishes candidates to Pub/Sub topic
3. Exits when complete

Triggered by: Cloud Scheduler (daily at 6am)
"""

import os
import sys
import logging
import arxiv
from datetime import datetime, timedelta
from typing import List, Dict
import json

from google.cloud import pubsub_v1

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT')
PUBSUB_TOPIC = os.environ.get('PUBSUB_TOPIC', 'arxiv-candidates')
MAX_RESULTS = int(os.environ.get('MAX_RESULTS', '50'))

# Research interest categories (configurable)
CATEGORIES = [
    'cs.AI',  # Artificial Intelligence
    'cs.CL',  # Computation and Language
    'cs.LG',  # Machine Learning
    'cs.CV',  # Computer Vision
]


def fetch_recent_papers(days_back: int = 1) -> List[Dict]:
    """
    Fetch papers from arXiv published in the last N days.

    Args:
        days_back: How many days back to search

    Returns:
        List of paper dictionaries
    """
    logger.info(f"Fetching papers from last {days_back} days...")

    papers = []

    for category in CATEGORIES:
        logger.info(f"Searching category: {category}")

        try:
            search = arxiv.Search(
                query=f"cat:{category}",
                max_results=MAX_RESULTS,
                sort_by=arxiv.SortCriterion.SubmittedDate
            )

            for result in search.results():
                # Check if paper was published in our timeframe
                days_since_published = (datetime.now() - result.published.replace(tzinfo=None)).days

                if days_since_published <= days_back:
                    paper_data = {
                        'arxiv_id': result.get_short_id(),
                        'title': result.title,
                        'authors': [author.name for author in result.authors],
                        'abstract': result.summary,
                        'pdf_url': result.pdf_url,
                        'categories': result.categories,
                        'primary_category': result.primary_category,
                        'published': result.published.isoformat(),
                        'updated': result.updated.isoformat() if result.updated else None,
                        'comment': result.comment,
                        'journal_ref': result.journal_ref
                    }

                    papers.append(paper_data)
                    logger.info(f"Found: {paper_data['title'][:60]}...")

        except Exception as e:
            logger.error(f"Error searching category {category}: {str(e)}")
            continue

    logger.info(f"Total papers found: {len(papers)}")
    return papers


def publish_to_pubsub(papers: List[Dict]) -> int:
    """
    Publish paper candidates to Pub/Sub topic.

    Args:
        papers: List of paper dictionaries

    Returns:
        Number of papers successfully published
    """
    if not papers:
        logger.info("No papers to publish")
        return 0

    logger.info(f"Publishing {len(papers)} papers to Pub/Sub topic: {PUBSUB_TOPIC}")

    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, PUBSUB_TOPIC)

    published_count = 0

    for paper in papers:
        try:
            # Convert to JSON
            message_json = json.dumps(paper)
            message_bytes = message_json.encode('utf-8')

            # Publish
            future = publisher.publish(topic_path, message_bytes)
            message_id = future.result()

            logger.info(f"Published: {paper['title'][:50]}... (message_id: {message_id})")
            published_count += 1

        except Exception as e:
            logger.error(f"Error publishing paper {paper['arxiv_id']}: {str(e)}")
            continue

    logger.info(f"Successfully published {published_count}/{len(papers)} papers")
    return published_count


def main():
    """
    Main job execution.

    Steps:
    1. Fetch recent papers from arXiv
    2. Publish to Pub/Sub
    3. Exit with status code
    """
    logger.info("=" * 70)
    logger.info("ArXiv Watcher Job Started")
    logger.info("=" * 70)
    logger.info(f"Project ID: {PROJECT_ID}")
    logger.info(f"Pub/Sub Topic: {PUBSUB_TOPIC}")
    logger.info(f"Max Results per Category: {MAX_RESULTS}")
    logger.info(f"Categories: {', '.join(CATEGORIES)}")
    logger.info("=" * 70)

    try:
        # Step 1: Fetch papers
        papers = fetch_recent_papers(days_back=1)

        if not papers:
            logger.warning("No new papers found")
            return 0

        # Step 2: Publish to Pub/Sub
        published_count = publish_to_pubsub(papers)

        # Step 3: Exit
        logger.info("=" * 70)
        logger.info(f"ArXiv Watcher Job Complete: {published_count} papers published")
        logger.info("=" * 70)

        return 0 if published_count > 0 else 1

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

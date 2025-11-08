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
from typing import List, Dict, Set
import json

from google.cloud import pubsub_v1
from src.storage.firestore_client import FirestoreClient

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
    'cs.AI',   # Artificial Intelligence
    'cs.CL',   # Computation and Language
    'cs.LG',   # Machine Learning
    'cs.CV',   # Computer Vision
    'cs.MA',   # Multiagent Systems
    'math.ST', # Statistics Theory
    'stat.ML', # Machine Learning (Statistics)
    'stat.CO', # Computation (Statistics)
]


def fetch_papers_by_category(days_back: int = 1) -> List[Dict]:
    """
    Fetch papers from baseline arXiv categories (broad sweep).

    Args:
        days_back: How many days back to search

    Returns:
        List of paper dictionaries
    """
    logger.info(f"[Baseline] Fetching papers from last {days_back} days...")

    papers = []

    for category in CATEGORIES:
        logger.info(f"[Baseline] Searching category: {category}")

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
                        'journal_ref': result.journal_ref,
                        'source': 'baseline_category'
                    }

                    papers.append(paper_data)
                    logger.info(f"[Baseline] Found: {paper_data['title'][:60]}...")

        except Exception as e:
            logger.error(f"Error searching category {category}: {str(e)}")
            continue

    logger.info(f"[Baseline] Total papers found: {len(papers)}")
    return papers


def fetch_papers_by_watch_rules(firestore_client: FirestoreClient, days_back: int = 1) -> List[Dict]:
    """
    Fetch papers based on active watch rules with proactive search enabled.

    Args:
        firestore_client: Firestore client to fetch watch rules
        days_back: How many days back to search

    Returns:
        List of paper dictionaries
    """
    logger.info("[Watch Rules] Fetching papers based on active watch rules...")

    papers = []

    try:
        # Get all active watch rules
        active_rules = firestore_client.get_all_active_rules()
        logger.info(f"[Watch Rules] Found {len(active_rules)} active watch rules")

        if not active_rules:
            return papers

        # Track seen arxiv_ids to avoid duplicates
        seen_ids = set()

        for rule in active_rules:
            rule_type = rule.get('rule_type')
            rule_id = rule.get('rule_id', 'unknown')

            # Build arXiv query based on rule type
            arxiv_query = None

            if rule_type == 'keyword':
                keywords = rule.get('keywords', [])
                if keywords:
                    # Build query: all:keyword1 AND all:keyword2
                    query_parts = [f'all:{kw}' for kw in keywords[:3]]  # Limit to 3 keywords
                    arxiv_query = ' AND '.join(query_parts)
                    logger.info(f"[Watch Rules] Keyword rule {rule_id}: {arxiv_query}")

            elif rule_type == 'author':
                author_name = rule.get('author_name')
                if author_name:
                    # Build query: au:Author+Name
                    arxiv_query = f'au:{author_name.replace(" ", "+")}'
                    logger.info(f"[Watch Rules] Author rule {rule_id}: {arxiv_query}")

            elif rule_type == 'claim':
                # For claim rules, extract keywords from the claim
                claim = rule.get('claim', '')
                if claim:
                    # Simple keyword extraction (split on spaces, take meaningful words)
                    words = [w.lower() for w in claim.split() if len(w) > 4][:3]
                    if words:
                        query_parts = [f'all:{w}' for w in words]
                        arxiv_query = ' AND '.join(query_parts)
                        logger.info(f"[Watch Rules] Claim rule {rule_id}: {arxiv_query}")

            # Execute arXiv search if we have a query
            if arxiv_query:
                try:
                    search = arxiv.Search(
                        query=arxiv_query,
                        max_results=20,  # Limit per rule
                        sort_by=arxiv.SortCriterion.SubmittedDate
                    )

                    for result in search.results():
                        arxiv_id = result.get_short_id()

                        # Skip duplicates
                        if arxiv_id in seen_ids:
                            continue

                        # Check if paper was published in our timeframe
                        days_since_published = (datetime.now() - result.published.replace(tzinfo=None)).days

                        if days_since_published <= days_back:
                            paper_data = {
                                'arxiv_id': arxiv_id,
                                'title': result.title,
                                'authors': [author.name for author in result.authors],
                                'abstract': result.summary,
                                'pdf_url': result.pdf_url,
                                'categories': result.categories,
                                'primary_category': result.primary_category,
                                'published': result.published.isoformat(),
                                'updated': result.updated.isoformat() if result.updated else None,
                                'comment': result.comment,
                                'journal_ref': result.journal_ref,
                                'source': f'watch_rule_{rule_id}',
                                'matched_rule_id': rule_id,
                                'matched_rule_type': rule_type
                            }

                            papers.append(paper_data)
                            seen_ids.add(arxiv_id)
                            logger.info(f"[Watch Rules] Found: {paper_data['title'][:60]}... (rule: {rule_id})")

                except Exception as e:
                    logger.error(f"Error searching for rule {rule_id}: {str(e)}")
                    continue

    except Exception as e:
        logger.error(f"Error fetching watch rule papers: {str(e)}", exc_info=True)

    logger.info(f"[Watch Rules] Total papers found: {len(papers)}")
    return papers


def deduplicate_papers(papers: List[Dict]) -> List[Dict]:
    """
    Deduplicate papers by arxiv_id, keeping the first occurrence.

    Args:
        papers: List of paper dictionaries

    Returns:
        Deduplicated list of papers
    """
    seen_ids: Set[str] = set()
    deduplicated = []

    for paper in papers:
        arxiv_id = paper.get('arxiv_id')
        if arxiv_id and arxiv_id not in seen_ids:
            seen_ids.add(arxiv_id)
            deduplicated.append(paper)

    logger.info(f"Deduplication: {len(papers)} → {len(deduplicated)} papers")
    return deduplicated


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

    Hybrid approach:
    1. Fetch papers from baseline categories (broad sweep)
    2. Fetch papers based on active watch rules (targeted search)
    3. Deduplicate and publish to Pub/Sub
    4. Exit with status code
    """
    logger.info("=" * 70)
    logger.info("ArXiv Watcher Job Started (Hybrid Mode)")
    logger.info("=" * 70)
    logger.info(f"Project ID: {PROJECT_ID}")
    logger.info(f"Pub/Sub Topic: {PUBSUB_TOPIC}")
    logger.info(f"Max Results per Category: {MAX_RESULTS}")
    logger.info(f"Baseline Categories: {', '.join(CATEGORIES)}")
    logger.info("=" * 70)

    try:
        all_papers = []

        # Step 1: Fetch papers from baseline categories
        logger.info("\n=== Phase 1: Baseline Category Search ===")
        baseline_papers = fetch_papers_by_category(days_back=1)
        all_papers.extend(baseline_papers)

        # Step 2: Fetch papers based on watch rules
        logger.info("\n=== Phase 2: Watch Rule-Based Search ===")
        try:
            firestore_client = FirestoreClient(project_id=PROJECT_ID)
            watch_rule_papers = fetch_papers_by_watch_rules(firestore_client, days_back=1)
            all_papers.extend(watch_rule_papers)
        except Exception as e:
            logger.warning(f"Watch rule search failed (non-blocking): {str(e)}")

        # Step 3: Deduplicate
        logger.info("\n=== Phase 3: Deduplication ===")
        unique_papers = deduplicate_papers(all_papers)

        if not unique_papers:
            logger.warning("No new papers found")
            return 0

        # Step 4: Publish to Pub/Sub
        logger.info("\n=== Phase 4: Publishing to Pub/Sub ===")
        published_count = publish_to_pubsub(unique_papers)

        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("ArXiv Watcher Job Complete")
        logger.info(f"  Baseline papers: {len(baseline_papers)}")
        logger.info(f"  Watch rule papers: {len(watch_rule_papers) if 'watch_rule_papers' in locals() else 0}")
        logger.info(f"  Total unique: {len(unique_papers)}")
        logger.info(f"  Published: {published_count}")
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

"""
Ingestion Pipeline

Orchestrates the paper ingestion process:
1. Load PDF and extract text
2. Extract entities (title, authors, key finding)
3. Store in Firestore

Phase 1 approach: Simple Python orchestration for reliability and clarity.
"""

from typing import Dict, List, Tuple, Optional
import logging
from pathlib import Path
import time
import json
import os

from google.cloud import pubsub_v1

from src.tools.pdf_reader import read_pdf
from src.agents.ingestion.entity_agent import EntityAgent
from src.agents.ingestion.indexer_agent import IndexerAgent
from src.agents.ingestion.relationship_agent import RelationshipAgent
from src.tools.matching import (
    match_keyword_rule,
    match_claim_rule,
    match_relationship_rule,
    match_author_rule,
    match_template_rule,
    ClaimMatcher
)

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """
    Orchestrates the paper ingestion process.

    Phase 1 approach: Simple Python orchestration for reliability.
    Explicitly passes data between components for clarity.
    """

    def __init__(
        self,
        project_id: str = None,
        enable_relationships: bool = False,
        enable_alerting: bool = False,
        enable_pubsub: bool = True
    ):
        """
        Initialize the ingestion pipeline.

        Args:
            project_id: GCP project ID for Firestore
            enable_relationships: Whether to detect relationships (Phase 2.1 feature)
            enable_alerting: Whether to check watch rules and create alerts (Phase 2.2 feature)
            enable_pubsub: Whether to publish to Pub/Sub after ingestion (triggers graph updater)
        """
        self.entity_agent = EntityAgent()
        self.indexer_agent = IndexerAgent(project_id=project_id)
        self.enable_relationships = enable_relationships
        self.enable_alerting = enable_alerting
        self.enable_pubsub = enable_pubsub
        self.project_id = project_id or os.environ.get('GOOGLE_CLOUD_PROJECT')

        if enable_relationships:
            self.relationship_agent = RelationshipAgent()
            logger.info("IngestionPipeline initialized with relationship detection")
        else:
            self.relationship_agent = None

        if enable_alerting:
            self.claim_matcher = ClaimMatcher()
            logger.info("IngestionPipeline initialized with proactive alerting")
        else:
            self.claim_matcher = None

        if enable_pubsub:
            self.pubsub_publisher = pubsub_v1.PublisherClient()
            logger.info("IngestionPipeline initialized with Pub/Sub publishing")
        else:
            self.pubsub_publisher = None

        if not enable_relationships and not enable_alerting:
            logger.info("IngestionPipeline initialized (relationships and alerting disabled)")

    def ingest_paper(self, pdf_path: str, arxiv_id: str = "", metadata: Dict = None) -> Dict:
        """
        Ingest a single paper through the full pipeline.

        Args:
            pdf_path: Path to the PDF file
            arxiv_id: arXiv ID (optional, for metadata)
            metadata: Additional metadata (categories, primary_category, published, updated)

        Returns:
            Dictionary with:
                - success: bool
                - paper_id: str (if successful)
                - steps: dict with status of each step
                - duration: float (seconds)
                - error: str (if failed)
        """
        if metadata is None:
            metadata = {}
        start_time = time.time()

        result = {
            "success": False,
            "pdf_path": pdf_path,
            "arxiv_id": arxiv_id,
            "steps": {}
        }

        try:
            # Step 1: Extract text from PDF
            logger.info(f"Step 1/3: Extracting text from {pdf_path}")
            step_start = time.time()

            pdf_result = read_pdf(pdf_path)

            result["steps"]["pdf_extraction"] = {
                "success": True,
                "page_count": pdf_result["page_count"],
                "text_length": len(pdf_result["text"]),
                "duration": time.time() - step_start
            }

            paper_text = pdf_result["text"]
            pdf_metadata = pdf_result.get("metadata", {})

            # Step 2: Extract entities with EntityAgent
            logger.info("Step 2/3: Extracting entities")
            step_start = time.time()

            entities = self.entity_agent.extract(paper_text)

            # Check for extraction errors
            if "error" in entities:
                result["steps"]["entity_extraction"] = {
                    "success": False,
                    "error": entities["error"],
                    "duration": time.time() - step_start
                }
                result["error"] = f"Entity extraction failed: {entities['error']}"
                result["duration"] = time.time() - start_time
                return result

            result["steps"]["entity_extraction"] = {
                "success": True,
                "title": entities.get("title", ""),
                "authors_count": len(entities.get("authors", [])),
                "key_finding_length": len(entities.get("key_finding", "")),
                "duration": time.time() - step_start
            }

            # Step 3: Index to Firestore
            logger.info("Step 3/3: Indexing to Firestore")
            step_start = time.time()

            index_result = self.indexer_agent.index(
                entities=entities,
                pdf_path=pdf_path,
                arxiv_id=arxiv_id,
                metadata=metadata
            )

            result["steps"]["indexing"] = {
                "success": index_result["success"],
                "paper_id": index_result.get("paper_id", ""),
                "already_exists": index_result.get("already_exists", False),
                "duration": time.time() - step_start
            }

            if not index_result["success"]:
                result["error"] = f"Indexing failed: {index_result.get('error')}"
                result["duration"] = time.time() - start_time
                return result

            # Step 4 (Optional): Detect relationships
            if self.enable_relationships and self.relationship_agent:
                logger.info("Step 4/4: Detecting relationships")
                step_start = time.time()

                try:
                    # Get all existing papers from Firestore
                    existing_papers = self.indexer_agent.firestore_client.get_all_papers()

                    # Create paper object for new paper
                    new_paper = {
                        'paper_id': index_result['paper_id'],
                        'title': entities.get('title', ''),
                        'authors': entities.get('authors', []),
                        'key_finding': entities.get('key_finding', '')
                    }

                    # Detect relationships
                    relationships = self.relationship_agent.detect_relationships_batch(
                        new_paper=new_paper,
                        existing_papers=existing_papers,
                        min_confidence=0.6
                    )

                    # Store relationships in Firestore
                    relationship_ids = []
                    for rel in relationships:
                        rel_id = self.indexer_agent.firestore_client.store_relationship(rel)
                        relationship_ids.append(rel_id)

                    result["steps"]["relationship_detection"] = {
                        "success": True,
                        "relationships_found": len(relationships),
                        "relationship_ids": relationship_ids,
                        "duration": time.time() - step_start
                    }

                    logger.info(f"Found {len(relationships)} relationships")

                except Exception as e:
                    logger.warning(f"Relationship detection failed (non-blocking): {e}")
                    result["steps"]["relationship_detection"] = {
                        "success": False,
                        "error": str(e),
                        "duration": time.time() - step_start
                    }

            # Step 5 (Optional): Check watch rules and create alerts
            if self.enable_alerting and self.claim_matcher:
                logger.info("Step 5/5: Checking watch rules")
                step_start = time.time()

                try:
                    # Get all active watch rules
                    active_rules = self.indexer_agent.firestore_client.get_all_active_rules()

                    # Create paper object for matching
                    paper_for_matching = {
                        'paper_id': index_result['paper_id'],
                        'title': entities.get('title', ''),
                        'authors': entities.get('authors', []),
                        'key_finding': entities.get('key_finding', '')
                    }

                    # Check each rule
                    alerts_created = []
                    for rule in active_rules:
                        match_result = self._match_paper_against_rule(
                            paper_for_matching,
                            rule
                        )

                        if match_result:
                            # Create alert
                            alert_data = {
                                "user_id": rule.get("user_id", ""),
                                "rule_id": rule.get("rule_id", ""),
                                "paper_id": index_result["paper_id"],
                                "match_score": match_result["match_score"],
                                "match_explanation": match_result["match_explanation"],
                                "paper_title": entities.get("title", ""),
                                "paper_authors": entities.get("authors", []),
                                "status": "pending"
                            }

                            alert_id = self.indexer_agent.firestore_client.create_alert(alert_data)
                            alerts_created.append(alert_id)

                            logger.info(
                                f"Created alert {alert_id} for rule {rule.get('name', 'unnamed')} "
                                f"(score: {match_result['match_score']:.2f})"
                            )

                            # Publish to Pub/Sub to trigger email notification
                            if self.enable_pubsub and self.pubsub_publisher and self.project_id:
                                try:
                                    topic_path = self.pubsub_publisher.topic_path(
                                        self.project_id,
                                        'arxiv.matches'
                                    )

                                    # Prepare email notification data
                                    email_data = {
                                        'user_email': rule.get('user_email', ''),
                                        'user_name': rule.get('user_name', 'Researcher'),
                                        'paper_title': entities.get('title', ''),
                                        'paper_authors': entities.get('authors', []),
                                        'match_reason': match_result.get('match_explanation', f"Matches your watch rule: {rule.get('name', 'unnamed')}"),
                                        'paper_id': index_result['paper_id'],
                                        'arxiv_id': paper_data.get('arxiv_id', ''),
                                        'alert_id': alert_id
                                    }

                                    future = self.pubsub_publisher.publish(
                                        topic_path,
                                        json.dumps(email_data).encode('utf-8')
                                    )
                                    message_id = future.result()

                                    logger.info(
                                        f"Published alert {alert_id} to arxiv.matches "
                                        f"(message_id: {message_id})"
                                    )

                                except Exception as e:
                                    logger.warning(
                                        f"Failed to publish alert {alert_id} to Pub/Sub "
                                        f"(non-blocking): {e}"
                                    )

                    result["steps"]["alerting"] = {
                        "success": True,
                        "rules_checked": len(active_rules),
                        "alerts_created": len(alerts_created),
                        "alert_ids": alerts_created,
                        "duration": time.time() - step_start
                    }

                    logger.info(f"Created {len(alerts_created)} alerts from {len(active_rules)} active rules")

                except Exception as e:
                    logger.warning(f"Alerting failed (non-blocking): {e}")
                    result["steps"]["alerting"] = {
                        "success": False,
                        "error": str(e),
                        "duration": time.time() - step_start
                    }

            # All steps successful
            result["success"] = True
            result["paper_id"] = index_result["paper_id"]
            result["message"] = "Paper ingested successfully"
            result["duration"] = time.time() - start_time

            # Publish to Pub/Sub to trigger graph updater
            if self.enable_pubsub and self.pubsub_publisher and self.project_id:
                try:
                    topic_path = self.pubsub_publisher.topic_path(self.project_id, 'docs.ready')
                    message_data = {
                        'paper_id': result['paper_id'],
                        'title': entities.get('title', ''),
                        'status': 'ingested'
                    }

                    future = self.pubsub_publisher.publish(
                        topic_path,
                        json.dumps(message_data).encode('utf-8')
                    )
                    message_id = future.result()

                    logger.info(f"Published to docs.ready topic (message_id: {message_id})")
                    result["pubsub_message_id"] = message_id

                except Exception as e:
                    logger.warning(f"Failed to publish to Pub/Sub (non-blocking): {e}")

            logger.info(
                f"✅ Successfully ingested paper: {result['paper_id']} "
                f"({result['duration']:.2f}s)"
            )
            return result

        except FileNotFoundError as e:
            logger.error(f"PDF file not found: {pdf_path}")
            result["error"] = f"File not found: {str(e)}"
            result["duration"] = time.time() - start_time
            return result

        except Exception as e:
            logger.error(f"Unexpected error in ingestion pipeline: {str(e)}")
            result["error"] = f"Pipeline error: {str(e)}"
            result["duration"] = time.time() - start_time
            return result

    def ingest_papers_batch(
        self,
        papers: List[Tuple[str, str]]
    ) -> Dict:
        """
        Ingest multiple papers in batch.

        Args:
            papers: List of tuples (pdf_path, arxiv_id)

        Returns:
            Dictionary with:
                - total: int
                - successful: int
                - failed: int
                - success_rate: float
                - avg_duration: float
                - results: list of individual results
        """
        results = []
        successful = 0
        failed = 0
        total_duration = 0

        logger.info(f"Starting batch ingestion of {len(papers)} papers")

        for pdf_path, arxiv_id in papers:
            result = self.ingest_paper(pdf_path, arxiv_id)
            results.append(result)

            if result["success"]:
                successful += 1
            else:
                failed += 1

            total_duration += result.get("duration", 0)

        success_rate = successful / len(papers) if papers else 0
        avg_duration = total_duration / len(papers) if papers else 0

        summary = {
            "total": len(papers),
            "successful": successful,
            "failed": failed,
            "success_rate": success_rate,
            "avg_duration": avg_duration,
            "total_duration": total_duration,
            "results": results
        }

        logger.info(
            f"Batch ingestion complete: {successful}/{len(papers)} successful "
            f"({success_rate:.1%}, avg {avg_duration:.2f}s per paper)"
        )

        return summary

    def _match_paper_against_rule(self, paper: Dict, rule: Dict) -> Optional[Dict]:
        """
        Match a paper against a single watch rule.

        Args:
            paper: Paper data with title, authors, key_finding
            rule: Watch rule to match against

        Returns:
            Match result dict or None if no match:
            {
                'match_score': float,
                'match_explanation': str
            }
        """
        rule_type = rule.get("rule_type", "keyword")

        try:
            if rule_type == "keyword":
                return match_keyword_rule(paper, rule)

            elif rule_type == "claim":
                return match_claim_rule(paper, rule, self.claim_matcher)

            elif rule_type == "relationship":
                if self.relationship_agent:
                    return match_relationship_rule(paper, rule, self.relationship_agent)
                else:
                    logger.warning("Relationship rule requires enable_relationships=True")
                    return None

            elif rule_type == "author":
                return match_author_rule(paper, rule)

            elif rule_type == "template":
                return match_template_rule(paper, rule, self.claim_matcher)

            else:
                logger.warning(f"Unknown rule type: {rule_type}")
                return None

        except Exception as e:
            logger.warning(f"Error matching rule {rule.get('rule_id', 'unknown')}: {e}")
            return None

    def get_pipeline_status(self) -> Dict:
        """
        Get status of the pipeline components.

        Returns:
            Dictionary with component status
        """
        return {
            "entity_agent": {
                "status": "ready",
                "type": "LlmAgent"
            },
            "indexer_agent": {
                "status": "ready",
                "type": "StorageAgent"
            },
            "pipeline": "ready"
        }

"""
Indexer Agent

Stores extracted paper entities in Firestore.
For Phase 1 (Crawl), this is a simple storage agent that doesn't require LLM reasoning.
"""

from typing import Dict
from src.storage.firestore_client import FirestoreClient
import logging

logger = logging.getLogger(__name__)


class IndexerAgent:
    """
    Agent that stores paper entities in Firestore.

    For Phase 1, this is a simple non-LLM agent that performs direct storage.
    In Phase 2, we may add LLM-based validation and enrichment.
    """

    def __init__(self, project_id: str = None):
        """
        Initialize the indexer agent.

        Args:
            project_id: GCP project ID (uses default if None)
        """
        self.firestore_client = FirestoreClient(project_id=project_id)
        logger.info("IndexerAgent initialized")

    def index(self, entities: Dict, pdf_path: str = "", arxiv_id: str = "", metadata: Dict = None) -> Dict:
        """
        Index paper entities to Firestore.

        Args:
            entities: Dictionary with title, authors, key_finding
            pdf_path: Path to the PDF file (optional)
            arxiv_id: arXiv ID if available (optional)
            metadata: Additional metadata (categories, primary_category, published, updated)

        Returns:
            Dictionary with:
                - success: bool
                - paper_id: str (if successful)
                - message: str
        """
        if metadata is None:
            metadata = {}

        try:
            # Validate required fields
            if not entities.get("title"):
                return {
                    "success": False,
                    "error": "Missing required field: title"
                }

            # Prepare paper data
            paper_data = {
                "title": entities.get("title", ""),
                "authors": entities.get("authors", []),
                "key_finding": entities.get("key_finding", ""),
                "pdf_path": pdf_path,
                "arxiv_id": arxiv_id,
            }

            # Add metadata fields if provided
            if metadata.get("categories"):
                paper_data["categories"] = metadata["categories"]
            if metadata.get("primary_category"):
                paper_data["primary_category"] = metadata["primary_category"]
            if metadata.get("published"):
                paper_data["published"] = metadata["published"]
            if metadata.get("updated"):
                paper_data["updated"] = metadata["updated"]

            # Check if paper already exists
            if self.firestore_client.paper_exists(
                paper_data["title"],
                paper_data["authors"]
            ):
                logger.info(f"Paper already exists: {paper_data['title']}")
                # Get the existing paper ID
                paper_id = self.firestore_client.generate_paper_id(
                    paper_data["title"],
                    paper_data["authors"]
                )
                return {
                    "success": True,
                    "paper_id": paper_id,
                    "message": "Paper already indexed",
                    "already_exists": True
                }

            # Store the paper
            paper_id = self.firestore_client.store_paper(paper_data)

            logger.info(f"Successfully indexed paper: {paper_id}")

            return {
                "success": True,
                "paper_id": paper_id,
                "message": "Paper indexed successfully",
                "already_exists": False
            }

        except Exception as e:
            logger.error(f"Error indexing paper: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_paper(self, paper_id: str) -> Dict:
        """
        Retrieve a paper from Firestore.

        Args:
            paper_id: Document ID

        Returns:
            Paper data or error
        """
        try:
            paper = self.firestore_client.get_paper(paper_id)
            if paper:
                return {
                    "success": True,
                    "paper": paper
                }
            else:
                return {
                    "success": False,
                    "error": "Paper not found"
                }
        except Exception as e:
            logger.error(f"Error retrieving paper: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def list_recent_papers(self, limit: int = 10) -> Dict:
        """
        List recently indexed papers.

        Args:
            limit: Maximum number of papers to return

        Returns:
            List of papers or error
        """
        try:
            papers = self.firestore_client.list_papers(limit=limit)
            return {
                "success": True,
                "papers": papers,
                "count": len(papers)
            }
        except Exception as e:
            logger.error(f"Error listing papers: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

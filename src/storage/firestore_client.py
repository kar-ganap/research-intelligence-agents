"""
Firestore Client

Simple wrapper for Firestore operations used by the ingestion pipeline.
"""

from google.cloud import firestore
from typing import Dict, Optional, List
from datetime import datetime
import hashlib


class FirestoreClient:
    """Client for storing and retrieving papers from Firestore"""

    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize Firestore client.

        Args:
            project_id: GCP project ID (uses default if None)
        """
        if project_id:
            self.db = firestore.Client(project=project_id)
        else:
            self.db = firestore.Client()

        self.papers_collection = "papers"

    def generate_paper_id(self, title: str, authors: List[str]) -> str:
        """
        Generate a unique paper ID from title and authors.

        Args:
            title: Paper title
            authors: List of authors

        Returns:
            Unique hash-based paper ID
        """
        # Create deterministic ID from title + first author
        content = f"{title}_{authors[0] if authors else 'unknown'}"
        paper_id = hashlib.sha256(content.encode()).hexdigest()[:16]
        return paper_id

    def store_paper(self, paper_data: Dict) -> str:
        """
        Store a paper in Firestore.

        Args:
            paper_data: Dictionary containing:
                - title: str
                - authors: List[str]
                - key_finding: str
                - pdf_path: str (optional)
                - arxiv_id: str (optional)

        Returns:
            Document ID of the stored paper
        """
        # Generate paper ID
        paper_id = self.generate_paper_id(
            paper_data.get("title", "untitled"),
            paper_data.get("authors", [])
        )

        # Add metadata
        doc_data = {
            "title": paper_data.get("title", ""),
            "authors": paper_data.get("authors", []),
            "key_finding": paper_data.get("key_finding", ""),
            "pdf_path": paper_data.get("pdf_path", ""),
            "arxiv_id": paper_data.get("arxiv_id", ""),
            "ingested_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }

        # Store in Firestore
        doc_ref = self.db.collection(self.papers_collection).document(paper_id)
        doc_ref.set(doc_data)

        return paper_id

    def get_paper(self, paper_id: str) -> Optional[Dict]:
        """
        Retrieve a paper from Firestore.

        Args:
            paper_id: Document ID

        Returns:
            Paper data dictionary or None if not found
        """
        doc_ref = self.db.collection(self.papers_collection).document(paper_id)
        doc = doc_ref.get()

        if doc.exists:
            return doc.to_dict()
        return None

    def list_papers(self, limit: int = 10) -> List[Dict]:
        """
        List recent papers.

        Args:
            limit: Maximum number of papers to return

        Returns:
            List of paper dictionaries
        """
        docs = (
            self.db.collection(self.papers_collection)
            .order_by("ingested_at", direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )

        papers = []
        for doc in docs:
            paper_data = doc.to_dict()
            paper_data["id"] = doc.id
            papers.append(paper_data)

        return papers

    def paper_exists(self, title: str, authors: List[str]) -> bool:
        """
        Check if a paper already exists in Firestore.

        Args:
            title: Paper title
            authors: List of authors

        Returns:
            True if paper exists, False otherwise
        """
        paper_id = self.generate_paper_id(title, authors)
        return self.get_paper(paper_id) is not None

    def update_paper(self, paper_id: str, updates: Dict) -> bool:
        """
        Update a paper document.

        Args:
            paper_id: Document ID
            updates: Dictionary of fields to update

        Returns:
            True if successful, False if paper not found
        """
        doc_ref = self.db.collection(self.papers_collection).document(paper_id)

        if not doc_ref.get().exists:
            return False

        updates["updated_at"] = firestore.SERVER_TIMESTAMP
        doc_ref.update(updates)
        return True

    def delete_paper(self, paper_id: str) -> bool:
        """
        Delete a paper document.

        Args:
            paper_id: Document ID

        Returns:
            True if successful, False if paper not found
        """
        doc_ref = self.db.collection(self.papers_collection).document(paper_id)

        if not doc_ref.get().exists:
            return False

        doc_ref.delete()
        return True

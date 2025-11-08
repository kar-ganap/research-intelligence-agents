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
        self.relationships_collection = "relationships"
        self.watch_rules_collection = "watch_rules"
        self.alerts_collection = "alerts"

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
                - categories: List[str] (optional)
                - primary_category: str (optional)
                - published: str (optional)
                - updated: str (optional)

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

        # Add arXiv metadata if provided
        if "categories" in paper_data:
            doc_data["categories"] = paper_data["categories"]
        if "primary_category" in paper_data:
            doc_data["primary_category"] = paper_data["primary_category"]
        if "published" in paper_data:
            doc_data["published"] = paper_data["published"]
        if "updated" in paper_data and paper_data["updated"]:
            doc_data["updated"] = paper_data["updated"]

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

    # ========================================================================
    # Relationship Operations
    # ========================================================================

    def store_relationship(self, relationship_data: Dict) -> str:
        """
        Store a relationship between papers in Firestore.

        Args:
            relationship_data: Dictionary containing:
                - source_paper_id: str
                - target_paper_id: str
                - relationship_type: str (supports/contradicts/extends)
                - confidence: float (0.0-1.0)
                - evidence: str

        Returns:
            Document ID of the stored relationship
        """
        # Generate unique relationship ID
        relationship_id = hashlib.sha256(
            f"{relationship_data['source_paper_id']}_"
            f"{relationship_data['target_paper_id']}_"
            f"{relationship_data['relationship_type']}".encode()
        ).hexdigest()[:16]

        # Add metadata
        doc_data = {
            "source_paper_id": relationship_data.get("source_paper_id", ""),
            "target_paper_id": relationship_data.get("target_paper_id", ""),
            "relationship_type": relationship_data.get("relationship_type", "none"),
            "confidence": relationship_data.get("confidence", 0.0),
            "evidence": relationship_data.get("evidence", ""),
            "detected_by": relationship_data.get("detected_by", "RelationshipAgent"),
            "detected_at": firestore.SERVER_TIMESTAMP,
        }

        # Store in Firestore
        doc_ref = self.db.collection(self.relationships_collection).document(relationship_id)
        doc_ref.set(doc_data)

        return relationship_id

    def get_relationship(self, relationship_id: str) -> Optional[Dict]:
        """
        Retrieve a relationship from Firestore.

        Args:
            relationship_id: Document ID

        Returns:
            Relationship data dictionary or None if not found
        """
        doc_ref = self.db.collection(self.relationships_collection).document(relationship_id)
        doc = doc_ref.get()

        if doc.exists:
            return doc.to_dict()
        return None

    def get_relationships_for_paper(self, paper_id: str) -> List[Dict]:
        """
        Get all relationships where a paper is the source.

        Args:
            paper_id: Paper ID to find relationships for

        Returns:
            List of relationship dictionaries
        """
        docs = (
            self.db.collection(self.relationships_collection)
            .where("source_paper_id", "==", paper_id)
            .stream()
        )

        relationships = []
        for doc in docs:
            rel_data = doc.to_dict()
            rel_data["relationship_id"] = doc.id
            relationships.append(rel_data)

        return relationships

    def get_all_relationships(self, limit: int = 100) -> List[Dict]:
        """
        Get all relationships in the graph.

        Args:
            limit: Maximum number of relationships to return

        Returns:
            List of relationship dictionaries
        """
        # Note: Don't use order_by as it filters out documents missing the field
        docs = (
            self.db.collection(self.relationships_collection)
            .limit(limit)
            .stream()
        )

        relationships = []
        for doc in docs:
            rel_data = doc.to_dict()
            rel_data["relationship_id"] = doc.id
            relationships.append(rel_data)

        return relationships

    def count_relationships(self) -> int:
        """
        Count total number of relationships.

        Returns:
            Number of relationships in Firestore
        """
        docs = self.db.collection(self.relationships_collection).stream()
        return sum(1 for _ in docs)

    def get_all_papers(self) -> List[Dict]:
        """
        Get all papers in the corpus (for relationship detection).

        Returns:
            List of all paper dictionaries with paper_id
        """
        docs = self.db.collection(self.papers_collection).stream()

        papers = []
        for doc in docs:
            paper_data = doc.to_dict()
            paper_data["paper_id"] = doc.id
            papers.append(paper_data)

        return papers

    # ========================================================================
    # Watch Rules Operations
    # ========================================================================

    def create_watch_rule(self, rule_data: Dict) -> str:
        """
        Create a watch rule for proactive alerting.

        Args:
            rule_data: Dictionary containing:
                - user_id: str
                - name: str
                - rule_type: str (keyword/claim/relationship/author/template)
                - keywords: List[str] (optional, for keyword type)
                - claim_description: str (optional, for claim type)
                - target_paper_id: str (optional, for relationship type)
                - relationship_type: str (optional, for relationship type)
                - authors: List[str] (optional, for author type)
                - template_name: str (optional, for template type)
                - template_params: Dict (optional, for template type)
                - min_relevance_score: float (default 0.7)
                - active: bool (default True)

        Returns:
            Rule ID
        """
        import uuid
        rule_id = f"rule_{uuid.uuid4().hex[:12]}"

        doc_data = {
            "user_id": rule_data.get("user_id", ""),
            "name": rule_data.get("name", ""),
            "rule_type": rule_data.get("rule_type", "keyword"),
            "keywords": rule_data.get("keywords", []),
            "claim_description": rule_data.get("claim_description", ""),
            "target_paper_id": rule_data.get("target_paper_id", ""),
            "relationship_type": rule_data.get("relationship_type", ""),
            "authors": rule_data.get("authors", []),
            "template_name": rule_data.get("template_name", ""),
            "template_params": rule_data.get("template_params", {}),
            "min_relevance_score": rule_data.get("min_relevance_score", 0.7),
            "active": rule_data.get("active", True),
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }

        doc_ref = self.db.collection(self.watch_rules_collection).document(rule_id)
        doc_ref.set(doc_data)

        return rule_id

    def get_watch_rule(self, rule_id: str) -> Optional[Dict]:
        """Get a watch rule by ID."""
        doc_ref = self.db.collection(self.watch_rules_collection).document(rule_id)
        doc = doc_ref.get()

        if doc.exists:
            rule = doc.to_dict()
            rule["rule_id"] = doc.id
            return rule
        return None

    def get_watch_rules(self, user_id: str) -> List[Dict]:
        """Get all watch rules for a user."""
        docs = (
            self.db.collection(self.watch_rules_collection)
            .where("user_id", "==", user_id)
            .stream()
        )

        rules = []
        for doc in docs:
            rule = doc.to_dict()
            rule["rule_id"] = doc.id
            rules.append(rule)

        return rules

    def get_all_active_rules(self) -> List[Dict]:
        """Get all active watch rules."""
        docs = (
            self.db.collection(self.watch_rules_collection)
            .where("active", "==", True)
            .stream()
        )

        rules = []
        for doc in docs:
            rule = doc.to_dict()
            rule["rule_id"] = doc.id
            rules.append(rule)

        return rules

    def update_watch_rule(self, rule_id: str, updates: Dict) -> bool:
        """Update a watch rule."""
        doc_ref = self.db.collection(self.watch_rules_collection).document(rule_id)

        if not doc_ref.get().exists:
            return False

        updates["updated_at"] = firestore.SERVER_TIMESTAMP
        doc_ref.update(updates)
        return True

    def delete_watch_rule(self, rule_id: str) -> bool:
        """Delete a watch rule."""
        doc_ref = self.db.collection(self.watch_rules_collection).document(rule_id)

        if not doc_ref.get().exists:
            return False

        doc_ref.delete()
        return True

    # ========================================================================
    # Alerts Operations
    # ========================================================================

    def create_alert(self, alert_data: Dict) -> str:
        """
        Create an alert when a paper matches a watch rule.

        Args:
            alert_data: Dictionary containing:
                - user_id: str
                - rule_id: str
                - paper_id: str
                - match_score: float
                - match_explanation: str (optional)
                - paper_title: str (denormalized)
                - paper_authors: List[str] (denormalized)
                - status: str (default 'pending')

        Returns:
            Alert ID
        """
        import uuid
        alert_id = f"alert_{uuid.uuid4().hex[:12]}"

        doc_data = {
            "user_id": alert_data.get("user_id", ""),
            "rule_id": alert_data.get("rule_id", ""),
            "paper_id": alert_data.get("paper_id", ""),
            "match_score": alert_data.get("match_score", 0.0),
            "match_explanation": alert_data.get("match_explanation", ""),
            "paper_title": alert_data.get("paper_title", ""),
            "paper_authors": alert_data.get("paper_authors", []),
            "status": alert_data.get("status", "pending"),
            "created_at": firestore.SERVER_TIMESTAMP,
            "sent_at": None,
            "read_at": None,
        }

        doc_ref = self.db.collection(self.alerts_collection).document(alert_id)
        doc_ref.set(doc_data)

        return alert_id

    def get_alerts(self, user_id: str, status: Optional[str] = None) -> List[Dict]:
        """Get alerts for a user, optionally filtered by status."""
        query = self.db.collection(self.alerts_collection).where("user_id", "==", user_id)

        if status:
            query = query.where("status", "==", status)

        docs = query.order_by("created_at", direction=firestore.Query.DESCENDING).stream()

        alerts = []
        for doc in docs:
            alert = doc.to_dict()
            alert["alert_id"] = doc.id
            alerts.append(alert)

        return alerts

    def mark_alert_sent(self, alert_id: str) -> bool:
        """Mark an alert as sent."""
        doc_ref = self.db.collection(self.alerts_collection).document(alert_id)

        if not doc_ref.get().exists:
            return False

        doc_ref.update({
            "status": "sent",
            "sent_at": firestore.SERVER_TIMESTAMP
        })
        return True

    def mark_alert_read(self, alert_id: str) -> bool:
        """Mark an alert as read by user."""
        doc_ref = self.db.collection(self.alerts_collection).document(alert_id)

        if not doc_ref.get().exists:
            return False

        doc_ref.update({
            "status": "read",
            "read_at": firestore.SERVER_TIMESTAMP
        })
        return True

    def count_alerts(self, user_id: str, status: Optional[str] = None) -> int:
        """Count alerts for a user."""
        query = self.db.collection(self.alerts_collection).where("user_id", "==", user_id)

        if status:
            query = query.where("status", "==", status)

        docs = query.stream()
        return sum(1 for _ in docs)

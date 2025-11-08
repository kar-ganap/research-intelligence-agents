"""
Graph Query Tool

Provides templated queries for navigating the knowledge graph.
Enables questions like:
- "Which papers cite X?"
- "Which papers contradict Y?"
- "What are the most cited papers?"
- "Show me papers by author Z"
"""

from typing import List, Dict, Optional
from src.storage.firestore_client import FirestoreClient
import logging

logger = logging.getLogger(__name__)


class GraphQueryTool:
    """Tool for executing graph-based queries on the research corpus."""

    def __init__(self, firestore_client: FirestoreClient = None):
        """Initialize with Firestore client."""
        self.firestore_client = firestore_client or FirestoreClient()

    def find_papers_citing(self, paper_id: str) -> Dict:
        """
        Find all papers that cite/reference a given paper.

        Args:
            paper_id: ID of the target paper

        Returns:
            Dict with citing papers and relationship details
        """
        logger.info(f"Finding papers that cite: {paper_id}")

        # Get target paper info
        target_paper = self.firestore_client.get_paper(paper_id)
        if not target_paper:
            return {
                'success': False,
                'error': f'Paper {paper_id} not found',
                'citing_papers': []
            }

        # Query relationships where target is referenced
        relationships = list(self.firestore_client.db.collection('relationships')
                            .where('target_paper_id', '==', paper_id)
                            .stream())

        citing_papers = []
        for rel in relationships:
            rel_data = rel.to_dict()
            source_paper_id = rel_data.get('source_paper_id')

            # Get source paper details
            source_paper = self.firestore_client.get_paper(source_paper_id)
            if source_paper:
                citing_papers.append({
                    'paper_id': source_paper_id,
                    'title': source_paper.get('title', 'Unknown'),
                    'authors': source_paper.get('authors', []),
                    'relationship_type': rel_data.get('relationship_type', 'unknown'),
                    'description': rel_data.get('description', ''),
                    'confidence': rel_data.get('confidence', 0.0)
                })

        logger.info(f"Found {len(citing_papers)} papers citing {paper_id}")

        return {
            'success': True,
            'target_paper': {
                'paper_id': paper_id,
                'title': target_paper.get('title', 'Unknown')
            },
            'citing_papers': citing_papers,
            'count': len(citing_papers)
        }

    def find_contradictions(self, paper_id: str = None, topic: str = None) -> Dict:
        """
        Find contradictory papers.

        Args:
            paper_id: Optional - find papers contradicting this specific paper
            topic: Optional - find contradictory papers about a topic

        Returns:
            Dict with contradictory paper pairs
        """
        logger.info(f"Finding contradictions - paper: {paper_id}, topic: {topic}")

        contradictions = []

        if paper_id:
            # Find papers that contradict the specified paper
            relationships = list(self.firestore_client.db.collection('relationships')
                                .where('relationship_type', '==', 'contradicts')
                                .stream())

            for rel in relationships:
                rel_data = rel.to_dict()
                source_id = rel_data.get('source_paper_id')
                target_id = rel_data.get('target_paper_id')

                # Check if either source or target matches our paper
                if source_id == paper_id or target_id == paper_id:
                    other_id = target_id if source_id == paper_id else source_id
                    other_paper = self.firestore_client.get_paper(other_id)

                    if other_paper:
                        contradictions.append({
                            'paper_id': other_id,
                            'title': other_paper.get('title', 'Unknown'),
                            'authors': other_paper.get('authors', []),
                            'description': rel_data.get('description', ''),
                            'confidence': rel_data.get('confidence', 0.0)
                        })

        elif topic:
            # Find all contradictory relationships, filter by topic
            relationships = list(self.firestore_client.db.collection('relationships')
                                .where('relationship_type', '==', 'contradicts')
                                .stream())

            for rel in relationships:
                rel_data = rel.to_dict()
                source_id = rel_data.get('source_paper_id')
                target_id = rel_data.get('target_paper_id')

                # Get both papers
                source_paper = self.firestore_client.get_paper(source_id)
                target_paper = self.firestore_client.get_paper(target_id)

                # Check if topic is mentioned in either paper
                if source_paper and target_paper:
                    topic_lower = topic.lower()
                    source_text = f"{source_paper.get('title', '')} {source_paper.get('key_finding', '')}".lower()
                    target_text = f"{target_paper.get('title', '')} {target_paper.get('key_finding', '')}".lower()

                    if topic_lower in source_text or topic_lower in target_text:
                        contradictions.append({
                            'paper_1': {
                                'paper_id': source_id,
                                'title': source_paper.get('title', 'Unknown'),
                                'authors': source_paper.get('authors', [])
                            },
                            'paper_2': {
                                'paper_id': target_id,
                                'title': target_paper.get('title', 'Unknown'),
                                'authors': target_paper.get('authors', [])
                            },
                            'description': rel_data.get('description', ''),
                            'confidence': rel_data.get('confidence', 0.0)
                        })

        else:
            # No paper or topic specified - return ALL contradictions
            relationships = list(self.firestore_client.db.collection('relationships')
                                .where('relationship_type', '==', 'contradicts')
                                .stream())

            for rel in relationships:
                rel_data = rel.to_dict()
                source_id = rel_data.get('source_paper_id')
                target_id = rel_data.get('target_paper_id')

                # Get both papers
                source_paper = self.firestore_client.get_paper(source_id)
                target_paper = self.firestore_client.get_paper(target_id)

                if source_paper and target_paper:
                    contradictions.append({
                        'paper_1': {
                            'paper_id': source_id,
                            'title': source_paper.get('title', 'Unknown'),
                            'authors': source_paper.get('authors', [])
                        },
                        'paper_2': {
                            'paper_id': target_id,
                            'title': target_paper.get('title', 'Unknown'),
                            'authors': target_paper.get('authors', [])
                        },
                        'description': rel_data.get('description', ''),
                        'confidence': rel_data.get('confidence', 0.0)
                    })

        logger.info(f"Found {len(contradictions)} contradictions")

        return {
            'success': True,
            'contradictions': contradictions,
            'count': len(contradictions),
            'query': {'paper_id': paper_id, 'topic': topic}
        }

    def find_papers_by_author(self, author_name: str) -> Dict:
        """
        Find all papers by a specific author.

        Args:
            author_name: Name to search for (partial match)

        Returns:
            Dict with matching papers
        """
        logger.info(f"Finding papers by author: {author_name}")

        all_papers = self.firestore_client.get_all_papers()
        matching_papers = []

        author_lower = author_name.lower()

        for paper in all_papers:
            authors = paper.get('authors', [])
            # Check if any author contains the search name
            if any(author_lower in author.lower() for author in authors):
                matching_papers.append({
                    'paper_id': paper.get('paper_id'),
                    'title': paper.get('title', 'Unknown'),
                    'authors': authors,
                    'key_finding': paper.get('key_finding', '')
                })

        logger.info(f"Found {len(matching_papers)} papers by {author_name}")

        return {
            'success': True,
            'author': author_name,
            'papers': matching_papers,
            'count': len(matching_papers)
        }

    def find_most_cited_papers(self, limit: int = 10) -> Dict:
        """
        Find the most cited/referenced papers.

        Args:
            limit: Max number of papers to return

        Returns:
            Dict with papers ranked by citation count
        """
        logger.info(f"Finding top {limit} most cited papers")

        # Get all relationships
        relationships = list(self.firestore_client.db.collection('relationships').stream())

        # Count citations per paper
        citation_counts = {}
        for rel in relationships:
            rel_data = rel.to_dict()
            target_id = rel_data.get('target_paper_id')

            if target_id:
                citation_counts[target_id] = citation_counts.get(target_id, 0) + 1

        # Sort by citation count
        sorted_papers = sorted(citation_counts.items(), key=lambda x: x[1], reverse=True)

        # Get paper details for top papers
        top_papers = []
        for paper_id, count in sorted_papers[:limit]:
            paper = self.firestore_client.get_paper(paper_id)
            if paper:
                top_papers.append({
                    'paper_id': paper_id,
                    'title': paper.get('title', 'Unknown'),
                    'authors': paper.get('authors', []),
                    'citation_count': count,
                    'key_finding': paper.get('key_finding', '')
                })

        logger.info(f"Top cited paper: {top_papers[0]['title'] if top_papers else 'None'} ({top_papers[0]['citation_count'] if top_papers else 0} citations)")

        return {
            'success': True,
            'papers': top_papers,
            'count': len(top_papers)
        }

    def find_papers_extending(self, paper_id: str) -> Dict:
        """
        Find papers that extend/build upon a given paper.

        Args:
            paper_id: ID of the base paper

        Returns:
            Dict with papers that extend it
        """
        logger.info(f"Finding papers that extend: {paper_id}")

        # Get target paper info
        target_paper = self.firestore_client.get_paper(paper_id)
        if not target_paper:
            return {
                'success': False,
                'error': f'Paper {paper_id} not found',
                'extending_papers': []
            }

        # Query relationships where this paper is extended
        relationships = list(self.firestore_client.db.collection('relationships')
                            .where('target_paper_id', '==', paper_id)
                            .where('relationship_type', '==', 'extends')
                            .stream())

        extending_papers = []
        for rel in relationships:
            rel_data = rel.to_dict()
            source_paper_id = rel_data.get('source_paper_id')

            # Get source paper details
            source_paper = self.firestore_client.get_paper(source_paper_id)
            if source_paper:
                extending_papers.append({
                    'paper_id': source_paper_id,
                    'title': source_paper.get('title', 'Unknown'),
                    'authors': source_paper.get('authors', []),
                    'description': rel_data.get('description', ''),
                    'confidence': rel_data.get('confidence', 0.0)
                })

        logger.info(f"Found {len(extending_papers)} papers extending {paper_id}")

        return {
            'success': True,
            'target_paper': {
                'paper_id': paper_id,
                'title': target_paper.get('title', 'Unknown')
            },
            'extending_papers': extending_papers,
            'count': len(extending_papers)
        }


def detect_graph_query_type(question: str) -> Optional[str]:
    """
    Detect if question is a graph query and what type.

    Returns:
        Query type string or None if not a graph query
    """
    question_lower = question.lower()

    # Citation queries
    if any(keyword in question_lower for keyword in ['cite', 'build on', 'reference', 'based on']):
        return 'citations'

    # Contradiction queries
    if any(keyword in question_lower for keyword in ['contradict', 'disagree', 'conflict']):
        return 'contradictions'

    # Extension queries
    if any(keyword in question_lower for keyword in ['extend', 'improve', 'advance']):
        return 'extensions'

    # Author queries
    if any(keyword in question_lower for keyword in ['by author', 'papers by', 'authored by', 'written by']):
        return 'author'

    # Popularity queries
    if any(keyword in question_lower for keyword in ['most cited', 'most influential', 'most popular', 'most referenced']):
        return 'popularity'

    return None

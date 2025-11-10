"""
Retrieval Tool

Keyword-based search for finding relevant papers in Firestore.
Phase 1 approach: Simple keyword matching with TF-IDF-style scoring.
"""

from typing import List, Dict, Set
import logging
import re
from src.storage.firestore_client import FirestoreClient

logger = logging.getLogger(__name__)

# Common English stopwords to filter out
STOPWORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
    'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
    'to', 'was', 'will', 'with', 'what', 'who', 'where', 'when', 'how'
}


def extract_keywords(text: str) -> Set[str]:
    """
    Extract keywords from text.

    Args:
        text: Input text (query or document)

    Returns:
        Set of lowercase keywords (excluding stopwords)
    """
    # Convert to lowercase
    text = text.lower()

    # Extract words (alphanumeric only)
    words = re.findall(r'\b[a-z0-9]+\b', text)

    # Filter out stopwords and short words
    keywords = {w for w in words if w not in STOPWORDS and len(w) > 2}

    return keywords


def calculate_relevance_score(keywords: Set[str], paper: Dict) -> float:
    """
    Calculate relevance score between keywords and paper.

    Simple scoring:
    - Title match: 2 points per keyword
    - Key finding match: 1 point per keyword
    - Author match: 1.5 points per keyword

    Args:
        keywords: Set of query keywords
        paper: Paper dictionary with title, authors, key_finding

    Returns:
        Relevance score (higher = more relevant)
    """
    if not keywords:
        return 0.0

    score = 0.0

    # Extract paper text fields
    title = paper.get('title', '').lower()
    key_finding = paper.get('key_finding', '').lower()
    authors = ' '.join(paper.get('authors', [])).lower()

    # Score keyword matches
    for keyword in keywords:
        # Title matches are most important
        if keyword in title:
            score += 2.0

        # Key finding matches
        if keyword in key_finding:
            score += 1.0

        # Author name matches
        if keyword in authors:
            score += 1.5

    # Normalize by number of keywords to prevent bias toward many-keyword queries
    normalized_score = score / len(keywords) if keywords else 0.0

    # Cap at 1.0 to ensure relevance scores are in 0-1 range (for percentage display)
    return min(normalized_score, 1.0)


def keyword_search(
    query: str,
    firestore_client: FirestoreClient = None,
    limit: int = 5
) -> List[Dict]:
    """
    Search for papers using keyword matching.

    Phase 1 approach: Simple keyword overlap scoring.
    Future: Can be upgraded to semantic search with embeddings.

    Args:
        query: User's question or search query
        firestore_client: Firestore client (creates new if None)
        limit: Maximum number of papers to return

    Returns:
        List of papers sorted by relevance score, with relevance_score field added
    """
    logger.info(f"Searching for: '{query}' (limit={limit})")

    # Create Firestore client if not provided
    if firestore_client is None:
        firestore_client = FirestoreClient()

    # Extract keywords from query
    keywords = extract_keywords(query)
    logger.info(f"Extracted keywords: {keywords}")

    if not keywords:
        logger.warning("No keywords extracted from query")
        return []

    # Get all papers from Firestore
    # TODO: In Phase 2, add Firestore query filtering for efficiency
    all_papers = firestore_client.list_papers(limit=100)
    logger.info(f"Retrieved {len(all_papers)} papers from Firestore")

    if not all_papers:
        logger.warning("No papers found in Firestore")
        return []

    # Score each paper
    scored_papers = []
    for paper in all_papers:
        score = calculate_relevance_score(keywords, paper)

        if score > 0:  # Only include papers with non-zero relevance
            paper['relevance_score'] = score
            scored_papers.append(paper)

    # Sort by relevance score (highest first)
    scored_papers.sort(key=lambda p: p['relevance_score'], reverse=True)

    # Return top N papers
    top_papers = scored_papers[:limit]

    logger.info(
        f"Found {len(scored_papers)} relevant papers, returning top {len(top_papers)}"
    )

    for i, paper in enumerate(top_papers, 1):
        logger.debug(
            f"  {i}. {paper.get('title', 'N/A')[:50]}... "
            f"(score: {paper['relevance_score']:.2f})"
        )

    return top_papers


def search_by_author(
    author_name: str,
    firestore_client: FirestoreClient = None,
    limit: int = 5
) -> List[Dict]:
    """
    Search for papers by author name.

    Args:
        author_name: Author name to search for
        firestore_client: Firestore client (creates new if None)
        limit: Maximum number of papers to return

    Returns:
        List of papers by the author
    """
    logger.info(f"Searching for papers by author: '{author_name}'")

    if firestore_client is None:
        firestore_client = FirestoreClient()

    # Get all papers
    all_papers = firestore_client.list_papers(limit=100)

    # Filter by author (case-insensitive partial match)
    author_lower = author_name.lower()
    matching_papers = []

    for paper in all_papers:
        authors = paper.get('authors', [])
        for author in authors:
            if author_lower in author.lower():
                matching_papers.append(paper)
                break  # Don't add same paper multiple times

    logger.info(f"Found {len(matching_papers)} papers by {author_name}")

    return matching_papers[:limit]

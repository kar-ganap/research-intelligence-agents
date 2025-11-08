"""
Embeddings Utility

Provides functions for generating and using text embeddings for semantic similarity.
Uses Google's text-embedding-004 model for high-quality embeddings.
"""

import logging
import numpy as np
from typing import List, Dict, Tuple, Optional
from google import genai

logger = logging.getLogger(__name__)


def generate_embedding(text: str, model: str = 'text-embedding-004') -> List[float]:
    """
    Generate embedding for text using Google's embedding model.

    Args:
        text: Text to embed
        model: Embedding model to use (default: text-embedding-004)

    Returns:
        List of floats representing the embedding vector
    """
    try:
        client = genai.Client()
        result = client.models.embed_content(
            model=model,
            contents=[text]
        )
        # Return the first (and only) embedding from the list
        return result.embeddings[0].values
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        raise


def generate_paper_embedding(paper: Dict) -> List[float]:
    """
    Generate embedding for a research paper.

    Combines title, abstract, and key finding for richer representation.

    Args:
        paper: Paper dict with title, abstract, key_finding

    Returns:
        Embedding vector
    """
    # Combine relevant fields
    parts = []

    if paper.get('title'):
        parts.append(f"Title: {paper['title']}")

    if paper.get('abstract'):
        parts.append(f"Abstract: {paper['abstract']}")
    elif paper.get('key_finding'):
        # Fallback to key_finding if no abstract
        parts.append(f"Key Finding: {paper['key_finding']}")

    text = "\n\n".join(parts)

    logger.debug(f"Generating embedding for paper: {paper.get('title', 'Unknown')[:60]}...")
    return generate_embedding(text)


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Similarity score between 0 and 1
    """
    vec1_np = np.array(vec1)
    vec2_np = np.array(vec2)

    dot_product = np.dot(vec1_np, vec2_np)
    norm1 = np.linalg.norm(vec1_np)
    norm2 = np.linalg.norm(vec2_np)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(dot_product / (norm1 * norm2))


def find_similar_papers(
    paper: Dict,
    all_papers: List[Dict],
    embeddings_cache: Dict[str, List[float]],
    top_k: int = 20,
    min_similarity: float = 0.6
) -> List[Tuple[Dict, float]]:
    """
    Find papers similar to given paper using cosine similarity.

    Args:
        paper: Paper to find similar papers for
        all_papers: List of all papers to compare against
        embeddings_cache: Dict mapping paper_id -> embedding vector
        top_k: Maximum number of similar papers to return
        min_similarity: Minimum similarity threshold (0-1)

    Returns:
        List of (paper, similarity_score) tuples, sorted by similarity descending
    """
    paper_id = paper.get('paper_id')

    if paper_id not in embeddings_cache:
        raise ValueError(f"No embedding found for paper {paper_id}")

    paper_embedding = embeddings_cache[paper_id]
    similarities = []

    for other_paper in all_papers:
        other_id = other_paper.get('paper_id')

        # Skip self
        if other_id == paper_id:
            continue

        # Skip if no embedding
        if other_id not in embeddings_cache:
            logger.warning(f"No embedding found for paper {other_id}")
            continue

        other_embedding = embeddings_cache[other_id]

        # Calculate similarity
        similarity = cosine_similarity(paper_embedding, other_embedding)

        # Only include if above threshold
        if similarity >= min_similarity:
            similarities.append((other_paper, similarity))

    # Sort by similarity descending and return top-k
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_k]


def generate_embeddings_for_papers(papers: List[Dict]) -> Dict[str, List[float]]:
    """
    Generate embeddings for a list of papers.

    Args:
        papers: List of paper dicts

    Returns:
        Dict mapping paper_id -> embedding vector
    """
    logger.info(f"Generating embeddings for {len(papers)} papers...")

    embeddings = {}

    for i, paper in enumerate(papers):
        paper_id = paper.get('paper_id')

        if not paper_id:
            logger.warning(f"Paper missing paper_id, skipping")
            continue

        try:
            embedding = generate_paper_embedding(paper)
            embeddings[paper_id] = embedding

            if (i + 1) % 10 == 0:
                logger.info(f"Generated {i + 1}/{len(papers)} embeddings...")

        except Exception as e:
            logger.error(f"Failed to generate embedding for paper {paper_id}: {e}")
            continue

    logger.info(f"Successfully generated {len(embeddings)} embeddings")
    return embeddings

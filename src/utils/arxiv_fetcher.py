"""
arXiv Metadata Fetcher

Utility to extract arXiv IDs from filenames and fetch metadata from arXiv API.
"""

import re
import logging
from typing import Optional, Dict
import arxiv

logger = logging.getLogger(__name__)


def extract_arxiv_id(filename: str) -> Optional[str]:
    """
    Extract arXiv ID from filename.

    Supports formats:
    - 2411.04997.pdf
    - 2411.04997v4.pdf
    - 2411.04997v1.pdf

    Args:
        filename: PDF filename

    Returns:
        arXiv ID (e.g., "2411.04997") or None if not found
    """
    # Remove any path components
    basename = filename.split('/')[-1]

    # Match arXiv ID pattern: YYMM.NNNNN or YYMM.NNNN (with optional version)
    match = re.match(r'(\d{4}\.\d{4,5})(v\d+)?\.pdf$', basename, re.IGNORECASE)

    if match:
        return match.group(1)

    logger.warning(f"Could not extract arXiv ID from filename: {filename}")
    return None


def fetch_arxiv_metadata(arxiv_id: str) -> Dict:
    """
    Fetch metadata from arXiv API.

    Args:
        arxiv_id: arXiv ID (e.g., "2411.04997")

    Returns:
        Dictionary with paper metadata:
        {
            'arxiv_id': str,
            'title': str,
            'authors': list[str],
            'abstract': str,
            'categories': list[str],
            'primary_category': str,
            'published': str (ISO format),
            'updated': str (ISO format),
            'pdf_url': str
        }

    Raises:
        StopIteration: If paper not found
        Exception: For other arXiv API errors
    """
    try:
        logger.info(f"Fetching metadata for arXiv ID: {arxiv_id}")

        # Query arXiv API
        search = arxiv.Search(id_list=[arxiv_id])
        paper = next(search.results())

        metadata = {
            'arxiv_id': arxiv_id,
            'title': paper.title,
            'authors': [author.name for author in paper.authors],
            'abstract': paper.summary,
            'categories': paper.categories,
            'primary_category': paper.primary_category,
            'published': paper.published.isoformat(),
            'updated': paper.updated.isoformat(),
            'pdf_url': paper.pdf_url
        }

        logger.info(f"Successfully fetched metadata for: {paper.title[:50]}...")
        return metadata

    except StopIteration:
        logger.error(f"Paper not found on arXiv: {arxiv_id}")
        raise ValueError(f"Paper not found on arXiv: {arxiv_id}")

    except Exception as e:
        logger.error(f"Error fetching arXiv metadata for {arxiv_id}: {str(e)}")
        raise

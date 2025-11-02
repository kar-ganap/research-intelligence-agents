"""
PDF Reader Tool

Extracts text and metadata from PDF files using PyMuPDF.
Used by the ingestion pipeline to process research papers.
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, List, Optional


def read_pdf(file_path: str) -> Dict[str, any]:
    """
    Extract text and metadata from a PDF file.

    Args:
        file_path: Path to the PDF file

    Returns:
        Dictionary containing:
        - text: Full text content of the PDF
        - page_count: Number of pages
        - pages: List of text per page
        - metadata: PDF metadata (title, author, etc.)

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        Exception: If PDF cannot be read
    """
    pdf_path = Path(file_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    try:
        # Open the PDF
        doc = fitz.open(str(pdf_path))

        # Extract text from all pages
        pages = []
        full_text = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            pages.append({
                "page_number": page_num + 1,
                "text": text
            })
            full_text.append(text)

        # Get PDF metadata
        metadata = doc.metadata

        # Close the document
        doc.close()

        return {
            "text": "\n\n".join(full_text),
            "page_count": len(pages),
            "pages": pages,
            "metadata": {
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "keywords": metadata.get("keywords", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", ""),
            },
            "file_path": str(pdf_path),
            "file_name": pdf_path.name,
        }

    except Exception as e:
        raise Exception(f"Error reading PDF {file_path}: {str(e)}")


def read_pdf_pages(file_path: str, start_page: int = 1, end_page: Optional[int] = None) -> Dict[str, any]:
    """
    Extract text from specific pages of a PDF.

    Args:
        file_path: Path to the PDF file
        start_page: Starting page number (1-indexed)
        end_page: Ending page number (inclusive), None for last page

    Returns:
        Dictionary with text from specified pages
    """
    pdf_path = Path(file_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    try:
        doc = fitz.open(str(pdf_path))
        total_pages = len(doc)

        # Adjust page numbers (convert to 0-indexed)
        start_idx = max(0, start_page - 1)
        end_idx = min(total_pages, end_page if end_page else total_pages)

        # Extract text from specified pages
        pages = []
        full_text = []

        for page_num in range(start_idx, end_idx):
            page = doc[page_num]
            text = page.get_text()
            pages.append({
                "page_number": page_num + 1,
                "text": text
            })
            full_text.append(text)

        doc.close()

        return {
            "text": "\n\n".join(full_text),
            "page_count": len(pages),
            "pages": pages,
            "start_page": start_page,
            "end_page": end_idx,
            "total_pages": total_pages,
        }

    except Exception as e:
        raise Exception(f"Error reading PDF pages {file_path}: {str(e)}")


def extract_first_page(file_path: str) -> str:
    """
    Quick extraction of just the first page (useful for title/authors).

    Args:
        file_path: Path to the PDF file

    Returns:
        Text content of the first page
    """
    result = read_pdf_pages(file_path, start_page=1, end_page=1)
    return result["pages"][0]["text"]


def get_pdf_info(file_path: str) -> Dict[str, any]:
    """
    Get basic information about a PDF without extracting all text.

    Args:
        file_path: Path to the PDF file

    Returns:
        Dictionary with basic PDF info (page count, metadata)
    """
    pdf_path = Path(file_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    try:
        doc = fitz.open(str(pdf_path))
        metadata = doc.metadata
        page_count = len(doc)
        doc.close()

        return {
            "page_count": page_count,
            "metadata": {
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "keywords": metadata.get("keywords", ""),
            },
            "file_path": str(pdf_path),
            "file_name": pdf_path.name,
        }

    except Exception as e:
        raise Exception(f"Error getting PDF info {file_path}: {str(e)}")

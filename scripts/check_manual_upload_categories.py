#!/usr/bin/env python3
"""
Check category data for manually uploaded papers
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.firestore_client import FirestoreClient

def main():
    client = FirestoreClient()

    # Get all papers
    papers = client.get_all_papers()

    print(f"Total papers: {len(papers)}")
    print()

    # Find papers without primary_category
    manual_uploads = []
    for paper in papers:
        if not paper.get('primary_category'):
            manual_uploads.append(paper)

    print(f"Papers without primary_category: {len(manual_uploads)}")
    print()

    # Show details of manually uploaded papers
    for paper in manual_uploads:
        print(f"Paper ID: {paper['paper_id']}")
        print(f"Title: {paper['title'][:80]}...")
        print(f"ArXiv ID: {paper.get('arxiv_id', 'N/A')}")
        print(f"Primary Category: {paper.get('primary_category', 'N/A')}")
        print(f"Categories: {paper.get('categories', 'N/A')}")
        print(f"PDF Path: {paper.get('pdf_path', 'N/A')[:60]}...")
        print()

if __name__ == "__main__":
    main()

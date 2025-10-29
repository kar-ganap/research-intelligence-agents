"""
List Papers - Quick script to see what's in Firestore
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.firestore_client import FirestoreClient

def list_papers():
    """List all papers in Firestore."""
    firestore_client = FirestoreClient()

    papers = firestore_client.get_all_papers()

    print(f"Total papers in Firestore: {len(papers)}\n")

    for i, paper in enumerate(papers, 1):
        print(f"{i}. {paper.get('title', 'N/A')}")
        print(f"   ID: {paper.get('paper_id', 'N/A')}")
        print(f"   Authors: {', '.join(paper.get('authors', [])[:3])}")
        print(f"   PDF Path: {paper.get('pdf_path', 'N/A')}")
        print(f"   Key Finding: {paper.get('key_finding', 'N/A')[:150]}...")
        print()

if __name__ == "__main__":
    list_papers()

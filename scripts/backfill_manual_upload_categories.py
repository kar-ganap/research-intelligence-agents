#!/usr/bin/env python3
"""
Backfill arXiv categories for manually uploaded papers

This script finds papers without primary_category and infers their category
using the EntityAgent.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.firestore_client import FirestoreClient
from src.agents.ingestion.entity_agent import EntityAgent

def main():
    print("=" * 80)
    print("Backfilling arXiv Categories for Manually Uploaded Papers")
    print("=" * 80)
    print()

    client = FirestoreClient()
    entity_agent = EntityAgent()

    # Get all papers
    papers = client.get_all_papers()

    # Find papers without primary_category
    papers_to_update = []
    for paper in papers:
        if not paper.get('primary_category'):
            papers_to_update.append(paper)

    print(f"Found {len(papers_to_update)} papers without primary_category")
    print()

    if not papers_to_update:
        print("No papers to update!")
        return

    # Update each paper
    for i, paper in enumerate(papers_to_update, 1):
        paper_id = paper['paper_id']
        title = paper['title']
        key_finding = paper.get('key_finding', '')

        print(f"[{i}/{len(papers_to_update)}] Processing: {title[:60]}...")

        # Infer category
        try:
            inferred_category = entity_agent.infer_arxiv_category(title, key_finding)
            print(f"  Inferred category: {inferred_category}")

            # Update in Firestore
            client.db.collection('papers').document(paper_id).update({
                'primary_category': inferred_category,
                'categories': [inferred_category]
            })

            print(f"  ✓ Updated paper {paper_id}")
            print()

        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            print()

    print("=" * 80)
    print("Backfill complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()

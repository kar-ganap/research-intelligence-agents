#!/usr/bin/env python3
"""
Add cs.AI papers to the database.
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage.firestore_client import FirestoreClient
from scripts.backfill_paper_metadata import fetch_arxiv_metadata

# cs.AI papers to add
AI_PAPERS = [
    {
        "title": "Monte Carlo Game Solver",
        "authors": ["Tristan Cazenave"],
        "key_finding": "Introduced Monte Carlo methods for solving games completely, combining MCTS with proof-number search to verify optimal solutions in game trees.",
        "arxiv_id": "2001.05087"
    },
    {
        "title": "Batch Monte Carlo Tree Search",
        "authors": ["Tristan Cazenave"],
        "key_finding": "Extended MCTS to batch processing, enabling efficient parallelization and GPU acceleration for tree search algorithms in game playing.",
        "arxiv_id": "2104.04278"
    },
    {
        "title": "Multiplayer AlphaZero",
        "authors": ["Nick Petosa", "Tucker Balch"],
        "key_finding": "Extended AlphaZero's self-play reinforcement learning approach to multiplayer games, addressing the challenge of non-deterministic opponent strategies.",
        "arxiv_id": "1910.13012"
    },
    {
        "title": "From Single Agent to Multi-Agent: Improving Traffic Signal Control",
        "authors": ["Maksim Tislenko", "Dmitrii Kisilev"],
        "key_finding": "Demonstrated how multi-agent reinforcement learning improves traffic signal control over single-agent approaches, achieving better traffic flow coordination.",
        "arxiv_id": "2406.13693"
    },
    {
        "title": "Prompting Fairness: Artificial Intelligence as Game Players",
        "authors": ["Jazmia Henry"],
        "key_finding": "Analyzed fairness considerations when AI systems act as players in game-theoretic scenarios, examining strategic behavior and equilibrium concepts.",
        "arxiv_id": "2402.05786"
    },
    {
        "title": "Monte Carlo Search Algorithms Discovering Monte Carlo Tree Search Exploration Terms",
        "authors": ["Tristan Cazenave"],
        "key_finding": "Used genetic programming to automatically discover improved exploration terms for MCTS, finding novel formulas that outperform traditional UCT.",
        "arxiv_id": "2404.09304"
    },
]

def add_ai_papers():
    """Add cs.AI papers to the database."""

    print(f"\n{'='*80}")
    print(f"ADDING CS.AI PAPERS TO DATABASE")
    print(f"{'='*80}\n")

    # Initialize Firestore client
    firestore_client = FirestoreClient()

    success_count = 0
    skip_count = 0
    fail_count = 0

    for i, paper in enumerate(AI_PAPERS, 1):
        print(f"[{i}/{len(AI_PAPERS)}] Adding: {paper['title']}")
        print(f"  Authors: {', '.join(paper['authors'][:3])}{' et al.' if len(paper['authors']) > 3 else ''}")
        print(f"  ArXiv: {paper['arxiv_id']}")

        try:
            # Check if paper already exists
            if firestore_client.paper_exists(paper['title'], paper['authors']):
                print(f"  ⚠️  Paper already exists, skipping\n")
                skip_count += 1
                continue

            # Fetch metadata from arXiv
            print(f"  Fetching metadata from arXiv...")
            metadata = fetch_arxiv_metadata(paper['arxiv_id'])

            if not metadata:
                print(f"  ✗ Failed to fetch arXiv metadata\n")
                fail_count += 1
                continue

            # Verify it's actually cs.AI
            if metadata.get('primary_category') != 'cs.AI':
                print(f"  ⚠️  Primary category is {metadata.get('primary_category')}, not cs.AI")
                print(f"  Adding anyway since cs.AI is in categories: {metadata.get('categories')}\n")

            # Prepare paper data
            paper_data = {
                "title": paper["title"],
                "authors": paper["authors"],
                "key_finding": paper["key_finding"],
                "arxiv_id": paper["arxiv_id"],
                "categories": metadata.get('categories', []),
                "primary_category": metadata.get('primary_category', ''),
                "published": metadata.get('published'),
                "updated": metadata.get('updated')
            }

            # Store in Firestore
            paper_id = firestore_client.store_paper(paper_data)
            print(f"  ✅ Added successfully: {paper_id}")
            print(f"  Category: {metadata.get('primary_category', 'unknown')}")
            print(f"  Published: {metadata.get('published', 'unknown')}\n")
            success_count += 1

        except Exception as e:
            print(f"  ✗ Exception: {str(e)}\n")
            fail_count += 1

        # Rate limit to avoid overwhelming arXiv API
        time.sleep(1)

    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Successfully added: {success_count}")
    print(f"Skipped (already exist): {skip_count}")
    print(f"Failed: {fail_count}")
    print(f"Total attempted: {len(AI_PAPERS)}")
    print()

if __name__ == '__main__':
    add_ai_papers()

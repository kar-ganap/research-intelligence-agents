#!/usr/bin/env python3
"""
Check which papers exist in each category.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage.firestore_client import FirestoreClient

def check_papers():
    """Check existing papers by category."""

    # Initialize Firestore client
    firestore_client = FirestoreClient()

    # Get all papers
    print("\n📚 Fetching all papers from Firestore...")
    papers = firestore_client.get_all_papers()
    print(f"Found {len(papers)} total papers\n")

    # Group by primary_category
    lg_papers = []
    cv_papers = []
    ai_papers = []
    stat_ml_papers = []
    other_papers = []

    for paper in papers:
        primary_category = paper.get('primary_category', '')
        title = paper.get('title', '')

        if primary_category == 'cs.LG':
            lg_papers.append(title)
        elif primary_category == 'cs.CV':
            cv_papers.append(title)
        elif primary_category == 'cs.AI':
            ai_papers.append(title)
        elif primary_category == 'stat.ML':
            stat_ml_papers.append(title)
        else:
            other_papers.append((title, primary_category))

    # Print results
    print(f"{'='*80}")
    print(f"LG (Machine Learning): {len(lg_papers)} papers")
    print(f"{'='*80}")
    for i, title in enumerate(lg_papers, 1):
        print(f"{i}. {title}")

    print(f"\n{'='*80}")
    print(f"CV (Computer Vision): {len(cv_papers)} papers")
    print(f"{'='*80}")
    for i, title in enumerate(cv_papers, 1):
        print(f"{i}. {title}")

    print(f"\n{'='*80}")
    print(f"AI (Artificial Intelligence): {len(ai_papers)} papers")
    print(f"{'='*80}")
    for i, title in enumerate(ai_papers, 1):
        print(f"{i}. {title}")

    print(f"\n{'='*80}")
    print(f"stat.ML (Statistics - Machine Learning): {len(stat_ml_papers)} papers")
    print(f"{'='*80}")
    for i, title in enumerate(stat_ml_papers, 1):
        print(f"{i}. {title}")

    print(f"\n{'='*80}")
    print(f"Other categories: {len(other_papers)} papers")
    print(f"{'='*80}")
    for i, (title, arxiv_id) in enumerate(other_papers, 1):
        print(f"{i}. {title} ({arxiv_id})")

    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"LG: {len(lg_papers)} papers (need {max(0, 8-len(lg_papers))} more to reach 8)")
    print(f"CV: {len(cv_papers)} papers (need {max(0, 8-len(cv_papers))} more to reach 8)")
    print(f"AI: {len(ai_papers)} papers (need {max(0, 8-len(ai_papers))} more to reach 8)")
    print(f"stat.ML: {len(stat_ml_papers)} papers (need {max(0, 8-len(stat_ml_papers))} more to reach 8)")
    print(f"Total: {len(papers)} papers")
    print()

if __name__ == "__main__":
    check_papers()

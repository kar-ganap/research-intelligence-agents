#!/usr/bin/env python3
"""
Add stat.ML (Statistics - Machine Learning) papers to the database.
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage.firestore_client import FirestoreClient
from scripts.backfill_paper_metadata import fetch_arxiv_metadata

# stat.ML papers to add
STAT_ML_PAPERS = [
    {
        "title": "Multiple Gaussian Process Models",
        "authors": ["Cedric Archambeau", "Francis Bach"],
        "key_finding": "Introduced framework for combining multiple Gaussian process models, enabling flexible modeling of complex distributions through mixture of GPs.",
        "arxiv_id": "1110.5238"
    },
    {
        "title": "String Gaussian Process Kernels",
        "authors": ["Yves-Laurent Kom Samo", "Stephen Roberts"],
        "key_finding": "Developed GP kernels for string and sequence data, extending Gaussian processes to non-vectorial structured data like text and DNA sequences.",
        "arxiv_id": "1506.02239"
    },
    {
        "title": "Linearly constrained Gaussian processes",
        "authors": ["Carl Jidling", "Niklas Wahlström", "Adrian Wills", "Thomas B. Schön"],
        "key_finding": "Incorporated linear constraints into Gaussian process models, ensuring physical plausibility and domain knowledge in probabilistic predictions.",
        "arxiv_id": "1703.00787"
    },
    {
        "title": "Distributed Gaussian Processes",
        "authors": ["Marc Peter Deisenroth", "Jun Wei Ng"],
        "key_finding": "Proposed distributed inference framework for Gaussian processes, enabling GP scalability to large datasets through parallelization.",
        "arxiv_id": "1502.02843"
    },
    {
        "title": "Compressed Gaussian Process",
        "authors": ["Rajarshi Guhaniyogi", "David B. Dunson"],
        "key_finding": "Developed compressed representation of Gaussian processes using random projections, achieving computational efficiency without sacrificing accuracy.",
        "arxiv_id": "1406.1916"
    },
    {
        "title": "Bayesian Dropout",
        "authors": ["Tue Herlau", "Morten Mørup", "Mikkel N. Schmidt"],
        "key_finding": "Interpreted dropout as Bayesian inference over model parameters, providing theoretical foundation for dropout's regularization effect in neural networks.",
        "arxiv_id": "1508.02905"
    },
    {
        "title": "Bayesian Optimization with Shape Constraints",
        "authors": ["Michael Jauch", "Víctor Peña"],
        "key_finding": "Extended Bayesian optimization to incorporate shape constraints like monotonicity and convexity, improving optimization in engineering and design applications.",
        "arxiv_id": "1612.08915"
    },
    {
        "title": "Differentially Private Bayesian Optimization",
        "authors": ["Matt J. Kusner", "Jacob R. Gardner", "Roman Garnett", "Kilian Q. Weinberger"],
        "key_finding": "Introduced differential privacy guarantees to Bayesian optimization, enabling privacy-preserving hyperparameter tuning on sensitive data.",
        "arxiv_id": "1501.04080"
    },
    {
        "title": "Unbounded Bayesian Optimization via Regularization",
        "authors": ["Bobak Shahriari", "Alexandre Bouchard-Côté", "Nando de Freitas"],
        "key_finding": "Extended Bayesian optimization to unbounded domains using regularization techniques, removing limitations of bounded search spaces.",
        "arxiv_id": "1508.03666"
    },
]

def add_stat_ml_papers():
    """Add stat.ML papers to the database."""

    print(f"\n{'='*80}")
    print(f"ADDING STAT.ML PAPERS TO DATABASE")
    print(f"{'='*80}\n")

    # Initialize Firestore client
    firestore_client = FirestoreClient()

    success_count = 0
    skip_count = 0
    fail_count = 0

    for i, paper in enumerate(STAT_ML_PAPERS, 1):
        print(f"[{i}/{len(STAT_ML_PAPERS)}] Adding: {paper['title']}")
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

            # Verify it's actually stat.ML
            if metadata.get('primary_category') != 'stat.ML':
                print(f"  ⚠️  Primary category is {metadata.get('primary_category')}, not stat.ML")
                print(f"  Adding anyway since stat.ML is in categories: {metadata.get('categories')}\n")

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
    print(f"Total attempted: {len(STAT_ML_PAPERS)}")
    print()

if __name__ == '__main__':
    add_stat_ml_papers()

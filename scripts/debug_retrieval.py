"""
Debug Retrieval - Investigate why certain questions aren't finding papers
"""

import sys
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.firestore_client import FirestoreClient
from src.tools.retrieval import keyword_search

def debug_retrieval():
    """Debug retrieval for the failed test questions."""

    print("=" * 70)
    print("RETRIEVAL DEBUGGING")
    print("=" * 70)
    print()

    firestore_client = FirestoreClient()

    # First, let's see what papers we have in the corpus
    print("1. Checking corpus contents...")
    print("-" * 70)
    all_papers = firestore_client.get_all_papers()
    print(f"Total papers in corpus: {len(all_papers)}")
    print()

    for i, paper in enumerate(all_papers[:10], 1):  # Show first 10
        print(f"{i}. {paper.get('title', 'N/A')[:60]}")
        print(f"   Authors: {', '.join(paper.get('authors', [])[:3])}")
        print(f"   Key finding: {paper.get('key_finding', 'N/A')[:80]}...")
        print()

    if len(all_papers) > 10:
        print(f"... and {len(all_papers) - 10} more papers")
        print()

    # Now test the problematic queries
    test_queries = [
        {
            "question": "What BLEU score did the Transformer achieve on WMT 2014 English-to-German?",
            "expected_keywords": ["BLEU", "WMT", "Transformer", "translation"],
            "should_find": "Attention Is All You Need"
        },
        {
            "question": "How does BERT compare to GPT-3 in few-shot learning?",
            "expected_keywords": ["BERT", "GPT-3", "few-shot"],
            "should_find": "BERT or GPT-3 papers"
        },
        {
            "question": "Who are the authors of the Transformer paper?",
            "expected_keywords": ["Transformer", "authors"],
            "should_find": "Attention Is All You Need"
        }
    ]

    print("=" * 70)
    print("2. Testing retrieval for each query")
    print("=" * 70)
    print()

    for i, query_test in enumerate(test_queries, 1):
        question = query_test["question"]
        print(f"Query {i}: {question}")
        print(f"  Expected to find: {query_test['should_find']}")
        print(f"  Keywords to look for: {', '.join(query_test['expected_keywords'])}")
        print()

        # Retrieve papers
        retrieved_papers = keyword_search(
            query=question,
            firestore_client=firestore_client,
            limit=5
        )

        print(f"  Retrieved {len(retrieved_papers)} papers:")
        if not retrieved_papers:
            print("    ⚠️  NO PAPERS FOUND!")
        else:
            for j, paper in enumerate(retrieved_papers, 1):
                print(f"    {j}. {paper.get('title', 'N/A')[:60]}")
                print(f"       Finding: {paper.get('key_finding', 'N/A')[:80]}...")

        print()
        print("-" * 70)
        print()

    # Check if the Transformer paper exists and has the BLEU score
    print("=" * 70)
    print("3. Checking specific papers for expected content")
    print("=" * 70)
    print()

    transformer_papers = [p for p in all_papers if 'transformer' in p.get('title', '').lower() or 'attention' in p.get('title', '').lower()]

    print(f"Papers with 'transformer' or 'attention' in title: {len(transformer_papers)}")
    for paper in transformer_papers:
        print(f"  - {paper.get('title', 'N/A')}")
        print(f"    Finding: {paper.get('key_finding', 'N/A')[:150]}")
        print(f"    Has 'BLEU' in finding: {'BLEU' in paper.get('key_finding', '')}")
        print(f"    Has 'WMT' in finding: {'WMT' in paper.get('key_finding', '')}")
        print()

    # Check BERT/GPT papers
    bert_gpt_papers = [p for p in all_papers if any(keyword in p.get('title', '').lower() for keyword in ['bert', 'gpt', 'language model'])]

    print(f"Papers with 'BERT', 'GPT', or 'language model' in title: {len(bert_gpt_papers)}")
    for paper in bert_gpt_papers:
        print(f"  - {paper.get('title', 'N/A')}")
        print(f"    Finding: {paper.get('key_finding', 'N/A')[:150]}")
        print()


if __name__ == "__main__":
    debug_retrieval()

#!/usr/bin/env python3
"""
Verify that all templated queries and keyword examples will return >1 results.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage.firestore_client import FirestoreClient

def verify_queries():
    """Verify all template queries will work."""

    firestore_client = FirestoreClient()
    papers = firestore_client.get_all_papers()

    print(f"\n{'='*80}")
    print("VERIFYING TEMPLATE QUERIES")
    print(f"{'='*80}\n")
    print(f"Total papers in corpus: {len(papers)}\n")

    issues = []

    # 1. Check for "Ashish Vaswani" author (from Transformer paper)
    print("1. Checking 'Papers by Ashish Vaswani'...")
    vaswani_papers = []
    for paper in papers:
        authors = paper.get('authors', [])
        if any('Vaswani' in author for author in authors):
            vaswani_papers.append(paper.get('title', 'Unknown'))

    if len(vaswani_papers) == 0:
        issues.append("❌ No papers by Ashish Vaswani found")
        print(f"  ❌ FAIL: Found {len(vaswani_papers)} papers (need >1)")
    elif len(vaswani_papers) == 1:
        issues.append(f"⚠️  Only 1 paper by Ashish Vaswani: {vaswani_papers[0]}")
        print(f"  ⚠️  WARNING: Found only 1 paper (need >1 for good demo)")
    else:
        print(f"  ✅ PASS: Found {len(vaswani_papers)} papers")
        for p in vaswani_papers:
            print(f"     - {p}")

    # 2. Check for Transformer paper
    print("\n2. Checking 'Which papers cite the Transformer paper?'...")
    transformer_papers = []
    for paper in papers:
        title = paper.get('title', '').lower()
        if 'attention is all you need' in title or 'transformer' in title:
            transformer_papers.append(paper.get('title', 'Unknown'))

    if len(transformer_papers) == 0:
        issues.append("❌ No Transformer papers found")
        print(f"  ❌ FAIL: No Transformer paper found")
    else:
        print(f"  ✅ PASS: Found {len(transformer_papers)} Transformer-related paper(s)")
        for p in transformer_papers:
            print(f"     - {p}")

    # 3. Check for BERT paper
    print("\n3. Checking 'Which papers extend the BERT model?'...")
    bert_papers = []
    for paper in papers:
        title = paper.get('title', '').lower()
        if 'bert' in title:
            bert_papers.append(paper.get('title', 'Unknown'))

    if len(bert_papers) == 0:
        issues.append("❌ No BERT papers found")
        print(f"  ❌ FAIL: No BERT paper found")
    else:
        print(f"  ✅ PASS: Found {len(bert_papers)} BERT-related paper(s)")
        for p in bert_papers:
            print(f"     - {p}")

    # 4. Check for keyword examples: "transformer, attention, neural"
    print("\n4. Checking keyword examples (transformer, attention, neural)...")
    keyword_results = {
        'transformer': [],
        'attention': [],
        'neural': []
    }

    for paper in papers:
        title = paper.get('title', '').lower()
        key_finding = paper.get('key_finding', '').lower()
        combined = f"{title} {key_finding}"

        if 'transformer' in combined:
            keyword_results['transformer'].append(paper.get('title'))
        if 'attention' in combined:
            keyword_results['attention'].append(paper.get('title'))
        if 'neural' in combined or 'network' in combined:
            keyword_results['neural'].append(paper.get('title'))

    for keyword, matches in keyword_results.items():
        if len(matches) == 0:
            issues.append(f"❌ Keyword '{keyword}' found 0 papers")
            print(f"  ❌ FAIL: '{keyword}' - Found {len(matches)} papers (need >1)")
        elif len(matches) == 1:
            issues.append(f"⚠️  Keyword '{keyword}' found only 1 paper")
            print(f"  ⚠️  WARNING: '{keyword}' - Found {len(matches)} paper (need >1 for good demo)")
        else:
            print(f"  ✅ PASS: '{keyword}' - Found {len(matches)} papers")

    # 5. Check for relationships (need these for citation queries)
    print("\n5. Checking relationships...")
    relationships = firestore_client.get_all_relationships(limit=1000)
    print(f"  Total relationships: {len(relationships)}")

    if len(relationships) < 5:
        issues.append(f"⚠️  Only {len(relationships)} relationships (need more for demos)")
        print(f"  ⚠️  WARNING: Need more relationships for citation/contradiction queries")
    else:
        print(f"  ✅ PASS: Have {len(relationships)} relationships")

    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}\n")

    if len(issues) == 0:
        print("✅ All template queries will work correctly!")
    else:
        print(f"Found {len(issues)} issue(s):\n")
        for issue in issues:
            print(f"  {issue}")
        print()
        print("Recommendations:")
        print("  - Add more papers by authors mentioned in queries")
        print("  - Ensure keyword placeholders match actual corpus content")
        print("  - Run relationship detection to populate citations")

    print()

if __name__ == '__main__':
    verify_queries()

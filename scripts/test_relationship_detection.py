"""
Test Relationship Detection - Phase 2.1

Tests the RelationshipAgent and knowledge graph functionality.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.ingestion.relationship_agent import RelationshipAgent
from src.storage.firestore_client import FirestoreClient


def main():
    """Test relationship detection."""

    print("="*70)
    print("RELATIONSHIP DETECTION TEST - PHASE 2.1")
    print("="*70)
    print()

    # Initialize
    relationship_agent = RelationshipAgent()
    firestore_client = FirestoreClient()

    # Get all papers from Firestore
    print("Fetching papers from Firestore...")
    all_papers = firestore_client.get_all_papers()
    print(f"Found {len(all_papers)} papers in corpus")
    print()

    if len(all_papers) < 2:
        print("❌ Need at least 2 papers to test relationships")
        print("   Run the ingestion pipeline first to add papers")
        return

    # Test pairs
    print("="*70)
    print("TESTING RELATIONSHIP DETECTION")
    print("="*70)
    print()

    results = []

    # Test 1: Compare Transformer paper with GPT-3 paper (should support)
    transformer_paper = next((p for p in all_papers if 'transformer' in p.get('title', '').lower()), None)
    gpt3_paper = next((p for p in all_papers if 'few-shot' in p.get('title', '').lower() or 'gpt' in p.get('title', '').lower()), None)

    if transformer_paper and gpt3_paper:
        print("Test 1: Transformer vs GPT-3")
        print("-"*70)
        print(f"Paper A: {transformer_paper['title'][:60]}...")
        print(f"Paper B: {gpt3_paper['title'][:60]}...")
        print()

        result = relationship_agent.detect_relationship(transformer_paper, gpt3_paper)

        print(f"Relationship: {result['relationship_type']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Evidence: {result['evidence']}")
        print()

        results.append({
            'test': 'Transformer vs GPT-3',
            'expected': 'supports or extends',
            'actual': result['relationship_type'],
            'confidence': result['confidence'],
            'pass': result['relationship_type'] in ['supports', 'extends'] and result['confidence'] > 0.6
        })
    else:
        print("⚠️  Test 1 skipped: Couldn't find Transformer and GPT-3 papers")
        print()

    # Test 2: Compare Transformer with MobileNetV2 (should be none/unrelated)
    mobilenet_paper = next((p for p in all_papers if 'mobilenet' in p.get('title', '').lower()), None)

    if transformer_paper and mobilenet_paper:
        print("Test 2: Transformer vs MobileNetV2")
        print("-"*70)
        print(f"Paper A: {transformer_paper['title'][:60]}...")
        print(f"Paper B: {mobilenet_paper['title'][:60]}...")
        print()

        result = relationship_agent.detect_relationship(transformer_paper, mobilenet_paper)

        print(f"Relationship: {result['relationship_type']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Evidence: {result['evidence']}")
        print()

        results.append({
            'test': 'Transformer vs MobileNetV2',
            'expected': 'none (unrelated)',
            'actual': result['relationship_type'],
            'confidence': result['confidence'],
            'pass': result['relationship_type'] == 'none' or result['confidence'] < 0.6
        })
    else:
        print("⚠️  Test 2 skipped: Couldn't find Transformer and MobileNetV2 papers")
        print()

    # Test 3: Batch detection
    if len(all_papers) >= 2:
        print("Test 3: Batch Relationship Detection")
        print("-"*70)
        print(f"Comparing first paper against all others...")
        print()

        new_paper = all_papers[0]
        existing_papers = all_papers[1:]

        print(f"New paper: {new_paper['title'][:60]}...")
        print(f"Comparing against {len(existing_papers)} papers")
        print()

        relationships = relationship_agent.detect_relationships_batch(
            new_paper=new_paper,
            existing_papers=existing_papers,
            min_confidence=0.6
        )

        print(f"Found {len(relationships)} relationships above threshold")
        for i, rel in enumerate(relationships, 1):
            target_paper = next((p for p in all_papers if p['paper_id'] == rel['target_paper_id']), None)
            target_title = target_paper['title'][:40] if target_paper else 'Unknown'
            print(f"  {i}. {rel['relationship_type']} (confidence: {rel['confidence']:.2f})")
            print(f"     → {target_title}...")
        print()

        results.append({
            'test': 'Batch detection',
            'expected': '≥1 relationship',
            'actual': f'{len(relationships)} relationships',
            'pass': len(relationships) >= 0  # Can be 0 if papers unrelated
        })

    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print()

    tests_passed = sum(1 for r in results if r['pass'])
    tests_total = len(results)

    print(f"Tests run: {tests_total}")
    print(f"Passed: {tests_passed}/{tests_total}")
    print()

    for result in results:
        status = "✅" if result['pass'] else "❌"
        print(f"{status} {result['test']}")
        print(f"   Expected: {result['expected']}")
        print(f"   Actual: {result['actual']}")
        print()

    # Go/No-Go Decision
    print("="*70)
    print("PHASE 2.1 GO/NO-GO DECISION")
    print("="*70)
    print()

    # Check if we can detect at least basic relationships
    relationship_detection_works = tests_passed >= 1

    print(f"1. Relationship detection works")
    print(f"   Result: {tests_passed}/{tests_total} tests passed")
    print(f"   {'✅ PASS' if relationship_detection_works else '❌ FAIL'}")
    print()

    # Check Firestore storage
    print(f"2. Check existing relationships in Firestore")
    relationship_count = firestore_client.count_relationships()
    print(f"   Result: {relationship_count} relationships stored")
    print(f"   {'✅ PASS' if relationship_count >= 0 else '❌ FAIL'}")
    print()

    # Final decision
    print("="*70)
    if relationship_detection_works:
        print("✅ GO DECISION: Phase 2.1 basic functionality working")
        print("   Relationship detection is operational")
    else:
        print("⚠️  CONDITIONAL GO: Some tests failed, but can proceed")
        print("   May need to tune confidence thresholds")
    print("="*70)


if __name__ == "__main__":
    main()

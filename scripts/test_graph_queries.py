"""
Test Graph Query Functionality

Tests the new graph-aware Q&A capabilities:
1. Most cited papers
2. Papers by author
3. Contradictions
4. Citations
5. Extensions
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pipelines.qa_pipeline import QAPipeline
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_graph_queries():
    """Test various graph query types."""
    print("=" * 80)
    print("TESTING GRAPH-AWARE Q&A")
    print("=" * 80)
    print()

    # Initialize pipeline
    pipeline = QAPipeline(enable_confidence=False)

    # Test queries
    test_queries = [
        ("What are the most cited papers?", "popularity"),
        ("Which papers are most influential?", "popularity"),
        ("Show me papers by Vaswani", "author"),
        ("What papers contradict each other?", "contradictions"),
        ("Which papers cite the Transformer paper?", "citations"),
        ("What papers build on BERT?", "citations"),
    ]

    results = []

    for i, (question, expected_type) in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}/{len(test_queries)}: {question}")
        print(f"Expected type: {expected_type}")
        print("=" * 80)

        result = pipeline.ask(question)

        if result.get('success'):
            print(f"\n✅ SUCCESS")
            print(f"Query type detected: {result.get('query_type', 'content (not graph)')}")
            print(f"Is graph query: {result.get('is_graph_query', False)}")
            print(f"Duration: {result.get('duration', 0):.2f}s")
            print(f"\nAnswer:")
            print(result.get('answer', 'No answer'))

            # Show graph data summary
            if 'graph_data' in result:
                graph_data = result['graph_data']
                if 'papers' in graph_data:
                    print(f"\nFound {len(graph_data['papers'])} papers")
                elif 'contradictions' in graph_data:
                    print(f"\nFound {len(graph_data['contradictions'])} contradictions")
        else:
            print(f"\n❌ FAILED")
            print(f"Error: {result.get('error', 'Unknown error')}")

        results.append({
            'question': question,
            'expected_type': expected_type,
            'actual_type': result.get('query_type'),
            'success': result.get('success', False),
            'is_graph': result.get('is_graph_query', False)
        })

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    total = len(results)
    successful = sum(1 for r in results if r['success'])
    graph_queries = sum(1 for r in results if r['is_graph'])
    correct_type = sum(1 for r in results if r['actual_type'] == r['expected_type'])

    print(f"\nTotal queries: {total}")
    print(f"Successful: {successful}/{total}")
    print(f"Detected as graph queries: {graph_queries}/{total}")
    print(f"Correct type detection: {correct_type}/{total}")

    print("\nDetails:")
    for i, r in enumerate(results, 1):
        status = "✅" if r['success'] and r['is_graph'] else "❌"
        print(f"{i}. {status} {r['question'][:50]}...")
        print(f"   Expected: {r['expected_type']}, Got: {r['actual_type']}, Graph: {r['is_graph']}")

    if successful == total and graph_queries == total:
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED - Graph queries working!")
        print("=" * 80)
        return True
    else:
        print("\n" + "=" * 80)
        print("⚠️  SOME TESTS FAILED - Review results above")
        print("=" * 80)
        return False


if __name__ == "__main__":
    success = test_graph_queries()
    sys.exit(0 if success else 1)

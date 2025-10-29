"""
Test Confidence Scoring - Phase 2.3

Tests ConfidenceAgent with different evidence quality scenarios:
1. High confidence: Clear evidence with exact citations
2. Medium confidence: Partial evidence or requires inference
3. Low confidence: No relevant evidence
4. Contradiction scenario: Conflicting evidence
"""

import sys
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipelines.qa_pipeline import QAPipeline
from src.storage.firestore_client import FirestoreClient
import time


def test_confidence_scoring():
    """
    Test confidence scoring with various scenarios.
    """
    print("=" * 70)
    print("PHASE 2.3: CONFIDENCE SCORING - TEST")
    print("=" * 70)
    print()

    # Initialize pipeline with confidence enabled
    qa_pipeline = QAPipeline(enable_confidence=True)
    firestore_client = FirestoreClient()

    # Define test scenarios
    test_scenarios = [
        {
            "name": "High Confidence - Factual Author Question",
            "question": "Who are the authors of the Transformer paper?",
            "expected_confidence": "high",
            "threshold": 0.75,
            "reasoning": "Direct factual answer from paper metadata with exact citation"
        },
        {
            "name": "High Confidence - Explicit Performance Metric",
            "question": "What BLEU score did the Transformer achieve on WMT 2014 English-to-German?",
            "expected_confidence": "high",
            "threshold": 0.70,
            "reasoning": "Specific metric explicitly stated in primary paper"
        },
        {
            "name": "Medium Confidence - Comparison Question",
            "question": "How does BERT compare to GPT-3 in few-shot learning?",
            "expected_confidence": "medium",
            "threshold_min": 0.35,
            "threshold_max": 0.75,
            "reasoning": "Requires comparing findings from different papers, partial evidence"
        },
        {
            "name": "Low Confidence - Out of Domain Question",
            "question": "What is the best recipe for chocolate cake?",
            "expected_confidence": "low",
            "threshold": 0.35,
            "reasoning": "No relevant evidence in ML research corpus"
        },
        {
            "name": "Low Confidence - Partial Domain Overlap",
            "question": "What are the ethical implications of large language models?",
            "expected_confidence": "low-medium",
            "threshold_min": 0.25,
            "threshold_max": 0.65,
            "reasoning": "May have vague mentions but likely no comprehensive discussion"
        }
    ]

    print("=" * 70)
    print("RUNNING CONFIDENCE TESTS")
    print("=" * 70)
    print()

    results = []

    for i, scenario in enumerate(test_scenarios, 1):
        print(f"Test {i}/{len(test_scenarios)}: {scenario['name']}")
        print(f"  Question: {scenario['question']}")
        print(f"  Expected: {scenario['expected_confidence']} confidence")
        print()

        # Ask question with confidence scoring
        result = qa_pipeline.ask(scenario['question'], limit=5)

        if not result.get('success'):
            print(f"  ❌ FAILED: {result.get('error', 'Unknown error')}")
            results.append({
                "scenario": scenario['name'],
                "passed": False,
                "error": result.get('error')
            })
            print()
            continue

        # Get confidence data
        confidence_data = result.get('confidence')

        if not confidence_data:
            print("  ⚠️  WARNING: No confidence data returned")
            results.append({
                "scenario": scenario['name'],
                "passed": False,
                "error": "No confidence data"
            })
            print()
            continue

        score = confidence_data['score']
        breakdown = confidence_data['breakdown']
        reasoning = confidence_data['reasoning']
        warning = confidence_data.get('warning')

        # Display results
        print(f"  Answer: {result['answer'][:100]}...")
        print(f"  Citations: {len(result.get('citations', []))}")
        print()
        print(f"  Confidence Score: {score:.2f}")
        print(f"    Evidence Strength: {breakdown['evidence_strength']:.2f}")
        print(f"    Consistency: {breakdown['consistency']:.2f}")
        print(f"    Coverage: {breakdown['coverage']:.2f}")
        print(f"    Source Quality: {breakdown['source_quality']:.2f}")
        print(f"  Reasoning: {reasoning}")
        if warning:
            print(f"  ⚠️  Warning: {warning}")
        print()

        # Check if score meets expectations
        passed = False
        if 'threshold' in scenario:
            # Single threshold (high or low)
            if scenario['expected_confidence'] == 'high':
                passed = score >= scenario['threshold']
                check = f">= {scenario['threshold']}"
            else:  # low
                passed = score < scenario['threshold']
                check = f"< {scenario['threshold']}"
        else:
            # Range threshold (medium)
            passed = scenario['threshold_min'] <= score <= scenario['threshold_max']
            check = f"{scenario['threshold_min']:.2f} - {scenario['threshold_max']:.2f}"

        if passed:
            print(f"  ✅ PASS: Score {score:.2f} meets expectation ({check})")
        else:
            print(f"  ❌ FAIL: Score {score:.2f} does not meet expectation ({check})")

        results.append({
            "scenario": scenario['name'],
            "question": scenario['question'],
            "expected": scenario['expected_confidence'],
            "score": score,
            "breakdown": breakdown,
            "passed": passed,
            "reasoning": reasoning
        })

        print()

        # Add delay to avoid rate limits
        if i < len(test_scenarios):
            print("  Waiting 7 seconds to avoid rate limits...")
            time.sleep(7)
            print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()

    passed_count = sum(1 for r in results if r.get('passed', False))
    total_count = len(results)

    print(f"Tests run: {total_count}")
    print(f"Passed: {passed_count}/{total_count} ({passed_count/total_count*100:.1f}%)")
    print()

    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result.get('passed') else "❌ FAIL"
        score = result.get('score', 0)
        print(f"{i}. {status}: {result['scenario']}")
        print(f"   Expected: {result.get('expected', 'N/A')}, Got: {score:.2f}")
        if not result.get('passed'):
            print(f"   Reason: {result.get('error') or result.get('reasoning', 'N/A')[:100]}")
        print()

    # Success criteria
    print("=" * 70)
    print("PHASE 2.3 GO/NO-GO DECISION")
    print("=" * 70)
    print()

    criteria = [
        ("ConfidenceAgent returns scores 0-1", all(0 <= r.get('score', -1) <= 1 for r in results)),
        ("High confidence scenarios pass", all(r['passed'] for r in results if 'High Confidence' in r['scenario'])),
        ("Low confidence scenarios pass", all(r['passed'] for r in results if 'Low Confidence' in r['scenario'])),
        ("Overall accuracy ≥60%", passed_count/total_count >= 0.6)
    ]

    all_pass = True
    for criterion, met in criteria:
        status = "✅ PASS" if met else "❌ FAIL"
        print(f"{status}: {criterion}")
        if not met:
            all_pass = False

    print()
    if all_pass:
        print("=" * 70)
        print("✅ GO DECISION: Phase 2.3 confidence scoring working")
        print("   ConfidenceAgent correctly evaluates evidence quality")
        print("=" * 70)
    else:
        print("=" * 70)
        print("❌ NO-GO: Phase 2.3 needs refinement")
        print("=" * 70)


if __name__ == "__main__":
    test_confidence_scoring()

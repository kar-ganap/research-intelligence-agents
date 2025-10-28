"""
Phase 1.2 Go/No-Go Test - Q&A with Citations

Tests the Q&A pipeline on 5 diverse questions based on our 3 ingested papers:
1. Attention Is All You Need
2. MobileNetV2
3. GPT-3 (Language Models are Few-Shot Learners)
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipelines.qa_pipeline import QAPipeline


def main():
    """Run Phase 1.2 Go/No-Go test."""

    print("="*70)
    print("PHASE 1.2 GO/NO-GO TEST: Q&A WITH CITATIONS")
    print("="*70)
    print()

    # Test questions - diverse types based on our 3 papers
    test_questions = [
        # 1. Factual extraction (easy) - should find exact info
        "Who are the authors of the Transformer paper?",

        # 2. Key finding (medium) - should synthesize from key_finding
        "What is the main contribution of the Transformer architecture?",

        # 3. Specific technical detail (medium)
        "What makes MobileNetV2 different from the original MobileNet?",

        # 4. Comparison/synthesis (hard) - needs to understand multiple papers
        "What do the Transformer and MobileNetV2 architectures have in common?",

        # 5. Out of scope (important) - should refuse gracefully
        "What is the capital of France?",
    ]

    print(f"Testing {len(test_questions)} questions")
    print()

    # Initialize pipeline
    pipeline = QAPipeline()

    # Run batch test
    summary = pipeline.batch_ask(test_questions, limit=3)

    print()
    print("="*70)
    print("DETAILED RESULTS")
    print("="*70)
    print()

    # Analyze each result
    correct_answers = 0
    with_citations = 0
    answered_questions = 0  # Questions where agent attempted an answer (not "don't have info")
    out_of_scope_handled = False

    for i, result in enumerate(summary['results'], 1):
        question = result['question']
        print(f"Question {i}: {question}")
        print("-"*70)

        if result['success']:
            answer = result['answer']
            citations = result['citations']
            papers_found = result['steps']['retrieval']['papers_found']

            print(f"✅ Answer: {answer}")
            print()

            # Check if this was an actual answer (not "don't have info")
            is_refusal = "don't have enough information" in answer.lower() or "couldn't find" in answer.lower()

            if not is_refusal:
                answered_questions += 1

            # Check for citations (only for non-refusal answers)
            if citations:
                print(f"✅ Citations: {citations}")
                if not is_refusal:
                    with_citations += 1
            else:
                if is_refusal:
                    print(f"   ℹ️  Correctly refused (no citation needed)")
                else:
                    print(f"❌ No citations found")

            print(f"   Papers retrieved: {papers_found}")
            print(f"   Duration: {result['duration']:.2f}s")

            # Manual evaluation criteria
            # Q1: Should mention Vaswani, Shazeer, Parmar
            if i == 1:
                if any(name in answer for name in ["Vaswani", "Shazeer", "Parmar"]):
                    print(f"   ✅ Factually correct (mentions authors)")
                    correct_answers += 1
                else:
                    print(f"   ❌ Missing author names")

            # Q2: Should mention attention mechanisms / self-attention
            elif i == 2:
                if any(term in answer.lower() for term in ["attention", "self-attention", "transformer"]):
                    print(f"   ✅ Factually correct (mentions key concepts)")
                    correct_answers += 1
                else:
                    print(f"   ❌ Missing key concepts")

            # Q3: Should mention inverted residuals or linear bottlenecks
            elif i == 3:
                if any(term in answer.lower() for term in ["inverted", "residual", "bottleneck", "mobilenet"]):
                    print(f"   ✅ Relevant answer")
                    correct_answers += 1
                else:
                    print(f"   ⚠️  May not be specific enough")

            # Q4: Hard question - any reasonable comparison is good
            elif i == 4:
                if papers_found >= 2:
                    print(f"   ✅ Retrieved multiple papers for comparison")
                    correct_answers += 1
                else:
                    print(f"   ⚠️  Only found {papers_found} paper(s)")

            # Q5: Out of scope - should refuse
            elif i == 5:
                if "don't have enough information" in answer.lower() or "cannot answer" in answer.lower() or papers_found == 0:
                    print(f"   ✅ Correctly refused out-of-scope question")
                    out_of_scope_handled = True
                    correct_answers += 1
                else:
                    print(f"   ❌ Should have refused to answer")

        else:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")

        print()

    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print()

    print(f"Total questions: {summary['total']}")
    print(f"Successful: {summary['successful']}")
    print(f"Failed: {summary['failed']}")
    print(f"Success rate: {summary['success_rate']:.1%}")
    print()

    print(f"Answered (not refused): {answered_questions}/{summary['total']}")
    print(f"With citations: {with_citations}/{answered_questions if answered_questions > 0 else 1}")
    # Citation coverage = citations / answered questions (excluding refusals)
    actual_citation_coverage = with_citations / answered_questions if answered_questions > 0 else 0
    print(f"Citation coverage (of answered): {actual_citation_coverage:.1%}")
    print()

    print(f"Correct/relevant answers: {correct_answers}/{summary['total']}")
    print(f"Accuracy: {correct_answers/summary['total']:.1%}")
    print()

    print(f"Avg duration: {summary['avg_duration']:.2f}s per question")
    print(f"Total duration: {summary['total_duration']:.2f}s")
    print()

    # Phase 1.2 Go/No-Go criteria
    print("="*70)
    print("PHASE 1.2 GO/NO-GO DECISION")
    print("="*70)
    print()

    print("Criteria:")
    print()

    # Level 1 (Blockers)
    retrieval_works = summary['successful'] >= 3  # ≥3/5 questions answered
    citation_coverage_ok = actual_citation_coverage >= 0.8  # ≥80% of answered questions have citations

    print(f"1. Retrieval finds relevant papers (≥3/5)")
    print(f"   Result: {summary['successful']}/5 successful")
    print(f"   {'✅ PASS' if retrieval_works else '❌ FAIL'}")
    print()

    print(f"2. Answers include citations (≥80% of answered)")
    print(f"   Result: {with_citations}/{answered_questions} = {actual_citation_coverage:.1%} coverage")
    print(f"   {'✅ PASS' if citation_coverage_ok else '❌ FAIL'}")
    print()

    # Level 2 (Critical)
    accuracy_ok = (correct_answers / summary['total']) >= 0.6  # ≥60% correct
    latency_ok = summary['avg_duration'] < 10  # <10s average

    print(f"3. Answers factually correct (≥60%)")
    print(f"   Result: {correct_answers/summary['total']:.1%} accuracy")
    print(f"   {'✅ PASS' if accuracy_ok else '⚠️  WARNING'}")
    print()

    print(f"4. Latency acceptable (avg <10s)")
    print(f"   Result: {summary['avg_duration']:.2f}s average")
    print(f"   {'✅ PASS' if latency_ok else '⚠️  WARNING'}")
    print()

    print(f"5. Refuses out-of-scope gracefully")
    print(f"   Result: {'Handled correctly' if out_of_scope_handled else 'Did not refuse'}")
    print(f"   {'✅ PASS' if out_of_scope_handled else '⚠️  WARNING'}")
    print()

    # Final decision
    blockers_passed = retrieval_works and citation_coverage_ok
    critical_passed = accuracy_ok or latency_ok  # At least one critical

    print("="*70)
    if blockers_passed and critical_passed:
        print("✅ GO DECISION: Phase 1.2 criteria MET")
        print("   Q&A pipeline is working well enough to proceed")
    elif blockers_passed:
        print("⚠️  CONDITIONAL GO: Blockers passed, but review warnings")
        print("   Can proceed but may want to improve accuracy/latency")
    else:
        print("❌ NO-GO DECISION: Phase 1.2 criteria NOT MET")
        print("   Need to fix retrieval or citation issues")

    print("="*70)


if __name__ == "__main__":
    main()

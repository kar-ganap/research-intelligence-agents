"""
Comprehensive Q&A Test - Phase 1.2

10 questions with 7-3 split:
- 7 questions that SHOULD be answerable from our 3 papers
- 3 questions that SHOULD be refused (out of scope / no info)

Papers we have:
1. Attention Is All You Need (Transformer paper)
2. MobileNetV2: Inverted Residuals and Linear Bottlenecks
3. Language Models are Few-Shot Learners (GPT-3)
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipelines.qa_pipeline import QAPipeline


def main():
    """Run comprehensive Q&A test."""

    print("="*70)
    print("COMPREHENSIVE Q&A TEST - PHASE 1.2")
    print("="*70)
    print()

    # Test questions - 7 answerable, 3 should refuse
    test_questions = [
        # === ANSWERABLE QUESTIONS (7) ===
        # These should have citations and correct answers

        # 1. Direct factual (easy) - from Transformer paper
        {
            "question": "Who are the authors of the Transformer paper?",
            "should_answer": True,
            "expected_contains": ["Vaswani", "Shazeer", "Parmar"],
            "expected_paper": "Attention Is All You Need"
        },

        # 2. Key contribution (medium) - from Transformer paper
        {
            "question": "What is the main innovation of the Transformer architecture?",
            "should_answer": True,
            "expected_contains": ["attention", "self-attention", "recurrence", "convolution"],
            "expected_paper": "Attention Is All You Need"
        },

        # 3. Direct from GPT-3 title
        {
            "question": "What are few-shot learners?",
            "should_answer": True,
            "expected_contains": ["language model", "few-shot", "learning"],
            "expected_paper": "Language Models are Few-Shot Learners"
        },

        # 4. From MobileNetV2 title
        {
            "question": "What is MobileNetV2 about?",
            "should_answer": True,
            "expected_contains": ["inverted residual", "bottleneck", "mobile"],
            "expected_paper": "MobileNetV2"
        },

        # 5. Search by "transformer" keyword
        {
            "question": "Tell me about the Transformer model",
            "should_answer": True,
            "expected_contains": ["attention", "transformer"],
            "expected_paper": "Attention Is All You Need"
        },

        # 6. Search by "language model"
        {
            "question": "What papers discuss language models?",
            "should_answer": True,
            "expected_contains": ["language model", "GPT", "few-shot"],
            "expected_paper": "Language Models are Few-Shot Learners"
        },

        # 7. Author search
        {
            "question": "What paper did Ashish Vaswani author?",
            "should_answer": True,
            "expected_contains": ["Attention", "Transformer"],
            "expected_paper": "Attention Is All You Need"
        },

        # === SHOULD REFUSE (3) ===
        # These should NOT answer or should say "don't have info"

        # 8. Comparison requiring deep analysis (info not in key_finding)
        {
            "question": "Which is better, Transformer or LSTM?",
            "should_answer": False,
            "reason": "Comparison not in papers"
        },

        # 9. Specific technical detail not in key_finding
        {
            "question": "What is the exact learning rate used in GPT-3 training?",
            "should_answer": False,
            "reason": "Technical detail not in key findings"
        },

        # 10. Completely out of scope
        {
            "question": "What is the capital of France?",
            "should_answer": False,
            "reason": "Out of scope"
        },
    ]

    print(f"Testing {len(test_questions)} questions")
    print(f"  Answerable: 7")
    print(f"  Should refuse: 3")
    print()

    # Initialize pipeline
    pipeline = QAPipeline()

    # Run questions
    results = []
    for test in test_questions:
        result = pipeline.ask(test["question"])
        result["test_case"] = test
        results.append(result)

    print()
    print("="*70)
    print("DETAILED RESULTS")
    print("="*70)
    print()

    # Analyze results
    correct_answers = 0
    correct_refusals = 0
    incorrect_answers = 0
    incorrect_refusals = 0
    citations_present = 0
    correct_citations = 0

    for i, result in enumerate(results, 1):
        test_case = result["test_case"]
        question = result['question']
        should_answer = test_case.get("should_answer", True)

        print(f"Question {i}: {question}")
        print("-"*70)
        print(f"Expected: {'Answer' if should_answer else 'Refuse'}")

        if result['success']:
            answer = result['answer']
            citations = result['citations']
            papers_found = result['steps']['retrieval']['papers_found']

            # Check if answered or refused
            is_refusal = (
                "don't have enough information" in answer.lower() or
                "couldn't find" in answer.lower() or
                "cannot answer" in answer.lower() or
                papers_found == 0
            )

            print(f"Actual: {'Refused' if is_refusal else 'Answered'}")
            print()
            print(f"Answer: {answer[:200]}{'...' if len(answer) > 200 else ''}")
            print()

            # Evaluate based on what should happen
            if should_answer:
                # Should have answered
                if not is_refusal:
                    # Check for expected content
                    expected_terms = test_case.get("expected_contains", [])
                    found_terms = [term for term in expected_terms
                                  if term.lower() in answer.lower()]

                    # Check for correct citation
                    expected_paper = test_case.get("expected_paper", "")
                    has_correct_citation = any(expected_paper.lower() in cite.lower()
                                              for cite in citations)

                    if found_terms or has_correct_citation:
                        print(f"✅ CORRECT: Answered appropriately")
                        correct_answers += 1

                        if citations:
                            citations_present += 1
                            print(f"✅ Has citations: {citations}")

                            if has_correct_citation:
                                correct_citations += 1
                                print(f"✅ Correct citation: {expected_paper}")
                            else:
                                print(f"⚠️  Citations don't match expected paper: {expected_paper}")
                        else:
                            print(f"❌ Missing citations")
                    else:
                        print(f"⚠️  WEAK: Answered but missing expected content")
                        print(f"   Expected terms: {expected_terms}")
                        print(f"   Found: {found_terms}")
                        incorrect_answers += 1
                else:
                    print(f"❌ INCORRECT: Should have answered but refused")
                    print(f"   Reason: {test_case.get('reason', 'N/A')}")
                    incorrect_refusals += 1
            else:
                # Should have refused
                if is_refusal:
                    print(f"✅ CORRECT: Appropriately refused")
                    print(f"   Reason: {test_case.get('reason')}")
                    correct_refusals += 1
                else:
                    print(f"❌ INCORRECT: Should have refused but answered")
                    incorrect_answers += 1

            print(f"Papers retrieved: {papers_found}")
            print(f"Duration: {result['duration']:.2f}s")

        else:
            print(f"❌ Pipeline failed: {result.get('error')}")

        print()

    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print()

    total_questions = len(results)
    should_answer_count = sum(1 for r in results if r["test_case"].get("should_answer", True))
    should_refuse_count = total_questions - should_answer_count

    print(f"Total questions: {total_questions}")
    print(f"  Should answer: {should_answer_count}")
    print(f"  Should refuse: {should_refuse_count}")
    print()

    print("Performance:")
    print(f"  Correct answers: {correct_answers}/{should_answer_count} ({correct_answers/should_answer_count:.1%})")
    print(f"  Correct refusals: {correct_refusals}/{should_refuse_count} ({correct_refusals/should_refuse_count:.1%})")
    print(f"  Incorrect (answered when should refuse): {incorrect_answers}")
    print(f"  Incorrect (refused when should answer): {incorrect_refusals}")
    print()

    print("Citations:")
    print(f"  Questions with citations: {citations_present}/{correct_answers}")
    if correct_answers > 0:
        citation_coverage = citations_present / correct_answers
        print(f"  Citation coverage: {citation_coverage:.1%}")
    print(f"  Correct citations: {correct_citations}/{correct_answers}")
    if correct_answers > 0:
        citation_accuracy = correct_citations / correct_answers
        print(f"  Citation accuracy: {citation_accuracy:.1%}")
    print()

    # Overall accuracy
    total_correct = correct_answers + correct_refusals
    overall_accuracy = total_correct / total_questions
    print(f"Overall accuracy: {total_correct}/{total_questions} ({overall_accuracy:.1%})")
    print()

    # Phase 1.2 Go/No-Go
    print("="*70)
    print("PHASE 1.2 GO/NO-GO DECISION")
    print("="*70)
    print()

    # Criteria
    answers_enough = correct_answers >= 5  # ≥5/7 answerable questions correct
    citation_coverage_ok = (citations_present / correct_answers if correct_answers > 0 else 0) >= 0.8
    citation_accuracy_ok = (correct_citations / correct_answers if correct_answers > 0 else 0) >= 0.7
    refusal_ok = correct_refusals >= 2  # ≥2/3 refusals correct
    overall_ok = overall_accuracy >= 0.7  # ≥70% overall

    print(f"1. Answers enough questions (≥5/7 answerable)")
    print(f"   Result: {correct_answers}/7")
    print(f"   {'✅ PASS' if answers_enough else '❌ FAIL'}")
    print()

    print(f"2. Citation coverage (≥80% of answers)")
    print(f"   Result: {citations_present}/{correct_answers} = {citations_present/correct_answers if correct_answers > 0 else 0:.1%}")
    print(f"   {'✅ PASS' if citation_coverage_ok else '❌ FAIL'}")
    print()

    print(f"3. Citation accuracy (≥70% cite correct paper)")
    print(f"   Result: {correct_citations}/{correct_answers} = {correct_citations/correct_answers if correct_answers > 0 else 0:.1%}")
    print(f"   {'✅ PASS' if citation_accuracy_ok else '⚠️  WARNING'}")
    print()

    print(f"4. Appropriate refusals (≥2/3)")
    print(f"   Result: {correct_refusals}/3")
    print(f"   {'✅ PASS' if refusal_ok else '⚠️  WARNING'}")
    print()

    print(f"5. Overall accuracy (≥70%)")
    print(f"   Result: {total_correct}/{total_questions} = {overall_accuracy:.1%}")
    print(f"   {'✅ PASS' if overall_ok else '❌ FAIL'}")
    print()

    # Final decision
    blockers_passed = answers_enough and citation_coverage_ok and overall_ok
    warnings = not (citation_accuracy_ok and refusal_ok)

    print("="*70)
    if blockers_passed:
        if warnings:
            print("⚠️  CONDITIONAL GO: Core criteria met, review warnings")
        else:
            print("✅ GO DECISION: All Phase 1.2 criteria MET")
        print("   Q&A pipeline ready for Phase 2")
    else:
        print("❌ NO-GO DECISION: Phase 1.2 criteria NOT MET")
        print("   Need to improve retrieval, answers, or citations")

    print("="*70)


if __name__ == "__main__":
    main()

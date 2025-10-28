"""
Comprehensive Relationship Detection Test - Phase 2.1

Tests all three relationship types with synthetic test cases:
- supports: 5 cases
- contradicts: 5 cases
- extends: 5 cases
"""

import sys
from pathlib import Path
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.ingestion.relationship_agent import RelationshipAgent


def main():
    """Test relationship detection with comprehensive test cases."""

    print("="*70)
    print("COMPREHENSIVE RELATIONSHIP DETECTION TEST - PHASE 2.1")
    print("="*70)
    print()

    # Initialize agent
    relationship_agent = RelationshipAgent()

    # Test cases: (paper_a, paper_b, expected_relationship)
    test_cases = [
        # ===== SUPPORTS (5 cases) =====
        {
            "type": "supports",
            "paper_a": {
                "title": "Attention Is All You Need",
                "authors": ["Vaswani", "Shazeer", "Parmar"],
                "key_finding": "The Transformer architecture using self-attention achieves 28.4 BLEU on WMT 2014 English-to-German translation."
            },
            "paper_b": {
                "title": "Transformers for Machine Translation",
                "authors": ["Smith", "Johnson"],
                "key_finding": "Transformer models achieve state-of-the-art results on translation tasks, with BLEU scores exceeding 27 on WMT benchmarks."
            },
            "reason": "Both papers show Transformer achieves high BLEU scores on translation"
        },
        {
            "type": "supports",
            "paper_a": {
                "title": "Deep Residual Learning for Image Recognition",
                "authors": ["He", "Zhang", "Ren"],
                "key_finding": "Residual networks with skip connections enable training of very deep networks and achieve top-1 accuracy of 78.5% on ImageNet."
            },
            "paper_b": {
                "title": "ResNet Architectures for Computer Vision",
                "authors": ["Brown", "Davis"],
                "key_finding": "Residual connections improve training stability and our ResNet variants achieve 77-79% top-1 accuracy on ImageNet classification."
            },
            "reason": "Both papers validate ResNet effectiveness with similar ImageNet accuracy"
        },
        {
            "type": "supports",
            "paper_a": {
                "title": "BERT: Pre-training of Deep Bidirectional Transformers",
                "authors": ["Devlin", "Chang", "Lee"],
                "key_finding": "BERT pre-training improves performance on 11 NLP tasks, achieving 93.2 F1 on SQuAD."
            },
            "paper_b": {
                "title": "RoBERTa: A Robustly Optimized BERT Approach",
                "authors": ["Liu", "Ott"],
                "key_finding": "Optimized BERT training achieves strong results across NLP benchmarks, with 94.6 F1 on SQuAD."
            },
            "reason": "Both papers show BERT-style pre-training works well, similar SQuAD scores"
        },
        {
            "type": "supports",
            "paper_a": {
                "title": "Diffusion Models Beat GANs on Image Synthesis",
                "authors": ["Dhariwal", "Nichol"],
                "key_finding": "Diffusion models achieve FID of 2.9 on ImageNet 256x256, outperforming GANs."
            },
            "paper_b": {
                "title": "Improved Diffusion Probabilistic Models",
                "authors": ["Nichol", "Dhariwal"],
                "key_finding": "Diffusion models generate high-quality images with FID scores below 3.0 on ImageNet."
            },
            "reason": "Both papers report diffusion models achieving FID < 3 on ImageNet"
        },
        {
            "type": "supports",
            "paper_a": {
                "title": "Scaling Laws for Neural Language Models",
                "authors": ["Kaplan", "McCandlish"],
                "key_finding": "Language model performance improves predictably with scale, following power law relationships."
            },
            "paper_b": {
                "title": "Chinchilla: Training Compute-Optimal Large Language Models",
                "authors": ["Hoffmann", "Borgeaud"],
                "key_finding": "Model performance scales predictably with compute budget, confirming scaling law predictions."
            },
            "reason": "Both papers validate scaling laws for LLMs"
        },

        # ===== CONTRADICTS (5 cases) =====
        {
            "type": "contradicts",
            "paper_a": {
                "title": "Batch Normalization: Accelerating Deep Network Training",
                "authors": ["Ioffe", "Szegedy"],
                "key_finding": "Batch normalization significantly improves training speed and final accuracy across all tested architectures."
            },
            "paper_b": {
                "title": "Group Normalization Shows Batch Norm Limitations",
                "authors": ["Wu", "He"],
                "key_finding": "Batch normalization fails with small batch sizes and group normalization achieves better accuracy in these settings."
            },
            "reason": "First says BatchNorm always improves accuracy, second finds failure cases"
        },
        {
            "type": "contradicts",
            "paper_a": {
                "title": "Dropout: A Simple Way to Prevent Neural Networks from Overfitting",
                "authors": ["Srivastava", "Hinton"],
                "key_finding": "Dropout consistently reduces overfitting and improves generalization across various network architectures."
            },
            "paper_b": {
                "title": "When Does Dropout Hurt Performance?",
                "authors": ["Li", "Savarese"],
                "key_finding": "Dropout can hurt performance on modern architectures with batch normalization, reducing final accuracy by 2-3%."
            },
            "reason": "First claims dropout always helps, second shows it can hurt"
        },
        {
            "type": "contradicts",
            "paper_a": {
                "title": "Sim-to-Real Transfer with Domain Randomization",
                "authors": ["Tobin", "Fong"],
                "key_finding": "Domain randomization enables reliable sim-to-real transfer for robotic manipulation with 90% success rate."
            },
            "paper_b": {
                "title": "Domain Randomization Failure Cases in Robotics",
                "authors": ["Chen", "Kumar"],
                "key_finding": "Domain randomization shows poor sim-to-real transfer in our experiments, achieving only 45% success rate on manipulation tasks."
            },
            "reason": "First reports 90% success, second reports 45% - contradictory results"
        },
        {
            "type": "contradicts",
            "paper_a": {
                "title": "Fine-tuning Pre-trained Models Outperforms Training from Scratch",
                "authors": ["Howard", "Ruder"],
                "key_finding": "Fine-tuning pre-trained language models consistently outperforms training from scratch across all NLP tasks."
            },
            "paper_b": {
                "title": "Training from Scratch Matches Pre-training on Small Datasets",
                "authors": ["Zhang", "Wallace"],
                "key_finding": "On datasets with fewer than 10K examples, training from scratch achieves equal or better performance than fine-tuning."
            },
            "reason": "First claims fine-tuning always better, second finds cases where it's not"
        },
        {
            "type": "contradicts",
            "paper_a": {
                "title": "Large Batch Training of Convolutional Networks",
                "authors": ["You", "Gitman"],
                "key_finding": "Large batch sizes (up to 32K) maintain accuracy while reducing training time when learning rate is scaled appropriately."
            },
            "paper_b": {
                "title": "On the Inadequacy of Large Batch Training",
                "authors": ["Keskar", "Mudigere"],
                "key_finding": "Large batch training leads to poor generalization, with test accuracy dropping 5% when batch size exceeds 1024."
            },
            "reason": "First says large batches work with proper tuning, second says they hurt generalization"
        },

        # ===== NONE / UNRELATED (5 cases) =====
        {
            "type": "none",
            "paper_a": {
                "title": "Attention Is All You Need",
                "authors": ["Vaswani", "Shazeer"],
                "key_finding": "The Transformer architecture using self-attention achieves 28.4 BLEU on WMT 2014 English-to-German translation."
            },
            "paper_b": {
                "title": "MobileNetV2: Inverted Residuals and Linear Bottlenecks",
                "authors": ["Sandler", "Howard"],
                "key_finding": "MobileNetV2 uses inverted residuals to improve efficiency, achieving better accuracy with fewer FLOPs on mobile devices."
            },
            "reason": "Different domains: NLP translation vs mobile computer vision"
        },
        {
            "type": "none",
            "paper_a": {
                "title": "Deep Reinforcement Learning for Robotic Manipulation",
                "authors": ["Levine", "Finn"],
                "key_finding": "Deep RL enables robots to learn grasping skills with 85% success rate through trial and error."
            },
            "paper_b": {
                "title": "BERT: Pre-training of Deep Bidirectional Transformers",
                "authors": ["Devlin", "Chang"],
                "key_finding": "BERT pre-training improves performance on 11 NLP tasks, achieving 93.2 F1 on SQuAD."
            },
            "reason": "Different domains: robotics vs NLP"
        },
        {
            "type": "none",
            "paper_a": {
                "title": "Quantum Computing for Chemistry Simulations",
                "authors": ["Aspuru-Guzik", "Whitfield"],
                "key_finding": "Quantum algorithms can simulate molecular energies with exponential speedup over classical methods."
            },
            "paper_b": {
                "title": "Diffusion Models for Image Synthesis",
                "authors": ["Dhariwal", "Nichol"],
                "key_finding": "Diffusion models achieve FID of 2.9 on ImageNet 256x256, outperforming GANs."
            },
            "reason": "Different domains: quantum computing vs computer vision"
        },
        {
            "type": "none",
            "paper_a": {
                "title": "Graph Neural Networks for Social Network Analysis",
                "authors": ["Hamilton", "Ying"],
                "key_finding": "GNNs can predict user connections with 89% accuracy on social graphs."
            },
            "paper_b": {
                "title": "Speech Recognition with Convolutional Neural Networks",
                "authors": ["Abdel-Hamid", "Mohamed"],
                "key_finding": "CNNs reduce word error rate to 16.5% on TIMIT speech recognition benchmark."
            },
            "reason": "Different domains: social networks vs speech recognition"
        },
        {
            "type": "none",
            "paper_a": {
                "title": "Medical Image Segmentation with U-Net",
                "authors": ["Ronneberger", "Fischer"],
                "key_finding": "U-Net architecture achieves 92% IoU on medical image segmentation tasks."
            },
            "paper_b": {
                "title": "Recommender Systems with Matrix Factorization",
                "authors": ["Koren", "Bell"],
                "key_finding": "Matrix factorization improves recommendation accuracy by 15% on Netflix dataset."
            },
            "reason": "Different domains: medical imaging vs recommender systems"
        },

        # ===== EXTENDS (5 cases) =====
        {
            "type": "extends",
            "paper_a": {
                "title": "Language Models are Few-Shot Learners",
                "authors": ["Brown", "Mann", "Ryder"],
                "key_finding": "GPT-3, a 175B parameter language model, demonstrates strong few-shot learning without task-specific fine-tuning."
            },
            "paper_b": {
                "title": "Attention Is All You Need",
                "authors": ["Vaswani", "Shazeer"],
                "key_finding": "The Transformer architecture based solely on attention mechanisms achieves state-of-the-art translation quality."
            },
            "reason": "GPT-3 builds upon and scales the Transformer architecture"
        },
        {
            "type": "extends",
            "paper_a": {
                "title": "DALL-E 2: Hierarchical Text-Conditional Image Generation",
                "authors": ["Ramesh", "Dhariwal"],
                "key_finding": "DALL-E 2 generates high-fidelity images from text using diffusion models and CLIP embeddings."
            },
            "paper_b": {
                "title": "Diffusion Models Beat GANs on Image Synthesis",
                "authors": ["Dhariwal", "Nichol"],
                "key_finding": "Diffusion models achieve FID of 2.9 on ImageNet, outperforming GANs."
            },
            "reason": "DALL-E 2 extends diffusion models to text-conditional generation"
        },
        {
            "type": "extends",
            "paper_a": {
                "title": "MobileNetV2: Inverted Residuals and Linear Bottlenecks",
                "authors": ["Sandler", "Howard"],
                "key_finding": "MobileNetV2 uses inverted residuals to improve efficiency over MobileNetV1, achieving better accuracy with fewer FLOPs."
            },
            "paper_b": {
                "title": "MobileNets: Efficient Convolutional Neural Networks",
                "authors": ["Howard", "Zhu"],
                "key_finding": "MobileNet uses depthwise separable convolutions to reduce computation while maintaining accuracy on mobile devices."
            },
            "reason": "MobileNetV2 extends MobileNetV1 with architectural improvements"
        },
        {
            "type": "extends",
            "paper_a": {
                "title": "InstructGPT: Training Language Models to Follow Instructions",
                "authors": ["Ouyang", "Wu"],
                "key_finding": "Instruction fine-tuning with RLHF improves alignment and makes models more helpful and harmless."
            },
            "paper_b": {
                "title": "Language Models are Few-Shot Learners",
                "authors": ["Brown", "Mann"],
                "key_finding": "GPT-3 demonstrates strong few-shot learning without task-specific fine-tuning."
            },
            "reason": "InstructGPT extends GPT-3 with instruction following via RLHF"
        },
        {
            "type": "extends",
            "paper_a": {
                "title": "ViT: An Image is Worth 16x16 Words",
                "authors": ["Dosovitskiy", "Beyer"],
                "key_finding": "Vision Transformers applied directly to image patches match or exceed CNN performance on ImageNet when pre-trained on large datasets."
            },
            "paper_b": {
                "title": "Attention Is All You Need",
                "authors": ["Vaswani", "Shazeer"],
                "key_finding": "The Transformer architecture achieves state-of-the-art results on machine translation."
            },
            "reason": "ViT extends Transformers from NLP to computer vision"
        },
    ]

    # Run tests
    results = []

    print(f"Testing {len(test_cases)} relationship pairs")
    print(f"  - supports: 5 cases")
    print(f"  - contradicts: 5 cases")
    print(f"  - extends: 5 cases")
    print(f"  - none (unrelated): 5 cases")
    print()

    for i, test_case in enumerate(test_cases, 1):
        expected_type = test_case["type"]
        paper_a = test_case["paper_a"]
        paper_b = test_case["paper_b"]

        print(f"Test {i}/{len(test_cases)}: {expected_type.upper()}")
        print("-"*70)
        print(f"Paper A: {paper_a['title'][:55]}...")
        print(f"Paper B: {paper_b['title'][:55]}...")
        print(f"Reason: {test_case['reason']}")
        print()

        # Detect relationship
        result = relationship_agent.detect_relationship(paper_a, paper_b)

        # Add delay to avoid rate limits (10 req/min = 6 second spacing)
        time.sleep(7)

        detected_type = result['relationship_type']
        confidence = result['confidence']
        evidence = result['evidence']

        print(f"Expected: {expected_type}")
        print(f"Detected: {detected_type} (confidence: {confidence:.2f})")
        print(f"Evidence: {evidence}")
        print()

        # Evaluate
        is_correct = detected_type == expected_type and confidence >= 0.6

        if is_correct:
            print("✅ CORRECT")
        else:
            print(f"❌ INCORRECT")
            if detected_type != expected_type:
                print(f"   Wrong type: expected {expected_type}, got {detected_type}")
            if confidence < 0.6:
                print(f"   Low confidence: {confidence:.2f} < 0.6")

        print()

        results.append({
            'test_num': i,
            'expected': expected_type,
            'detected': detected_type,
            'confidence': confidence,
            'correct': is_correct
        })

    # Summary
    print("="*70)
    print("SUMMARY BY RELATIONSHIP TYPE")
    print("="*70)
    print()

    for rel_type in ['supports', 'contradicts', 'extends', 'none']:
        type_results = [r for r in results if r['expected'] == rel_type]
        correct = sum(1 for r in type_results if r['correct'])
        total = len(type_results)
        accuracy = correct / total if total > 0 else 0

        print(f"{rel_type.upper()}:")
        print(f"  Accuracy: {correct}/{total} ({accuracy:.1%})")

        if total > 0:
            avg_confidence = sum(r['confidence'] for r in type_results) / total
            print(f"  Avg confidence: {avg_confidence:.2f}")

        # Show failures
        failures = [r for r in type_results if not r['correct']]
        if failures:
            print(f"  Failed tests: {[r['test_num'] for r in failures]}")
        print()

    # Overall summary
    print("="*70)
    print("OVERALL SUMMARY")
    print("="*70)
    print()

    total_correct = sum(1 for r in results if r['correct'])
    total_tests = len(results)
    overall_accuracy = total_correct / total_tests

    print(f"Total tests: {total_tests}")
    print(f"Correct: {total_correct}/{total_tests} ({overall_accuracy:.1%})")
    print()

    # Breakdown by error type
    wrong_type = sum(1 for r in results if r['detected'] != r['expected'])
    low_confidence = sum(1 for r in results if r['confidence'] < 0.6 and r['detected'] == r['expected'])

    print(f"Wrong relationship type: {wrong_type}")
    print(f"Correct type but low confidence: {low_confidence}")
    print()

    # Phase 2.1 Go/No-Go
    print("="*70)
    print("PHASE 2.1 GO/NO-GO DECISION")
    print("="*70)
    print()

    print("Criteria:")
    print()

    # Criterion 1: Can detect "supports"
    supports_accuracy = sum(1 for r in results if r['expected'] == 'supports' and r['correct']) / 5
    supports_pass = supports_accuracy >= 0.6
    print(f"1. Can detect 'supports' relationship (≥60%)")
    print(f"   Result: {supports_accuracy:.1%}")
    print(f"   {'✅ PASS' if supports_pass else '❌ FAIL'}")
    print()

    # Criterion 2: Can detect "contradicts"
    contradicts_accuracy = sum(1 for r in results if r['expected'] == 'contradicts' and r['correct']) / 5
    contradicts_pass = contradicts_accuracy >= 0.6
    print(f"2. Can detect 'contradicts' relationship (≥60%)")
    print(f"   Result: {contradicts_accuracy:.1%}")
    print(f"   {'✅ PASS' if contradicts_pass else '❌ FAIL'}")
    print()

    # Criterion 3: Can detect "extends"
    extends_accuracy = sum(1 for r in results if r['expected'] == 'extends' and r['correct']) / 5
    extends_pass = extends_accuracy >= 0.6
    print(f"3. Can detect 'extends' relationship (≥60%)")
    print(f"   Result: {extends_accuracy:.1%}")
    print(f"   {'✅ PASS' if extends_pass else '❌ FAIL'}")
    print()

    # Criterion 4: Can detect "none" (unrelated)
    none_accuracy = sum(1 for r in results if r['expected'] == 'none' and r['correct']) / 5
    none_pass = none_accuracy >= 0.6
    print(f"4. Can detect 'none' / unrelated (≥60%)")
    print(f"   Result: {none_accuracy:.1%}")
    print(f"   {'✅ PASS' if none_pass else '❌ FAIL'}")
    print()

    # Criterion 5: Overall accuracy
    overall_pass = overall_accuracy >= 0.6
    print(f"5. Overall accuracy (≥60%)")
    print(f"   Result: {overall_accuracy:.1%}")
    print(f"   {'✅ PASS' if overall_pass else '❌ FAIL'}")
    print()

    # Final decision
    all_pass = supports_pass and contradicts_pass and extends_pass and none_pass and overall_pass

    print("="*70)
    if all_pass:
        print("✅ GO DECISION: All Phase 2.1 criteria MET")
        print("   Relationship detection is accurate across all types")
    elif overall_pass:
        print("⚠️  CONDITIONAL GO: Overall accuracy acceptable")
        print("   Some relationship types may need threshold tuning")
    else:
        print("❌ NO-GO DECISION: Phase 2.1 criteria NOT MET")
        print("   Relationship detection accuracy too low")
    print("="*70)


if __name__ == "__main__":
    main()

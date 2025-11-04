#!/usr/bin/env python3
"""
Seed demo papers from arXiv.

Downloads and ingests 20-30 high-impact ML/AI papers to create a compelling demo.
Papers are chosen to showcase different aspects:
- Foundational models (Transformers, BERT, GPT)
- Computer vision (ResNet, CLIP, Vision Transformers)
- Efficiency (LoRA, Quantization)
- Agents and reasoning
- Reinforcement learning
"""

import sys
import os
import requests
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipelines.ingestion_pipeline import IngestionPipeline

# Curated list of impactful papers
DEMO_PAPERS = [
    # Foundational Transformer papers
    {
        "arxiv_id": "1706.03762",
        "title": "Attention Is All You Need",
        "year": 2017,
        "topic": "transformers"
    },
    {
        "arxiv_id": "1810.04805",
        "title": "BERT: Pre-training of Deep Bidirectional Transformers",
        "year": 2018,
        "topic": "language-models"
    },
    {
        "arxiv_id": "2005.14165",
        "title": "Language Models are Few-Shot Learners (GPT-3)",
        "year": 2020,
        "topic": "language-models"
    },
    {
        "arxiv_id": "1801.04381",
        "title": "Universal Transformers",
        "year": 2018,
        "topic": "transformers"
    },

    # Vision papers
    {
        "arxiv_id": "1512.03385",
        "title": "Deep Residual Learning for Image Recognition (ResNet)",
        "year": 2015,
        "topic": "computer-vision"
    },
    {
        "arxiv_id": "2010.11929",
        "title": "An Image is Worth 16x16 Words: Transformers for Image Recognition (ViT)",
        "year": 2020,
        "topic": "computer-vision"
    },
    {
        "arxiv_id": "2103.00020",
        "title": "Learning Transferable Visual Models From Natural Language Supervision (CLIP)",
        "year": 2021,
        "topic": "multimodal"
    },

    # Efficiency and optimization
    {
        "arxiv_id": "2106.09685",
        "title": "LoRA: Low-Rank Adaptation of Large Language Models",
        "year": 2021,
        "topic": "efficiency"
    },
    {
        "arxiv_id": "1910.01108",
        "title": "ZeRO: Memory Optimizations Toward Training Trillion Parameter Models",
        "year": 2019,
        "topic": "efficiency"
    },
    {
        "arxiv_id": "2210.17323",
        "title": "GLM-130B: An Open Bilingual Pre-trained Model",
        "year": 2022,
        "topic": "language-models"
    },

    # Recent influential papers
    {
        "arxiv_id": "2303.08774",
        "title": "GPT-4 Technical Report",
        "year": 2023,
        "topic": "language-models"
    },
    {
        "arxiv_id": "2302.13971",
        "title": "LLaMA: Open and Efficient Foundation Language Models",
        "year": 2023,
        "topic": "language-models"
    },
    {
        "arxiv_id": "2307.09288",
        "title": "Llama 2: Open Foundation and Fine-Tuned Chat Models",
        "year": 2023,
        "topic": "language-models"
    },

    # Reinforcement Learning
    {
        "arxiv_id": "1707.06347",
        "title": "Proximal Policy Optimization Algorithms (PPO)",
        "year": 2017,
        "topic": "reinforcement-learning"
    },
    {
        "arxiv_id": "1312.5602",
        "title": "Playing Atari with Deep Reinforcement Learning (DQN)",
        "year": 2013,
        "topic": "reinforcement-learning"
    },

    # Reasoning and agents
    {
        "arxiv_id": "2201.11903",
        "title": "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models",
        "year": 2022,
        "topic": "reasoning"
    },
    {
        "arxiv_id": "2210.03629",
        "title": "ReAct: Synergizing Reasoning and Acting in Language Models",
        "year": 2022,
        "topic": "agents"
    },
    {
        "arxiv_id": "2305.10601",
        "title": "Tree of Thoughts: Deliberate Problem Solving with Large Language Models",
        "year": 2023,
        "topic": "reasoning"
    },

    # Multimodal
    {
        "arxiv_id": "2304.08485",
        "title": "Visual Instruction Tuning (LLaVA)",
        "year": 2023,
        "topic": "multimodal"
    },
    {
        "arxiv_id": "2303.11366",
        "title": "GPT-4V(ision) System Card",
        "year": 2023,
        "topic": "multimodal"
    },

    # Additional influential papers
    {
        "arxiv_id": "2005.11401",
        "title": "Denoising Diffusion Probabilistic Models",
        "year": 2020,
        "topic": "generative-models"
    },
    {
        "arxiv_id": "1910.10683",
        "title": "Exploring the Limits of Transfer Learning with T5",
        "year": 2019,
        "topic": "language-models"
    },
    {
        "arxiv_id": "2203.02155",
        "title": "Training Compute-Optimal Large Language Models (Chinchilla)",
        "year": 2022,
        "topic": "language-models"
    },
]


def download_paper(arxiv_id: str, output_dir: Path) -> str:
    """Download paper from arXiv."""
    output_file = output_dir / f"{arxiv_id.replace('.', '_')}.pdf"

    if output_file.exists():
        print(f"  ✓ Already downloaded: {arxiv_id}")
        return str(output_file)

    url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    print(f"  Downloading: {url}")

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        with open(output_file, 'wb') as f:
            f.write(response.content)

        print(f"  ✓ Downloaded: {output_file.name} ({len(response.content) / 1024:.1f} KB)")
        return str(output_file)

    except Exception as e:
        print(f"  ✗ Failed to download {arxiv_id}: {str(e)}")
        return None


def main():
    """Download and ingest demo papers."""
    print("=" * 70)
    print("SEEDING DEMO PAPERS")
    print("=" * 70)
    print(f"\nPapers to ingest: {len(DEMO_PAPERS)}")
    print()

    # Create output directory
    output_dir = Path("data/demo_papers")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize pipeline with relationship detection and alerting
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'research-intel-agents')
    pipeline = IngestionPipeline(
        project_id=project_id,
        enable_relationships=True,
        enable_alerting=False  # Disable for bulk ingestion
    )

    # Download and ingest papers
    success_count = 0
    skip_count = 0
    fail_count = 0

    for idx, paper_info in enumerate(DEMO_PAPERS, 1):
        arxiv_id = paper_info['arxiv_id']
        title = paper_info['title']

        print(f"\n[{idx}/{len(DEMO_PAPERS)}] {title}")
        print(f"  arXiv ID: {arxiv_id}")
        print(f"  Topic: {paper_info['topic']}")

        # Download paper
        pdf_path = download_paper(arxiv_id, output_dir)

        if not pdf_path:
            fail_count += 1
            continue

        # Ingest paper
        try:
            print(f"  Ingesting...")
            result = pipeline.ingest_paper(pdf_path, arxiv_id)

            if result['success']:
                if result['steps']['indexing'].get('already_exists'):
                    print(f"  ✓ Already indexed: {result.get('paper_id', 'unknown')}")
                    skip_count += 1
                else:
                    print(f"  ✓ Successfully ingested: {result.get('paper_id', 'unknown')}")
                    success_count += 1

                    # Show relationship detection if enabled
                    if 'relationship_detection' in result.get('steps', {}):
                        rel_count = result['steps']['relationship_detection'].get('relationship_count', 0)
                        if rel_count > 0:
                            print(f"    → Detected {rel_count} relationships")
            else:
                print(f"  ✗ Failed: {result.get('error', 'Unknown error')}")
                fail_count += 1

            # Rate limiting
            time.sleep(2)

        except Exception as e:
            print(f"  ✗ Error during ingestion: {str(e)}")
            fail_count += 1

    # Summary
    print("\n" + "=" * 70)
    print("SEEDING COMPLETE")
    print("=" * 70)
    print(f"\n✓ Successfully ingested: {success_count} papers")
    print(f"○ Already in database: {skip_count} papers")
    print(f"✗ Failed: {fail_count} papers")
    print(f"\nTotal papers in corpus: {success_count + skip_count}")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()

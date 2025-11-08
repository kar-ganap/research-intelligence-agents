#!/usr/bin/env python3
"""
Add influential papers to LG, CV, and AI categories.
Uses arXiv IDs that will automatically get proper metadata via arXiv API.
"""

import sys
import os
import time
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage.firestore_client import FirestoreClient
from scripts.backfill_paper_metadata import fetch_arxiv_metadata

logging.basicConfig(level=logging.INFO)

# Papers to add (arXiv will provide categories and metadata)
NEW_PAPERS = [
    # cs.LG papers (need 4)
    {
        "title": "Adam: A Method for Stochastic Optimization",
        "authors": ["Diederik P. Kingma", "Jimmy Ba"],
        "key_finding": "Introduced Adam optimizer combining advantages of AdaGrad and RMSProp with adaptive learning rates, becoming the default optimizer for deep learning.",
        "arxiv_id": "1412.6980"
    },
    {
        "title": "Batch Normalization: Accelerating Deep Network Training by Reducing Internal Covariate Shift",
        "authors": ["Sergey Ioffe", "Christian Szegedy"],
        "key_finding": "Introduced batch normalization to normalize layer inputs, enabling much higher learning rates and faster training while acting as regularization.",
        "arxiv_id": "1502.03167"
    },
    {
        "title": "Dropout: A Simple Way to Prevent Neural Networks from Overfitting",
        "authors": ["Nitish Srivastava", "Geoffrey Hinton", "Alex Krizhevsky", "Ilya Sutskever", "Ruslan Salakhutdinov"],
        "key_finding": "Introduced dropout regularization technique that randomly drops units during training, significantly reducing overfitting in neural networks.",
        "arxiv_id": "1207.0580"
    },
    {
        "title": "XGBoost: A Scalable Tree Boosting System",
        "authors": ["Tianqi Chen", "Carlos Guestrin"],
        "key_finding": "Introduced highly efficient gradient boosting implementation that became dominant in ML competitions, winning many Kaggle challenges.",
        "arxiv_id": "1603.02754"
    },

    # cs.CV papers (need 3)
    {
        "title": "You Only Look Once: Unified, Real-Time Object Detection",
        "authors": ["Joseph Redmon", "Santosh Divvala", "Ross Girshick", "Ali Farhadi"],
        "key_finding": "Introduced YOLO, the first single-shot object detector that frames detection as regression, achieving real-time speeds (45 FPS) while maintaining competitive accuracy.",
        "arxiv_id": "1506.02640"
    },
    {
        "title": "Mask R-CNN",
        "authors": ["Kaiming He", "Georgia Gkioxari", "Piotr Dollár", "Ross Girshick"],
        "key_finding": "Extended Faster R-CNN by adding a branch for predicting segmentation masks, enabling simultaneous object detection and instance segmentation.",
        "arxiv_id": "1703.06870"
    },
    {
        "title": "U-Net: Convolutional Networks for Biomedical Image Segmentation",
        "authors": ["Olaf Ronneberger", "Philipp Fischer", "Thomas Brox"],
        "key_finding": "Introduced U-Net architecture with symmetric encoder-decoder structure and skip connections, becoming standard for medical image segmentation.",
        "arxiv_id": "1505.04597"
    },

    # cs.AI papers (need 7)
    {
        "title": "Playing Atari with Deep Reinforcement Learning",
        "authors": ["Volodymyr Mnih", "Koray Kavukcuoglu", "David Silver", "Alex Graves", "Ioannis Antonoglou", "Daan Wierstra", "Martin Riedmiller"],
        "key_finding": "First deep learning model to successfully learn control policies directly from high-dimensional sensory input using Q-learning, achieving human-level performance on Atari games.",
        "arxiv_id": "1312.5602"
    },
    {
        "title": "Mastering the Game of Go with Deep Neural Networks and Tree Search",
        "authors": ["David Silver", "Aja Huang", "Chris J. Maddison", "Arthur Guez", "Laurent Sifre"],
        "key_finding": "AlphaGo combined deep neural networks with Monte Carlo tree search to defeat world champion Lee Sedol 4-1, solving the grand challenge of Go.",
        "arxiv_id": "1712.01815"
    },
    {
        "title": "Continuous Control with Deep Reinforcement Learning",
        "authors": ["Timothy P. Lillicrap", "Jonathan J. Hunt", "Alexander Pritzel", "Nicolas Heess", "Tom Erez", "Yuval Tassa", "David Silver", "Daan Wierstra"],
        "key_finding": "Introduced DDPG (Deep Deterministic Policy Gradient), an actor-critic algorithm that can learn policies in continuous action spaces using deep function approximators.",
        "arxiv_id": "1509.02971"
    },
    {
        "title": "Trust Region Policy Optimization",
        "authors": ["John Schulman", "Sergey Levine", "Philipp Moritz", "Michael I. Jordan", "Pieter Abbeel"],
        "key_finding": "Introduced TRPO, a policy gradient method that monotonically improves policy performance by constraining policy updates to a trust region.",
        "arxiv_id": "1502.05477"
    },
    {
        "title": "Asynchronous Methods for Deep Reinforcement Learning",
        "authors": ["Volodymyr Mnih", "Adrià Puigdomènech Badia", "Mehdi Mirza", "Alex Graves", "Timothy P. Lillicrap", "Tim Harley", "David Silver", "Koray Kavukcuoglu"],
        "key_finding": "Introduced A3C (Asynchronous Advantage Actor-Critic), enabling parallel training of RL agents on multi-core CPUs, significantly speeding up training.",
        "arxiv_id": "1602.01783"
    },
    {
        "title": "Human-level Control through Deep Reinforcement Learning",
        "authors": ["Volodymyr Mnih", "Koray Kavukcuoglu", "David Silver", "Andrei A. Rusu", "Joel Veness", "Marc G. Bellemare", "Alex Graves", "Martin Riedmiller", "Andreas K. Fidjeland", "Georg Ostrovski"],
        "key_finding": "Published in Nature, this extended the DQN work showing human-level performance across 49 Atari games using a single architecture and hyperparameters.",
        "arxiv_id": "1518"  # Nature paper, not on arXiv - will skip this
    },
    {
        "title": "Soft Actor-Critic: Off-Policy Maximum Entropy Deep Reinforcement Learning with a Stochastic Actor",
        "authors": ["Tuomas Haarnoja", "Aurick Zhou", "Pieter Abbeel", "Sergey Levine"],
        "key_finding": "Introduced SAC, an off-policy actor-critic algorithm based on maximum entropy RL that achieves state-of-the-art performance on continuous control benchmarks.",
        "arxiv_id": "1801.01290"
    },
]

def add_papers():
    """Add papers to the database directly via Firestore."""

    print(f"\n{'='*80}")
    print(f"ADDING PAPERS TO DATABASE")
    print(f"{'='*80}\n")

    # Initialize Firestore client
    firestore_client = FirestoreClient()

    success_count = 0
    skip_count = 0
    fail_count = 0

    for i, paper in enumerate(NEW_PAPERS, 1):
        # Skip papers without proper arXiv IDs
        if len(paper['arxiv_id']) < 6:
            print(f"[{i}/{len(NEW_PAPERS)}] Skipping: {paper['title'][:60]}...")
            print(f"  ⚠️  No valid arXiv ID\n")
            skip_count += 1
            continue

        print(f"[{i}/{len(NEW_PAPERS)}] Adding: {paper['title']}")
        print(f"  Authors: {', '.join(paper['authors'][:3])}{' et al.' if len(paper['authors']) > 3 else ''}")
        print(f"  ArXiv: {paper['arxiv_id']}")

        try:
            # Fetch metadata from arXiv
            print(f"  Fetching metadata from arXiv...")
            metadata = fetch_arxiv_metadata(paper['arxiv_id'])

            if not metadata:
                print(f"  ✗ Failed to fetch arXiv metadata\n")
                fail_count += 1
                continue

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
            print(f"  Category: {metadata.get('primary_category', 'unknown')}\n")
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
    print(f"Skipped: {skip_count}")
    print(f"Failed: {fail_count}")
    print(f"Total attempted: {len(NEW_PAPERS)}")
    print()

if __name__ == '__main__':
    add_papers()

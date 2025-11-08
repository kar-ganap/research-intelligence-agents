#!/usr/bin/env python3
"""
Add interesting relationships to make the graph more compelling for demo.

Adds:
1. Contradiction relationships between papers with different approaches
   (unidirectional: newer paper -> older paper)

Note: Respects temporal ordering - only creates relationships from newer to older papers.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage.firestore_client import FirestoreClient
from src.agents.ingestion.relationship_agent import get_paper_date
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_interesting_relationships():
    """Add compelling relationships for demo."""

    firestore_client = FirestoreClient()

    # Get all papers
    papers = firestore_client.get_all_papers()
    paper_map = {p['title']: p for p in papers}

    print(f"\n{'='*80}")
    print("ADDING INTERESTING RELATIONSHIPS")
    print(f"{'='*80}\n")

    # Track additions
    added = 0

    # 1. Add some contradictions (different RL approaches, optimization methods, etc.)
    contradictions = [
        {
            'source': 'Proximal Policy Optimization Algorithms',
            'target': 'Soft Actor-Critic: Off-Policy Maximum Entropy Deep Reinforcement Learning with a Stochastic Actor',
            'description': 'PPO (on-policy) contradicts SAC (off-policy) regarding sample efficiency: PPO requires more environment interactions but provides more stable training, while SAC claims superior sample efficiency through off-policy learning but with potential stability trade-offs.'
        },
        {
            'source': 'Batch Normalization: Accelerating Deep Network Training by Reducing Internal Covariate Shift',
            'target': 'LAYER NORMALIZATION',
            'description': 'Batch Normalization and Layer Normalization disagree on the normalization dimension: BatchNorm normalizes across the batch dimension (requiring batch statistics), while LayerNorm normalizes across features (independent of batch size), leading to different behavior in small batch or sequence scenarios.'
        },
    ]

    for contra in contradictions:
        source = paper_map.get(contra['source'])
        target = paper_map.get(contra['target'])

        if source and target:
            # Determine temporal ordering
            source_date = get_paper_date(source)
            target_date = get_paper_date(target)

            # Only create unidirectional relationship: newer -> older
            if source_date and target_date:
                if source_date >= target_date:
                    # Source is newer or same age, create source -> target
                    newer_paper = source
                    older_paper = target
                    direction_str = f"{contra['source'][:50]}... → {contra['target'][:50]}..."
                else:
                    # Target is newer, create target -> source
                    newer_paper = target
                    older_paper = source
                    direction_str = f"{contra['target'][:50]}... → {contra['source'][:50]}..."

                # Add unidirectional contradiction (newer -> older)
                firestore_client.db.collection('relationships').add({
                    'source_paper_id': newer_paper['paper_id'],
                    'target_paper_id': older_paper['paper_id'],
                    'relationship_type': 'contradicts',
                    'confidence': 0.75,
                    'evidence': contra['description']
                })

                added += 1
                print(f"✅ Added contradiction: {direction_str}")
                print(f"   ({newer_paper.get('published', 'unknown')[:10]} → {older_paper.get('published', 'unknown')[:10]})")
            else:
                # If no dates, skip (or could default to original order)
                logger.warning(f"⚠️  Skipping contradiction - missing publication dates")
                logger.warning(f"   {contra['source'][:50]}... vs {contra['target'][:50]}...")

    print(f"\n{'='*80}")
    print(f"SUMMARY: Added {added} relationships")
    print(f"{'='*80}\n")

    # Check final counts
    relationships = list(firestore_client.db.collection('relationships').stream())
    types = {}
    for rel in relationships:
        rel_data = rel.to_dict()
        rel_type = rel_data.get('relationship_type', 'unknown')
        types[rel_type] = types.get(rel_type, 0) + 1

    print("Final relationship breakdown:")
    for rel_type, count in sorted(types.items()):
        print(f"  {rel_type}: {count}")
    print()

if __name__ == "__main__":
    add_interesting_relationships()

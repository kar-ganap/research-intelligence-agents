"""Seed demo data to Firestore for testing."""
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage.firestore_client import FirestoreClient

def seed_demo_data():
    """Add sample papers and relationships to Firestore."""
    client = FirestoreClient()
    
    # Sample papers
    papers = [
        {
            "paper_id": "2312.00001",
            "title": "Attention Is All You Need",
            "authors": ["Vaswani et al."],
            "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms.",
            "arxiv_url": "https://arxiv.org/abs/1706.03762",
            "pdf_url": "https://arxiv.org/pdf/1706.03762.pdf",
            "categories": ["cs.LG", "cs.CL"],
            "published_date": "2017-06-12",
            "ingested_at": datetime.utcnow().isoformat(),
            "status": "processed"
        },
        {
            "paper_id": "2312.00002",
            "title": "BERT: Pre-training of Deep Bidirectional Transformers",
            "authors": ["Devlin et al."],
            "abstract": "We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers. BERT is designed to pre-train deep bidirectional representations.",
            "arxiv_url": "https://arxiv.org/abs/1810.04805",
            "pdf_url": "https://arxiv.org/pdf/1810.04805.pdf",
            "categories": ["cs.CL"],
            "published_date": "2018-10-11",
            "ingested_at": datetime.utcnow().isoformat(),
            "status": "processed"
        },
        {
            "paper_id": "2312.00003",
            "title": "GPT-3: Language Models are Few-Shot Learners",
            "authors": ["Brown et al."],
            "abstract": "We demonstrate that scaling up language models greatly improves task-agnostic, few-shot performance. We train GPT-3, an autoregressive language model with 175 billion parameters.",
            "arxiv_url": "https://arxiv.org/abs/2005.14165",
            "pdf_url": "https://arxiv.org/pdf/2005.14165.pdf",
            "categories": ["cs.CL"],
            "published_date": "2020-05-28",
            "ingested_at": datetime.utcnow().isoformat(),
            "status": "processed"
        },
        {
            "paper_id": "2312.00004",
            "title": "ResNet: Deep Residual Learning for Image Recognition",
            "authors": ["He et al."],
            "abstract": "We present a residual learning framework to ease the training of networks that are substantially deeper than those used previously. We explicitly reformulate the layers as learning residual functions.",
            "arxiv_url": "https://arxiv.org/abs/1512.03385",
            "pdf_url": "https://arxiv.org/pdf/1512.03385.pdf",
            "categories": ["cs.CV"],
            "published_date": "2015-12-10",
            "ingested_at": datetime.utcnow().isoformat(),
            "status": "processed"
        },
        {
            "paper_id": "2312.00005",
            "title": "Generative Adversarial Networks",
            "authors": ["Goodfellow et al."],
            "abstract": "We propose a new framework for estimating generative models via an adversarial process. We simultaneously train two models: a generative model G and a discriminative model D.",
            "arxiv_url": "https://arxiv.org/abs/1406.2661",
            "pdf_url": "https://arxiv.org/pdf/1406.2661.pdf",
            "categories": ["cs.LG", "stat.ML"],
            "published_date": "2014-06-10",
            "ingested_at": datetime.utcnow().isoformat(),
            "status": "processed"
        }
    ]
    
    # Sample relationships
    relationships = [
        {
            "relationship_id": "rel_001",
            "source_paper_id": "2312.00002",
            "target_paper_id": "2312.00001",
            "relationship_type": "builds_on",
            "description": "BERT builds on the Transformer architecture introduced in 'Attention Is All You Need'",
            "confidence": 0.95,
            "detected_at": datetime.utcnow().isoformat()
        },
        {
            "relationship_id": "rel_002",
            "source_paper_id": "2312.00003",
            "target_paper_id": "2312.00001",
            "relationship_type": "builds_on",
            "description": "GPT-3 uses the Transformer architecture for autoregressive language modeling",
            "confidence": 0.92,
            "detected_at": datetime.utcnow().isoformat()
        },
        {
            "relationship_id": "rel_003",
            "source_paper_id": "2312.00003",
            "target_paper_id": "2312.00002",
            "relationship_type": "extends",
            "description": "GPT-3 extends ideas from BERT by scaling up model size for few-shot learning",
            "confidence": 0.88,
            "detected_at": datetime.utcnow().isoformat()
        }
    ]
    
    # Store papers
    print("Storing demo papers...")
    for paper in papers:
        client.store_paper(paper)
        print(f"  ✓ Stored: {paper['title'][:50]}...")
    
    # Store relationships
    print("\nStoring demo relationships...")
    for rel in relationships:
        client.store_relationship(rel)
        print(f"  ✓ Stored relationship: {rel['source_paper_id']} -> {rel['target_paper_id']} ({rel['relationship_type']})")
    
    print(f"\n✅ Successfully seeded {len(papers)} papers and {len(relationships)} relationships!")
    print("\nYou can now test the frontend at:")
    print("  https://frontend-338657477881.us-central1.run.app")

if __name__ == "__main__":
    seed_demo_data()

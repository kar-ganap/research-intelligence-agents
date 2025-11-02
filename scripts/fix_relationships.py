"""Fix demo relationships to use actual paper IDs from Firestore."""
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage.firestore_client import FirestoreClient

def fix_relationships():
    """Delete old relationships and create new ones with correct IDs."""
    client = FirestoreClient()

    # Get all papers
    papers = client.get_all_papers()
    print(f"Found {len(papers)} papers")

    # Find papers by title
    paper_map = {}
    for paper in papers:
        title_lower = paper['title'].lower()
        if 'attention is all you need' in title_lower and 'vaswani' in str(paper.get('authors', [])).lower():
            paper_map['transformer'] = paper['paper_id']
            print(f"  Transformer: {paper['paper_id']}")
        elif 'bert' in title_lower and 'devlin' in str(paper.get('authors', [])).lower():
            paper_map['bert'] = paper['paper_id']
            print(f"  BERT: {paper['paper_id']}")
        elif 'gpt-3' in title_lower or ('language models are few-shot' in title_lower and 'brown' in str(paper.get('authors', [])).lower()):
            paper_map['gpt3'] = paper['paper_id']
            print(f"  GPT-3: {paper['paper_id']}")

    if len(paper_map) < 3:
        print(f"\nWarning: Only found {len(paper_map)} out of 3 expected papers")
        return

    # Delete all existing relationships
    old_rels = client.get_all_relationships()
    print(f"\nDeleting {len(old_rels)} old relationships...")
    for rel in old_rels:
        # Firestore delete via collection reference
        from google.cloud import firestore
        db = client.db
        db.collection('relationships').document(rel.get('relationship_id', rel.get('id', 'unknown'))).delete()

    print("Old relationships deleted")

    # Create new relationships with correct IDs
    relationships = [
        {
            "relationship_id": "rel_001",
            "source_paper_id": paper_map['bert'],
            "target_paper_id": paper_map['transformer'],
            "relationship_type": "builds_on",
            "description": "BERT builds on the Transformer architecture introduced in 'Attention Is All You Need'",
            "confidence": 0.95,
            "detected_at": datetime.utcnow().isoformat()
        },
        {
            "relationship_id": "rel_002",
            "source_paper_id": paper_map['gpt3'],
            "target_paper_id": paper_map['transformer'],
            "relationship_type": "builds_on",
            "description": "GPT-3 uses the Transformer architecture for autoregressive language modeling",
            "confidence": 0.92,
            "detected_at": datetime.utcnow().isoformat()
        },
        {
            "relationship_id": "rel_003",
            "source_paper_id": paper_map['gpt3'],
            "target_paper_id": paper_map['bert'],
            "relationship_type": "extends",
            "description": "GPT-3 extends ideas from BERT by scaling up model size for few-shot learning",
            "confidence": 0.88,
            "detected_at": datetime.utcnow().isoformat()
        }
    ]

    print(f"\nStoring {len(relationships)} new relationships...")
    for rel in relationships:
        client.store_relationship(rel)
        print(f"  ✓ {rel['source_paper_id'][:8]}... -> {rel['target_paper_id'][:8]}... ({rel['relationship_type']})")

    print(f"\n✅ Successfully fixed relationships!")

if __name__ == "__main__":
    fix_relationships()

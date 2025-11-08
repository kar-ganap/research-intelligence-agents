"""Remove fake demo papers, keep only real ingested papers."""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage.firestore_client import FirestoreClient

def cleanup_demo_papers():
    """Delete demo papers that don't have actual PDF content."""
    client = FirestoreClient()

    # Get all papers
    papers = client.get_all_papers()
    print(f"Found {len(papers)} papers total")

    # Find papers without PDFs or key findings (demo papers)
    demo_papers = []
    real_papers = []

    for paper in papers:
        if not paper.get('pdf_path') or not paper.get('key_finding'):
            demo_papers.append(paper)
        else:
            real_papers.append(paper)

    print(f"\nDemo papers (to delete): {len(demo_papers)}")
    for p in demo_papers:
        print(f"  - {p['paper_id']}: {p['title'][:60]}")

    print(f"\nReal papers (to keep): {len(real_papers)}")
    for p in real_papers:
        print(f"  - {p['paper_id']}: {p['title'][:60]}")

    # Delete demo papers
    print(f"\nDeleting {len(demo_papers)} demo papers...")
    from google.cloud import firestore
    db = client.db

    for paper in demo_papers:
        paper_id = paper['paper_id']
        db.collection('papers').document(paper_id).delete()
        print(f"  ✓ Deleted {paper_id}")

    print(f"\n✅ Cleanup complete! {len(real_papers)} real papers remaining.")

if __name__ == "__main__":
    cleanup_demo_papers()

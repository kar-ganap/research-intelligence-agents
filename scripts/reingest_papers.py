"""
Re-ingest Papers - Update existing papers with improved key finding extraction
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.firestore_client import FirestoreClient
from src.tools.pdf_reader import read_pdf
from src.agents.ingestion.entity_agent import EntityAgent

def reingest_papers():
    """Re-ingest existing papers to get improved key findings."""

    print("=" * 70)
    print("RE-INGESTING PAPERS WITH IMPROVED EXTRACTION")
    print("=" * 70)
    print()

    firestore_client = FirestoreClient()
    entity_agent = EntityAgent()

    # Get all existing papers
    papers = firestore_client.get_all_papers()

    print(f"Found {len(papers)} papers to re-ingest\n")

    for i, paper in enumerate(papers, 1):
        title = paper.get('title', 'Unknown')
        pdf_path = paper.get('pdf_path', '')
        paper_id = paper.get('paper_id', '')

        print(f"{i}. Re-ingesting: {title[:60]}")
        print(f"   Paper ID: {paper_id}")
        print(f"   PDF Path: {pdf_path}")

        if not pdf_path or not Path(pdf_path).exists():
            print(f"   ⚠️  PDF not found at {pdf_path} - SKIPPING")
            print()
            continue

        try:
            # Read PDF
            pdf_data = read_pdf(pdf_path)
            paper_text = pdf_data.get('text', '')
            pdf_metadata = pdf_data.get('metadata', {})

            if not paper_text:
                print(f"   ⚠️  Could not extract text from PDF - SKIPPING")
                print()
                continue

            print(f"   ✓ Extracted {len(paper_text)} characters from PDF")

            # Extract entities with improved prompt
            extracted = entity_agent.extract(paper_text)

            # Show old vs new key finding
            old_key_finding = paper.get('key_finding', '')
            new_key_finding = extracted.get('key_finding', '')

            print(f"\n   OLD Key Finding:")
            print(f"   {old_key_finding[:150]}...")
            print(f"\n   NEW Key Finding:")
            print(f"   {new_key_finding[:300]}...")
            print()

            # Update in Firestore
            update_result = firestore_client.update_paper(
                paper_id=paper_id,
                updates={'key_finding': new_key_finding}
            )

            if update_result:
                print(f"   ✅ Updated key finding in Firestore")
            else:
                print(f"   ❌ Failed to update Firestore")

        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

        print()
        print("-" * 70)
        print()

    print("=" * 70)
    print("RE-INGESTION COMPLETE")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Run: python scripts/list_papers.py")
    print("2. Verify key findings now include metrics")
    print("3. Run: python scripts/test_confidence.py")


if __name__ == "__main__":
    reingest_papers()

"""
Add BERT Paper - Download and ingest BERT paper for testing
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import urllib.request
from src.pipelines.ingestion_pipeline import IngestionPipeline

def download_and_ingest_bert():
    """Download BERT paper and ingest it."""

    print("=" * 70)
    print("ADDING BERT PAPER TO CORPUS")
    print("=" * 70)
    print()

    # BERT paper: https://arxiv.org/abs/1810.04805
    arxiv_id = "1810.04805"
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    pdf_path = f"tests/fixtures/sample_papers/{arxiv_id}.pdf"

    # Create directory if needed
    Path(pdf_path).parent.mkdir(parents=True, exist_ok=True)

    # Download PDF
    print(f"1. Downloading BERT paper from ArXiv...")
    print(f"   URL: {pdf_url}")

    try:
        urllib.request.urlretrieve(pdf_url, pdf_path)
        print(f"   ✅ Downloaded to {pdf_path}")
    except Exception as e:
        print(f"   ❌ Download failed: {e}")
        return

    print()

    # Ingest paper
    print(f"2. Ingesting BERT paper...")
    pipeline = IngestionPipeline()

    result = pipeline.ingest_paper(
        pdf_path=pdf_path,
        arxiv_id=arxiv_id
    )

    if result.get('success'):
        print(f"   ✅ Successfully ingested BERT paper")
        print(f"   Paper ID: {result.get('paper_id')}")
        print(f"   Title: {result.get('title', 'N/A')[:60]}...")
        print(f"   Key Finding: {result.get('key_finding', 'N/A')[:150]}...")
    else:
        print(f"   ❌ Ingestion failed: {result.get('error', 'Unknown error')}")

    print()
    print("=" * 70)
    print("BERT PAPER ADDED")
    print("=" * 70)


if __name__ == "__main__":
    download_and_ingest_bert()

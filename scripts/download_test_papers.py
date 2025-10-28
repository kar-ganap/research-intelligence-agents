"""
Download Test Papers from arXiv

Downloads a set of test papers for validating the ingestion pipeline.
"""

import arxiv
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def download_paper(arxiv_id: str, output_dir: Path) -> bool:
    """
    Download a paper from arXiv.

    Args:
        arxiv_id: arXiv ID (e.g., "1706.03762")
        output_dir: Directory to save the PDF

    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"Downloading {arxiv_id}...")

        # Search for the paper
        search = arxiv.Search(id_list=[arxiv_id])
        paper = next(search.results())

        # Generate filename
        filename = f"{arxiv_id.replace('.', '_')}.pdf"
        filepath = output_dir / filename

        # Download
        paper.download_pdf(dirpath=str(output_dir), filename=filename)

        print(f"✅ Downloaded: {paper.title}")
        print(f"   Saved to: {filepath}")
        print(f"   Authors: {', '.join([a.name for a in paper.authors[:3]])}")
        print()

        return True

    except Exception as e:
        print(f"❌ Error downloading {arxiv_id}: {str(e)}")
        print()
        return False


def main():
    """Download test papers."""
    # Output directory
    output_dir = Path("tests/fixtures/sample_papers")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Test papers - diverse set from different domains
    test_papers = [
        ("1706.03762", "Attention Is All You Need (NLP/Deep Learning)"),
        ("1801.04381", "MobileNetV2 (Computer Vision)"),
        ("2005.14165", "GPT-3 (Language Models)"),
    ]

    print("="*70)
    print("DOWNLOADING TEST PAPERS FROM ARXIV")
    print("="*70)
    print()

    results = []
    for arxiv_id, description in test_papers:
        print(f"Paper: {description}")
        print(f"arXiv ID: {arxiv_id}")
        success = download_paper(arxiv_id, output_dir)
        results.append((arxiv_id, success))

    print("="*70)
    print("DOWNLOAD SUMMARY")
    print("="*70)
    successful = sum(1 for _, success in results if success)
    print(f"Total: {len(test_papers)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(test_papers) - successful}")
    print()

    if successful >= 2:
        print("✅ Sufficient papers downloaded for testing")
    else:
        print("⚠️  Not enough papers downloaded - need at least 2")


if __name__ == "__main__":
    main()

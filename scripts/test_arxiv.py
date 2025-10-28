#!/usr/bin/env python3
"""Test arXiv API connectivity and basic functionality."""

import arxiv

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


def test_arxiv_search():
    """Test basic arXiv search."""
    print(f"{BLUE}Testing arXiv API Search...{RESET}\n")

    try:
        # Search for recent AI papers
        search = arxiv.Search(
            query="cat:cs.AI",
            max_results=5,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )

        results = list(search.results())

        if not results:
            print(f"{RED}❌ No results returned{RESET}")
            return False

        print(f"{GREEN}✅ arXiv API Search Working!{RESET}\n")
        print(f"Found {len(results)} recent AI papers:\n")

        for i, paper in enumerate(results, 1):
            print(f"{i}. {BOLD}{paper.title}{RESET}")
            authors = [a.name for a in paper.authors[:3]]
            if len(paper.authors) > 3:
                authors.append(f"+ {len(paper.authors) - 3} more")
            print(f"   Authors: {', '.join(authors)}")
            print(f"   Published: {paper.published.strftime('%Y-%m-%d')}")
            print(f"   arXiv ID: {paper.entry_id.split('/')[-1]}")
            print(f"   PDF: {paper.pdf_url}")
            print()

        return True

    except Exception as e:
        print(f"{RED}❌ arXiv API Search Failed: {e}{RESET}")
        return False


def test_arxiv_specific_paper():
    """Test fetching a specific paper by ID."""
    print(f"{BLUE}Testing Specific Paper Fetch...{RESET}\n")

    try:
        # Fetch a well-known paper (Attention Is All You Need)
        search = arxiv.Search(id_list=["1706.03762"])
        paper = next(search.results())

        print(f"{GREEN}✅ Specific Paper Fetch Working!{RESET}\n")
        print(f"Title: {BOLD}{paper.title}{RESET}")
        print(f"Authors: {', '.join([a.name for a in paper.authors[:5]])}")
        print(f"Published: {paper.published.strftime('%Y-%m-%d')}")
        print(f"Categories: {', '.join(paper.categories)}")
        print(f"Abstract: {paper.summary[:200]}...")
        print()

        return True

    except Exception as e:
        print(f"{RED}❌ Specific Paper Fetch Failed: {e}{RESET}")
        return False


def test_arxiv_metadata():
    """Test extracting metadata from papers."""
    print(f"{BLUE}Testing Metadata Extraction...{RESET}\n")

    try:
        search = arxiv.Search(
            query="machine learning",
            max_results=3
        )

        papers = list(search.results())

        print(f"{GREEN}✅ Metadata Extraction Working!{RESET}\n")

        for paper in papers:
            print(f"Paper: {paper.title[:50]}...")
            print(f"  - Entry ID: {paper.entry_id}")
            print(f"  - arXiv ID: {paper.get_short_id()}")
            print(f"  - Categories: {paper.categories}")
            print(f"  - Primary Category: {paper.primary_category}")
            print(f"  - Comment: {paper.comment if paper.comment else 'None'}")
            print(f"  - Journal Ref: {paper.journal_ref if paper.journal_ref else 'None'}")
            print()

        return True

    except Exception as e:
        print(f"{RED}❌ Metadata Extraction Failed: {e}{RESET}")
        return False


def test_arxiv_download():
    """Test PDF download capability (without actually downloading)."""
    print(f"{BLUE}Testing PDF Download URLs...{RESET}\n")

    try:
        # Get one paper
        search = arxiv.Search(
            query="cat:cs.AI",
            max_results=1
        )

        paper = next(search.results())

        # Check if PDF URL is valid
        if paper.pdf_url and paper.pdf_url.startswith('http'):
            print(f"{GREEN}✅ PDF URL Generation Working!{RESET}")
            print(f"Paper: {paper.title}")
            print(f"PDF URL: {paper.pdf_url}")
            print(f"\n{YELLOW}Note: Not actually downloading to avoid storage use{RESET}\n")
            return True
        else:
            print(f"{RED}❌ Invalid PDF URL{RESET}")
            return False

    except Exception as e:
        print(f"{RED}❌ PDF Download Test Failed: {e}{RESET}")
        return False


def main():
    """Run all arXiv API tests."""
    print(f"\n{BOLD}{BLUE}{'=' * 70}{RESET}")
    print(f"{BOLD}{BLUE}{'arXiv API Test Suite'.center(70)}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 70}{RESET}\n")

    tests = [
        ("API Search", test_arxiv_search),
        ("Specific Paper", test_arxiv_specific_paper),
        ("Metadata Extraction", test_arxiv_metadata),
        ("PDF URLs", test_arxiv_download),
    ]

    results = {}
    for name, test_func in tests:
        results[name] = test_func()
        print(f"{'-' * 70}\n")

    # Summary
    print(f"{BOLD}{BLUE}{'=' * 70}{RESET}")
    print(f"{BOLD}Test Summary:{RESET}\n")

    passed = sum(results.values())
    total = len(results)

    for name, result in results.items():
        status = f"{GREEN}✅ PASS{RESET}" if result else f"{RED}❌ FAIL{RESET}"
        print(f"  {status} | {name}")

    print(f"\n{BOLD}Total: {passed}/{total} tests passed{RESET}")

    if passed == total:
        print(f"\n{GREEN}✅ All arXiv API tests passed! Ready for paper ingestion.{RESET}")
        return 0
    else:
        print(f"\n{RED}❌ Some arXiv tests failed. Check your connection.{RESET}")
        return 1

    print(f"{BOLD}{BLUE}{'=' * 70}{RESET}\n")


if __name__ == "__main__":
    import sys
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Test interrupted by user{RESET}")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n{RED}Unexpected error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

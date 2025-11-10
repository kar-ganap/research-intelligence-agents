#!/usr/bin/env python3
"""
Test ArXiv Watcher Job - Simulates a one-off run without Cloud Scheduler

This script allows you to test the ArXiv watcher functionality locally
without needing to deploy or schedule it.

Usage:
    python scripts/test_arxiv_watcher.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.jobs.arxiv_watcher.main import main

if __name__ == "__main__":
    print("=" * 80)
    print("ArXiv Watcher - One-Off Test Run")
    print("=" * 80)
    print()
    print("This will:")
    print("  1. Fetch latest papers from ArXiv (last 24 hours)")
    print("  2. Match against active watch rules in Firestore")
    print("  3. Create alerts for matching papers")
    print("  4. Publish to Pub/Sub for email notifications")
    print()
    print("=" * 80)
    print()

    # Run the main function from the ArXiv watcher
    main()

#!/usr/bin/env python3
"""
Phase 0 Setup Verification Script

Tests all requirements for Phase 0 completion:
- Python version
- Package imports
- Google Cloud credentials
- Gemini API connectivity
- Firestore connectivity
- Project structure

Usage:
    python scripts/test_setup.py
"""

import os
import sys
from pathlib import Path
from typing import Tuple, List

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv()

# ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{BOLD}{BLUE}{'=' * 70}{RESET}")
    print(f"{BOLD}{BLUE}{text.center(70)}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 70}{RESET}\n")


def print_test(name: str, passed: bool, details: str = "") -> None:
    """Print test result."""
    status = f"{GREEN}✅ PASS{RESET}" if passed else f"{RED}❌ FAIL{RESET}"
    print(f"{status} | {name}")
    if details:
        print(f"      {details}")


def test_python_version() -> Tuple[bool, str]:
    """Test Python version is 3.9+."""
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    if version.major == 3 and version.minor >= 9:
        return True, f"Python {version_str}"
    else:
        return False, f"Python {version_str} (need 3.9+)"


def test_package_imports() -> Tuple[bool, List[str]]:
    """Test that all critical packages can be imported."""
    packages_to_test = [
        ("google.adk", "Google ADK"),
        ("google.genai", "Google GenAI SDK (Gemini)"),
        ("google.cloud.firestore", "Firestore"),
        ("google.cloud.storage", "Cloud Storage"),
        ("google.cloud.pubsub", "Pub/Sub"),
        ("flask", "Flask"),
        ("pydantic", "Pydantic"),
        ("numpy", "NumPy"),
        ("pytest", "Pytest"),
        ("black", "Black"),
        ("ruff", "Ruff"),
    ]

    results = []
    all_passed = True

    for module_name, display_name in packages_to_test:
        try:
            __import__(module_name)
            results.append(f"{GREEN}✓{RESET} {display_name}")
        except ImportError as e:
            results.append(f"{RED}✗{RESET} {display_name}: {e}")
            all_passed = False

    return all_passed, results


def test_adk_imports() -> Tuple[bool, str]:
    """Test specific ADK imports."""
    try:
        from google.adk import Agent, Runner
        from google.adk.agents import SequentialAgent, ParallelAgent, LoopAgent
        return True, "ADK core classes imported successfully (Agent, Runner, Sequential, Parallel, Loop)"
    except ImportError as e:
        return False, f"ADK import failed: {e}"


def test_project_structure() -> Tuple[bool, List[str]]:
    """Test that project structure is in place."""
    project_root = Path(__file__).parent.parent

    required_dirs = [
        "src/agents",
        "src/tools",
        "src/pipelines",
        "src/services",
        "src/jobs",
        "src/workers",
        "src/storage",
        "src/models",
        "src/utils",
        "tests/unit",
        "tests/integration",
        "tests/e2e",
        "docs",
        "scripts",
    ]

    required_files = [
        "pyproject.toml",
        "README.md",
        ".env.example",
        ".gitignore",
        "src/agents/base.py",
        "src/utils/config.py",
        "src/utils/logging.py",
        "tests/conftest.py",
    ]

    results = []
    all_passed = True

    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if full_path.exists():
            results.append(f"{GREEN}✓{RESET} {dir_path}/")
        else:
            results.append(f"{RED}✗{RESET} {dir_path}/ (missing)")
            all_passed = False

    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            results.append(f"{GREEN}✓{RESET} {file_path}")
        else:
            results.append(f"{RED}✗{RESET} {file_path} (missing)")
            all_passed = False

    return all_passed, results


def test_env_file() -> Tuple[bool, str]:
    """Test that .env file exists (optional but recommended)."""
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"

    if env_file.exists():
        return True, ".env file found"
    else:
        return False, ".env file not found (copy from .env.example)"


def test_gemini_api() -> Tuple[bool, str]:
    """Test Gemini API connectivity (requires API key)."""
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return False, "GEMINI_API_KEY not set in environment"

    try:
        from google import genai

        # Create client with API key
        client = genai.Client(api_key=api_key)

        # Try to list models as a connectivity test
        models = client.models.list()
        model_names = [m.name for m in models if 'gemini' in m.name.lower()]

        if model_names:
            return True, f"Connected! Found {len(model_names)} Gemini models"
        else:
            return False, "Connected but no Gemini models found"

    except Exception as e:
        return False, f"Connection failed: {str(e)[:100]}"


def test_firestore() -> Tuple[bool, str]:
    """Test Firestore connectivity (requires GCP credentials)."""
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")

    if not project_id:
        return False, "GOOGLE_CLOUD_PROJECT not set in environment"

    try:
        from google.cloud import firestore

        # Try to create a client
        db = firestore.Client(project=project_id)

        # Try to access a collection (doesn't need to exist)
        # This will fail if credentials are wrong
        collection_ref = db.collection("_test_connection")

        return True, f"Connected to Firestore (project: {project_id})"

    except Exception as e:
        return False, f"Connection failed: {str(e)[:100]}"


def test_gcp_credentials() -> Tuple[bool, str]:
    """Test that GCP credentials are configured."""
    creds_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if creds_file and Path(creds_file).exists():
        return True, f"Credentials file: {creds_file}"
    elif creds_file:
        return False, f"Credentials file not found: {creds_file}"
    else:
        # Check for default credentials
        try:
            from google.auth import default
            credentials, project = default()
            return True, f"Using default credentials (project: {project})"
        except Exception as e:
            return False, "No credentials configured"


def main():
    """Run all setup verification tests."""
    print_header("Phase 0 Setup Verification")

    # Track results
    all_tests = []
    critical_failed = []
    optional_failed = []

    # Level 1: Critical (must pass)
    print(f"\n{BOLD}Level 1: Critical Requirements (Must Pass){RESET}")
    print("-" * 70)

    passed, details = test_python_version()
    print_test("Python Version (3.9+)", passed, details)
    all_tests.append(("Python Version", passed, True))
    if not passed:
        critical_failed.append("Python Version")

    passed, details = test_adk_imports()
    print_test("Google ADK Imports", passed, details)
    all_tests.append(("ADK Imports", passed, True))
    if not passed:
        critical_failed.append("Google ADK")

    passed, results = test_project_structure()
    print_test("Project Structure", passed, f"{len([r for r in results if '✓' in r])} items found")
    all_tests.append(("Project Structure", passed, True))
    if not passed:
        critical_failed.append("Project Structure")
        print(f"\n{YELLOW}Details:{RESET}")
        for result in results:
            if '✗' in result:
                print(f"  {result}")

    # Level 2: Important (should pass)
    print(f"\n{BOLD}Level 2: Important Requirements (Should Pass){RESET}")
    print("-" * 70)

    passed, results = test_package_imports()
    print_test("Package Imports", passed, f"{len([r for r in results if '✓' in r])}/{len(results)} packages")
    all_tests.append(("Package Imports", passed, True))
    if not passed:
        critical_failed.append("Package Imports")
        print(f"\n{YELLOW}Package Status:{RESET}")
        for result in results:
            print(f"  {result}")

    passed, details = test_env_file()
    print_test("Environment File", passed, details)
    all_tests.append(("Environment File", passed, False))
    if not passed:
        optional_failed.append("Environment File")

    # Level 3: Optional (nice to have)
    print(f"\n{BOLD}Level 3: Optional Requirements (Nice to Have){RESET}")
    print("-" * 70)

    passed, details = test_gcp_credentials()
    print_test("GCP Credentials", passed, details)
    all_tests.append(("GCP Credentials", passed, False))
    if not passed:
        optional_failed.append("GCP Credentials")

    passed, details = test_gemini_api()
    print_test("Gemini API Connection", passed, details)
    all_tests.append(("Gemini API", passed, False))
    if not passed:
        optional_failed.append("Gemini API")

    passed, details = test_firestore()
    print_test("Firestore Connection", passed, details)
    all_tests.append(("Firestore", passed, False))
    if not passed:
        optional_failed.append("Firestore")

    # Summary
    print_header("Test Summary")

    critical_count = len([t for t in all_tests if t[2] and t[1]])
    critical_total = len([t for t in all_tests if t[2]])
    optional_count = len([t for t in all_tests if not t[2] and t[1]])
    optional_total = len([t for t in all_tests if not t[2]])

    print(f"Critical Tests: {critical_count}/{critical_total} passed")
    print(f"Optional Tests: {optional_count}/{optional_total} passed")
    print(f"Total: {critical_count + optional_count}/{len(all_tests)} passed")

    # Decision
    print(f"\n{BOLD}Go/No-Go Decision:{RESET}")

    if critical_failed:
        print(f"{RED}❌ NO-GO{RESET}")
        print(f"\n{RED}Critical failures:{RESET}")
        for item in critical_failed:
            print(f"  • {item}")
        print(f"\n{YELLOW}Action required:{RESET}")
        print(f"  1. Review PHASE_0_SETUP_GUIDE.md")
        print(f"  2. Fix critical issues")
        print(f"  3. Re-run this script")
        return 1
    else:
        print(f"{GREEN}✅ GO{RESET}")
        print(f"\nAll critical requirements met! You can proceed to Phase 1.")

        if optional_failed:
            print(f"\n{YELLOW}⚠️  Optional items to configure:{RESET}")
            for item in optional_failed:
                print(f"  • {item}")
            print(f"\nThese are needed for full functionality but not required to start Phase 1.")

        return 0


if __name__ == "__main__":
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

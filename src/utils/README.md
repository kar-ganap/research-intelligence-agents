# Utilities

Shared utility functions for the Research Intelligence Platform.

## arxiv_fetcher.py

Utilities for extracting arXiv IDs from filenames and fetching metadata from the arXiv API.

### Functions

#### `extract_arxiv_id(filename: str) -> Optional[str]`

Extracts arXiv ID from filename.

**Supported formats:**
- `2411.04997.pdf` → `2411.04997`
- `2411.04997v4.pdf` → `2411.04997`
- `2411.04997v1.pdf` → `2411.04997`

**Pattern**: `(\d{4}\.\d{4,5})(v\d+)?\.pdf`

**Parameters:**
- `filename` (str): The filename to extract arXiv ID from

**Returns:**
- `str | None`: arXiv ID string or None if not found

**Example:**
```python
from src.utils.arxiv_fetcher import extract_arxiv_id

arxiv_id = extract_arxiv_id("2411.04997.pdf")  # Returns: "2411.04997"
arxiv_id = extract_arxiv_id("2411.04997v4.pdf")  # Returns: "2411.04997"
arxiv_id = extract_arxiv_id("invalid.pdf")  # Returns: None
```

#### `fetch_arxiv_metadata(arxiv_id: str) -> Dict`

Fetches complete metadata from arXiv API using the `arxiv` Python library.

**Parameters:**
- `arxiv_id` (str): The arXiv ID to fetch metadata for (e.g., "2411.04997")

**Returns:**
```python
{
    'arxiv_id': str,          # e.g., "2411.04997"
    'title': str,             # Paper title
    'authors': list[str],     # List of author names
    'abstract': str,          # Paper abstract
    'categories': list[str],  # All arXiv categories
    'primary_category': str,  # Primary arXiv category (e.g., "cs.AI")
    'published': str,         # ISO format date (e.g., "2024-11-07T00:00:00Z")
    'updated': str,           # ISO format date (e.g., "2024-11-08T10:30:00Z")
    'pdf_url': str            # Direct PDF download URL
}
```

**Raises:**
- `ValueError`: If paper not found on arXiv
- `Exception`: For other arXiv API errors (network issues, rate limiting, etc.)

**Example:**
```python
from src.utils.arxiv_fetcher import fetch_arxiv_metadata

try:
    metadata = fetch_arxiv_metadata("2411.04997")
    print(metadata['title'])  # "LLM2CLIP: Powerful Language Model Unlock Richer Visual Representation"
    print(metadata['primary_category'])  # "cs.CV"
    print(metadata['authors'])  # ['Weiquan Huang', 'Aoqi Wu', ...]
except ValueError as e:
    print(f"Paper not found: {e}")
except Exception as e:
    print(f"arXiv API error: {e}")
```

### Usage in Upload Flow

The arxiv_fetcher utilities are used in the manual upload flow to automatically fetch paper metadata:

1. User uploads PDF via frontend (e.g., `2411.04997.pdf`)
2. Orchestrator extracts arXiv ID from filename using `extract_arxiv_id()`
3. Orchestrator fetches complete metadata using `fetch_arxiv_metadata()`
4. Metadata is passed to ingestion pipeline for processing

**Key Files:**
- `src/services/orchestrator/main.py` (lines 213-338): Upload endpoint
- `src/pipelines/ingestion_pipeline.py`: Uses fetched metadata for paper ingestion

### Error Handling

The arxiv_fetcher includes robust error handling:

- **Invalid filename**: Returns `None` from `extract_arxiv_id()`
- **Paper not found**: Raises `ValueError` with descriptive message
- **arXiv API failure**: Raises `Exception` with error details
- **Network issues**: Automatically retried by `arxiv` library

### Dependencies

- `arxiv`: Python library for accessing the arXiv API
  - Install: `pip install arxiv` or `uv pip install arxiv`
  - Documentation: https://pypi.org/project/arxiv/

## config.py

Configuration management for the platform.

**Key Features:**
- Loads environment variables from `.env` file
- Provides default values for all configuration
- Validates required environment variables

**Environment Variables:**
- `GOOGLE_CLOUD_PROJECT`: GCP project ID
- `GOOGLE_API_KEY`: Gemini API key
- `DEFAULT_MODEL`: Model to use (default: gemini-2.5-pro)
- `FROM_EMAIL`: Email address for alert notifications
- `SENDGRID_API_KEY`: SendGrid API key (optional)

## embeddings.py

Embedding generation utilities for semantic search.

**Functions:**
- `generate_embedding(text: str) -> list[float]`: Generate embeddings using Gemini
- `cosine_similarity(vec1, vec2) -> float`: Calculate similarity between embeddings

## logging_config.py

Structured logging configuration for all services.

**Features:**
- JSON-formatted logs for Cloud Logging
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Request correlation IDs
- Automatic service name detection

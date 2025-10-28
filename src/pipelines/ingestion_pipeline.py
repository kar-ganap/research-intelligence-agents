"""
Ingestion Pipeline

Orchestrates the paper ingestion process:
1. Load PDF and extract text
2. Extract entities (title, authors, key finding)
3. Store in Firestore

Phase 1 approach: Simple Python orchestration for reliability and clarity.
"""

from typing import Dict, List, Tuple
import logging
from pathlib import Path
import time

from src.tools.pdf_reader import read_pdf
from src.agents.ingestion.entity_agent import EntityAgent
from src.agents.ingestion.indexer_agent import IndexerAgent

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """
    Orchestrates the paper ingestion process.

    Phase 1 approach: Simple Python orchestration for reliability.
    Explicitly passes data between components for clarity.
    """

    def __init__(self, project_id: str = None):
        """
        Initialize the ingestion pipeline.

        Args:
            project_id: GCP project ID for Firestore
        """
        self.entity_agent = EntityAgent()
        self.indexer_agent = IndexerAgent(project_id=project_id)
        logger.info("IngestionPipeline initialized")

    def ingest_paper(self, pdf_path: str, arxiv_id: str = "") -> Dict:
        """
        Ingest a single paper through the full pipeline.

        Args:
            pdf_path: Path to the PDF file
            arxiv_id: arXiv ID (optional, for metadata)

        Returns:
            Dictionary with:
                - success: bool
                - paper_id: str (if successful)
                - steps: dict with status of each step
                - duration: float (seconds)
                - error: str (if failed)
        """
        start_time = time.time()

        result = {
            "success": False,
            "pdf_path": pdf_path,
            "arxiv_id": arxiv_id,
            "steps": {}
        }

        try:
            # Step 1: Extract text from PDF
            logger.info(f"Step 1/3: Extracting text from {pdf_path}")
            step_start = time.time()

            pdf_result = read_pdf(pdf_path)

            result["steps"]["pdf_extraction"] = {
                "success": True,
                "page_count": pdf_result["page_count"],
                "text_length": len(pdf_result["text"]),
                "duration": time.time() - step_start
            }

            paper_text = pdf_result["text"]
            pdf_metadata = pdf_result.get("metadata", {})

            # Step 2: Extract entities with EntityAgent
            logger.info("Step 2/3: Extracting entities")
            step_start = time.time()

            entities = self.entity_agent.extract(paper_text)

            # Check for extraction errors
            if "error" in entities:
                result["steps"]["entity_extraction"] = {
                    "success": False,
                    "error": entities["error"],
                    "duration": time.time() - step_start
                }
                result["error"] = f"Entity extraction failed: {entities['error']}"
                result["duration"] = time.time() - start_time
                return result

            result["steps"]["entity_extraction"] = {
                "success": True,
                "title": entities.get("title", ""),
                "authors_count": len(entities.get("authors", [])),
                "key_finding_length": len(entities.get("key_finding", "")),
                "duration": time.time() - step_start
            }

            # Step 3: Index to Firestore
            logger.info("Step 3/3: Indexing to Firestore")
            step_start = time.time()

            index_result = self.indexer_agent.index(
                entities=entities,
                pdf_path=pdf_path,
                arxiv_id=arxiv_id
            )

            result["steps"]["indexing"] = {
                "success": index_result["success"],
                "paper_id": index_result.get("paper_id", ""),
                "already_exists": index_result.get("already_exists", False),
                "duration": time.time() - step_start
            }

            if not index_result["success"]:
                result["error"] = f"Indexing failed: {index_result.get('error')}"
                result["duration"] = time.time() - start_time
                return result

            # All steps successful
            result["success"] = True
            result["paper_id"] = index_result["paper_id"]
            result["message"] = "Paper ingested successfully"
            result["duration"] = time.time() - start_time

            logger.info(
                f"✅ Successfully ingested paper: {result['paper_id']} "
                f"({result['duration']:.2f}s)"
            )
            return result

        except FileNotFoundError as e:
            logger.error(f"PDF file not found: {pdf_path}")
            result["error"] = f"File not found: {str(e)}"
            result["duration"] = time.time() - start_time
            return result

        except Exception as e:
            logger.error(f"Unexpected error in ingestion pipeline: {str(e)}")
            result["error"] = f"Pipeline error: {str(e)}"
            result["duration"] = time.time() - start_time
            return result

    def ingest_papers_batch(
        self,
        papers: List[Tuple[str, str]]
    ) -> Dict:
        """
        Ingest multiple papers in batch.

        Args:
            papers: List of tuples (pdf_path, arxiv_id)

        Returns:
            Dictionary with:
                - total: int
                - successful: int
                - failed: int
                - success_rate: float
                - avg_duration: float
                - results: list of individual results
        """
        results = []
        successful = 0
        failed = 0
        total_duration = 0

        logger.info(f"Starting batch ingestion of {len(papers)} papers")

        for pdf_path, arxiv_id in papers:
            result = self.ingest_paper(pdf_path, arxiv_id)
            results.append(result)

            if result["success"]:
                successful += 1
            else:
                failed += 1

            total_duration += result.get("duration", 0)

        success_rate = successful / len(papers) if papers else 0
        avg_duration = total_duration / len(papers) if papers else 0

        summary = {
            "total": len(papers),
            "successful": successful,
            "failed": failed,
            "success_rate": success_rate,
            "avg_duration": avg_duration,
            "total_duration": total_duration,
            "results": results
        }

        logger.info(
            f"Batch ingestion complete: {successful}/{len(papers)} successful "
            f"({success_rate:.1%}, avg {avg_duration:.2f}s per paper)"
        )

        return summary

    def get_pipeline_status(self) -> Dict:
        """
        Get status of the pipeline components.

        Returns:
            Dictionary with component status
        """
        return {
            "entity_agent": {
                "status": "ready",
                "type": "LlmAgent"
            },
            "indexer_agent": {
                "status": "ready",
                "type": "StorageAgent"
            },
            "pipeline": "ready"
        }

"""
Q&A Pipeline

Orchestrates question answering with citations:
1. Retrieve relevant papers
2. Generate answer with citations

Phase 1 approach: Simple Python orchestration.
"""

from typing import Dict, List, Optional
import logging
import time
import re

from src.tools.retrieval import keyword_search
from src.agents.qa.answer_agent import AnswerAgent
from src.agents.qa.confidence_agent import ConfidenceAgent
from src.storage.firestore_client import FirestoreClient

logger = logging.getLogger(__name__)


class QAPipeline:
    """
    Orchestrates the Q&A process.

    Simple Python orchestration: Question → Retrieval → Answer
    """

    def __init__(self, project_id: str = None, enable_confidence: bool = False):
        """
        Initialize the Q&A pipeline.

        Args:
            project_id: GCP project ID for Firestore
            enable_confidence: Whether to score answer confidence (Phase 2.3 feature)
        """
        self.answer_agent = AnswerAgent()
        self.firestore_client = FirestoreClient(project_id=project_id)
        self.enable_confidence = enable_confidence

        if enable_confidence:
            self.confidence_agent = ConfidenceAgent()
            logger.info("QAPipeline initialized with confidence scoring")
        else:
            self.confidence_agent = None
            logger.info("QAPipeline initialized (confidence scoring disabled)")

    def ask(self, question: str, limit: int = 5) -> Dict:
        """
        Answer a question with citations.

        Args:
            question: User's question
            limit: Max papers to retrieve

        Returns:
            Dictionary with:
                - success: bool
                - question: str
                - answer: str
                - citations: List[str] (paper titles)
                - retrieved_papers: List[Dict]
                - steps: dict with status of each step
                - duration: float (seconds)
        """
        start_time = time.time()

        result = {
            "success": False,
            "question": question,
            "steps": {}
        }

        try:
            # Step 1: Retrieve relevant papers
            logger.info(f"Step 1/2: Retrieving papers for: '{question}'")
            step_start = time.time()

            papers = keyword_search(
                query=question,
                firestore_client=self.firestore_client,
                limit=limit
            )

            result["steps"]["retrieval"] = {
                "success": True,
                "papers_found": len(papers),
                "duration": time.time() - step_start
            }
            result["retrieved_papers"] = papers

            # Handle no papers found
            if not papers:
                result["answer"] = "I couldn't find any relevant papers to answer this question."
                result["citations"] = []
                result["success"] = True
                result["duration"] = time.time() - start_time
                logger.info("No papers found - returning graceful response")
                return result

            # Step 2: Generate answer with citations
            logger.info(f"Step 2/2: Generating answer using {len(papers)} papers")
            step_start = time.time()

            answer = self.answer_agent.answer(question, papers)

            result["steps"]["answering"] = {
                "success": True,
                "duration": time.time() - step_start
            }

            # Extract citations from answer
            citations = self._extract_citations(answer)

            # Step 3 (Optional): Calculate confidence score
            confidence_result = None
            if self.enable_confidence and self.confidence_agent:
                logger.info("Step 3/3: Calculating confidence score")
                step_start = time.time()

                try:
                    # Check for contradictions in relationships (if available)
                    contradictions = self._find_contradictions(papers)

                    confidence_result = self.confidence_agent.score_confidence(
                        question=question,
                        answer=answer,
                        papers=papers,
                        contradictions=contradictions
                    )

                    result["steps"]["confidence"] = {
                        "success": True,
                        "score": confidence_result['final_score'],
                        "duration": time.time() - step_start
                    }

                    logger.info(f"Confidence score: {confidence_result['final_score']:.2f}")

                except Exception as e:
                    logger.warning(f"Confidence scoring failed (non-blocking): {e}")
                    result["steps"]["confidence"] = {
                        "success": False,
                        "error": str(e),
                        "duration": time.time() - step_start
                    }

            # Success!
            result["success"] = True
            result["answer"] = answer
            result["citations"] = citations
            result["duration"] = time.time() - start_time

            # Add confidence data if enabled
            if confidence_result:
                result["confidence"] = {
                    "score": confidence_result['final_score'],
                    "breakdown": {
                        "evidence_strength": confidence_result['evidence_strength'],
                        "consistency": confidence_result['consistency'],
                        "coverage": confidence_result['coverage'],
                        "source_quality": confidence_result['source_quality']
                    },
                    "reasoning": confidence_result['reasoning'],
                    "warning": confidence_result.get('warning')
                }

            logger.info(
                f"✅ Question answered ({result['duration']:.2f}s, "
                f"{len(citations)} citations"
                f"{', confidence: ' + str(confidence_result['final_score']) if confidence_result else ''})"
            )

            return result

        except Exception as e:
            logger.error(f"Error in Q&A pipeline: {str(e)}")
            result["error"] = str(e)
            result["duration"] = time.time() - start_time
            return result

    def _extract_citations(self, answer: str) -> List[str]:
        """
        Extract paper titles from [Citation] format.

        Args:
            answer: Answer text with citations

        Returns:
            List of cited paper titles
        """
        citations = re.findall(r'\[(.*?)\]', answer)
        # Remove duplicates while preserving order
        seen = set()
        unique_citations = []
        for citation in citations:
            if citation not in seen:
                seen.add(citation)
                unique_citations.append(citation)

        return unique_citations

    def _find_contradictions(self, papers: List[Dict]) -> List[Dict]:
        """
        Find contradictions between papers using Phase 2.1 relationship data.

        Args:
            papers: List of retrieved papers

        Returns:
            List of contradictions (relationships with type='contradicts')
        """
        contradictions = []

        try:
            # Get paper IDs
            paper_ids = [p.get('paper_id') for p in papers if p.get('paper_id')]

            if not paper_ids:
                return []

            # Check for contradicting relationships between these papers
            for paper_id in paper_ids:
                relationships = self.firestore_client.get_relationships_for_paper(paper_id)

                for rel in relationships:
                    # Check if this is a contradiction and involves papers in our set
                    if (rel.get('relationship_type') == 'contradicts' and
                        rel.get('target_paper_id') in paper_ids):
                        contradictions.append(rel)

        except Exception as e:
            logger.warning(f"Could not check for contradictions: {e}")

        return contradictions

    def batch_ask(self, questions: List[str], limit: int = 5) -> Dict:
        """
        Answer multiple questions in batch.

        Args:
            questions: List of questions
            limit: Max papers to retrieve per question

        Returns:
            Summary with individual results
        """
        results = []
        successful = 0
        failed = 0
        total_duration = 0

        logger.info(f"Starting batch Q&A for {len(questions)} questions")

        for question in questions:
            result = self.ask(question, limit=limit)
            results.append(result)

            if result["success"]:
                successful += 1
            else:
                failed += 1

            total_duration += result.get("duration", 0)

        success_rate = successful / len(questions) if questions else 0
        avg_duration = total_duration / len(questions) if questions else 0

        # Calculate citation coverage
        with_citations = sum(
            1 for r in results
            if r.get("success") and len(r.get("citations", [])) > 0
        )
        citation_coverage = with_citations / len(questions) if questions else 0

        summary = {
            "total": len(questions),
            "successful": successful,
            "failed": failed,
            "success_rate": success_rate,
            "citation_coverage": citation_coverage,
            "avg_duration": avg_duration,
            "total_duration": total_duration,
            "results": results
        }

        logger.info(
            f"Batch Q&A complete: {successful}/{len(questions)} successful "
            f"({success_rate:.1%}, citation coverage: {citation_coverage:.1%})"
        )

        return summary

    def get_pipeline_status(self) -> Dict:
        """
        Get status of the pipeline components.

        Returns:
            Dictionary with component status
        """
        return {
            "answer_agent": {
                "status": "ready",
                "type": "LlmAgent"
            },
            "retrieval": {
                "status": "ready",
                "type": "KeywordSearch"
            },
            "pipeline": "ready"
        }

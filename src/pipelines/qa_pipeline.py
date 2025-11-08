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
from src.agents.qa.graph_query_agent import GraphQueryAgent
from src.storage.firestore_client import FirestoreClient
from src.tools.graph_queries import GraphQueryTool, detect_graph_query_type

logger = logging.getLogger(__name__)


class QAPipeline:
    """
    Orchestrates the Q&A process.

    Simple Python orchestration: Question → Retrieval → Answer
    """

    def __init__(self, project_id: str = None, enable_confidence: bool = False, use_nl_graph_queries: bool = True):
        """
        Initialize the Q&A pipeline.

        Args:
            project_id: GCP project ID for Firestore
            enable_confidence: Whether to score answer confidence (Phase 2.3 feature)
            use_nl_graph_queries: Whether to use LLM-based natural language graph query detection (default: True)
        """
        self.answer_agent = AnswerAgent()
        self.firestore_client = FirestoreClient(project_id=project_id)
        self.graph_query_tool = GraphQueryTool(self.firestore_client)
        self.enable_confidence = enable_confidence
        self.use_nl_graph_queries = use_nl_graph_queries

        if use_nl_graph_queries:
            self.graph_query_agent = GraphQueryAgent()
            logger.info("QAPipeline initialized with NL graph query detection")
        else:
            self.graph_query_agent = None
            logger.info("QAPipeline initialized with keyword-based graph query detection")

        if enable_confidence:
            self.confidence_agent = ConfidenceAgent()
            logger.info("Confidence scoring enabled")
        else:
            self.confidence_agent = None
            logger.info("Confidence scoring disabled")

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
            # Step 0: Check if this is a graph query
            if self.use_nl_graph_queries and self.graph_query_agent:
                # Use LLM-based natural language detection
                analysis = self.graph_query_agent.analyze_query(question)

                if analysis['is_graph_query'] and analysis['confidence'] >= 0.6:
                    query_type = analysis['query_type']
                    logger.info(f"NL detected graph query: {query_type} (confidence: {analysis['confidence']})")
                    return self._handle_graph_query_nl(question, analysis, start_time)
                else:
                    logger.info(f"NL analysis: Not a graph query (confidence: {analysis['confidence']})")
                    query_type = None
            else:
                # Fall back to keyword-based detection
                query_type = detect_graph_query_type(question)

                if query_type:
                    logger.info(f"Keyword detected graph query type: {query_type}")
                    return self._handle_graph_query(question, query_type, start_time)

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

    def _handle_graph_query_nl(self, question: str, analysis: Dict, start_time: float) -> Dict:
        """
        Handle graph-based queries using NL analysis from GraphQueryAgent.

        Args:
            question: User's question
            analysis: Analysis result from GraphQueryAgent with query_type and parameters
            start_time: Query start time

        Returns:
            Result dictionary with graph query response
        """
        query_type = analysis['query_type']
        params = analysis.get('parameters', {})

        logger.info(f"Executing NL graph query: {query_type}, params: {params}")

        result = {
            "success": False,
            "question": question,
            "query_type": query_type,
            "is_graph_query": True,
            "nl_confidence": analysis.get('confidence', 0.0)
        }

        try:
            if query_type == 'citations':
                # Extract paper and find papers that cite it
                paper_title = params.get('paper_title')
                if paper_title:
                    paper_id = self.graph_query_agent.extract_paper_id(paper_title, self.firestore_client)
                    if paper_id:
                        graph_result = self.graph_query_tool.find_papers_citing(paper_id)
                    else:
                        # Fall back to most cited if paper not found
                        graph_result = self.graph_query_tool.find_most_cited_papers(limit=10)
                else:
                    # No specific paper mentioned, show most cited
                    graph_result = self.graph_query_tool.find_most_cited_papers(limit=10)

                answer = self._format_graph_result(graph_result, query_type)

            elif query_type == 'contradictions':
                paper_title = params.get('paper_title')
                topic = params.get('topic')

                if paper_title:
                    paper_id = self.graph_query_agent.extract_paper_id(paper_title, self.firestore_client)
                    graph_result = self.graph_query_tool.find_contradictions(paper_id=paper_id, topic=topic)
                else:
                    graph_result = self.graph_query_tool.find_contradictions(topic=topic)

                answer = self._format_graph_result(graph_result, query_type)

            elif query_type == 'extensions':
                paper_title = params.get('paper_title')

                if paper_title:
                    paper_id = self.graph_query_agent.extract_paper_id(paper_title, self.firestore_client)
                    if paper_id:
                        graph_result = self.graph_query_tool.find_papers_extending(paper_id)
                    else:
                        # Fall back to showing highly cited papers
                        graph_result = self.graph_query_tool.find_most_cited_papers(limit=10)
                        answer = f"Could not find paper '{paper_title}'. Showing most cited papers instead:\n\n"
                        answer += self._format_graph_result(graph_result, 'popularity')
                        result["success"] = True
                        result["answer"] = answer
                        result["graph_data"] = graph_result
                        result["citations"] = []
                        result["duration"] = time.time() - start_time
                        return result
                else:
                    graph_result = self.graph_query_tool.find_most_cited_papers(limit=10)

                answer = self._format_graph_result(graph_result, query_type)

            elif query_type == 'author':
                author_name = params.get('author_name')

                if not author_name:
                    # Try to extract from paper title
                    paper_title = params.get('paper_title')
                    if paper_title:
                        paper_id = self.graph_query_agent.extract_paper_id(paper_title, self.firestore_client)
                        if paper_id:
                            paper = self.firestore_client.get_paper(paper_id)
                            if paper and paper.get('authors'):
                                # Show papers by first author
                                author_name = paper['authors'][0]

                if author_name:
                    graph_result = self.graph_query_tool.find_papers_by_author(author_name)
                    answer = self._format_graph_result(graph_result, query_type)
                else:
                    answer = "Could not identify author name in the question."
                    graph_result = {'success': False, 'papers': []}

            elif query_type == 'popularity':
                limit = params.get('limit', 10)
                graph_result = self.graph_query_tool.find_most_cited_papers(limit=limit)
                answer = self._format_graph_result(graph_result, query_type)

            elif query_type == 'relationships':
                # General relationship query - show all contradictions or most connected papers
                graph_result = self.graph_query_tool.find_most_cited_papers(limit=10)
                answer = "Here are the most connected papers in the knowledge graph:\n\n"
                answer += self._format_graph_result(graph_result, 'popularity')

            else:
                answer = f"Graph query type '{query_type}' not yet implemented."
                graph_result = {'success': False}

            result["success"] = graph_result.get('success', True)
            result["answer"] = answer
            result["graph_data"] = graph_result
            result["citations"] = []  # Graph queries don't use traditional citations
            result["duration"] = time.time() - start_time

            logger.info(f"✅ NL graph query answered ({result['duration']:.2f}s)")

            return result

        except Exception as e:
            logger.error(f"Error in NL graph query: {str(e)}", exc_info=True)
            result["error"] = str(e)
            result["duration"] = time.time() - start_time
            return result

    def _handle_graph_query(self, question: str, query_type: str, start_time: float) -> Dict:
        """
        Handle graph-based queries using GraphQueryTool.

        Args:
            question: User's question
            query_type: Type of graph query (citations, contradictions, author, popularity, extensions)
            start_time: Query start time

        Returns:
            Result dictionary with graph query response
        """
        logger.info(f"Executing graph query: {query_type}")

        result = {
            "success": False,
            "question": question,
            "query_type": query_type,
            "is_graph_query": True
        }

        try:
            # Extract parameters from question
            # For now, use simple heuristics - we'll improve this with LLM later

            if query_type == 'citations':
                # Try to find paper title in question
                # For demo, show most cited papers
                graph_result = self.graph_query_tool.find_most_cited_papers(limit=10)
                answer = self._format_graph_result(graph_result, query_type)

            elif query_type == 'contradictions':
                # Find all contradictions
                graph_result = self.graph_query_tool.find_contradictions()
                answer = self._format_graph_result(graph_result, query_type)

            elif query_type == 'extensions':
                # Show most cited papers that have extensions
                graph_result = self.graph_query_tool.find_most_cited_papers(limit=10)
                answer = self._format_graph_result(graph_result, query_type)

            elif query_type == 'author':
                # Extract author name from question
                author_name = self._extract_author_name(question)
                if author_name:
                    graph_result = self.graph_query_tool.find_papers_by_author(author_name)
                    answer = self._format_graph_result(graph_result, query_type)
                else:
                    answer = "Could not identify author name in the question."
                    graph_result = {'success': False, 'papers': []}

            elif query_type == 'popularity':
                graph_result = self.graph_query_tool.find_most_cited_papers(limit=10)
                answer = self._format_graph_result(graph_result, query_type)

            else:
                answer = f"Graph query type '{query_type}' not yet implemented."
                graph_result = {'success': False}

            result["success"] = graph_result.get('success', True)
            result["answer"] = answer
            result["graph_data"] = graph_result
            result["citations"] = []  # Graph queries don't use traditional citations
            result["duration"] = time.time() - start_time

            logger.info(f"✅ Graph query answered ({result['duration']:.2f}s)")

            return result

        except Exception as e:
            logger.error(f"Error in graph query: {str(e)}", exc_info=True)
            result["error"] = str(e)
            result["duration"] = time.time() - start_time
            return result

    def _format_graph_result(self, graph_result: Dict, query_type: str) -> str:
        """
        Format graph query results into natural language.

        Args:
            graph_result: Result from GraphQueryTool
            query_type: Type of query

        Returns:
            Natural language response
        """
        if not graph_result.get('success'):
            return f"I encountered an error: {graph_result.get('error', 'Unknown error')}"

        if query_type == 'popularity':
            papers = graph_result.get('papers', [])
            if not papers:
                return "I couldn't find any citation data in the knowledge graph."

            response = f"Here are the {len(papers)} most cited papers in the corpus:\n\n"
            for i, paper in enumerate(papers, 1):
                response += f"{i}. **{paper['title']}** by {', '.join(paper['authors'][:2])}"
                if len(paper['authors']) > 2:
                    response += " et al."
                response += f" ({paper['citation_count']} citations)\n"

            return response

        elif query_type == 'author':
            papers = graph_result.get('papers', [])
            author = graph_result.get('author', 'unknown')

            if not papers:
                return f"I couldn't find any papers by {author} in the corpus."

            response = f"Found {len(papers)} paper(s) by {author}:\n\n"
            for i, paper in enumerate(papers, 1):
                response += f"{i}. **{paper['title']}**\n"
                if paper.get('key_finding'):
                    response += f"   {paper['key_finding'][:150]}...\n"

            return response

        elif query_type == 'contradictions':
            contradictions = graph_result.get('contradictions', [])

            if not contradictions:
                return "I couldn't find any documented contradictions in the knowledge graph."

            response = f"Found {len(contradictions)} contradiction(s):\n\n"
            for i, contra in enumerate(contradictions, 1):
                if 'paper_1' in contra:
                    response += f"{i}. **{contra['paper_1']['title']}** contradicts **{contra['paper_2']['title']}**\n"
                    if contra.get('description'):
                        response += f"   {contra['description']}\n"
                else:
                    response += f"{i}. **{contra['title']}**\n"

            return response

        elif query_type in ['citations', 'extensions']:
            papers = graph_result.get('papers', graph_result.get('citing_papers', graph_result.get('extending_papers', [])))

            if not papers:
                return "I couldn't find any related papers in the knowledge graph."

            action = "cite" if query_type == 'citations' else "extend"
            response = f"Found {len(papers)} paper(s) that {action} the target:\n\n"
            for i, paper in enumerate(papers, 1):
                response += f"{i}. **{paper['title']}**"
                if paper.get('relationship_type'):
                    response += f" (relationship: {paper['relationship_type']})"
                response += "\n"

            return response

        return "Successfully retrieved graph data."

    def _extract_author_name(self, question: str) -> Optional[str]:
        """
        Extract author name from question.

        Args:
            question: User's question

        Returns:
            Extracted author name or None
        """
        # Simple heuristic: look for capitalized words after "by"
        import re

        patterns = [
            r'by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # "by John Smith"
            r'authored by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'written by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'papers by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        ]

        for pattern in patterns:
            match = re.search(pattern, question)
            if match:
                return match.group(1)

        return None

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

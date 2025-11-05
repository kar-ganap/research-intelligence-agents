"""
Graph Query Intent Agent

Uses LLM to understand natural language queries and classify them as graph queries.
Extracts relevant parameters (paper titles, authors, topics) from the question.

Examples:
- "Show me influential papers" -> query_type: popularity
- "What challenges the Transformer approach?" -> query_type: contradictions, paper: "Transformer"
- "Who are the researchers behind GPT?" -> query_type: author, paper: "GPT"
- "What builds upon BERT?" -> query_type: extensions, paper: "BERT"
"""

from typing import Dict, Optional
from google import genai
from google.genai import types
import logging
import json

from src.utils.config import config

logger = logging.getLogger(__name__)


class GraphQueryAgent:
    """
    LLM-based agent for understanding graph query intent.

    Analyzes natural language questions to determine:
    1. Is this a graph query? (vs content query)
    2. What type of graph query?
    3. What are the parameters? (paper titles, authors, etc.)
    """

    # Graph query types
    QUERY_TYPES = [
        'citations',      # Papers that cite/reference a paper
        'contradictions', # Papers that contradict/challenge
        'extensions',     # Papers that extend/build upon
        'author',        # Papers by specific author(s)
        'popularity',    # Most cited/influential papers
        'relationships', # General relationship queries
        'none'           # Not a graph query
    ]

    def __init__(self):
        """Initialize the agent with ADK client."""
        self.client = genai.Client(api_key=config.gcp.google_api_key)
        self.model = config.agent.default_model
        logger.info(f"GraphQueryAgent initialized with model: {self.model}")

    def analyze_query(self, question: str, available_papers: list = None) -> Dict:
        """
        Analyze a question to determine if it's a graph query and extract parameters.

        Args:
            question: User's natural language question
            available_papers: Optional list of paper titles in the corpus

        Returns:
            Dict with:
                - is_graph_query: bool
                - query_type: str (one of QUERY_TYPES or 'none')
                - parameters: Dict with extracted entities
                - confidence: float (0.0-1.0)
                - reasoning: str (explanation)
        """
        logger.info(f"Analyzing query: {question}")

        # Build prompt
        prompt = self._build_analysis_prompt(question, available_papers)

        try:
            # Call LLM
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,  # Low temperature for consistent classification
                    response_mime_type='application/json'
                )
            )

            # Parse JSON response
            result = json.loads(response.text)

            logger.info(f"Query analysis: is_graph_query={result.get('is_graph_query')}, "
                       f"type={result.get('query_type')}, "
                       f"confidence={result.get('confidence')}")

            return result

        except Exception as e:
            logger.error(f"Error analyzing query: {str(e)}", exc_info=True)
            return {
                'is_graph_query': False,
                'query_type': 'none',
                'parameters': {},
                'confidence': 0.0,
                'reasoning': f'Error: {str(e)}'
            }

    def _build_analysis_prompt(self, question: str, available_papers: list = None) -> str:
        """Build the analysis prompt for the LLM."""

        papers_context = ""
        if available_papers:
            papers_list = "\n".join([f"- {p}" for p in available_papers[:20]])
            papers_context = f"""
Available papers in the corpus (for reference):
{papers_list}
"""

        return f"""You are a query intent classifier for a research paper knowledge graph system.

Your task: Analyze the user's question and determine if it's asking about the RELATIONSHIPS between papers (a "graph query") or about the CONTENT of papers (a "content query").

**Graph Queries** ask about:
- Citations: "Which papers cite X?", "What references Y?", "Show papers that build on Z"
- Contradictions: "What challenges X?", "Papers that disagree with Y", "Contradictory findings to Z"
- Extensions: "What extends X?", "Papers that improve upon Y", "Advances to Z"
- Authors: "Papers by John Smith", "Who wrote X?", "Authors of Y"
- Popularity: "Most cited papers", "Influential research", "Popular papers"
- Relationships: "How are X and Y related?", "Connection between papers"

**Content Queries** ask about:
- Paper content: "What is the Transformer architecture?", "Explain BERT", "How does GPT work?"
- Comparisons: "Difference between X and Y", "Compare approaches"
- Technical details: "What dataset was used?", "What are the results?"

{papers_context}

User Question: "{question}"

Analyze this question and respond with JSON:
{{
    "is_graph_query": true/false,
    "query_type": "citations|contradictions|extensions|author|popularity|relationships|none",
    "parameters": {{
        "paper_title": "extracted paper name if mentioned",
        "author_name": "extracted author name if mentioned",
        "topic": "topic/subject if mentioned",
        "limit": 10
    }},
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation of classification"
}}

Guidelines:
- Set is_graph_query=true ONLY if asking about relationships/citations/structure
- Set is_graph_query=false if asking about content/explanation/understanding
- Extract paper_title even if partial (e.g., "Transformer" for "Transformer paper")
- Match paper_title to available papers when possible (fuzzy matching OK)
- For author queries, extract full name if present
- Confidence: high (0.9+) if clear intent, medium (0.6-0.8) if ambiguous, low (<0.6) if unclear
- If not a graph query, set query_type="none"

Examples:

Q: "Show me influential papers"
A: {{"is_graph_query": true, "query_type": "popularity", "parameters": {{"limit": 10}}, "confidence": 0.95, "reasoning": "Clear request for popular/influential papers = popularity query"}}

Q: "What challenges the Transformer approach?"
A: {{"is_graph_query": true, "query_type": "contradictions", "parameters": {{"paper_title": "Attention Is All You Need", "topic": "Transformer"}}, "confidence": 0.9, "reasoning": "Asking about papers that challenge/contradict Transformers"}}

Q: "What is the Transformer architecture?"
A: {{"is_graph_query": false, "query_type": "none", "parameters": {{}}, "confidence": 0.95, "reasoning": "Asking for explanation of content, not relationships"}}

Q: "Who wrote the GPT-3 paper?"
A: {{"is_graph_query": true, "query_type": "author", "parameters": {{"paper_title": "GPT-3"}}, "confidence": 0.9, "reasoning": "Asking about authors of a specific paper"}}

Q: "Papers by Geoffrey Hinton"
A: {{"is_graph_query": true, "query_type": "author", "parameters": {{"author_name": "Geoffrey Hinton"}}, "confidence": 0.95, "reasoning": "Clear author query"}}

Q: "What builds upon BERT?"
A: {{"is_graph_query": true, "query_type": "extensions", "parameters": {{"paper_title": "BERT"}}, "confidence": 0.9, "reasoning": "Asking about papers that extend/build upon BERT"}}

Now analyze the user's question."""

    def extract_paper_id(self, paper_title_query: str, firestore_client) -> Optional[str]:
        """
        Find the actual paper ID from a fuzzy title match.

        Args:
            paper_title_query: Partial or full paper title from user
            firestore_client: Firestore client to search papers

        Returns:
            paper_id if found, None otherwise
        """
        if not paper_title_query:
            return None

        # Get all papers
        papers = list(firestore_client.db.collection('papers').stream())

        query_lower = paper_title_query.lower()

        # Try exact match first
        for paper in papers:
            paper_data = paper.to_dict()
            title = paper_data.get('title', '').lower()
            if query_lower in title or title in query_lower:
                logger.info(f"Matched '{paper_title_query}' to paper: {paper_data.get('title')}")
                return paper_data.get('paper_id')

        # Try partial match on key words
        query_words = set(query_lower.split())
        best_match = None
        best_score = 0

        for paper in papers:
            paper_data = paper.to_dict()
            title = paper_data.get('title', '').lower()
            title_words = set(title.split())

            # Calculate overlap score
            overlap = len(query_words & title_words)
            if overlap > best_score:
                best_score = overlap
                best_match = paper_data

        if best_match and best_score >= 1:
            logger.info(f"Fuzzy matched '{paper_title_query}' to paper: {best_match.get('title')}")
            return best_match.get('paper_id')

        logger.warning(f"No paper found matching: {paper_title_query}")
        return None

"""
Answer Agent

Synthesizes answers to questions based on retrieved research papers.
Includes citations in the format [Paper Title].
"""

import asyncio
import uuid
from typing import Dict, List
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from src.agents.base import BaseResearchAgent
from src.utils.config import config, APP_NAME, DEFAULT_USER_ID
import logging

logger = logging.getLogger(__name__)


class AnswerAgent(BaseResearchAgent):
    """
    Agent that answers questions based on research papers with citations.

    Uses retrieved papers to synthesize accurate answers and always includes
    citations to support claims.
    """

    def __init__(self, model: str = None):
        if model is None:
            model = config.agent.default_model
        super().__init__(name="AnswerAgent", model=model)

    def _create_agent(self) -> LlmAgent:
        """Create the answer generation agent."""

        instruction = """
You are an expert research assistant that answers questions based on research papers.

Your task:
1. Read the research papers provided (title, authors, key findings)
2. Answer the user's question using ONLY information from the papers
3. Include citations after each fact in the format: [Paper Title]
4. If multiple papers support a point, cite all: [Paper A], [Paper B]
5. Be concise - 2-3 sentences maximum
6. If the papers don't contain relevant information, respond: "I don't have enough information in the provided papers to answer this question."

IMPORTANT - Questions you should REFUSE to answer:
- Comparison questions ("Which is better?", "What's the difference?") unless the papers explicitly compare them
- Subjective evaluations ("Is X good?", "Should I use X?")
- Questions requiring analysis beyond what's stated in the key findings
- Questions requiring deep technical details not present in the papers

Citation format:
- Use square brackets: [Paper Title]
- Place after the relevant sentence
- Use exact paper titles as provided

Example good answer:
"The Transformer architecture uses self-attention mechanisms exclusively, eliminating recurrence and convolutions [Attention Is All You Need]. This approach enables better parallelization during training [Attention Is All You Need]."

Example when no information available:
"I don't have enough information in the provided papers to answer this question."

Example when refusing comparison:
"I don't have enough information in the provided papers to answer this question."

Remember:
- NO hallucination - use ONLY the provided papers
- ALWAYS include citations for factual statements
- Refuse comparison/evaluation questions unless papers explicitly address them
- Be direct and concise
- If unsure, say you don't have enough information
"""

        return LlmAgent(
            name="AnswerAgent",
            model=self.model,
            description="Answers questions about research papers with citations",
            instruction=instruction
        )

    def _format_papers(self, papers: List[Dict]) -> str:
        """
        Format papers for inclusion in the prompt.

        Args:
            papers: List of paper dictionaries

        Returns:
            Formatted string with paper information
        """
        if not papers:
            return "No papers provided."

        formatted = []
        for i, paper in enumerate(papers, 1):
            title = paper.get('title', 'Unknown Title')
            authors = paper.get('authors', [])
            key_finding = paper.get('key_finding', 'No key finding available')

            authors_str = ', '.join(authors[:3])  # First 3 authors
            if len(authors) > 3:
                authors_str += ' et al.'

            paper_text = f"""
Paper {i}:
Title: {title}
Authors: {authors_str}
Key Finding: {key_finding}
"""
            formatted.append(paper_text)

        return '\n'.join(formatted)

    def answer(self, question: str, papers: List[Dict]) -> str:
        """
        Answer a question using retrieved papers.

        Args:
            question: User's question
            papers: List of paper dicts with title, authors, key_finding, etc.

        Returns:
            Answer with citations
        """
        logger.info(f"Answering question: '{question}' using {len(papers)} papers")

        if not papers:
            return "I couldn't find any relevant papers to answer this question."

        # Format papers for the LLM
        papers_context = self._format_papers(papers)

        # Create prompt
        prompt = f"""Question: {question}

Research Papers:
{papers_context}

Please answer the question using the papers above. Remember to include citations."""

        # Run the agent using ADK Runner
        async def run_answer():
            """Run the agent asynchronously."""
            # Create session service
            session_service = InMemorySessionService()

            # Generate unique session ID
            session_id = f"answer_{uuid.uuid4().hex[:8]}"

            # Create session
            session = await session_service.create_session(
                app_name=APP_NAME,
                user_id=DEFAULT_USER_ID,
                session_id=session_id
            )

            # Create runner
            runner = Runner(
                agent=self.agent,
                app_name=APP_NAME,
                session_service=session_service
            )

            # Prepare message
            user_content = types.Content(
                role='user',
                parts=[types.Part(text=prompt)]
            )

            # Run agent and collect response
            response_text = ""
            async for event in runner.run_async(
                user_id=DEFAULT_USER_ID,
                session_id=session_id,
                new_message=user_content
            ):
                if event.is_final_response() and event.content:
                    response_text = event.content.parts[0].text
                    break

            return response_text

        # Run async answer generation
        answer = asyncio.run(run_answer())

        logger.info(f"Generated answer: {answer[:100]}...")

        return answer

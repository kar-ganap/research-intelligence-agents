"""
Confidence Agent

Evaluates answer confidence based on evidence quality, consistency, and coverage.
Does not verify against ground truth - only assesses internal consistency of evidence.
"""

import asyncio
import uuid
from typing import Dict, List, Optional
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from src.agents.base import BaseResearchAgent
from src.utils.config import config, APP_NAME, DEFAULT_USER_ID
import logging
import json
import re

logger = logging.getLogger(__name__)


class ConfidenceAgent(BaseResearchAgent):
    """
    Agent that evaluates answer confidence based on evidence quality.

    Evaluates:
    1. Evidence Strength (40%) - Direct quotes vs weak inference
    2. Consistency (30%) - Papers agree vs contradict
    3. Coverage (20%) - Question fully answered vs partial
    4. Source Quality (10%) - Number and relevance of sources

    Returns confidence score 0.0-1.0 with breakdown and reasoning.
    """

    def __init__(self, model: str = None):
        if model is None:
            model = config.agent.default_model
        super().__init__(name="ConfidenceAgent", model=model)

    def _create_agent(self) -> LlmAgent:
        """Create the confidence evaluation agent."""

        instruction = """You are a research confidence evaluator. Your job is to assess how confident we should be in an answer based on the evidence quality.

You will be given:
- Question: The user's question
- Answer: The generated answer with citations
- Papers: List of retrieved papers with their key findings
- Contradictions: Any detected conflicts between papers (optional)

Your task is to evaluate confidence based on these factors:

1. **Evidence Strength** (0.0-1.0):
   - 1.0: Direct quotes, exact facts from primary sources, explicit citations
   - 0.7: Clear evidence but paraphrased or from secondary sources
   - 0.4: Weak evidence requiring inference, vague claims
   - 0.0: No evidence, complete speculation

2. **Consistency** (0.0-1.0):
   - 1.0: All papers agree, no contradictions detected
   - 0.7: Most papers agree with minor differences
   - 0.4: Mixed evidence, some disagreement
   - 0.0: Direct contradictions between papers

3. **Coverage** (0.0-1.0):
   - 1.0: Question completely answered, all parts addressed
   - 0.7: Most of question answered, minor gaps
   - 0.4: Partial answer, significant gaps
   - 0.0: Question not answered at all

4. **Source Quality** (0.0-1.0):
   - Consider: number of papers (more is better), relevance to question
   - 1.0: Multiple highly relevant papers
   - 0.7: 2-3 relevant papers
   - 0.4: Only 1 paper or low relevance
   - 0.0: No relevant sources

Important Guidelines:
- If the answer explicitly states "I don't have enough information", evidence_strength should be 0.0
- If contradictions are detected, consistency should be low (<0.4)
- If papers are irrelevant to the question, source_quality should be low
- Be conservative - only give high scores when evidence is truly strong

Output Format (JSON only, no other text):
{
    "evidence_strength": 0.0-1.0,
    "consistency": 0.0-1.0,
    "coverage": 0.0-1.0,
    "source_quality": 0.0-1.0,
    "final_score": 0.0-1.0,
    "reasoning": "Brief 1-2 sentence explanation of the score",
    "warning": "Optional warning if confidence is low or contradictions exist (can be null)"
}

Calculate final_score as weighted average:
- Evidence Strength: 40%
- Consistency: 30%
- Coverage: 20%
- Source Quality: 10%

Return ONLY valid JSON, no markdown, no code blocks."""

        return LlmAgent(
            name="ConfidenceAgent",
            model=self.model,
            description="Evaluates answer confidence based on evidence quality",
            instruction=instruction
        )

    def score_confidence(
        self,
        question: str,
        answer: str,
        papers: List[Dict],
        contradictions: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Score answer confidence based on evidence quality.

        Args:
            question: The user's question
            answer: The generated answer with citations
            papers: List of retrieved papers with their data
            contradictions: Optional list of detected contradictions from Phase 2.1

        Returns:
            {
                'final_score': float (0.0-1.0),
                'evidence_strength': float,
                'consistency': float,
                'coverage': float,
                'source_quality': float,
                'reasoning': str,
                'warning': Optional[str]
            }
        """
        logger.info(f"Scoring confidence for question: {question[:50]}...")

        # Build papers summary
        papers_summary = "\n".join([
            f"Paper {i+1}: {p.get('title', 'Unknown')}\n"
            f"  Authors: {', '.join(p.get('authors', ['Unknown'])[:3])}\n"
            f"  Key Finding: {p.get('key_finding', 'N/A')[:200]}"
            for i, p in enumerate(papers[:5])  # Limit to 5 papers to avoid token limits
        ])

        # Build contradictions summary
        contradictions_summary = ""
        if contradictions and len(contradictions) > 0:
            contradictions_summary = "\n\nContradictions detected:\n" + "\n".join([
                f"- {c.get('evidence', 'Conflicting evidence found')}"
                for c in contradictions[:3]
            ])

        # Create prompt
        prompt = f"""Question: {question}

Answer: {answer}

Retrieved Papers:
{papers_summary}
{contradictions_summary}

Evaluate the confidence we should have in this answer based on the evidence quality."""

        # Run the agent
        async def run_evaluation():
            session_service = InMemorySessionService()
            session_id = f"confidence_{uuid.uuid4().hex[:8]}"

            session = await session_service.create_session(
                app_name=APP_NAME,
                user_id=DEFAULT_USER_ID,
                session_id=session_id
            )

            agent = self._create_agent()
            runner = Runner(
                agent=agent,
                app_name=APP_NAME,
                session_service=session_service
            )

            user_content = types.Content(
                role='user',
                parts=[types.Part(text=prompt)]
            )

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

        response = asyncio.run(run_evaluation())

        # Parse JSON response
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_match = re.search(r'\{.*?\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    logger.error("No JSON found in confidence response")
                    return self._default_confidence_score("Failed to parse response")

            result = json.loads(json_str)

            # Validate and normalize scores
            final_score = float(result.get('final_score', 0.5))
            evidence_strength = float(result.get('evidence_strength', 0.5))
            consistency = float(result.get('consistency', 0.5))
            coverage = float(result.get('coverage', 0.5))
            source_quality = float(result.get('source_quality', 0.5))

            # Clamp all scores to [0, 1]
            final_score = max(0.0, min(1.0, final_score))
            evidence_strength = max(0.0, min(1.0, evidence_strength))
            consistency = max(0.0, min(1.0, consistency))
            coverage = max(0.0, min(1.0, coverage))
            source_quality = max(0.0, min(1.0, source_quality))

            logger.info(f"Confidence score: {final_score:.2f}")

            return {
                'final_score': final_score,
                'evidence_strength': evidence_strength,
                'consistency': consistency,
                'coverage': coverage,
                'source_quality': source_quality,
                'reasoning': result.get('reasoning', 'Confidence evaluated based on evidence quality'),
                'warning': result.get('warning')
            }

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Failed to parse confidence response: {e}")
            logger.error(f"Response was: {response[:200]}")
            return self._default_confidence_score(f"Parse error: {str(e)}")

    def _default_confidence_score(self, reason: str) -> Dict:
        """Return a default medium confidence score when parsing fails."""
        return {
            'final_score': 0.5,
            'evidence_strength': 0.5,
            'consistency': 0.5,
            'coverage': 0.5,
            'source_quality': 0.5,
            'reasoning': f"Unable to evaluate confidence accurately: {reason}",
            'warning': "Confidence score may be inaccurate due to evaluation error"
        }

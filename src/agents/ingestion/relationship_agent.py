"""
Relationship Agent

Detects relationships between research papers by comparing their key findings.
Identifies supports, contradicts, and extends relationships.
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


class RelationshipAgent(BaseResearchAgent):
    """
    Agent that detects relationships between research papers.

    Compares a new paper against existing papers to identify:
    - supports: Similar findings, corroborating evidence
    - contradicts: Conflicting findings
    - extends: Builds upon previous work
    """

    def __init__(self, model: str = None):
        if model is None:
            model = config.agent.default_model
        super().__init__(name="RelationshipAgent", model=model)

    def _create_agent(self) -> LlmAgent:
        """Create the relationship detection agent."""

        instruction = """
You are an expert at analyzing research papers and identifying relationships between them.

Given two papers (Paper A and Paper B), determine if there is a relationship:

Relationship Types:
1. supports: Paper A has similar findings to Paper B, provides corroborating evidence
   - Example: Both papers show improvements using similar methods
   - Example: Papers validate each other's claims

2. contradicts: Paper A has conflicting findings with Paper B
   - Example: Paper A claims method works, Paper B shows negative results
   - Example: Different conclusions about effectiveness

3. extends: Paper A builds upon or extends Paper B's work
   - Example: Paper A uses Paper B's method and adds improvements
   - Example: Paper A applies Paper B's technique to a new domain

4. none: Papers are unrelated or relationship is too weak

Your task:
1. Read the key findings from both papers
2. Identify the relationship type (supports/contradicts/extends/none)
3. Assign a confidence score (0.0-1.0)
4. Provide brief evidence (1-2 sentences)

Output Format (JSON):
{
  "relationship_type": "supports",
  "confidence": 0.85,
  "evidence": "Both papers demonstrate improvements in translation quality using attention mechanisms."
}

Guidelines:
- Only assign a relationship if confidence > 0.6
- If uncertain or papers are unrelated, use "none"
- Be conservative with "contradicts" - only use for clear conflicts
- "supports" is most common for papers in similar areas
- Evidence should reference specific findings from both papers
"""

        return LlmAgent(
            name="RelationshipAgent",
            model=self.model,
            description="Detects relationships between research papers",
            instruction=instruction
        )

    def detect_relationship(self, paper_a: Dict, paper_b: Dict) -> Dict:
        """
        Detect relationship between two papers.

        Args:
            paper_a: First paper with title, authors, key_finding
            paper_b: Second paper

        Returns:
            {
                'relationship_type': str,  # supports/contradicts/extends/none
                'confidence': float,       # 0.0-1.0
                'evidence': str           # Brief explanation
            }
        """
        logger.info(f"Detecting relationship: '{paper_a.get('title', 'Unknown')[:50]}...' vs '{paper_b.get('title', 'Unknown')[:50]}...'")

        # Format papers for comparison
        prompt = f"""Compare these two papers and identify their relationship:

Paper A:
Title: {paper_a.get('title', 'Unknown')}
Authors: {', '.join(paper_a.get('authors', [])[:3])}
Key Finding: {paper_a.get('key_finding', 'Unknown')}

Paper B:
Title: {paper_b.get('title', 'Unknown')}
Authors: {', '.join(paper_b.get('authors', [])[:3])}
Key Finding: {paper_b.get('key_finding', 'Unknown')}

Analyze the relationship between Paper A and Paper B."""

        # Run the agent
        async def run_detection():
            session_service = InMemorySessionService()
            session_id = f"relationship_{uuid.uuid4().hex[:8]}"

            session = await session_service.create_session(
                app_name=APP_NAME,
                user_id=DEFAULT_USER_ID,
                session_id=session_id
            )

            runner = Runner(
                agent=self.agent,
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

        response = asyncio.run(run_detection())

        # Parse JSON response
        import json
        import re

        try:
            # Extract JSON from response
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_match = re.search(r'\{.*?\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("No JSON found in response")

            result = json.loads(json_str)

            # Validate and normalize
            relationship_type = result.get('relationship_type', 'none')
            confidence = float(result.get('confidence', 0.0))
            evidence = result.get('evidence', 'No evidence provided')

            # Validate relationship type
            valid_types = ['supports', 'contradicts', 'extends', 'none']
            if relationship_type not in valid_types:
                logger.warning(f"Invalid relationship type: {relationship_type}, defaulting to 'none'")
                relationship_type = 'none'

            # Clamp confidence to [0, 1]
            confidence = max(0.0, min(1.0, confidence))

            logger.info(f"Relationship: {relationship_type} (confidence: {confidence:.2f})")

            return {
                'relationship_type': relationship_type,
                'confidence': confidence,
                'evidence': evidence
            }

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Failed to parse relationship response: {e}")
            logger.error(f"Raw response: {response}")

            return {
                'relationship_type': 'none',
                'confidence': 0.0,
                'evidence': 'Failed to parse relationship detection response'
            }

    def detect_relationships_batch(
        self,
        new_paper: Dict,
        existing_papers: List[Dict],
        min_confidence: float = 0.6
    ) -> List[Dict]:
        """
        Detect relationships between a new paper and existing corpus.

        Args:
            new_paper: New paper to compare
            existing_papers: List of existing papers in corpus
            min_confidence: Minimum confidence threshold (default 0.6)

        Returns:
            List of relationships with paper IDs and metadata
        """
        logger.info(f"Detecting relationships for new paper against {len(existing_papers)} existing papers")

        relationships = []

        for existing_paper in existing_papers:
            # Skip if same paper
            if new_paper.get('paper_id') == existing_paper.get('paper_id'):
                continue

            # Detect relationship
            result = self.detect_relationship(new_paper, existing_paper)

            # Only include if confidence meets threshold and not "none"
            if result['confidence'] >= min_confidence and result['relationship_type'] != 'none':
                relationships.append({
                    'source_paper_id': new_paper.get('paper_id'),
                    'target_paper_id': existing_paper.get('paper_id'),
                    'relationship_type': result['relationship_type'],
                    'confidence': result['confidence'],
                    'evidence': result['evidence']
                })

                logger.info(f"Found relationship: {result['relationship_type']} (confidence: {result['confidence']:.2f})")

        logger.info(f"Found {len(relationships)} relationships above threshold")

        return relationships

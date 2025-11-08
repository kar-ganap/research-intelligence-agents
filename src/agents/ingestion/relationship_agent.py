"""
Relationship Agent

Detects relationships between research papers by comparing their key findings.
Identifies supports, contradicts, and extends relationships.
"""

import asyncio
import uuid
from typing import Dict, List
from datetime import datetime
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from src.agents.base import BaseResearchAgent
from src.utils.config import config, APP_NAME, DEFAULT_USER_ID
import logging

logger = logging.getLogger(__name__)


def parse_date(date_str: str) -> datetime:
    """Parse arXiv date string to datetime."""
    if not date_str:
        return None

    try:
        # Try ISO format first
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except:
        try:
            # Try common formats
            for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y']:
                try:
                    return datetime.strptime(date_str, fmt)
                except:
                    continue
        except:
            pass
    return None


def get_paper_date(paper: Dict) -> datetime:
    """Extract publication date from paper."""
    # Try 'published' field first
    if 'published' in paper and paper['published']:
        date = parse_date(paper['published'])
        if date:
            return date

    # Try 'updated' field
    if 'updated' in paper and paper['updated']:
        date = parse_date(paper['updated'])
        if date:
            return date

    return None


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

Given two papers (Paper A and Paper B), determine if there is a meaningful relationship.

Relationship Types:
1. **extends**: Paper A builds upon or extends Paper B's work
   - Paper A uses Paper B's method and adds improvements
   - Paper A applies Paper B's technique to a new domain
   - Paper A addresses limitations mentioned in Paper B

2. **supports**: Paper A has similar findings to Paper B
   - Both papers show improvements using similar methods
   - Papers validate each other's claims with independent evidence
   - Papers reach similar conclusions through different approaches

3. **contradicts**: Paper A has conflicting findings with Paper B
   - Paper A claims method works, Paper B shows negative results
   - Different conclusions about effectiveness or applicability
   - NOTE: Only use if conflict is clear and direct

4. **none**: Papers are unrelated or relationship is too weak

Your task:
1. Read the abstracts and key findings from both papers carefully
2. Look for meaningful connections - even moderate-strength relationships are valuable
3. Identify the relationship type (extends/supports/contradicts/none)
4. Assign a confidence score (0.0-1.0)
5. Provide brief evidence (1-2 sentences)

Output Format (JSON):
{
  "relationship_type": "extends",
  "confidence": 0.75,
  "evidence": "Paper A extends Paper B's attention mechanism by adding sparse patterns for efficiency."
}

Guidelines:
- Focus on finding real relationships - weak relationships are OK if they're accurate
- Evidence should reference specific findings from both papers
- For "extends": Look for citations, method reuse, or explicit building-upon
- For "supports": Look for independent validation, similar results
- For "contradicts": Be conservative - only use for clear conflicts
"""

        # Create generation config with temperature
        gen_config = types.GenerateContentConfig(
            temperature=config.agent.temperature
        )

        return LlmAgent(
            name="RelationshipAgent",
            model=self.model,
            description="Detects relationships between research papers",
            instruction=instruction,
            generate_content_config=gen_config
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
        # Include abstract if available, otherwise fall back to key_finding
        paper_a_abstract = paper_a.get('abstract', paper_a.get('key_finding', 'Unknown'))
        paper_b_abstract = paper_b.get('abstract', paper_b.get('key_finding', 'Unknown'))

        prompt = f"""Compare these two papers and identify their relationship:

Paper A:
Title: {paper_a.get('title', 'Unknown')}
Authors: {', '.join(paper_a.get('authors', [])[:3])}
Abstract: {paper_a_abstract}
Key Finding: {paper_a.get('key_finding', 'Unknown')}

Paper B:
Title: {paper_b.get('title', 'Unknown')}
Authors: {', '.join(paper_b.get('authors', [])[:3])}
Abstract: {paper_b_abstract}
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
        new_paper_date = get_paper_date(new_paper)
        temporal_violations = 0

        for existing_paper in existing_papers:
            # Skip if same paper
            if new_paper.get('paper_id') == existing_paper.get('paper_id'):
                continue

            # Check temporal constraint: new_paper must be published after or at same time as existing_paper
            # for directional relationships (extends, supports, contradicts)
            existing_paper_date = get_paper_date(existing_paper)

            if new_paper_date and existing_paper_date:
                if new_paper_date < existing_paper_date:
                    # New paper is older than existing paper - skip relationship detection
                    temporal_violations += 1
                    logger.debug(f"Skipping temporal violation: {new_paper.get('title', 'Unknown')[:50]}... "
                               f"({new_paper_date.strftime('%Y-%m-%d')}) -> "
                               f"{existing_paper.get('title', 'Unknown')[:50]}... "
                               f"({existing_paper_date.strftime('%Y-%m-%d')})")
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

        if temporal_violations > 0:
            logger.info(f"Skipped {temporal_violations} papers due to temporal constraints")

        logger.info(f"Found {len(relationships)} relationships above threshold")

        return relationships

    def detect_relationships_batch_filtered(
        self,
        new_paper: Dict,
        existing_papers: List[Dict],
        embeddings_cache: Dict[str, List[float]],
        top_k: int = 20,
        min_similarity: float = 0.6
    ) -> List[Dict]:
        """
        Detect relationships using embedding-based pre-filtering (Option 1)
        and selective confidence thresholds (Option 5).

        Args:
            new_paper: New paper to compare
            existing_papers: List of existing papers in corpus
            embeddings_cache: Dict mapping paper_id -> embedding vector
            top_k: Maximum number of similar papers to compare (default 20)
            min_similarity: Minimum embedding similarity threshold (default 0.6)

        Returns:
            List of relationships with paper IDs, metadata, and similarity scores
        """
        from src.utils.embeddings import find_similar_papers

        logger.info(f"Detecting relationships for new paper with embedding pre-filtering")

        # Option 1: Filter to semantically similar papers first
        similar_papers = find_similar_papers(
            new_paper,
            existing_papers,
            embeddings_cache,
            top_k=top_k,
            min_similarity=min_similarity
        )

        logger.info(f"Filtered from {len(existing_papers)} to {len(similar_papers)} similar papers "
                   f"(reduction: {(1 - len(similar_papers)/len(existing_papers))*100:.1f}%)")

        relationships = []
        new_paper_date = get_paper_date(new_paper)
        temporal_violations = 0

        # Option 5: Selective thresholds by relationship type
        thresholds = {
            'contradicts': 0.7,  # High bar - need to be sure about conflicts
            'extends': 0.5,      # Medium bar - building upon is common
            'supports': 0.5,     # Medium bar - similar findings are common
        }

        for similar_paper, sim_score in similar_papers:
            # Check temporal constraint
            existing_paper_date = get_paper_date(similar_paper)

            if new_paper_date and existing_paper_date:
                if new_paper_date < existing_paper_date:
                    temporal_violations += 1
                    logger.debug(f"Skipping temporal violation: {new_paper.get('title', 'Unknown')[:50]}... "
                               f"({new_paper_date.strftime('%Y-%m-%d')}) -> "
                               f"{similar_paper.get('title', 'Unknown')[:50]}... "
                               f"({existing_paper_date.strftime('%Y-%m-%d')})")
                    continue

            # Detect relationship
            result = self.detect_relationship(new_paper, similar_paper)

            rel_type = result['relationship_type']

            # Skip "none" relationships
            if rel_type == 'none':
                continue

            # Apply selective threshold based on relationship type
            min_conf = thresholds.get(rel_type, 0.6)

            if result['confidence'] >= min_conf:
                relationships.append({
                    'source_paper_id': new_paper.get('paper_id'),
                    'target_paper_id': similar_paper.get('paper_id'),
                    'relationship_type': rel_type,
                    'confidence': result['confidence'],
                    'evidence': result['evidence'],
                    'similarity_score': sim_score  # Store embedding similarity for analysis
                })

                logger.info(f"Found relationship: {rel_type} (confidence: {result['confidence']:.2f}, "
                          f"similarity: {sim_score:.2f})")

        if temporal_violations > 0:
            logger.info(f"Skipped {temporal_violations} papers due to temporal constraints")

        logger.info(f"Found {len(relationships)} relationships with filtered approach")

        return relationships

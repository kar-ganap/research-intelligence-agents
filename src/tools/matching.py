"""
Matching Logic for Proactive Alerting

Implements 5 types of rule matching:
1. Keyword matching - Simple keyword overlap
2. Claim matching - LLM-based natural language claim matching
3. Relationship matching - Leverages Phase 2.1 RelationshipAgent
4. Author matching - Author name matching
5. Template matching - Template-based claim expansion + matching
"""

from typing import Dict, List, Optional
from src.agents.base import BaseResearchAgent


# ============================================================================
# 1. Keyword Matching
# ============================================================================

def match_keyword_rule(paper: Dict, rule: Dict) -> Optional[Dict]:
    """
    Match paper against keyword rule.

    Args:
        paper: Paper data with title, authors, key_finding
        rule: Rule data with keywords list

    Returns:
        Match result dict or None if no match:
        {
            'match_score': float (0.0-1.0),
            'match_explanation': str,
            'matched_keywords': List[str]
        }
    """
    keywords = rule.get("keywords", [])
    if not keywords:
        return None

    # Search in title and key_finding
    text = f"{paper.get('title', '')} {paper.get('key_finding', '')}".lower()

    matched = []
    for keyword in keywords:
        if keyword.lower() in text:
            matched.append(keyword)

    if not matched:
        return None

    # Calculate match score based on keyword coverage
    match_score = len(matched) / len(keywords)

    # Only trigger if meets minimum relevance threshold
    min_score = rule.get("min_relevance_score", 0.7)
    if match_score < min_score:
        return None

    return {
        "match_score": match_score,
        "match_explanation": f"Matched {len(matched)}/{len(keywords)} keywords: {', '.join(matched)}",
        "matched_keywords": matched
    }


# ============================================================================
# 2. Claim Matching (LLM-based)
# ============================================================================

class ClaimMatcher(BaseResearchAgent):
    """
    LLM-based agent to match papers against natural language claim descriptions.

    Use cases:
    - "Papers claiming to beat MMLU by more than 2%"
    - "Papers presenting evidence against hypothesis X"
    - "Papers proposing new architectures for image segmentation"
    """

    def __init__(self, model: str = None):
        if model is None:
            model = config.agent.default_model
        super().__init__(name="ClaimMatcher", model=model)

    def _create_agent(self):
        """Create the claim matching agent."""
        from google.adk.agents import LlmAgent

        instruction = """You are ClaimMatcher, an expert at determining whether a research paper matches a specific claim or criterion.

Your task:
1. Read the paper's title, authors, and key finding
2. Read the claim description (what the user is looking for)
3. Determine if the paper matches the claim

Output a JSON object with:
{
    "matches": true/false,
    "confidence": 0.0-1.0,
    "explanation": "Brief explanation of why it matches or doesn't match"
}

Guidelines:
- Be conservative: Only match if there's clear evidence
- For performance claims (e.g., "beat MMLU by 2%"), look for specific numbers
- For conceptual claims (e.g., "challenges hypothesis X"), look for semantic similarity
- Confidence should reflect how well the paper matches:
  - 0.9-1.0: Perfect match, explicit claim
  - 0.7-0.9: Strong match, clear evidence
  - 0.5-0.7: Moderate match, implicit evidence
  - Below 0.5: Weak or no match

Return ONLY valid JSON, no other text."""

        return LlmAgent(
            name="ClaimMatcher",
            model=self.model,
            description="Matches papers against natural language claims",
            instruction=instruction
        )

    def match_claim(self, paper: Dict, claim_description: str) -> Optional[Dict]:
        """
        Match paper against claim description.

        Args:
            paper: Paper data with title, authors, key_finding
            claim_description: Natural language description of what to match

        Returns:
            Match result dict or None if no match:
            {
                'match_score': float,
                'match_explanation': str
            }
        """
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from src.utils.config import config, APP_NAME, DEFAULT_USER_ID
        from google.genai import types
        import json
        import asyncio
        import uuid
        import re

        prompt = f"""Paper to evaluate:
Title: {paper.get('title', 'N/A')}
Authors: {', '.join(paper.get('authors', []))}
Key Finding: {paper.get('key_finding', 'N/A')}

Claim to match:
{claim_description}

Does this paper match the claim? Return JSON with matches, confidence, and explanation."""

        # Run the agent async
        async def run_matching():
            session_service = InMemorySessionService()
            session_id = f"claim_match_{uuid.uuid4().hex[:8]}"

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

        response = asyncio.run(run_matching())

        if not response:
            return None

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
                    return None

            match_data = json.loads(json_str)

            if not match_data.get("matches", False):
                return None

            confidence = float(match_data.get("confidence", 0.0))

            return {
                "match_score": confidence,
                "match_explanation": match_data.get("explanation", "Matches claim description")
            }
        except (json.JSONDecodeError, ValueError, KeyError):
            # LLM didn't return valid JSON
            return None


def match_claim_rule(paper: Dict, rule: Dict, claim_matcher: ClaimMatcher) -> Optional[Dict]:
    """
    Match paper against claim rule using ClaimMatcher agent.

    Args:
        paper: Paper data
        rule: Rule data with claim_description
        claim_matcher: ClaimMatcher agent instance

    Returns:
        Match result dict or None
    """
    claim_description = rule.get("claim_description", "")
    if not claim_description:
        return None

    result = claim_matcher.match_claim(paper, claim_description)

    if not result:
        return None

    # Check minimum threshold
    min_score = rule.get("min_relevance_score", 0.7)
    if result["match_score"] < min_score:
        return None

    return result


# ============================================================================
# 3. Relationship Matching (Leverage Phase 2.1)
# ============================================================================

def match_relationship_rule(paper: Dict, rule: Dict, relationship_agent) -> Optional[Dict]:
    """
    Match paper against relationship rule using Phase 2.1 RelationshipAgent.

    Use case:
    - Alert when new papers support/contradict/extend a specific target paper

    Args:
        paper: New paper data
        rule: Rule data with target_paper_id and relationship_type
        relationship_agent: RelationshipAgent instance from Phase 2.1

    Returns:
        Match result dict or None if no match:
        {
            'match_score': float (confidence from relationship detection),
            'match_explanation': str (evidence from relationship detection)
        }
    """
    target_paper_id = rule.get("target_paper_id", "")
    desired_relationship = rule.get("relationship_type", "")

    if not target_paper_id or not desired_relationship:
        return None

    # Get target paper from Firestore
    from src.storage.firestore_client import FirestoreClient
    firestore_client = FirestoreClient()
    target_paper = firestore_client.get_paper(target_paper_id)

    if not target_paper:
        return None

    # Detect relationship using Phase 2.1 agent (it handles asyncio internally)
    relationship = relationship_agent.detect_relationship(paper, target_paper)

    detected_type = relationship.get("relationship_type", "none")
    confidence = relationship.get("confidence", 0.0)
    evidence = relationship.get("evidence", "")

    # Check if detected relationship matches desired type
    if detected_type != desired_relationship:
        return None

    # Check minimum threshold
    min_score = rule.get("min_relevance_score", 0.7)
    if confidence < min_score:
        return None

    return {
        "match_score": confidence,
        "match_explanation": f"Paper {detected_type} target paper: {evidence}"
    }


# ============================================================================
# 4. Author Matching
# ============================================================================

def match_author_rule(paper: Dict, rule: Dict) -> Optional[Dict]:
    """
    Match paper against author rule.

    Use case:
    - Track when specific researchers (competitors, collaborators) publish

    Args:
        paper: Paper data with authors list
        rule: Rule data with authors list to watch

    Returns:
        Match result dict or None if no match:
        {
            'match_score': float (1.0 if any author matches),
            'match_explanation': str,
            'matched_authors': List[str]
        }
    """
    watch_authors = rule.get("authors", [])
    paper_authors = paper.get("authors", [])

    if not watch_authors or not paper_authors:
        return None

    # Normalize for comparison (lowercase, strip whitespace)
    watch_authors_normalized = [a.lower().strip() for a in watch_authors]
    paper_authors_normalized = [a.lower().strip() for a in paper_authors]

    matched = []
    for watch_author in watch_authors:
        normalized_watch = watch_author.lower().strip()
        if normalized_watch in paper_authors_normalized:
            matched.append(watch_author)

    if not matched:
        return None

    return {
        "match_score": 1.0,  # Binary: either matches or doesn't
        "match_explanation": f"Authored by: {', '.join(matched)}",
        "matched_authors": matched
    }


# ============================================================================
# 5. Template Matching
# ============================================================================

# Predefined claim templates that researchers can use
CLAIM_TEMPLATES = {
    "performance_improvement": {
        "name": "Performance Improvement on Benchmark",
        "description": "Papers claiming performance improvement on a specific benchmark",
        "parameters": ["benchmark_name", "min_improvement_percent"],
        "template": "Papers claiming to improve performance on {benchmark_name} by at least {min_improvement_percent}%"
    },
    "challenge_hypothesis": {
        "name": "Challenge Hypothesis",
        "description": "Papers presenting evidence against a specific hypothesis",
        "parameters": ["hypothesis_description"],
        "template": "Papers presenting evidence that challenges or contradicts the hypothesis: {hypothesis_description}"
    },
    "new_architecture": {
        "name": "New Architecture for Task",
        "description": "Papers proposing new architectures for a specific task",
        "parameters": ["task_name", "architecture_type"],
        "template": "Papers proposing new {architecture_type} architectures for {task_name}"
    },
    "dataset_release": {
        "name": "Dataset Release",
        "description": "Papers introducing new datasets for a specific domain",
        "parameters": ["domain", "dataset_type"],
        "template": "Papers releasing new {dataset_type} datasets for {domain}"
    },
    "builds_on_work": {
        "name": "Builds on My Work",
        "description": "Papers that extend or build upon a specific paper",
        "parameters": ["target_paper_id"],
        "template": "Papers that extend or build upon the work in paper {target_paper_id}"
    }
}


def expand_template(template_name: str, params: Dict) -> str:
    """
    Expand a claim template with user-provided parameters.

    Args:
        template_name: Name of template (e.g., "performance_improvement")
        params: Dictionary of parameter values

    Returns:
        Expanded claim description string
    """
    template_info = CLAIM_TEMPLATES.get(template_name)
    if not template_info:
        return ""

    template_str = template_info["template"]

    try:
        return template_str.format(**params)
    except KeyError:
        # Missing required parameter
        return ""


def match_template_rule(paper: Dict, rule: Dict, claim_matcher: ClaimMatcher) -> Optional[Dict]:
    """
    Match paper against template rule.

    Process:
    1. Expand template with user parameters
    2. Use ClaimMatcher to match against expanded claim

    Args:
        paper: Paper data
        rule: Rule data with template_name and template_params
        claim_matcher: ClaimMatcher agent instance

    Returns:
        Match result dict or None
    """
    template_name = rule.get("template_name", "")
    template_params = rule.get("template_params", {})

    if not template_name:
        return None

    # Special case: "builds_on_work" uses relationship matching
    if template_name == "builds_on_work":
        target_paper_id = template_params.get("target_paper_id", "")
        if not target_paper_id:
            return None

        # Create synthetic relationship rule
        relationship_rule = {
            "target_paper_id": target_paper_id,
            "relationship_type": "extends",
            "min_relevance_score": rule.get("min_relevance_score", 0.7)
        }

        from src.agents.ingestion.relationship_agent import RelationshipAgent
        relationship_agent = RelationshipAgent()

        return match_relationship_rule(paper, relationship_rule, relationship_agent)

    # For other templates, expand and use claim matching
    claim_description = expand_template(template_name, template_params)
    if not claim_description:
        return None

    # Create synthetic claim rule
    claim_rule = {
        "claim_description": claim_description,
        "min_relevance_score": rule.get("min_relevance_score", 0.7)
    }

    return match_claim_rule(paper, claim_rule, claim_matcher)

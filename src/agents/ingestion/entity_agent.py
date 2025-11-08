"""
Entity Agent

Extracts key information from research papers:
- Title
- Authors (first 3)
- One key finding

Uses LLM to parse paper text and extract structured information.
"""

import json
import uuid
from typing import Dict
from google.adk.agents import LlmAgent
from src.agents.base import BaseResearchAgent
from src.utils.config import APP_NAME, DEFAULT_USER_ID, config


class EntityAgent(BaseResearchAgent):
    """
    Agent that extracts entities (title, authors, key finding) from paper text.

    Input: Paper text
    Output: Structured JSON with extracted entities
    """

    def __init__(self, model: str = None):
        if model is None:
            model = config.agent.default_model
        super().__init__(name="EntityAgent", model=model)

    def _create_agent(self) -> LlmAgent:
        """Create the entity extraction agent."""

        instruction = """
You are an expert at extracting key information from research papers.

Given the text of a research paper, extract the following information:

1. **Title**: The full title of the paper
2. **Authors**: List of the first 3 authors (or all if less than 3)
3. **Key Finding**: A comprehensive summary (2-4 sentences) of the main contribution or finding

IMPORTANT for Key Finding:
- Include the main contribution or innovation
- Include SPECIFIC performance metrics, scores, or results (e.g., "BLEU score of 28.4", "92% accuracy")
- Include benchmark names and datasets (e.g., "on WMT 2014 English-to-German", "on ImageNet")
- Include comparisons to baselines if mentioned (e.g., "outperforming previous state-of-the-art by 5%")
- Focus on WHAT was achieved and HOW WELL it performed, not just methodology
- Be precise and extract numbers exactly as they appear

Response format:
{
  "title": "The title of the paper",
  "authors": ["First Author", "Second Author", "Third Author"],
  "key_finding": "2-4 sentences describing the main contribution with specific metrics and performance numbers"
}

Example of a good key_finding:
"We propose the Transformer, a novel architecture based solely on attention mechanisms. On WMT 2014 English-to-German translation, our model achieves a BLEU score of 28.4, and on English-to-French it achieves 41.8 BLEU, establishing new state-of-the-art results. The model trains significantly faster than recurrent architectures while achieving better performance."

If you cannot find some information, use empty strings or empty lists.
"""

        # Use entity-specific temperature for consistent extraction
        from google.genai import types
        gen_config = types.GenerateContentConfig(
            temperature=config.agent.entity_temperature  # 0.2 - needs consistency
        )

        return LlmAgent(
            name="EntityExtractor",
            model=self.model,
            description="Extracts title, authors, and key finding from research papers",
            instruction=instruction,
            generate_content_config=gen_config
        )

    def extract(self, paper_text: str) -> Dict[str, any]:
        """
        Extract entities from paper text.

        Args:
            paper_text: Full text of the paper or first few pages

        Returns:
            Dictionary with title, authors, key_finding
        """
        import asyncio
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types

        # Take first 5000 characters (usually enough for title/authors/abstract)
        # This saves on API costs and latency
        text_sample = paper_text[:5000]

        prompt = f"""Extract the title, authors, and key finding from this research paper:

{text_sample}

Return the information as JSON."""

        async def run_extraction():
            """Run the agent extraction asynchronously."""
            # Create session service
            session_service = InMemorySessionService()

            # Generate unique session ID for this extraction
            session_id = f"entity_extract_{uuid.uuid4().hex[:8]}"

            # Create session using platform-wide app_name
            session = await session_service.create_session(
                app_name=APP_NAME,
                user_id=DEFAULT_USER_ID,
                session_id=session_id
            )

            # Create runner with platform-wide app_name
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

        # Run async extraction
        response_text = asyncio.run(run_extraction())

        try:
            # Parse the JSON response
            # Strip markdown code blocks if present
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]  # Remove ```json
            if response_text.startswith("```"):
                response_text = response_text[3:]  # Remove ```
            if response_text.endswith("```"):
                response_text = response_text[:-3]  # Remove ```

            response_text = response_text.strip()

            result = json.loads(response_text)

            # Validate the result has required fields
            if "title" not in result:
                result["title"] = ""
            if "authors" not in result:
                result["authors"] = []
            if "key_finding" not in result:
                result["key_finding"] = ""

            return result

        except json.JSONDecodeError as e:
            # Fallback: return raw response
            return {
                "title": "",
                "authors": [],
                "key_finding": response_text,
                "error": f"Failed to parse JSON: {str(e)}",
                "raw_response": response_text
            }

    def extract_with_metadata(self, paper_text: str, pdf_metadata: Dict = None) -> Dict[str, any]:
        """
        Extract entities and merge with PDF metadata as fallback.

        Args:
            paper_text: Full text of the paper
            pdf_metadata: Optional PDF metadata from PyMuPDF

        Returns:
            Dictionary with extracted entities, using metadata as fallback
        """
        result = self.extract(paper_text)

        # Use PDF metadata as fallback if extraction failed
        if pdf_metadata:
            if not result.get("title") and pdf_metadata.get("title"):
                result["title"] = pdf_metadata["title"]

            if not result.get("authors") and pdf_metadata.get("author"):
                # PDF author field is often a single string
                result["authors"] = [pdf_metadata["author"]]

        return result

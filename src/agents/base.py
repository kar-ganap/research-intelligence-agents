"""
Base agent class for Research Intelligence Platform

Provides common functionality for all agents.
"""

from google.adk.agents import LlmAgent
from typing import List, Callable, Optional
import logging

logger = logging.getLogger(__name__)


class BaseResearchAgent:
    """Base class for all research intelligence agents"""

    def __init__(self, name: str, model: str = "gemini-2.0-flash-exp"):
        self.name = name
        self.model = model
        self._agent: Optional[LlmAgent] = None
        logger.info(f"Initialized {name}")

    def create_agent(
        self,
        description: str,
        instruction: str,
        tools: List[Callable],
        output_key: str
    ) -> LlmAgent:
        """
        Factory method to create ADK agent

        Args:
            description: Brief description for routing
            instruction: Detailed instruction for the agent
            tools: List of tool functions
            output_key: Key to store output in state

        Returns:
            LlmAgent instance
        """
        return LlmAgent(
            name=self.name,
            model=self.model,
            description=description,
            instruction=instruction,
            tools=tools,
            output_key=output_key
        )

    @property
    def agent(self) -> LlmAgent:
        """Lazy load agent"""
        if self._agent is None:
            self._agent = self._create_agent()
        return self._agent

    def _create_agent(self) -> LlmAgent:
        """Override in subclass to define agent"""
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _create_agent()"
        )

    def run(self, input_data: dict) -> dict:
        """Run the agent with input data"""
        logger.info(f"Running {self.name}")
        return self.agent.run(input_data)

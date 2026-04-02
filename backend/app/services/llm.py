"""
LLM service for generating communication choices using LangChain.

Uses chains from app.chains for prompts and LCEL; this service creates the LLM,
invokes the choices chain, and maps results to the API shape.
"""
from __future__ import annotations

import sys
from typing import List, Optional, TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from app.chains.choices_chain import (
    ChoicesChainInput,
    ChoicesOutput,
    create_choices_chain,
)
from app.settings import get_settings
from app.utils.logging import get_logger
from app.utils.retry import async_with_retry_and_timing

logger = get_logger(__name__)


class ChoiceResult(TypedDict, total=False):
    """Typed result for a single choice (avoids Dict[str, Any])."""

    text: str
    probability: float
    arasaac_keywords: Optional[List[str]]


# Fallback choices returned when the LLM call fails.
_FALLBACK_CHOICES: List[ChoiceResult] = [
    {"text": "Yes", "probability": 0.5},
    {"text": "No", "probability": 0.5},
    {"text": "More", "probability": 0.3},
    {"text": "Done", "probability": 0.2},
]


class LLMService:
    """Service for generating communication choices via the choices chain."""

    def __init__(
        self,
        provider: str = "openai",
        model: str = "",
        temperature: float = 0.7,
    ) -> None:
        """
        Initialize the LLM service.

        Args:
            provider: "openai" or "anthropic".
            model: Model name (e.g. "gpt-4", "claude-3-opus-20240229").
            temperature: Sampling temperature (0.0 to 2.0).
        """
        self.provider = provider.lower()
        self.model = model
        self.temperature = temperature
        self._llm = self._create_llm()

    def _create_llm(self):
        """Create the chat model instance for the configured provider."""
        settings = get_settings()
        if self.provider == "openai":
            api_key = settings.openai_api_key
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY not set. Set it in .env or environment."
                )
            model_name = self.model or "gpt-4"
            timeout = settings.llm_request_timeout_seconds
            return ChatOpenAI(
                model=model_name,
                temperature=self.temperature,
                api_key=api_key,
                request_timeout=timeout,
            )
        if self.provider == "anthropic":
            api_key = settings.anthropic_api_key
            if not api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY not set. Set it in .env or environment."
                )
            model_name = self.model or "claude-3-opus-20240229"
            timeout = settings.llm_request_timeout_seconds
            return ChatAnthropic(
                model=model_name,
                temperature=self.temperature,
                api_key=api_key,
                request_timeout=timeout,
            )
        raise ValueError(
            f"Unsupported provider: {self.provider}. Supported: 'openai', 'anthropic'"
        )

    async def generate_choices(
        self,
        system_prompt: str,
        conversation_history: List[dict],
        user_notes: Optional[str] = None,
        caregiver_description: Optional[str] = None,
        current_text: Optional[str] = None,
    ) -> List[ChoiceResult]:
        """
        Generate 2–8 communication choices using the choices chain.

        Args:
            system_prompt: System prompt from config.
            conversation_history: List of {"role": "...", "content": "..."}.
            user_notes: Optional user profile notes.
            caregiver_description: Optional caregiver description.
            current_text: Optional current text being composed.

        Returns:
            List of {"text": str, "probability": float}, sorted by probability descending.
        """
        context_parts: List[str] = []
        if user_notes:
            context_parts.append(f"User Profile:\n{user_notes}\n")
        if caregiver_description:
            context_parts.append(f"Caregiver Profile:\n{caregiver_description}\n")
        if current_text:
            context_parts.append(f"Current text being composed: {current_text}\n")
        context = "\n".join(context_parts)

        chain_input = ChoicesChainInput(
            system_prompt=system_prompt,
            context=context,
            conversation_history=conversation_history,
        )
        print(system_prompt)
        print(context)
        print(conversation_history)
        print(user_notes)
        print(caregiver_description)
        print(current_text)
        structured_llm = self._llm.with_structured_output(ChoicesOutput)
        chain = create_choices_chain(structured_llm)

        async def _invoke():
            return await chain.ainvoke(chain_input.model_dump())

        try:
            result: ChoicesOutput = await async_with_retry_and_timing(
                logger,
                "LLM generate_choices",
                _invoke,
                transient_exceptions=(ConnectionError, TimeoutError, OSError),
            )
            choices: List[ChoiceResult] = [
                {
                    "text": c.text,
                    "probability": c.probability,
                    "arasaac_keywords": c.arasaac_keywords,
                }
                for c in result.choices
            ]
            choices.sort(key=lambda x: x["probability"], reverse=True)
            return choices
        except Exception as e:
            logger.exception("LLM generate_choices failed: %s", e)
            return _FALLBACK_CHOICES.copy()

    def update_config(
        self, provider: str, model: str, temperature: float
    ) -> None:
        """Update provider, model, and temperature and recreate the LLM."""
        self.provider = provider.lower()
        self.model = model
        self.temperature = temperature
        self._llm = self._create_llm()


_llm_service: Optional[LLMService] = None


def get_llm_service(
    provider: str = "openai",
    model: str = "",
    temperature: float = 0.7,
) -> LLMService:
    """
    Get or create the global LLM service instance.

    Args:
        provider: "openai" or "anthropic".
        model: Model name.
        temperature: Sampling temperature.

    Returns:
        The shared LLMService instance.
    """
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService(
            provider=provider, model=model, temperature=temperature
        )
    else:
        if (
            _llm_service.provider != provider.lower()
            or _llm_service.model != model
            or _llm_service.temperature != temperature
        ):
            _llm_service.update_config(provider, model, temperature)
    return _llm_service


__all__ = ["get_llm_service", "LLMService", "ChoiceResult"]

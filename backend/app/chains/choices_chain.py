"""
LCEL chain for generating communication choices (2–8 options with probabilities).

Input: system prompt, context string, conversation history.
Output: Structured ChoicesOutput (Pydantic) for use by the communication service.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel, Field

from app.chains.prompts import (
    CONTEXT_HEADER,
    ROLE_CAREGIVER_PREFIX,
    ROLE_USER_PREFIX,
)


class ChoiceWithProbability(BaseModel):
    """A single choice with text and probability score."""

    text: str = Field(description="The text of the choice (word or phrase)")
    probability: float = Field(
        description="Probability score between 0.0 and 1.0",
        ge=0.0,
        le=1.0,
    )
    arasaac_keywords: Optional[List[str]] = Field(
        default=None,
        description="1-3 simple keywords for ARASAAC pictogram search (only when AAC pictograms are requested)",
    )


class ChoicesOutput(BaseModel):
    """Structured output: 2–8 choices with probabilities."""

    choices: List[ChoiceWithProbability] = Field(
        description="List of 2 to 8 choices, ordered by probability (highest first)",
        min_length=2,
        max_length=8,
    )


class ChoicesChainInput(BaseModel):
    """Input schema for the choices chain."""

    system_prompt: str = Field(description="System prompt from config")
    context: str = Field(default="", description="User/caregiver/current text context")
    conversation_history: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Messages as [{\"role\": \"user\"|\"assistant\"|\"caregiver\", \"content\": \"...\"}]",
    )


def _build_messages(
    input_dict: Union[Dict[str, Any], ChoicesChainInput],
) -> List[Union[SystemMessage, HumanMessage, AIMessage]]:
    """
    Build LangChain messages from chain input (for LCEL).

    Args:
        input_dict: Dict with system_prompt, context, conversation_history.

    Returns:
        List of SystemMessage, HumanMessage, AIMessage for the LLM.
    """
    data = (
        ChoicesChainInput(**input_dict)
        if isinstance(input_dict, dict)
        else input_dict
    )
    system_content = data.system_prompt
    if data.context:
        system_content += CONTEXT_HEADER + data.context
    messages: List[Union[SystemMessage, HumanMessage, AIMessage]] = [
        SystemMessage(content=system_content)
    ]
    for msg in data.conversation_history:
        role = (msg.get("role") or "").lower()
        content = msg.get("content") or ""
        if role in ("user", "human"):
            messages.append(HumanMessage(content=ROLE_USER_PREFIX + content))
        elif role == "caregiver":
            messages.append(HumanMessage(content=ROLE_CAREGIVER_PREFIX + content))
        elif role in ("assistant", "ai"):
            messages.append(AIMessage(content=content))
    return messages


def create_choices_chain(structured_llm: Any):
    """
    Create the LCEL choices chain: input dict -> messages -> structured output.

    Args:
        structured_llm: LLM with .with_structured_output(ChoicesOutput) already applied.

    Returns:
        A Runnable that accepts ChoicesChainInput (as dict) and returns ChoicesOutput.
    """
    return RunnableLambda(_build_messages) | structured_llm

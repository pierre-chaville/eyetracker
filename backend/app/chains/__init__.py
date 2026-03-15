"""
LangChain chains for LLM-backed features.

Prompts are in dedicated modules; chains use LCEL for composition with
clear input/output schemas. Services call into chains and stay thin.
"""
from app.chains.choices_chain import (
    ChoicesChainInput,
    ChoicesOutput,
    create_choices_chain,
)

__all__ = [
    "ChoicesChainInput",
    "ChoicesOutput",
    "create_choices_chain",
]

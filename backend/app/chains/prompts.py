"""
Prompt constants and fragments for LangChain chains.

System prompts for communication/keyboard are loaded from user config;
this module holds labels and structural fragments used when building messages.
"""
from __future__ import annotations

# Section header appended to system content when context (user/caregiver/current text) is present.
CONTEXT_HEADER = "\n\nContext:\n"

# Labels used when formatting conversation history into messages.
ROLE_USER_PREFIX = "User: "
ROLE_CAREGIVER_PREFIX = "Caregiver: "

"""Factory for constructing the configured LLM gateway.

Picks Gemini or Groq based on `settings.llm_provider` so the rest of the
codebase only depends on the abstract `LLMGateway` port.
"""

from __future__ import annotations

from app.application.ports.llm_gateway import LLMGateway
from app.config import settings
from app.domain.errors import ConfigurationError
from app.infrastructure.llm.gemini_gateway import GeminiLLMGateway
from app.infrastructure.llm.groq_gateway import GroqLLMGateway


def make_llm_gateway() -> LLMGateway:
    provider = (settings.llm_provider or "gemini").strip().lower()
    if provider == "groq":
        return GroqLLMGateway()
    if provider == "gemini":
        return GeminiLLMGateway()
    raise ConfigurationError(
        f"Unknown LLM_PROVIDER '{settings.llm_provider}'. Use 'gemini' or 'groq'."
    )

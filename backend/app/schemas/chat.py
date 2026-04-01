from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: uuid.UUID
    message: str = Field(..., min_length=1, max_length=16_000)


class CitationOut(BaseModel):
    title: str | None = None
    uri: str


class ChatResponse(BaseModel):
    blocked: bool = False
    reply: str | None = None
    safety_reason: str | None = None
    matched_terms: list[str] = Field(default_factory=list)
    citations: list[CitationOut] = Field(default_factory=list)
    web_search_queries: list[str] = Field(default_factory=list)
    blocked_by_model_safety: bool = False
    finish_reason: str | None = None

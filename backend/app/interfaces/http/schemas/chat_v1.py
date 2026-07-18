from __future__ import annotations

import uuid

from pydantic import BaseModel, Field, model_validator

from app.interfaces.http.schemas.chat import CitationOut


class ChatTurnRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=16_000)
    conversation_id: uuid.UUID | None = Field(
        default=None,
        description="Resume this conversation. Omit to start a new one.",
    )
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    @model_validator(mode="after")
    def _validate_latlon_pair(self) -> "ChatTurnRequest":
        if (self.latitude is None) ^ (self.longitude is None):
            raise ValueError("latitude and longitude must both be set or both omitted.")
        return self


class ChatTurnResponse(BaseModel):
    conversation_id: uuid.UUID
    blocked: bool = False
    response_text: str | None = None
    safety_reason: str | None = None
    matched_terms: list[str] = Field(default_factory=list)
    citations: list[CitationOut] = Field(default_factory=list)
    web_search_queries: list[str] = Field(default_factory=list)

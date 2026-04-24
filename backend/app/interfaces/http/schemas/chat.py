from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=16_000)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    @model_validator(mode="after")
    def _validate_latlon_pair(self) -> "ChatRequest":
        if (self.latitude is None) ^ (self.longitude is None):
            raise ValueError("latitude and longitude must both be set or both omitted.")
        return self


class CitationOut(BaseModel):
    source_name: str
    url: str


class ChatResponse(BaseModel):
    blocked: bool = False
    response_text: str | None = None
    safety_reason: str | None = None
    matched_terms: list[str] = Field(default_factory=list)
    citations: list[CitationOut] = Field(default_factory=list)
    web_search_queries: list[str] = Field(default_factory=list)
    blocked_by_model_safety: bool = False
    finish_reason: str | None = None

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class UserMemory:
    """A single Long-Term Memory (LTM) fact extracted about a user.

    Written by the Janitor worker (`SummarizeSession`) after a conversation
    ends — one row per durable, declarative fact (e.g. "User is lactose
    intolerant"), not a rolling log. The Orchestrator's Observe phase can
    semantically search these via `embedding` to pull only the facts relevant
    to the current turn, instead of resending the user's entire history.
    """

    id: uuid.UUID
    user_id: uuid.UUID
    fact_text: str
    embedding: list[float] | None = None
    source: str | None = None
    created_at: datetime | None = None

"""`POST /api/v1/chat` — chat traffic unified onto the `ChatOrchestrator` pipeline.

Supersedes the legacy `POST /chat` (`app/interfaces/http/routers/chat.py`),
which still exists for backwards compatibility but no longer receives new
feature work (Summary Cache, Long-Term Memory, outbound guard). Point clients
at this endpoint going forward.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.application.dtos import GenerateHealthReplyInput
from app.application.use_cases.chat_orchestrated import GenerateHealthReplyViaOrchestrator
from app.interfaces.http.deps import get_current_user_id, make_chat_orchestrated_use_case
from app.interfaces.http.schemas.chat import CitationOut
from app.interfaces.http.schemas.chat_v1 import ChatTurnRequest, ChatTurnResponse

router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.post("/chat", response_model=ChatTurnResponse)
async def chat_turn_v1(
    body: ChatTurnRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    uc: GenerateHealthReplyViaOrchestrator = Depends(make_chat_orchestrated_use_case),
) -> ChatTurnResponse:
    out = await uc.execute(
        GenerateHealthReplyInput(
            user_id=user_id,
            message=body.message,
            conversation_id=body.conversation_id,
            lat=body.latitude,
            lon=body.longitude,
        )
    )
    return ChatTurnResponse(
        conversation_id=out.conversation_id,
        blocked=out.blocked,
        response_text=out.reply_text,
        safety_reason=out.block_reason if out.blocked else None,
        citations=[CitationOut(source_name=c.title or c.url, url=c.url) for c in out.citations],
        web_search_queries=list(out.search_queries),
    )

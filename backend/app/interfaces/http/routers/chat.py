from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.application.dtos import GenerateHealthReplyInput
from app.application.use_cases.chat import GenerateHealthReply
from app.interfaces.http.deps import get_current_user_id, make_chat_use_case
from app.interfaces.http.schemas.chat import ChatRequest, ChatResponse, CitationOut

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat_turn(
    body: ChatRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    uc: GenerateHealthReply = Depends(make_chat_use_case),
) -> ChatResponse:
    out = await uc.execute(
        GenerateHealthReplyInput(
            user_id=user_id,
            message=body.message,
            lat=body.latitude,
            lon=body.longitude,
        )
    )
    return ChatResponse(
        blocked=out.blocked,
        response_text=out.reply_text,
        safety_reason=out.block_reason if out.blocked else None,
        citations=[CitationOut(source_name=c.title or c.url, url=c.url) for c in out.citations],
        web_search_queries=list(out.search_queries),
    )

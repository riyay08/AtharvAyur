"""Conversation lifecycle endpoints — the API side of 'Session Persistence'."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.application.use_cases.conversations import EndConversation
from app.infrastructure.background.summary_worker import run_janitor
from app.interfaces.http.deps import get_current_user_id, make_end_conversation
from app.interfaces.http.schemas.conversation import EndConversationResponse

router = APIRouter(prefix="/api/v1", tags=["conversations"])


@router.post(
    "/conversations/{conversation_id}/end",
    response_model=EndConversationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="End a conversation and schedule the Janitor summarization worker.",
)
async def end_conversation(
    conversation_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    user_id: uuid.UUID = Depends(get_current_user_id),
    uc: EndConversation = Depends(make_end_conversation),
) -> EndConversationResponse:
    """Marks the conversation `ENDED` and kicks off summarization in the background.

    The response returns immediately (202) — summarization + title generation
    happen asynchronously via `run_janitor`. Calling this twice on an already-
    ended conversation is a no-op (no duplicate Janitor run, no duplicate
    `SessionSummary` row); `summary_pending` tells the caller whether a new
    summarization run was actually scheduled.
    """
    result = await uc.execute(conversation_id=conversation_id, user_id=user_id)

    if not result.already_ended:
        background_tasks.add_task(run_janitor, conversation_id)

    return EndConversationResponse(
        conversation_id=conversation_id,
        status=result.conversation.status.value,
        summary_pending=not result.already_ended,
    )

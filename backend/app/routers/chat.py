from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.audit_log import AuditLog
from app.models.chat_history import ChatHistory, ChatRole
from app.models.health_profile import HealthProfile
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse, CitationOut
from app.services.llm_orchestrator import OrchestratorConfigError, generate_health_reply
from app.services.safety_engine import evaluate_message

router = APIRouter(tags=["chat"])

_HISTORY_LIMIT = 5


def _recent_history(db: Session, user_id: uuid.UUID, limit: int = _HISTORY_LIMIT) -> list[ChatHistory]:
    stmt = (
        select(ChatHistory)
        .where(ChatHistory.user_id == user_id)
        .order_by(desc(ChatHistory.timestamp))
        .limit(limit)
    )
    rows = list(db.execute(stmt).scalars().all())
    return list(reversed(rows))


@router.post("/chat", response_model=ChatResponse)
def chat_turn(
    body: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
    user = db.get(User, body.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    profile = db.execute(
        select(HealthProfile).where(HealthProfile.user_id == user.id)
    ).scalar_one_or_none()

    history = _recent_history(db, user.id)

    safety = evaluate_message(body.message, health_profile=profile)
    if not safety.allowed:
        db.add(
            AuditLog(
                actor=str(user.id),
                action=f"chat.safety_block reason={safety.reason.value} terms={','.join(safety.matched_terms)}",
            )
        )
        db.commit()
        return ChatResponse(
            blocked=True,
            reply=safety.escalation_message,
            safety_reason=safety.reason.value,
            matched_terms=list(safety.matched_terms),
        )

    try:
        result = generate_health_reply(
            body.message,
            health_profile=profile,
            chat_history=history,
        )
    except OrchestratorConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    user_row = ChatHistory(
        user_id=user.id,
        role=ChatRole.USER,
        message=body.message,
    )
    assistant_row = ChatHistory(
        user_id=user.id,
        role=ChatRole.ASSISTANT,
        message=result.text,
    )
    db.add(user_row)
    db.add(assistant_row)
    db.add(
        AuditLog(
            actor=str(user.id),
            action="chat.turn_completed",
        )
    )
    db.commit()

    return ChatResponse(
        blocked=False,
        reply=result.text,
        citations=[
            CitationOut(title=c.title, uri=c.uri) for c in result.citations
        ],
        web_search_queries=list(result.web_search_queries),
        blocked_by_model_safety=result.blocked_by_model_safety,
        finish_reason=result.finish_reason,
    )

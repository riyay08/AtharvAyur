"""HTTP-layer tests for POST /api/v1/conversations/{id}/end.

These exercise the real FastAPI app + router wiring, with the DB-backed
dependencies swapped for in-memory fakes via `app.dependency_overrides` — no
real Postgres/LLM calls. `run_janitor` itself is patched out (it does real
DB + LLM work) so we only assert that it was *scheduled correctly*, which is
this endpoint's job.
"""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.domain.entities import Conversation, ConversationStatus
from app.interfaces.http.deps import get_current_user_id, make_end_conversation
from app.main import create_app
from tests.fakes import FakeAsyncUnitOfWork, FakeConversationRepository

RUN_JANITOR_PATH = "app.interfaces.http.routers.v1.conversations.run_janitor"


def _client(
    *,
    user_id: uuid.UUID | None,
    conversation_repo: FakeConversationRepository,
    uow: FakeAsyncUnitOfWork | None = None,
) -> TestClient:
    from app.application.use_cases.conversations import EndConversation

    app = create_app()
    if user_id is not None:
        app.dependency_overrides[get_current_user_id] = lambda: user_id
    app.dependency_overrides[make_end_conversation] = lambda: EndConversation(
        conversations=conversation_repo, uow=uow or FakeAsyncUnitOfWork()
    )
    return TestClient(app)


def test_end_conversation_requires_authentication() -> None:
    client = _client(user_id=None, conversation_repo=FakeConversationRepository())

    with patch(RUN_JANITOR_PATH, new_callable=AsyncMock) as mock_janitor:
        response = client.post(f"/api/v1/conversations/{uuid.uuid4()}/end")

    assert response.status_code == 401
    mock_janitor.assert_not_called()


def test_end_conversation_404s_for_conversation_owned_by_another_user() -> None:
    owner_id = uuid.uuid4()
    requester_id = uuid.uuid4()
    conversation = Conversation(id=uuid.uuid4(), user_id=owner_id, status=ConversationStatus.ACTIVE)
    repo = FakeConversationRepository([conversation])
    client = _client(user_id=requester_id, conversation_repo=repo)

    with patch(RUN_JANITOR_PATH, new_callable=AsyncMock) as mock_janitor:
        response = client.post(f"/api/v1/conversations/{conversation.id}/end")

    assert response.status_code == 404
    mock_janitor.assert_not_called()


def test_end_conversation_404s_for_unknown_conversation() -> None:
    client = _client(user_id=uuid.uuid4(), conversation_repo=FakeConversationRepository())

    with patch(RUN_JANITOR_PATH, new_callable=AsyncMock) as mock_janitor:
        response = client.post(f"/api/v1/conversations/{uuid.uuid4()}/end")

    assert response.status_code == 404
    mock_janitor.assert_not_called()


def test_end_conversation_marks_ended_and_schedules_janitor() -> None:
    user_id = uuid.uuid4()
    conversation = Conversation(id=uuid.uuid4(), user_id=user_id, status=ConversationStatus.ACTIVE)
    repo = FakeConversationRepository([conversation])
    uow = FakeAsyncUnitOfWork()
    client = _client(user_id=user_id, conversation_repo=repo, uow=uow)

    with patch(RUN_JANITOR_PATH, new_callable=AsyncMock) as mock_janitor:
        response = client.post(f"/api/v1/conversations/{conversation.id}/end")

    assert response.status_code == 202
    body = response.json()
    assert body == {
        "conversation_id": str(conversation.id),
        "status": "ended",
        "summary_pending": True,
    }
    mock_janitor.assert_awaited_once_with(conversation.id)

    persisted = asyncio.run(repo.get_by_id(conversation.id))
    assert persisted is not None
    assert persisted.status is ConversationStatus.ENDED
    # Regression guard: the status flip must be committed on the async session,
    # not just flushed into the request-scoped identity map (see
    # `EndConversation.execute` — a missing commit here previously meant the
    # `ENDED` status was silently rolled back once the request's async
    # session closed).
    assert uow.commits == 1


def test_end_conversation_is_idempotent_and_does_not_reschedule_janitor() -> None:
    user_id = uuid.uuid4()
    conversation = Conversation(id=uuid.uuid4(), user_id=user_id, status=ConversationStatus.ENDED)
    repo = FakeConversationRepository([conversation])
    uow = FakeAsyncUnitOfWork()
    client = _client(user_id=user_id, conversation_repo=repo, uow=uow)

    with patch(RUN_JANITOR_PATH, new_callable=AsyncMock) as mock_janitor:
        response = client.post(f"/api/v1/conversations/{conversation.id}/end")

    assert response.status_code == 202
    assert response.json()["summary_pending"] is False
    mock_janitor.assert_not_called()
    # No-op path: nothing changed, so nothing should be committed.
    assert uow.commits == 0

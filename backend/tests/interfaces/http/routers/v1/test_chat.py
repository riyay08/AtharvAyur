"""HTTP-layer tests for POST /api/v1/chat — the unified `ChatOrchestrator` route.

Exercises the real FastAPI app + router wiring with in-memory fakes swapped in
via `app.dependency_overrides`, mirroring `test_conversations.py`.
"""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.application.orchestrator.orchestrator import ChatOrchestrator
from app.application.use_cases.chat_orchestrated import GenerateHealthReplyViaOrchestrator
from app.domain.entities import Conversation, ConversationStatus
from app.interfaces.http.deps import get_current_user_id, make_chat_orchestrated_use_case
from app.main import create_app
from tests.fakes import (
    FakeAsyncUnitOfWork,
    FakeAuditLogRepository,
    FakeChatRepository,
    FakeConversationRepository,
    FakeHealthProfileRepository,
    FakeLLMGateway,
    FakeSessionSummaryRepository,
    FakeUnitOfWork,
    FakeUserMemoryRepository,
    FakeWeatherGateway,
)


def _client(
    *,
    user_id: uuid.UUID | None,
    conversation_repo: FakeConversationRepository | None = None,
    chat_repo: FakeChatRepository | None = None,
    llm: FakeLLMGateway | None = None,
) -> TestClient:
    conversation_repo = conversation_repo or FakeConversationRepository()
    chat_repo = chat_repo or FakeChatRepository()
    profiles = FakeHealthProfileRepository()
    llm = llm or FakeLLMGateway()

    orchestrator = ChatOrchestrator(
        profiles=profiles,
        chat_repo=chat_repo,
        conversations=conversation_repo,
        summaries=FakeSessionSummaryRepository(),
        user_memories=FakeUserMemoryRepository(),
        llm=llm,
    )
    uc = GenerateHealthReplyViaOrchestrator(
        chat_repo=chat_repo,
        profiles=profiles,
        conversations=conversation_repo,
        audit=FakeAuditLogRepository(),
        orchestrator=orchestrator,
        weather=FakeWeatherGateway(),
        uow=FakeUnitOfWork(),
        async_uow=FakeAsyncUnitOfWork(),
    )

    app = create_app()
    if user_id is not None:
        app.dependency_overrides[get_current_user_id] = lambda: user_id
    app.dependency_overrides[make_chat_orchestrated_use_case] = lambda: uc
    return TestClient(app)


def test_chat_requires_authentication() -> None:
    client = _client(user_id=None)

    response = client.post("/api/v1/chat", json={"message": "Hello"})

    assert response.status_code == 401


def test_chat_starts_a_new_conversation_when_none_supplied() -> None:
    llm = FakeLLMGateway(reply_text="Rest well tonight.")
    client = _client(user_id=uuid.uuid4(), llm=llm)

    response = client.post("/api/v1/chat", json={"message": "Any sleep tips?"})

    assert response.status_code == 200
    body = response.json()
    assert body["blocked"] is False
    assert body["response_text"] == "Rest well tonight."
    assert uuid.UUID(body["conversation_id"])


def test_chat_resumes_an_existing_conversation() -> None:
    user_id = uuid.uuid4()
    conversation = Conversation(id=uuid.uuid4(), user_id=user_id, status=ConversationStatus.ACTIVE)
    repo = FakeConversationRepository([conversation])
    client = _client(user_id=user_id, conversation_repo=repo)

    response = client.post(
        "/api/v1/chat",
        json={"message": "What now?", "conversation_id": str(conversation.id)},
    )

    assert response.status_code == 200
    assert response.json()["conversation_id"] == str(conversation.id)


def test_chat_404s_for_conversation_owned_by_another_user() -> None:
    owner_id = uuid.uuid4()
    requester_id = uuid.uuid4()
    conversation = Conversation(id=uuid.uuid4(), user_id=owner_id, status=ConversationStatus.ACTIVE)
    repo = FakeConversationRepository([conversation])
    client = _client(user_id=requester_id, conversation_repo=repo)

    response = client.post(
        "/api/v1/chat",
        json={"message": "hi", "conversation_id": str(conversation.id)},
    )

    assert response.status_code == 404


def test_chat_blocks_on_red_flag_and_still_returns_a_conversation_id() -> None:
    chat_repo = FakeChatRepository()
    client = _client(user_id=uuid.uuid4(), chat_repo=chat_repo)

    response = client.post("/api/v1/chat", json={"message": "I have chest pain right now"})

    assert response.status_code == 200
    body = response.json()
    assert body["blocked"] is True
    assert body["safety_reason"]
    assert uuid.UUID(body["conversation_id"])
    assert len(chat_repo.messages) == 2


def test_chat_rejects_mismatched_lat_lon() -> None:
    client = _client(user_id=uuid.uuid4())

    response = client.post("/api/v1/chat", json={"message": "hi", "latitude": 1.0})

    assert response.status_code == 422

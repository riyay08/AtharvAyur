"""Unit tests for `GenerateHealthReplyViaOrchestrator` — the use case backing
`POST /api/v1/chat`.

Uses a real `ChatOrchestrator` (wired with fakes) rather than `FakeOrchestrator`
so these tests exercise the full Observe/Act/Replan cycle end-to-end, the same
way production wiring in `deps.py` does.
"""

from __future__ import annotations

import uuid

import pytest

from app.application.dtos import GenerateHealthReplyInput
from app.application.orchestrator.orchestrator import ChatOrchestrator
from app.application.ports.llm_gateway import GroundedReply
from app.application.use_cases.chat_orchestrated import GenerateHealthReplyViaOrchestrator
from app.domain.entities import Conversation, ConversationStatus, HealthProfile
from app.domain.errors import NotFoundError
from app.domain.value_objects import ChatRole, SafetyBlockReason
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


def _make_uc(**kwargs) -> tuple[GenerateHealthReplyViaOrchestrator, dict]:
    chat_repo = kwargs.pop("chat_repo", FakeChatRepository())
    profiles = kwargs.pop("profiles", FakeHealthProfileRepository())
    conversations = kwargs.pop("conversations", FakeConversationRepository())
    audit = kwargs.pop("audit", FakeAuditLogRepository())
    llm = kwargs.pop("llm", FakeLLMGateway())
    weather = kwargs.pop("weather", FakeWeatherGateway())
    uow = kwargs.pop("uow", FakeUnitOfWork())
    async_uow = kwargs.pop("async_uow", FakeAsyncUnitOfWork())
    orchestrator = kwargs.pop(
        "orchestrator",
        ChatOrchestrator(
            profiles=profiles,
            chat_repo=chat_repo,
            conversations=conversations,
            summaries=kwargs.pop("summaries", FakeSessionSummaryRepository()),
            user_memories=kwargs.pop("user_memories", FakeUserMemoryRepository()),
            llm=llm,
        ),
    )
    uc = GenerateHealthReplyViaOrchestrator(
        chat_repo=chat_repo,
        profiles=profiles,
        conversations=conversations,
        audit=audit,
        orchestrator=orchestrator,
        weather=weather,
        uow=uow,
        async_uow=async_uow,
    )
    parts = {
        "chat_repo": chat_repo,
        "profiles": profiles,
        "conversations": conversations,
        "audit": audit,
        "llm": llm,
        "weather": weather,
        "uow": uow,
        "async_uow": async_uow,
    }
    return uc, parts


@pytest.mark.asyncio
async def test_new_conversation_is_created_and_persisted_when_none_supplied() -> None:
    uc, parts = _make_uc(llm=FakeLLMGateway(reply_text="Rest well tonight."))
    user_id = uuid.uuid4()

    out = await uc.execute(GenerateHealthReplyInput(user_id=user_id, message="Any sleep tips?"))

    assert out.blocked is False
    assert out.conversation_id is not None
    stored = await parts["conversations"].get_by_id(out.conversation_id)
    assert stored is not None
    assert stored.user_id == user_id
    assert stored.status is ConversationStatus.ACTIVE
    assert parts["async_uow"].commits == 1


@pytest.mark.asyncio
async def test_existing_conversation_id_is_reused_without_creating_a_new_one() -> None:
    user_id = uuid.uuid4()
    conversation = Conversation(id=uuid.uuid4(), user_id=user_id, status=ConversationStatus.ACTIVE)
    conversations = FakeConversationRepository([conversation])
    uc, parts = _make_uc(conversations=conversations)

    out = await uc.execute(
        GenerateHealthReplyInput(user_id=user_id, message="What now?", conversation_id=conversation.id)
    )

    assert out.conversation_id == conversation.id
    # No new conversation write, so no async commit needed for creation.
    assert parts["async_uow"].commits == 0


@pytest.mark.asyncio
async def test_unknown_conversation_id_raises_not_found() -> None:
    uc, _ = _make_uc()

    with pytest.raises(NotFoundError):
        await uc.execute(
            GenerateHealthReplyInput(user_id=uuid.uuid4(), message="hi", conversation_id=uuid.uuid4())
        )


@pytest.mark.asyncio
async def test_conversation_owned_by_another_user_raises_not_found() -> None:
    owner_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    conversation = Conversation(id=uuid.uuid4(), user_id=owner_id, status=ConversationStatus.ACTIVE)
    uc, _ = _make_uc(conversations=FakeConversationRepository([conversation]))

    with pytest.raises(NotFoundError):
        await uc.execute(
            GenerateHealthReplyInput(user_id=other_user_id, message="hi", conversation_id=conversation.id)
        )


@pytest.mark.asyncio
async def test_persists_both_turns_tagged_with_conversation_id_and_embedding() -> None:
    chat_repo = FakeChatRepository()
    uc, parts = _make_uc(chat_repo=chat_repo, llm=FakeLLMGateway(embedding=[0.1, 0.2, 0.3]))
    user_id = uuid.uuid4()

    out = await uc.execute(GenerateHealthReplyInput(user_id=user_id, message="How do I relax?"))

    assert len(chat_repo.messages) == 2
    user_msg, assistant_msg = chat_repo.messages
    assert user_msg.role == ChatRole.USER
    assert user_msg.conversation_id == out.conversation_id
    assert user_msg.embedding == [0.1, 0.2, 0.3]
    assert assistant_msg.role == ChatRole.ASSISTANT
    assert assistant_msg.conversation_id == out.conversation_id
    assert parts["uow"].commits == 1
    assert ("chat.reply" in [a for _, a in parts["audit"].records])


@pytest.mark.asyncio
async def test_blocks_on_red_flag_without_calling_llm_but_still_tags_conversation() -> None:
    chat_repo = FakeChatRepository()
    llm = FakeLLMGateway()
    uc, parts = _make_uc(chat_repo=chat_repo, llm=llm)
    user_id = uuid.uuid4()

    out = await uc.execute(
        GenerateHealthReplyInput(user_id=user_id, message="I have chest pain right now")
    )

    assert out.blocked is True
    assert out.block_reason != SafetyBlockReason.NONE.value
    assert out.conversation_id is not None
    assert "generate_health_reply" not in llm.calls
    assert len(chat_repo.messages) == 2
    assert all(m.conversation_id == out.conversation_id for m in chat_repo.messages)
    assert parts["uow"].commits == 1


@pytest.mark.asyncio
async def test_weather_context_is_injected_when_lat_lon_provided() -> None:
    llm = FakeLLMGateway()
    weather = FakeWeatherGateway({"weather": "18°C, rain", "humidity_type": "damp", "habitat": "Coastal"})
    uc, _ = _make_uc(llm=llm, weather=weather)
    user_id = uuid.uuid4()

    await uc.execute(
        GenerateHealthReplyInput(user_id=user_id, message="Feeling stuffy today", lat=51.5, lon=-0.1)
    )

    assert llm.last_recent_history_block is not None


@pytest.mark.asyncio
async def test_weather_failure_does_not_block_the_reply() -> None:
    class _FailingWeather:
        async def get_context(self, *, lat: float, lon: float) -> dict[str, str]:
            from app.domain.errors import ExternalServiceError

            raise ExternalServiceError("weather provider down")

    uc, _ = _make_uc(weather=_FailingWeather())

    out = await uc.execute(
        GenerateHealthReplyInput(user_id=uuid.uuid4(), message="Hi", lat=1.0, lon=2.0)
    )

    assert out.blocked is False
    assert out.reply_text


@pytest.mark.asyncio
async def test_reply_uses_recent_summaries_and_ltm_facts_via_orchestrator() -> None:
    from app.domain.entities import SessionSummary, UserMemory

    user_id = uuid.uuid4()
    summaries = [
        SessionSummary(
            id=uuid.uuid4(), conversation_id=uuid.uuid4(),
            summary_text="Discussed sleep troubles last week.",
        )
    ]
    facts = [
        UserMemory(id=uuid.uuid4(), user_id=user_id, fact_text="User is lactose intolerant.")
    ]
    llm = FakeLLMGateway(embedding=[0.1] * 8, reply_text="Here's a dairy-free idea.")
    uc, parts = _make_uc(
        llm=llm,
        summaries=FakeSessionSummaryRepository(summaries),
        user_memories=FakeUserMemoryRepository(facts),
    )

    out = await uc.execute(GenerateHealthReplyInput(user_id=user_id, message="Breakfast ideas?"))

    assert out.reply_text == "Here's a dairy-free idea."
    assert "Discussed sleep troubles last week." in llm.last_recent_history_block
    assert "User is lactose intolerant." in llm.last_recent_history_block


@pytest.mark.asyncio
async def test_outbound_guard_softens_diagnostic_language_from_the_llm() -> None:
    uc, _ = _make_uc(llm=FakeLLMGateway(reply_text="You have irritable bowel syndrome."))

    out = await uc.execute(GenerateHealthReplyInput(user_id=uuid.uuid4(), message="What's wrong with me?"))

    assert "you have" not in out.reply_text.lower()


@pytest.mark.asyncio
async def test_profile_is_considered_for_safety_evaluation() -> None:
    """Sanity check that the profile lookup still feeds the safety policy the
    same way it did in the legacy `GenerateHealthReply` use case."""
    user_id = uuid.uuid4()
    profiles = FakeHealthProfileRepository()
    profiles.upsert(HealthProfile(id=uuid.uuid4(), user_id=user_id, conditions={}, allergies=[], medications=[]))
    uc, _ = _make_uc(profiles=profiles)

    out = await uc.execute(GenerateHealthReplyInput(user_id=user_id, message="How's my week looking?"))

    assert out.blocked is False

from __future__ import annotations

import uuid

import pytest

from app.application.orchestrator.orchestrator import ChatOrchestrator
from app.domain.entities import ChatMessage, Conversation, ConversationStatus, SessionSummary, UserMemory
from app.domain.errors import NotFoundError
from app.domain.value_objects import ChatRole
from tests.fakes import (
    FakeChatRepository,
    FakeConversationRepository,
    FakeHealthProfileRepository,
    FakeLLMGateway,
    FakeSessionSummaryRepository,
    FakeUserMemoryRepository,
)


def _make_orchestrator(**kwargs) -> ChatOrchestrator:
    return ChatOrchestrator(
        profiles=kwargs.pop("profiles", FakeHealthProfileRepository()),
        chat_repo=kwargs.pop("chat_repo", FakeChatRepository()),
        conversations=kwargs.pop("conversations", FakeConversationRepository()),
        summaries=kwargs.pop("summaries", FakeSessionSummaryRepository()),
        user_memories=kwargs.pop("user_memories", FakeUserMemoryRepository()),
        llm=kwargs.pop("llm", FakeLLMGateway()),
    )


@pytest.mark.asyncio
async def test_observe_without_conversation_id_builds_basic_context() -> None:
    user_id = uuid.uuid4()
    orch = _make_orchestrator()

    ctx = await orch.observe(user_id=user_id, conversation_id=None, user_message="Any sleep tips?")

    assert ctx.user_id == user_id
    assert ctx.conversation_id is None
    assert ctx.user_message == "Any sleep tips?"
    assert ctx.conversation_history_block == ""
    assert ctx.session_summaries == ()
    assert ctx.known_user_facts_block == ""


@pytest.mark.asyncio
async def test_observe_raises_not_found_for_unknown_conversation() -> None:
    orch = _make_orchestrator()

    with pytest.raises(NotFoundError):
        await orch.observe(user_id=uuid.uuid4(), conversation_id=uuid.uuid4(), user_message="hi")


@pytest.mark.asyncio
async def test_observe_raises_not_found_when_conversation_belongs_to_other_user() -> None:
    owner_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    conv = Conversation(id=uuid.uuid4(), user_id=owner_id, status=ConversationStatus.ACTIVE)
    orch = _make_orchestrator(conversations=FakeConversationRepository([conv]))

    with pytest.raises(NotFoundError):
        await orch.observe(user_id=other_user_id, conversation_id=conv.id, user_message="hi")


@pytest.mark.asyncio
async def test_observe_loads_conversation_transcript_and_recent_summaries() -> None:
    user_id = uuid.uuid4()
    conv = Conversation(id=uuid.uuid4(), user_id=user_id, status=ConversationStatus.ACTIVE)
    chat_repo = FakeChatRepository()
    chat_repo.add(
        ChatMessage(
            id=uuid.uuid4(), user_id=user_id, role=ChatRole.USER,
            message="I've been feeling sluggish.", conversation_id=conv.id,
        )
    )
    chat_repo.add(
        ChatMessage(
            id=uuid.uuid4(), user_id=user_id, role=ChatRole.ASSISTANT,
            message="Try warm water in the morning.", conversation_id=conv.id,
        )
    )
    summaries = [
        SessionSummary(id=uuid.uuid4(), conversation_id=uuid.uuid4(), summary_text="Prior session: discussed sleep."),
    ]
    orch = _make_orchestrator(
        conversations=FakeConversationRepository([conv]),
        chat_repo=chat_repo,
        summaries=FakeSessionSummaryRepository(summaries),
    )

    ctx = await orch.observe(user_id=user_id, conversation_id=conv.id, user_message="What now?")

    assert "sluggish" in ctx.conversation_history_block
    assert "warm water" in ctx.conversation_history_block.lower()
    assert ctx.session_summaries == tuple(summaries)


@pytest.mark.asyncio
async def test_observe_loads_semantically_relevant_user_memories() -> None:
    user_id = uuid.uuid4()
    facts = [
        UserMemory(
            id=uuid.uuid4(),
            user_id=user_id,
            fact_text="User is lactose intolerant.",
            source="session:abc",
        ),
        UserMemory(
            id=uuid.uuid4(),
            user_id=user_id,
            fact_text="User prefers mornings for exercise.",
            source="session:abc",
        ),
    ]
    orch = _make_orchestrator(
        user_memories=FakeUserMemoryRepository(facts),
        llm=FakeLLMGateway(embedding=[0.1] * 8),
    )

    ctx = await orch.observe(user_id=user_id, conversation_id=None, user_message="Any dairy-free breakfast ideas?")

    assert "Known User Facts:" in ctx.known_user_facts_block
    assert "User is lactose intolerant." in ctx.known_user_facts_block
    assert "User prefers mornings for exercise." in ctx.known_user_facts_block


@pytest.mark.asyncio
async def test_observe_exposes_the_computed_embedding_for_reuse() -> None:
    """`observe()` already calls `llm.embed()` for semantic search + LTM; the
    resulting vector is exposed on `ObservedContext` so a caller persisting the
    user's `ChatMessage` afterwards doesn't need a second, redundant call."""
    user_id = uuid.uuid4()
    orch = _make_orchestrator(llm=FakeLLMGateway(embedding=[0.2, 0.4]))

    ctx = await orch.observe(user_id=user_id, conversation_id=None, user_message="Any tips?")

    assert ctx.embedding == [0.2, 0.4]


@pytest.mark.asyncio
async def test_observe_skips_user_memories_when_embedding_unavailable() -> None:
    user_id = uuid.uuid4()
    facts = [
        UserMemory(
            id=uuid.uuid4(),
            user_id=user_id,
            fact_text="User is lactose intolerant.",
            source="session:abc",
        ),
    ]
    orch = _make_orchestrator(
        user_memories=FakeUserMemoryRepository(facts),
        llm=FakeLLMGateway(embedding=[]),
    )

    ctx = await orch.observe(user_id=user_id, conversation_id=None, user_message="Any tips?")

    assert ctx.known_user_facts_block == ""


def test_act_calls_llm_gateway_and_folds_context_in_injection_order() -> None:
    from app.application.ports.orchestrator import ObservedContext

    llm = FakeLLMGateway(reply_text="Rest well tonight.")
    orch = _make_orchestrator(llm=llm)
    summary = SessionSummary(id=uuid.uuid4(), conversation_id=uuid.uuid4(), summary_text="Talked about diet.")
    context = ObservedContext(
        user_id=uuid.uuid4(),
        conversation_id=None,
        user_message="Any tips?",
        profile_blob_json="{}",
        recent_history_block="- felt tired yesterday",
        semantic_history_block="",
        conversation_history_block="user: hi\nassistant: hello",
        session_summaries=(summary,),
        known_user_facts_block="Known User Facts:\n- User is lactose intolerant.",
    )

    reply = orch.act(context)

    assert reply.reply_text == "Rest well tonight."
    assert "generate_health_reply" in llm.calls
    assert llm.last_recent_history_block is not None
    block = llm.last_recent_history_block
    assert "Talked about diet." in block
    assert "User is lactose intolerant." in block
    assert "hi" in block
    assert "felt tired yesterday" in block
    # Injection order: summaries -> known facts -> transcript -> recent history
    assert block.index("Talked about diet.") < block.index("User is lactose intolerant.")
    assert block.index("User is lactose intolerant.") < block.index("user: hi")
    assert block.index("user: hi") < block.index("felt tired yesterday")


def test_replan_softens_diagnostic_language() -> None:
    from app.application.ports.llm_gateway import GroundedReply
    from app.application.ports.orchestrator import ObservedContext

    orch = _make_orchestrator()
    context = ObservedContext(
        user_id=uuid.uuid4(), conversation_id=None, user_message="What's wrong with me?",
        profile_blob_json="{}", recent_history_block="", semantic_history_block="",
    )
    draft = GroundedReply(reply_text="You have irritable bowel syndrome.")

    final = orch.replan(context, draft)

    assert "you have" not in final.reply_text.lower()
    assert final.reply_text != draft.reply_text


def test_replan_passes_through_when_nothing_to_rewrite() -> None:
    from app.application.ports.llm_gateway import GroundedReply
    from app.application.ports.orchestrator import ObservedContext

    orch = _make_orchestrator()
    context = ObservedContext(
        user_id=uuid.uuid4(), conversation_id=None, user_message="Any sleep tips?",
        profile_blob_json="{}", recent_history_block="", semantic_history_block="",
    )
    draft = GroundedReply(reply_text="Try winding down earlier tonight.")

    final = orch.replan(context, draft)

    assert final is draft

from __future__ import annotations

import uuid

import pytest

from app.application.use_cases.summarize_session import SummarizeSession
from app.domain.entities import ChatMessage, Conversation, ConversationStatus
from app.domain.errors import NotFoundError
from app.domain.value_objects import ChatRole
from tests.fakes import (
    FakeChatRepository,
    FakeConversationRepository,
    FakeLLMGateway,
    FakeSessionSummaryRepository,
    FakeUserMemoryRepository,
)


def _make_use_case(**kwargs) -> SummarizeSession:
    return SummarizeSession(
        chat_repo=kwargs.pop("chat_repo", FakeChatRepository()),
        conversations=kwargs.pop("conversations", FakeConversationRepository()),
        summaries=kwargs.pop("summaries", FakeSessionSummaryRepository()),
        user_memories=kwargs.pop("user_memories", FakeUserMemoryRepository()),
        llm=kwargs.pop("llm", FakeLLMGateway()),
    )


def _seed_conversation_with_messages(user_id: uuid.UUID) -> tuple[Conversation, FakeChatRepository]:
    conv = Conversation(id=uuid.uuid4(), user_id=user_id, status=ConversationStatus.ACTIVE)
    chat_repo = FakeChatRepository()
    chat_repo.add(
        ChatMessage(
            id=uuid.uuid4(), user_id=user_id, role=ChatRole.USER,
            message="I've been feeling really sluggish and my sleep is off.",
            conversation_id=conv.id,
        )
    )
    chat_repo.add(
        ChatMessage(
            id=uuid.uuid4(), user_id=user_id, role=ChatRole.ASSISTANT,
            message="Try warm water in the morning and an earlier wind-down routine.",
            conversation_id=conv.id,
        )
    )
    chat_repo.add(
        ChatMessage(
            id=uuid.uuid4(), user_id=user_id, role=ChatRole.USER,
            message="Thanks, I felt a bit better by the end of the day.",
            conversation_id=conv.id,
        )
    )
    return conv, chat_repo


@pytest.mark.asyncio
async def test_full_conversation_triggers_summary_and_title_update() -> None:
    user_id = uuid.uuid4()
    conv, chat_repo = _seed_conversation_with_messages(user_id)
    conversations = FakeConversationRepository([conv])
    summaries = FakeSessionSummaryRepository()
    llm = FakeLLMGateway(
        session_summary=(
            "The user reported sluggishness and disrupted sleep. "
            "Warm water in the morning and an earlier wind-down routine were suggested. "
            "The user felt somewhat better by the end of the conversation."
        )
    )
    uc = _make_use_case(chat_repo=chat_repo, conversations=conversations, summaries=summaries, llm=llm)

    result = await uc.execute(conv.id)

    assert result is not None
    assert result.conversation_id == conv.id
    assert "sluggishness" in result.summary_text

    stored = await summaries.list_for_conversation(conv.id)
    assert len(stored) == 1
    assert stored[0].summary_text == result.summary_text

    updated_conversation = await conversations.get_by_id(conv.id)
    assert updated_conversation is not None
    assert updated_conversation.status == ConversationStatus.ENDED
    assert updated_conversation.title == "The user reported sluggishness and disrupted sleep"

    assert "generate_session_summary" in llm.calls
    assert llm.last_transcript is not None
    assert "sluggish" in llm.last_transcript
    assert "warm water" in llm.last_transcript.lower()


@pytest.mark.asyncio
async def test_conversation_with_no_messages_produces_no_summary() -> None:
    conv = Conversation(id=uuid.uuid4(), user_id=uuid.uuid4(), status=ConversationStatus.ACTIVE)
    conversations = FakeConversationRepository([conv])
    llm = FakeLLMGateway()
    uc = _make_use_case(conversations=conversations, llm=llm)

    result = await uc.execute(conv.id)

    assert result is None
    assert "generate_session_summary" not in llm.calls
    unchanged = await conversations.get_by_id(conv.id)
    assert unchanged is not None
    assert unchanged.status == ConversationStatus.ACTIVE
    assert unchanged.title is None


@pytest.mark.asyncio
async def test_unknown_conversation_raises_not_found() -> None:
    uc = _make_use_case()

    with pytest.raises(NotFoundError):
        await uc.execute(uuid.uuid4())


@pytest.mark.asyncio
async def test_empty_llm_summary_is_not_persisted() -> None:
    user_id = uuid.uuid4()
    conv, chat_repo = _seed_conversation_with_messages(user_id)
    conversations = FakeConversationRepository([conv])
    summaries = FakeSessionSummaryRepository()
    llm = FakeLLMGateway(session_summary="   ")
    uc = _make_use_case(chat_repo=chat_repo, conversations=conversations, summaries=summaries, llm=llm)

    result = await uc.execute(conv.id)

    assert result is None
    assert await summaries.list_for_conversation(conv.id) == []
    unchanged = await conversations.get_by_id(conv.id)
    assert unchanged is not None
    assert unchanged.status == ConversationStatus.ACTIVE


@pytest.mark.asyncio
async def test_extracted_facts_are_embedded_and_stored_with_session_source() -> None:
    user_id = uuid.uuid4()
    conv, chat_repo = _seed_conversation_with_messages(user_id)
    conversations = FakeConversationRepository([conv])
    user_memories = FakeUserMemoryRepository()
    llm = FakeLLMGateway(
        long_term_facts=("User is lactose intolerant", "User prefers mornings for exercise"),
        embedding=[0.42] * 8,
    )
    uc = _make_use_case(
        chat_repo=chat_repo, conversations=conversations, user_memories=user_memories, llm=llm
    )

    result = await uc.execute(conv.id)

    assert result is not None
    assert "extract_long_term_facts" in llm.calls
    assert llm.last_facts_transcript is not None
    assert "sluggish" in llm.last_facts_transcript

    assert len(user_memories.facts) == 2
    fact_texts = {f.fact_text for f in user_memories.facts}
    assert fact_texts == {"User is lactose intolerant", "User prefers mornings for exercise"}
    for fact in user_memories.facts:
        assert fact.user_id == user_id
        assert fact.source == f"session:{conv.id}"
        assert fact.embedding == [0.42] * 8


@pytest.mark.asyncio
async def test_no_facts_extracted_means_nothing_stored() -> None:
    user_id = uuid.uuid4()
    conv, chat_repo = _seed_conversation_with_messages(user_id)
    conversations = FakeConversationRepository([conv])
    user_memories = FakeUserMemoryRepository()
    llm = FakeLLMGateway(long_term_facts=())
    uc = _make_use_case(
        chat_repo=chat_repo, conversations=conversations, user_memories=user_memories, llm=llm
    )

    result = await uc.execute(conv.id)

    assert result is not None
    assert "extract_long_term_facts" in llm.calls
    assert user_memories.facts == []


@pytest.mark.asyncio
async def test_fact_extraction_failure_does_not_break_summary_persistence() -> None:
    """A broken second pass must never take down the already-persisted summary."""
    user_id = uuid.uuid4()
    conv, chat_repo = _seed_conversation_with_messages(user_id)
    conversations = FakeConversationRepository([conv])
    summaries = FakeSessionSummaryRepository()
    user_memories = FakeUserMemoryRepository()

    class _BoomLLM(FakeLLMGateway):
        def extract_long_term_facts(self, *, transcript: str) -> tuple[str, ...]:
            raise RuntimeError("boom")

    llm = _BoomLLM()
    uc = _make_use_case(
        chat_repo=chat_repo,
        conversations=conversations,
        summaries=summaries,
        user_memories=user_memories,
        llm=llm,
    )

    result = await uc.execute(conv.id)

    assert result is not None
    stored = await summaries.list_for_conversation(conv.id)
    assert len(stored) == 1
    assert user_memories.facts == []
    updated_conversation = await conversations.get_by_id(conv.id)
    assert updated_conversation is not None
    assert updated_conversation.status == ConversationStatus.ENDED


@pytest.mark.asyncio
async def test_no_messages_means_facts_are_never_attempted() -> None:
    conv = Conversation(id=uuid.uuid4(), user_id=uuid.uuid4(), status=ConversationStatus.ACTIVE)
    conversations = FakeConversationRepository([conv])
    llm = FakeLLMGateway(long_term_facts=("Should never be extracted",))
    uc = _make_use_case(conversations=conversations, llm=llm)

    result = await uc.execute(conv.id)

    assert result is None
    assert "extract_long_term_facts" not in llm.calls

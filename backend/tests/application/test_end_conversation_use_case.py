from __future__ import annotations

import uuid

import pytest

from app.application.use_cases.conversations import EndConversation
from app.domain.entities import Conversation, ConversationStatus
from app.domain.errors import NotFoundError
from tests.fakes import FakeAsyncUnitOfWork, FakeConversationRepository


@pytest.mark.asyncio
async def test_end_conversation_commits_the_status_transition() -> None:
    user_id = uuid.uuid4()
    conversation = Conversation(id=uuid.uuid4(), user_id=user_id, status=ConversationStatus.ACTIVE)
    repo = FakeConversationRepository([conversation])
    uow = FakeAsyncUnitOfWork()
    uc = EndConversation(conversations=repo, uow=uow)

    result = await uc.execute(conversation_id=conversation.id, user_id=user_id)

    assert result.already_ended is False
    assert result.conversation.status is ConversationStatus.ENDED
    assert uow.commits == 1
    assert uow.rollbacks == 0


@pytest.mark.asyncio
async def test_end_conversation_already_ended_is_a_commit_free_noop() -> None:
    user_id = uuid.uuid4()
    conversation = Conversation(id=uuid.uuid4(), user_id=user_id, status=ConversationStatus.ENDED)
    repo = FakeConversationRepository([conversation])
    uow = FakeAsyncUnitOfWork()
    uc = EndConversation(conversations=repo, uow=uow)

    result = await uc.execute(conversation_id=conversation.id, user_id=user_id)

    assert result.already_ended is True
    assert uow.commits == 0


@pytest.mark.asyncio
async def test_end_conversation_raises_not_found_for_other_users_conversation() -> None:
    owner_id = uuid.uuid4()
    requester_id = uuid.uuid4()
    conversation = Conversation(id=uuid.uuid4(), user_id=owner_id, status=ConversationStatus.ACTIVE)
    repo = FakeConversationRepository([conversation])
    uow = FakeAsyncUnitOfWork()
    uc = EndConversation(conversations=repo, uow=uow)

    with pytest.raises(NotFoundError):
        await uc.execute(conversation_id=conversation.id, user_id=requester_id)

    assert uow.commits == 0

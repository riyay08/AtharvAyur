from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.application.dtos import GenerateHealthReplyInput
from app.application.use_cases.chat import GenerateHealthReply
from app.domain.value_objects import ChatRole, SafetyBlockReason
from tests.fakes import (
    FakeAuditLogRepository,
    FakeChatRepository,
    FakeHealthProfileRepository,
    FakeLLMGateway,
    FakeUnitOfWork,
    FakeWeatherGateway,
)


def _make_uc(**kwargs) -> GenerateHealthReply:
    return GenerateHealthReply(
        chat_repo=kwargs.pop("chat", FakeChatRepository()),
        profiles=kwargs.pop("profiles", FakeHealthProfileRepository()),
        audit=kwargs.pop("audit", FakeAuditLogRepository()),
        llm=kwargs.pop("llm", FakeLLMGateway()),
        weather=kwargs.pop("weather", FakeWeatherGateway()),
        uow=kwargs.pop("uow", FakeUnitOfWork()),
    )


@pytest.mark.asyncio
async def test_chat_returns_llm_reply_on_safe_message() -> None:
    llm = FakeLLMGateway(reply_text="Rest well tonight.")
    chat = FakeChatRepository()
    uc = _make_uc(llm=llm, chat=chat)

    out = await uc.execute(GenerateHealthReplyInput(user_id=uuid.uuid4(), message="Any sleep tips?"))

    assert out.blocked is False
    assert out.block_reason == SafetyBlockReason.NONE.value
    assert out.reply_text == "Rest well tonight."
    roles = [m.role for m in chat.messages]
    assert ChatRole.USER in roles and ChatRole.ASSISTANT in roles


@pytest.mark.asyncio
async def test_chat_blocks_on_red_flag_without_calling_llm() -> None:
    llm = FakeLLMGateway()
    chat = FakeChatRepository()
    uc = _make_uc(llm=llm, chat=chat)

    out = await uc.execute(
        GenerateHealthReplyInput(user_id=uuid.uuid4(), message="I have chest pain right now")
    )

    assert out.blocked is True
    assert out.block_reason == SafetyBlockReason.EMERGENCY_OR_RED_FLAG.value
    assert "generate_health_reply" not in llm.calls
    assert len(chat.messages) == 2


@pytest.mark.asyncio
async def test_chat_persists_two_turns_on_success() -> None:
    chat = FakeChatRepository()
    uc = _make_uc(chat=chat)
    await uc.execute(GenerateHealthReplyInput(user_id=uuid.uuid4(), message="How do I relax?"))
    assert len(chat.messages) == 2
    assert chat.messages[0].role == ChatRole.USER
    assert chat.messages[1].role == ChatRole.ASSISTANT

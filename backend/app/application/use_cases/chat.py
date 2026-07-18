from __future__ import annotations

import json
import uuid
from dataclasses import dataclass

from app.application.dtos import (
    GenerateHealthReplyInput,
    GenerateHealthReplyOutput,
)
from app.application.ports.llm_gateway import LLMGateway
from app.application.ports.repositories import (
    AuditLogRepository,
    ChatRepository,
    HealthProfileRepository,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.application.ports.weather_gateway import WeatherGateway
from app.domain.entities import ChatMessage
from app.domain.errors import ExternalServiceError
from app.domain.services.context_blocks import build_history_block, build_profile_blob_json
from app.domain.services.safety_policy import SafetyResult, evaluate_message
from app.domain.value_objects import ChatRole, SafetyBlockReason


@dataclass(frozen=True, slots=True)
class GenerateHealthReply:
    chat_repo: ChatRepository
    profiles: HealthProfileRepository
    audit: AuditLogRepository
    llm: LLMGateway
    weather: WeatherGateway
    uow: UnitOfWork

    async def execute(self, cmd: GenerateHealthReplyInput) -> GenerateHealthReplyOutput:
        profile = self.profiles.get_by_user_id(cmd.user_id)

        safety: SafetyResult = evaluate_message(cmd.message, health_profile=profile)
        if not safety.allowed:
            self.chat_repo.add(
                ChatMessage(
                    id=uuid.uuid4(),
                    user_id=cmd.user_id,
                    role=ChatRole.USER,
                    message=cmd.message,
                )
            )
            self.chat_repo.add(
                ChatMessage(
                    id=uuid.uuid4(),
                    user_id=cmd.user_id,
                    role=ChatRole.ASSISTANT,
                    message=safety.escalation_message or "",
                )
            )
            self.audit.record(
                actor=str(cmd.user_id),
                action=f"chat.blocked:{safety.reason.value}",
            )
            self.uow.commit()
            return GenerateHealthReplyOutput(
                reply_text=safety.escalation_message or "",
                blocked=True,
                block_reason=safety.reason.value,
            )

        embedding = self.llm.embed(cmd.message)

        environment_block: str | None = None
        if cmd.lat is not None and cmd.lon is not None:
            try:
                ctx = await self.weather.get_context(lat=cmd.lat, lon=cmd.lon)
                environment_block = json.dumps(ctx, indent=2)
            except ExternalServiceError:
                environment_block = None

        recent = self.chat_repo.list_recent_user_messages(cmd.user_id, days=7, limit=80)
        semantic = (
            self.chat_repo.list_semantic_user_messages(
                cmd.user_id, embedding, days=7, limit=5
            )
            if embedding
            else []
        )

        reply = self.llm.generate_health_reply(
            user_message=cmd.message,
            profile_blob_json=build_profile_blob_json(profile),
            recent_history_block=build_history_block(recent),
            semantic_history_block=build_history_block(semantic),
            environment_block=environment_block,
        )

        user_msg = ChatMessage(
            id=uuid.uuid4(),
            user_id=cmd.user_id,
            role=ChatRole.USER,
            message=cmd.message,
            embedding=embedding or None,
        )
        self.chat_repo.add(user_msg)
        self.chat_repo.add(
            ChatMessage(
                id=uuid.uuid4(),
                user_id=cmd.user_id,
                role=ChatRole.ASSISTANT,
                message=reply.reply_text,
            )
        )
        self.audit.record(actor=str(cmd.user_id), action="chat.reply")
        self.uow.commit()

        return GenerateHealthReplyOutput(
            reply_text=reply.reply_text,
            blocked=False,
            block_reason=SafetyBlockReason.NONE.value,
            citations=reply.citations,
            search_queries=reply.search_queries,
        )

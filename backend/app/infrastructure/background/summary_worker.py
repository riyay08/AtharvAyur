"""The Janitor — background worker that summarizes an ended conversation.

Wired for FastAPI `BackgroundTasks`:

    background_tasks.add_task(run_janitor, conversation_id)

Starlette's `BackgroundTasks` awaits async callables directly, so `run_janitor`
can be scheduled as-is with no wrapper.

This module is plumbing only — it opens its own DB sessions (same pattern as
`app/scheduler.py`, since the job outlives the HTTP request/response cycle) and
wires concrete adapters into `SummarizeSession`, which holds all the actual
business logic and is unit-tested independently with fakes.
"""

from __future__ import annotations

import logging
import uuid

from app.application.use_cases.summarize_session import SummarizeSession
from app.database import get_async_session_factory, get_session_factory
from app.infrastructure.db.repositories.chat_repository import SqlAlchemyChatRepository
from app.infrastructure.db.repositories.conversation_repository import (
    SqlAlchemyConversationRepository,
)
from app.infrastructure.db.repositories.session_summary_repository import (
    SqlAlchemySessionSummaryRepository,
)
from app.infrastructure.db.repositories.user_memory_repository import (
    SqlAlchemyUserMemoryRepository,
)
from app.infrastructure.llm.factory import make_llm_gateway

logger = logging.getLogger(__name__)


async def run_janitor(conversation_id: uuid.UUID) -> None:
    """Summarize `conversation_id` and update its title.

    Safe to schedule via `BackgroundTasks.add_task` — logs and swallows any
    failure instead of raising, since by the time this runs there is no HTTP
    request left to report an error to.
    """
    try:
        llm = make_llm_gateway()
    except Exception:
        logger.exception("Janitor: LLM gateway unavailable, skipping conversation %s", conversation_id)
        return

    sync_session_factory = get_session_factory()
    sync_session = sync_session_factory()
    try:
        chat_repo = SqlAlchemyChatRepository(sync_session)

        async_session_factory = get_async_session_factory()
        async with async_session_factory() as async_session:
            use_case = SummarizeSession(
                chat_repo=chat_repo,
                conversations=SqlAlchemyConversationRepository(async_session),
                summaries=SqlAlchemySessionSummaryRepository(async_session),
                user_memories=SqlAlchemyUserMemoryRepository(async_session),
                llm=llm,
            )
            try:
                summary = await use_case.execute(conversation_id)
            except Exception:
                logger.exception("Janitor: failed to summarize conversation %s", conversation_id)
                return

            if summary is None:
                logger.info("Janitor: nothing to summarize for conversation %s", conversation_id)
                return

            await async_session.commit()
            logger.info("Janitor: summarized conversation %s", conversation_id)
    finally:
        sync_session.close()

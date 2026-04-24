from __future__ import annotations

import uuid

from app.application.dtos import IssueTokenInput
from app.application.use_cases.auth import IssueAccessToken
from app.domain.entities import User
from tests.fakes import (
    FakeAuditLogRepository,
    FakeTokenService,
    FakeUnitOfWork,
    FakeUserRepository,
)


def _make_uc(existing: User | None = None) -> tuple[IssueAccessToken, FakeUserRepository, FakeAuditLogRepository, FakeTokenService, FakeUnitOfWork]:
    users = FakeUserRepository([existing] if existing else [])
    audit = FakeAuditLogRepository()
    tokens = FakeTokenService()
    uow = FakeUnitOfWork()
    uc = IssueAccessToken(users=users, audit=audit, tokens=tokens, uow=uow)
    return uc, users, audit, tokens, uow


def test_issue_token_creates_user_when_none() -> None:
    uc, users, audit, tokens, uow = _make_uc()
    out = uc.execute(IssueTokenInput(user_id=None))
    assert out.token_type == "bearer"
    assert out.access_token.startswith("fake-token-for-")
    assert users.get_by_id(out.user_id) is not None
    assert any(a == "auth.user_created" for _, a in audit.records)
    assert any(a == "auth.token_issued" for _, a in audit.records)
    assert uow.commits == 1


def test_issue_token_reuses_existing_user() -> None:
    existing = User.new()
    uc, users, audit, _, uow = _make_uc(existing)
    out = uc.execute(IssueTokenInput(user_id=existing.id))
    assert out.user_id == existing.id
    actions = [a for _, a in audit.records]
    assert "auth.user_created" not in actions
    assert "auth.token_issued" in actions
    assert uow.commits == 1


def test_issue_token_creates_user_when_unknown_id() -> None:
    uc, users, audit, _, _ = _make_uc()
    out = uc.execute(IssueTokenInput(user_id=uuid.uuid4()))
    assert users.get_by_id(out.user_id) is not None
    assert any(a == "auth.user_created" for _, a in audit.records)

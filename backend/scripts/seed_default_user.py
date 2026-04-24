"""Seed (or reset) a development convenience user.

Creates `subodh@gmail.com` with password `12345`. Bypasses the normal
SignUpWithEmail validation (8-char minimum) on purpose — this is a dev
backdoor only. If the user already exists, the password is rotated to
match so you always know the credentials.

Run from the repo root:

    cd backend && . .venv/bin/activate && python -m scripts.seed_default_user
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

from app.database import get_session_factory
from app.domain.entities import User
from app.domain.value_objects import AuthProvider, Email
from app.infrastructure.auth.bcrypt_password_hasher import BcryptPasswordHasher
from app.infrastructure.db.repositories.user_repository import (
    SqlAlchemyUserRepository,
)

DEFAULT_EMAIL = "subodh@gmail.com"
DEFAULT_PASSWORD = "12345"
DEFAULT_DISPLAY_NAME = "Subodh"


def main() -> int:
    session_factory = get_session_factory()
    hasher = BcryptPasswordHasher()
    email = Email(DEFAULT_EMAIL)
    password_hash = hasher.hash(DEFAULT_PASSWORD)
    now = datetime.now(timezone.utc)

    with session_factory() as session:
        repo = SqlAlchemyUserRepository(session)
        existing = repo.get_by_email(email)
        if existing is None:
            user = User.new()
            user.email = email
            user.email_verified = False
            user.password_hash = password_hash
            user.display_name = DEFAULT_DISPLAY_NAME
            user.primary_provider = AuthProvider.PASSWORD
            user.last_login_at = None
            repo.add(user)
            session.commit()
            print(
                f"[seed] Created {DEFAULT_EMAIL} (id={user.id}) "
                f"with password '{DEFAULT_PASSWORD}'."
            )
        else:
            existing.password_hash = password_hash
            if existing.primary_provider == AuthProvider.ANONYMOUS:
                existing.primary_provider = AuthProvider.PASSWORD
            if not existing.display_name:
                existing.display_name = DEFAULT_DISPLAY_NAME
            repo.update(existing)
            session.commit()
            print(
                f"[seed] Reset password for {DEFAULT_EMAIL} (id={existing.id}) "
                f"to '{DEFAULT_PASSWORD}'."
            )

    print(
        "[seed] Done. You can now log in at the UI with "
        f"'{DEFAULT_EMAIL}' / '{DEFAULT_PASSWORD}'."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

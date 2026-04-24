from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class WebAuthnCredential:
    """A single passkey registered by a user.

    ``credential_id`` is the raw (bytes) credential identifier returned by
    the authenticator; it is compared as-is during login. ``public_key``
    is the COSE-encoded public key blob. ``sign_count`` is the signature
    counter used for clone detection.
    """

    id: uuid.UUID
    user_id: uuid.UUID
    credential_id: bytes
    public_key: bytes
    sign_count: int
    transports: tuple[str, ...] = ()
    label: str | None = None
    created_at: datetime | None = None
    last_used_at: datetime | None = None

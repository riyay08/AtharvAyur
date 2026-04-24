from __future__ import annotations

from typing import Protocol


class PasswordHasher(Protocol):
    """Salted one-way hashing for passwords.

    Implementations should be slow by design (bcrypt/argon2/scrypt) and
    must never raise on wrong-password; they return ``False`` from
    ``verify`` instead.
    """

    def hash(self, plaintext: str) -> str: ...

    def verify(self, plaintext: str, hashed: str) -> bool: ...

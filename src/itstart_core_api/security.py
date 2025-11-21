from __future__ import annotations

from passlib.hash import argon2


def hash_password(password: str) -> str:
    """Return Argon2 hashed password."""
    return argon2.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Verify plain password against Argon2 hash."""
    return argon2.verify(password, hashed)

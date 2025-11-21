from __future__ import annotations

import pgpy


def encrypt_contact_info(plain: str | None, public_key: str | None) -> bytes | None:
    if not plain or not public_key:
        return None
    key, _ = pgpy.PGPKey.from_blob(public_key)
    msg = pgpy.PGPMessage.new(plain)
    enc = key.encrypt(msg)
    return bytes(enc)

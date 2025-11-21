from __future__ import annotations

from typing import Optional

import pgpy


def encrypt_contact_info(plain: Optional[str], public_key: Optional[str]) -> Optional[bytes]:
    if not plain or not public_key:
        return None
    key, _ = pgpy.PGPKey.from_blob(public_key)
    msg = pgpy.PGPMessage.new(plain)
    enc = key.encrypt(msg)
    return bytes(enc)

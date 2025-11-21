import datetime
import pytest
from uuid import uuid4

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy import select
import pgpy

from itstart_core_api import models
from itstart_core_api.publications import update_publication
from itstart_core_api.crypto import encrypt_contact_info
from itstart_core_api.config import Settings


def make_key():
    key = pgpy.PGPKey.new(pgpy.constants.PubKeyAlgorithm.RSAEncryptOrSign, 2048)
    uid = pgpy.PGPUID.new("Test User", email="test@example.com")
    key.add_uid(uid, usage={pgpy.constants.KeyFlags.EncryptCommunications})
    return key


@pytest.mark.asyncio
async def test_encrypt_contact_info(monkeypatch):
    pubkey = str(make_key().pubkey)
    encrypted = encrypt_contact_info("secret", pubkey)
    assert encrypted is not None
    assert len(encrypted) > 0

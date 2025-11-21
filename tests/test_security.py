from itstart_core_api.security import hash_password, verify_password


def test_hash_and_verify_password():
    raw = "P@ssw0rd!"
    hashed = hash_password(raw)
    assert hashed != raw
    assert verify_password(raw, hashed)
    assert not verify_password("wrong", hashed)

from backend.auth import generate_api_key, verify_api_key


def test_api_key_verification_is_one_way_and_rejects_bad_values():
    key, stored_hash = generate_api_key()

    assert verify_api_key(key, stored_hash)
    assert not verify_api_key("wrong-key", stored_hash)
    assert not verify_api_key(key, None)
    assert not verify_api_key(None, stored_hash)

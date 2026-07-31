from app.security import hash_password, verify_password


def test_password_hash_is_not_plain_text():
    password_hash = hash_password("ClaveSegura123!")
    assert password_hash != "ClaveSegura123!"
    assert verify_password("ClaveSegura123!", password_hash)


def test_wrong_password_is_rejected():
    password_hash = hash_password("ClaveCorrecta123!")
    assert not verify_password("ClaveIncorrecta", password_hash)

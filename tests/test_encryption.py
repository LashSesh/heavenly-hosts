from app.encryption import generate_keypair, encrypt_message, decrypt_message


def test_encryption_cycle():
    keys = generate_keypair()
    msg = "secret"
    enc = encrypt_message(keys["private"], keys["public"], msg)
    dec = decrypt_message(keys["private"], keys["public"], enc)
    assert dec == msg

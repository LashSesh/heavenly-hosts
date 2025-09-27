import nacl.utils
from nacl.public import PrivateKey, Box


def generate_keypair():
    sk = PrivateKey.generate()
    pk = sk.public_key
    return {"private": sk, "public": pk}


def encrypt_message(sk, pk, message: str):
    box = Box(sk, pk)
    nonce = nacl.utils.random(Box.NONCE_SIZE)
    encrypted = box.encrypt(message.encode(), nonce)
    return encrypted.hex()


def decrypt_message(sk, pk, encrypted_hex: str):
    box = Box(sk, pk)
    encrypted = bytes.fromhex(encrypted_hex)
    decrypted = box.decrypt(encrypted)
    return decrypted.decode()

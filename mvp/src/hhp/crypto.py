import hmac, hashlib
from nacl import public
from nacl.encoding import RawEncoder
from nacl.bindings import (
    crypto_aead_xchacha20poly1305_ietf_encrypt,
    crypto_aead_xchacha20poly1305_ietf_decrypt,
)

INFO = b"HHPv1"
NONCE_SIZE = 24
SALT_SIZE = 16

def hkdf_sha256(ikm: bytes, salt: bytes, info: bytes=INFO, length: int=32) -> bytes:
    from hashlib import sha256
    if not salt:
        salt = bytes(32)
    prk = hmac.new(salt, ikm, sha256).digest()
    t=b""; okm=b""; i=1
    while len(okm)<length:
        t = hmac.new(prk, t+info+bytes([i]), sha256).digest()
        okm += t; i+=1
    return okm[:length]

def topic_seed(tag: str) -> bytes:
    return hmac.new(b"hhp-tag", tag.encode("utf-8"), hashlib.sha256).digest()

def derive_topic_key(tag: str, salt: bytes) -> bytes:
    return hkdf_sha256(topic_seed(tag), salt, INFO, 32)

def aead_encrypt(key: bytes, nonce: bytes, aad: bytes, plaintext: bytes) -> bytes:
    return crypto_aead_xchacha20poly1305_ietf_encrypt(plaintext, aad, nonce, key)

def aead_decrypt(key: bytes, nonce: bytes, aad: bytes, ciphertext: bytes) -> bytes:
    return crypto_aead_xchacha20poly1305_ietf_decrypt(ciphertext, aad, nonce, key)

def sealed_box_encrypt(recipient_pk: bytes, msg: bytes) -> bytes:
    pk = public.PublicKey(recipient_pk, encoder=RawEncoder)
    box = public.SealedBox(pk)
    return box.encrypt(msg, encoder=RawEncoder)

def sealed_box_decrypt(recipient_sk: bytes, blob: bytes) -> bytes:
    sk = public.PrivateKey(recipient_sk, encoder=RawEncoder)
    box = public.SealedBox(sk)
    return box.decrypt(blob, encoder=RawEncoder)

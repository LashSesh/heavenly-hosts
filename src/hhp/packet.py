import os, struct
from dataclasses import dataclass
from .crypto import aead_encrypt, aead_decrypt, derive_topic_key, NONCE_SIZE, SALT_SIZE

HDR_FMT = "!BBHII16s24s"  # ver, flags, pad_len, t_epoch, win_ctr, salt(16), nonce(24)
VER = 0x01
FLAG_SEALED = 1<<0
FLAG_COVER  = 1<<1
AAD_MAGIC = b"HHPv1"

@dataclass
class Header:
    ver:int; flags:int; pad_len:int; t_epoch:int; win_ctr:int; salt:bytes; nonce:bytes

def pack_header(h: Header)->bytes:
    return struct.pack(HDR_FMT, h.ver, h.flags, h.pad_len, h.t_epoch, h.win_ctr, h.salt, h.nonce)

def unpack_header(buf: bytes)->Header:
    size = struct.calcsize(HDR_FMT)
    ver, flags, pad, te, wc, salt, nonce = struct.unpack(HDR_FMT, buf[:size])
    return Header(ver, flags, pad, te, wc, salt, nonce)

def build_fragment(tag:str, payload:bytes, t_epoch:int, win_ctr:int, sealed_pk:bytes|None=None, fragment_size:int=1024, cover:bool=False):
    salt = os.urandom(SALT_SIZE); nonce = os.urandom(NONCE_SIZE)
    flags = 0
    if cover: flags |= FLAG_COVER
    hdr = Header(VER, flags, 0, t_epoch, win_ctr, salt, nonce)
    aad_base = pack_header(hdr) + AAD_MAGIC
    pad_len = max(0, fragment_size - len(aad_base) - len(payload) - 16)
    hdr.pad_len = pad_len
    aad = pack_header(hdr) + AAD_MAGIC
    key = derive_topic_key(tag, salt)
    payload_padded = payload + os.urandom(pad_len)
    ciphertext = aead_encrypt(key, nonce, aad, payload_padded)
    frag = aad + ciphertext
    assert len(frag) == fragment_size, f"fragment size {len(frag)} != {fragment_size}"
    return frag

def parse_fragment(tag:str, fragment:bytes)->bytes:
    hdr = unpack_header(fragment)
    aad = pack_header(hdr) + AAD_MAGIC
    ciphertext = fragment[len(aad):]
    key = derive_topic_key(tag, hdr.salt)
    plaintext = aead_decrypt(key, hdr.nonce, aad, ciphertext)
    if hdr.pad_len:
        plaintext = plaintext[:-hdr.pad_len]
    return plaintext

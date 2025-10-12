import numpy as np, hashlib
from .crypto import hkdf_sha256

DIM=128

def tag_vec(tag:str)->np.ndarray:
    h = hashlib.sha256(tag.encode()).digest()
    raw = hkdf_sha256(h, b"", b"HHPv1-tag", DIM*4)
    ints = np.frombuffer(raw, dtype=np.uint32, count=DIM)
    vec = ints.astype(np.float32) / np.float32(2**32)
    vec = vec - vec.mean()
    n = np.linalg.norm(vec)
    if n == 0:
        return vec
    return vec / n

def cosine(a:np.ndarray, b:np.ndarray)->float:
    denom = (np.linalg.norm(a)*np.linalg.norm(b)) or 1.0
    return float(np.dot(a,b) / denom)

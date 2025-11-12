import os
import base64
from typing import Tuple, Optional
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.fernet import Fernet, InvalidToken as FernetInvalidToken
from cryptography.hazmat.backends import default_backend

DEFAULT_SCRYPT_N = 2**14
DEFAULT_SCRYPT_R = 8
DEFAULT_SCRYPT_P = 1

def generate_salt(length: int = 16) -> bytes:
    return os.urandom(length)

def derive_kek(master_password: str, salt: bytes, n: int = DEFAULT_SCRYPT_N, r: int = DEFAULT_SCRYPT_R, p: int = DEFAULT_SCRYPT_P, length: int = 32) -> bytes:
    kdf = Scrypt(salt=salt, length=length, n=n, r=r, p=p, backend=default_backend())
    return kdf.derive(master_password.encode('utf-8'))

def wrap_dek(kek: bytes, dek: bytes) -> str:
    """Encrypt DEK with KEK using AES-GCM; returns base64(nonce+ciphertext)"""
    aes = AESGCM(kek)
    nonce = os.urandom(12)
    ct = aes.encrypt(nonce, dek, None)
    return base64.urlsafe_b64encode(nonce + ct).decode('utf-8')

def unwrap_dek(kek: bytes, wrapped_b64: str) -> bytes:
    """Decrypt wrapped DEK; input is base64(nonce+ciphertext)"""
    s = wrapped_b64 or ''
    pad = '=' * (-len(s) % 4)
    data = base64.urlsafe_b64decode((s + pad).encode('utf-8'))
    nonce, ct = data[:12], data[12:]
    aes = AESGCM(kek)
    return aes.decrypt(nonce, ct, None)

def encrypt_with_key(key: bytes, plaintext: str) -> str:
    aes = AESGCM(key)
    nonce = os.urandom(12)
    ct = aes.encrypt(nonce, plaintext.encode('utf-8'), None)
    return base64.urlsafe_b64encode(nonce + ct).decode('utf-8')

def decrypt_with_key(key: bytes, b64: str) -> str:
    data = base64.urlsafe_b64decode(b64.encode('utf-8'))
    nonce, ct = data[:12], data[12:]
    aes = AESGCM(key)
    pt = aes.decrypt(nonce, ct, None)
    return pt.decode('utf-8')

# Fernet-based wrap for compatibility and robustness
def wrap_dek_v2(kek: bytes, dek: bytes) -> str:
    """Wrap DEK using Fernet with KEK-derived key (urlsafe base64)."""
    f_key = base64.urlsafe_b64encode(kek)
    f = Fernet(f_key)
    token = f.encrypt(dek)
    return token.decode('utf-8')

def unwrap_dek_v2(kek: bytes, token_b64: str) -> bytes:
    f_key = base64.urlsafe_b64encode(kek)
    f = Fernet(f_key)
    return f.decrypt(token_b64.encode('utf-8'))


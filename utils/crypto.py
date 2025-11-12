import base64
import os
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.backends import default_backend

_FERNET: Optional[Fernet] = None

def _load_key_from_env() -> Optional[bytes]:
    key_b64 = os.environ.get('CREDENTIALS_KEY') or ''
    if not key_b64:
        return None
    try:
        # Expect URL-safe base64-encoded 32-byte key for Fernet
        key = key_b64.encode('utf-8')
        # Validate by constructing Fernet
        Fernet(key)
        return key
    except Exception:
        return None

def _get_fernet() -> Optional[Fernet]:
    global _FERNET
    if _FERNET is not None:
        return _FERNET
    key = _load_key_from_env()
    if key is None:
        return None
    try:
        _FERNET = Fernet(key)
        return _FERNET
    except Exception:
        return None

def is_crypto_ready() -> bool:
    return _get_fernet() is not None

def encrypt_text(plaintext: str) -> Optional[str]:
    if plaintext is None:
        return None
    f = _get_fernet()
    if f is None:
        return None
    token = f.encrypt(plaintext.encode('utf-8'))
    return token.decode('utf-8')

def decrypt_text(ciphertext: str) -> Optional[str]:
    if not ciphertext:
        return None
    f = _get_fernet()
    if f is None:
        return None
    try:
        data = f.decrypt(ciphertext.encode('utf-8'))
        return data.decode('utf-8')
    except InvalidToken:
        return None


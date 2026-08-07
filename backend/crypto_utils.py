from cryptography.fernet import Fernet
from config import ENCRYPTION_KEY, require


def _fernet() -> Fernet:
    key = require("ENCRYPTION_KEY")
    return Fernet(key.encode())


def encrypt(value: str) -> bytes:
    return _fernet().encrypt(value.encode())


def decrypt(value: bytes) -> str:
    return _fernet().decrypt(value).decode()

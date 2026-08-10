from cryptography.fernet import Fernet
from config import require


def _fernet() -> Fernet:
    key = require("ENCRYPTION_KEY")
    return Fernet(key.encode())


def encrypt(value: str) -> bytes:
    return _fernet().encrypt(value.encode())


def decrypt(value) -> str:
    if isinstance(value, memoryview):
        value = value.tobytes()
    elif isinstance(value, bytearray):
        value = bytes(value)

    if not isinstance(value, (bytes, str)):
        raise TypeError(
            f"Invalid encrypted value type: {type(value).__name__}"
        )

    return _fernet().decrypt(value).decode()

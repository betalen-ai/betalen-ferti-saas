import base64
import hashlib
import hmac
from cryptography.fernet import Fernet, InvalidToken

from app.config import settings


def _fernet() -> Fernet:
    raw = settings.ENCRYPTION_KEY.encode("utf-8")
    if len(raw) == 32:
        key = base64.urlsafe_b64encode(raw)
    else:
        try:
            key = base64.urlsafe_b64encode(hashlib.sha256(raw).digest())
        except Exception as exc:
            raise RuntimeError("invalid ENCRYPTION_KEY") from exc
    return Fernet(key)


def encrypt_payload(payload: str) -> str:
    return _fernet().encrypt(payload.encode("utf-8")).decode("ascii")


def decrypt_payload(payload: str) -> str:
    try:
        return _fernet().decrypt(payload.encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("invalid encrypted payload") from exc


def constant_time_key_match(actual: str, expected: str) -> bool:
    return hmac.compare_digest(actual.encode("utf-8"), expected.encode("utf-8"))


def service_key_map() -> dict[str, str]:
    result = {}
    for item in settings.SERVICE_API_KEYS.split(","):
        if ":" not in item:
            continue
        service, key = item.strip().split(":", 1)
        if service and key:
            result[service] = key
    return result

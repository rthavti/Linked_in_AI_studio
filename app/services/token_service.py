import base64
import hashlib

from app.config.settings import settings


class TokenService:

    @staticmethod
    def _key() -> bytes:
        secret = settings.LINKEDIN_TOKEN_SECRET or settings.LINKEDIN_CLIENT_SECRET
        if not secret:
            raise ValueError("LINKEDIN_TOKEN_SECRET is not configured.")
        return hashlib.sha256(secret.encode("utf-8")).digest()

    @classmethod
    def encrypt(cls, token: str | None) -> str | None:
        if token is None:
            return None
        raw = token.encode("utf-8")
        key = cls._key()
        encrypted = bytes(byte ^ key[index % len(key)] for index, byte in enumerate(raw))
        return base64.urlsafe_b64encode(encrypted).decode("ascii")

    @classmethod
    def decrypt(cls, token: str | None) -> str | None:
        if token is None:
            return None
        encrypted = base64.urlsafe_b64decode(token.encode("ascii"))
        key = cls._key()
        raw = bytes(byte ^ key[index % len(key)] for index, byte in enumerate(encrypted))
        return raw.decode("utf-8")

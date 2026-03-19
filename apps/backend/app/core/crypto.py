from __future__ import annotations

import base64

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings


def validate_fernet_key(key: str) -> None:
    """Validate that *key* is a well-formed 32-byte URL-safe base64 Fernet key.

    Raises ``ValueError`` with a human-readable message on any problem so the
    application fails fast at startup rather than at the first encrypt/decrypt call.
    """
    if not key:
        raise ValueError(
            "APP_SECRETS_MASTER_KEY is empty. Generate one with: "
            'python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
        )
    try:
        decoded = base64.urlsafe_b64decode(key.encode("utf-8"))
    except Exception as exc:
        raise ValueError(
            f"APP_SECRETS_MASTER_KEY is not valid URL-safe base64: {exc}. "
            'Generate a valid key with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
        ) from exc
    if len(decoded) != 32:
        raise ValueError(
            f"APP_SECRETS_MASTER_KEY decoded to {len(decoded)} bytes; expected 32. "
            'Generate a valid key with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
        )
    # Final sanity check: Fernet itself accepts it.
    try:
        Fernet(key.encode("utf-8"))
    except (ValueError, InvalidToken) as exc:
        raise ValueError(f"APP_SECRETS_MASTER_KEY rejected by Fernet: {exc}") from exc


class SecretsCipher:
    def __init__(self) -> None:
        settings = get_settings()
        validate_fernet_key(settings.secrets_master_key)
        self._fernet = Fernet(settings.secrets_master_key.encode("utf-8"))

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        return self._fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")


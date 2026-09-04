from __future__ import annotations

import base64

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


class LedgerSigner:
    """
    Ed25519 signing/verification for ledger blocks.

    Private key material never belongs in a database record.
    """

    def __init__(self, private_key: Ed25519PrivateKey) -> None:
        self._private_key = private_key

    @classmethod
    def generate(cls) -> "LedgerSigner":
        return cls(Ed25519PrivateKey.generate())

    def sign(self, message: bytes) -> str:
        return base64.b64encode(self._private_key.sign(message)).decode("ascii")

    def public_key_base64(self) -> str:
        raw = self._private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return base64.b64encode(raw).decode("ascii")

    @staticmethod
    def verify(
        *,
        message: bytes,
        signature_base64: str,
        public_key_base64: str,
    ) -> bool:
        try:
            signature = base64.b64decode(signature_base64, validate=True)
            public_key_raw = base64.b64decode(public_key_base64, validate=True)
            public_key = Ed25519PublicKey.from_public_bytes(public_key_raw)
            public_key.verify(signature, message)
            return True
        except (ValueError, InvalidSignature):
            return False
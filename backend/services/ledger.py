from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from backend.canon.crypto.hash import canonical_json, hash_block
from backend.canon.crypto.signer import LedgerSigner
from backend.database.models.ledger import LedgerBlockModel
from backend.database.repositories.ledger import LedgerRepository


GENESIS_PREVIOUS_HASH = "0" * 64


class LedgerIntegrityError(RuntimeError):
    pass


class LedgerService:
    """
    Persistent, hash-chained, cryptographically signed ledger.
    """

    def __init__(
        self,
        *,
        repository: LedgerRepository,
        signer: LedgerSigner,
    ) -> None:
        self.repository = repository
        self.signer = signer

    def append(
        self,
        *,
        event_type: str,
        payload: dict[str, Any],
        transaction_id: str | None = None,
    ) -> LedgerBlockModel:
        latest = self.repository.get_latest()
        if latest is None:
            sequence_number = 0
            previous_hash = GENESIS_PREVIOUS_HASH
        else:
            sequence_number = latest.sequence_number + 1
            previous_hash = latest.block_hash

        payload_json = canonical_json(payload)
        block_hash = hash_block(
            sequence_number=sequence_number,
            event_type=event_type,
            payload_json=payload_json,
            previous_hash=previous_hash,
        )
        block = LedgerBlockModel(
            id=str(uuid4()),
            sequence_number=sequence_number,
            transaction_id=transaction_id,
            event_type=event_type,
            payload_json=payload_json,
            previous_hash=previous_hash,
            block_hash=block_hash,
            signature=self.signer.sign(block_hash.encode("utf-8")),
            signer_public_key=self.signer.public_key_base64(),
            created_at=datetime.now(timezone.utc),
        )
        return self.repository.create(block=block)

    def verify_block(self, block: LedgerBlockModel) -> bool:
        expected_hash = hash_block(
            sequence_number=block.sequence_number,
            event_type=block.event_type,
            payload_json=block.payload_json,
            previous_hash=block.previous_hash,
        )
        if expected_hash != block.block_hash:
            return False
        return LedgerSigner.verify(
            message=block.block_hash.encode("utf-8"),
            signature_base64=block.signature,
            public_key_base64=block.signer_public_key,
        )

    def verify_chain(self) -> bool:
        blocks = self.repository.list_all()
        previous_hash = GENESIS_PREVIOUS_HASH
        for expected_sequence, block in enumerate(blocks):
            if block.sequence_number != expected_sequence:
                return False
            if block.previous_hash != previous_hash:
                return False
            if not self.verify_block(block):
                return False
            previous_hash = block.block_hash
        return True
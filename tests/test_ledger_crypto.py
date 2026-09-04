from backend.canon.crypto.hash import canonical_json, hash_block
from backend.canon.crypto.signer import LedgerSigner
from backend.services.ledger import LedgerService


def test_canonical_json_is_deterministic():
    first = canonical_json({"amount": 9500, "currency": "INR"})
    second = canonical_json({"currency": "INR", "amount": 9500})

    assert first == second


def test_hash_changes_when_payload_changes():
    first = hash_block(
        sequence_number=1,
        event_type="TEST",
        payload_json='{"amount":9500}',
        previous_hash="0" * 64,
    )
    second = hash_block(
        sequence_number=1,
        event_type="TEST",
        payload_json='{"amount":9600}',
        previous_hash="0" * 64,
    )

    assert first != second


def test_hash_changes_when_previous_hash_changes():
    first = hash_block(
        sequence_number=1,
        event_type="TEST",
        payload_json='{"amount":9500}',
        previous_hash="0" * 64,
    )
    second = hash_block(
        sequence_number=1,
        event_type="TEST",
        payload_json='{"amount":9500}',
        previous_hash="1" * 64,
    )

    assert first != second


def test_ed25519_signature_verifies():
    signer = LedgerSigner.generate()
    message = b"Governor decision"
    signature = signer.sign(message)

    assert LedgerSigner.verify(
        message=message,
        signature_base64=signature,
        public_key_base64=signer.public_key_base64(),
    )


def test_tampered_message_fails_verification():
    signer = LedgerSigner.generate()
    signature = signer.sign(b"original")

    assert not LedgerSigner.verify(
        message=b"tampered",
        signature_base64=signature,
        public_key_base64=signer.public_key_base64(),
    )


class FakeLedgerRepository:
    def __init__(self):
        self.blocks = []

    def get_latest(self):
        return self.blocks[-1] if self.blocks else None

    def create(self, *, block):
        self.blocks.append(block)
        return block

    def list_all(self):
        return list(self.blocks)


def test_ledger_chain_verifies():
    repository = FakeLedgerRepository()
    ledger = LedgerService(
        repository=repository,
        signer=LedgerSigner.generate(),
    )

    ledger.append(
        event_type="GENESIS",
        payload={"type": "GENESIS", "system": "The Governor"},
    )
    ledger.append(
        event_type="GOVERNOR_ALLOW",
        payload={"transaction_id": "tx-001", "authorized_amount": "9500.00"},
        transaction_id="tx-001",
    )
    ledger.append(
        event_type="PAYMENT_PENDING",
        payload={"transaction_id": "tx-001"},
        transaction_id="tx-001",
    )

    assert ledger.verify_chain() is True


def test_tampered_block_breaks_chain():
    repository = FakeLedgerRepository()
    ledger = LedgerService(
        repository=repository,
        signer=LedgerSigner.generate(),
    )

    ledger.append(event_type="GENESIS", payload={"type": "GENESIS"})
    ledger.append(event_type="GOVERNOR_ALLOW", payload={"amount": "9500.00"})

    assert ledger.verify_chain() is True

    repository.blocks[1].payload_json = '{"amount":"100.00"}'

    assert ledger.verify_chain() is False
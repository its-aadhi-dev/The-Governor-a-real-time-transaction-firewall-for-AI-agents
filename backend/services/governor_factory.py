from __future__ import annotations

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from backend.canon.crypto.signer import LedgerSigner
from backend.canon.governor import Governor
from backend.core.config import settings
from backend.database.repositories.collusion import CollusionRepository
from backend.database.repositories.ledger import LedgerRepository
from backend.database.repositories.reputation import ReputationRepository
from backend.database.repositories.transaction import TransactionRepository
from backend.database.repositories.velocity import VelocityRepository
from backend.payments.razorpay import RazorpayAdapter
from backend.services.collusion import CollusionService
from backend.services.governor import GovernorService
from backend.services.ledger import LedgerService
from backend.services.payment import PaymentService
from backend.services.reputation import ReputationService
from backend.services.transaction_lifecycle_service import (
    TransactionLifecycleService,
)
from backend.services.velocity import VelocityService


# One signer for the lifetime of this application process.
# Ledger blocks retain their own public key, so existing blocks
# remain independently verifiable.
_LEDGER_SIGNER = LedgerSigner.generate()


def build_governor_service(db: Session) -> GovernorService:
    transaction_repository = TransactionRepository(db)

    velocity_repository = VelocityRepository(
        transaction_repository=transaction_repository,
    )

    collusion_repository = CollusionRepository(
        transaction_repository=transaction_repository,
    )

    reputation_repository = ReputationRepository(db)

    velocity_service = VelocityService(
        velocity_repository=velocity_repository,
    )

    reputation_service = ReputationService(
        reputation_repository=reputation_repository,
    )

    collusion_service = CollusionService(
        collusion_repository=collusion_repository,
    )

    governor = Governor(
        velocity_service=velocity_service,
        reputation_service=reputation_service,
        collusion_service=collusion_service,
    )

    razorpay_adapter = RazorpayAdapter(
        key_id=settings.razorpay_key_id.get_secret_value(),
        key_secret=settings.razorpay_key_secret.get_secret_value(),
    )

    payment_service = PaymentService(
        gateway=razorpay_adapter,
    )

    ledger_service = LedgerService(
        repository=LedgerRepository(db),
        signer=_LEDGER_SIGNER,
    )

    lifecycle_service = TransactionLifecycleService(db)

    return GovernorService(
        governor=governor,
        transaction_repository=transaction_repository,
        lifecycle_service=lifecycle_service,
        payment_service=payment_service,
        ledger_service=ledger_service,
    )
    
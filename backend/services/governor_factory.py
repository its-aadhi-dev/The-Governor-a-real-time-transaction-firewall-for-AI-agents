from __future__ import annotations

from sqlalchemy.orm import Session

from backend.canon.governor import Governor
from backend.core.config import settings
from backend.database.repositories.collusion import CollusionRepository
from backend.database.repositories.reputation import ReputationRepository
from backend.database.repositories.transaction import TransactionRepository
from backend.database.repositories.velocity import VelocityRepository
from backend.payments.razorpay import RazorpayAdapter
from backend.services.collusion import CollusionService
from backend.services.governor import GovernorService
from backend.services.payment import PaymentService
from backend.services.reputation import ReputationService
from backend.services.transaction_lifecycle_service import (
    TransactionLifecycleService,
)
from backend.services.velocity import VelocityService


def build_governor_service(db: Session) -> GovernorService:
    """
    Build the single canonical Governor application stack.

    All transaction entry points should use this factory.
    """

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

    lifecycle_service = TransactionLifecycleService(db)

    return GovernorService(
        governor=governor,
        transaction_repository=transaction_repository,
        lifecycle_service=lifecycle_service,
        payment_service=payment_service,
    )

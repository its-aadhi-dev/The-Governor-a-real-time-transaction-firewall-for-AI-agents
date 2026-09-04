from decimal import Decimal

from backend.canon.policies.collusion import CollusionPolicy
from backend.core.collusion import CollusionVerdict
from backend.services.collusion import CollusionService


class FakeCollusionRepository:
    def __init__(
        self,
        *,
        buyer_count: int,
        pair_count: int,
    ) -> None:
        self.buyer_count = buyer_count
        self.pair_count = pair_count

    def get_relationship_counts(
        self,
        *,
        buyer_agent_id: str,
        merchant_id: str,
    ) -> tuple[int, int]:
        return self.buyer_count, self.pair_count


def test_service_builds_relationship_context():
    repository = FakeCollusionRepository(
        buyer_count=20,
        pair_count=17,
    )

    service = CollusionService(
        collusion_repository=repository,
        policy=CollusionPolicy(
            minimum_pair_transactions=5,
            review_concentration=Decimal("0.80"),
        ),
    )

    decision = service.evaluate(
        buyer_agent_id="buyer-001",
        merchant_id="merchant-001",
    )

    assert decision.verdict == CollusionVerdict.REVIEW
    assert decision.concentration_ratio == Decimal("0.85")
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from backend.canon.governor import Governor
from backend.canon.policies.collusion import CollusionVerdict
from backend.canon.policies.pricing import PricingPolicy
from backend.canon.policies.reputation import ReputationBand
from backend.canon.risk.engine import RiskEngine
from backend.core.collusion import CollusionDecision
from backend.core.governance import GovernanceContext
from backend.core.reputation import ReputationDecision
from backend.core.velocity import VelocityDecision


@dataclass(frozen=True)
class AttackSignals:
    velocity_allowed: bool = True
    velocity_count: int = 0
    velocity_limit: int = 5
    reputation_band: ReputationBand = ReputationBand.GOOD
    reputation_score: Decimal = Decimal("1.00")
    collusion_verdict: CollusionVerdict = CollusionVerdict.NORMAL
    concentration_ratio: Decimal = Decimal("0")


class AttackGovernorAdapter:
    """
    Benchmark adapter around the production Canon Governor.

    Policy, risk, and decision algorithms are production implementations.
    Only historical signal providers are injected as deterministic benchmark
    data, allowing scenarios to exercise controlled adversarial conditions.
    """

    def evaluate(self, scenario):
        signals = self._signals_for(scenario)
        governor = Governor(
            velocity_service=_ScenarioVelocityService(signals),
            reputation_service=_ScenarioReputationService(signals),
            collusion_service=_ScenarioCollusionService(signals),
            pricing_policy=PricingPolicy(),
            risk_engine=RiskEngine(),
        )
        return governor.evaluate(
            context=self._context_for(scenario),
        )

    @staticmethod
    def _context_for(scenario) -> GovernanceContext:
        if scenario.payload.get("price_mode") == "below_floor":
            negotiated_price = Decimal("850.00")
            floor_price = Decimal("900.00")
        else:
            negotiated_price = Decimal("950.00")
            floor_price = Decimal("900.00")

        return GovernanceContext(
            transaction_id=f"attack-{scenario.name}",
            buyer_agent_id="attack-buyer",
            merchant_id="attack-merchant",
            catalog_item_id="attack-item",
            catalog_price=Decimal("1000.00"),
            negotiated_price=negotiated_price,
            merchant_floor_price=floor_price,
            historical_min_price=None,
            historical_max_price=None,
        )

    @staticmethod
    def _signals_for(scenario) -> AttackSignals:
        payload = scenario.payload
        return AttackSignals(
            velocity_allowed=payload.get("velocity_mode", "normal") != "blocked",
            velocity_count=5 if payload.get("velocity_mode") == "blocked" else 0,
            reputation_band=(
                ReputationBand.POOR
                if payload.get("reputation_mode") == "poor"
                else ReputationBand.GOOD
            ),
            reputation_score=(
                Decimal("0.20")
                if payload.get("reputation_mode") == "poor"
                else Decimal("1.00")
            ),
            collusion_verdict=(
                CollusionVerdict.REVIEW
                if payload.get("collusion_mode") == "concentrated"
                else CollusionVerdict.NORMAL
            ),
            concentration_ratio=(
                Decimal("0.90")
                if payload.get("collusion_mode") == "concentrated"
                else Decimal("0")
            ),
        )


class _ScenarioVelocityService:
    def __init__(self, signals: AttackSignals):
        self.signals = signals

    def evaluate(self, *, buyer_agent_id: str, now=None):
        return VelocityDecision(
            allowed=self.signals.velocity_allowed,
            reason=(
                "Benchmark velocity attack."
                if not self.signals.velocity_allowed
                else "Benchmark velocity normal."
            ),
            transaction_count=self.signals.velocity_count,
            limit=self.signals.velocity_limit,
            window_seconds=60,
        )


class _ScenarioReputationService:
    def __init__(self, signals: AttackSignals):
        self.signals = signals

    def evaluate(self, *, agent_id: str):
        return ReputationDecision(
            band=self.signals.reputation_band,
            score=self.signals.reputation_score,
            reason=(
                "Benchmark poor reputation."
                if self.signals.reputation_band == ReputationBand.POOR
                else "Benchmark good reputation."
            ),
        )


class _ScenarioCollusionService:
    def __init__(self, signals: AttackSignals):
        self.signals = signals

    def evaluate(self, *, buyer_agent_id: str, merchant_id: str):
        return CollusionDecision(
            verdict=self.signals.collusion_verdict,
            concentration_ratio=self.signals.concentration_ratio,
            reason=(
                "Benchmark concentrated relationship."
                if self.signals.collusion_verdict == CollusionVerdict.REVIEW
                else "Benchmark normal relationship."
            ),
        )
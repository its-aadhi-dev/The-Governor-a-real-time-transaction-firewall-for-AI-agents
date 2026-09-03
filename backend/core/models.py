from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ============================================================
# TIME
# ============================================================


def utc_now() -> datetime:
    """
    Return a timezone-aware UTC timestamp.

    All transaction timestamps in the system use UTC so that
    ordering and rolling-window calculations remain unambiguous.
    """

    return datetime.now(timezone.utc)


# ============================================================
# BASE DOMAIN MODEL
# ============================================================


class GovernorBaseModel(BaseModel):
    """
    Base Pydantic model used by the transaction domain.

    extra='forbid' is intentional.

    Security-sensitive payloads should fail closed when an unexpected
    field is supplied instead of silently accepting arbitrary data.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )


# ============================================================
# AGENTS
# ============================================================


class AgentRole(str, Enum):
    BUYER = "BUYER"
    MERCHANT = "MERCHANT"
    GOVERNOR = "GOVERNOR"
    SYSTEM = "SYSTEM"


class AgentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    QUARANTINED = "QUARANTINED"
    DISABLED = "DISABLED"


class AgentIdentity(GovernorBaseModel):
    """
    Identity known to the commerce platform.

    This represents platform identity, not something an LLM
    is allowed to declare for itself.
    """

    agent_id: str = Field(
        min_length=1,
        max_length=128,
    )

    role: AgentRole

    display_name: str | None = Field(
        default=None,
        max_length=200,
    )

    merchant_id: str | None = Field(
        default=None,
        max_length=128,
    )

    status: AgentStatus = AgentStatus.ACTIVE

    trust_score: Decimal = Field(
        default=Decimal("1.0000"),
        ge=Decimal("0"),
        le=Decimal("1"),
    )


# ============================================================
# COMMERCE
# ============================================================


class CommerceItem(GovernorBaseModel):
    """
    Canonical representation of an item/service offered by a merchant.
    """

    item_id: str = Field(
        min_length=1,
        max_length=128,
    )

    item_name: str = Field(
        min_length=1,
        max_length=300,
    )

    base_price: Decimal = Field(
        gt=Decimal("0"),
        max_digits=18,
        decimal_places=2,
    )

    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=3,
    )

    @field_validator("currency")
    @classmethod
    def normalize_currency(
        cls,
        value: str,
    ) -> str:
        return value.upper()


# ============================================================
# NEGOTIATION
# ============================================================


class NegotiationStatus(str, Enum):
    OPEN = "OPEN"
    COUNTERED = "COUNTERED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class ProposalType(str, Enum):
    OFFER = "OFFER"
    COUNTER_OFFER = "COUNTER_OFFER"
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"


class NegotiationProposal(GovernorBaseModel):
    """
    Untrusted proposal produced by a marketplace participant.

    IMPORTANT:
    This is not an executable payment instruction.

    An LLM may influence this object.
    The Canon never treats it as authorization.
    """

    proposal_id: str = Field(
        min_length=1,
        max_length=128,
    )

    negotiation_id: str = Field(
        min_length=1,
        max_length=128,
    )

    transaction_id: str = Field(
        min_length=1,
        max_length=128,
    )

    agent_id: str = Field(
        min_length=1,
        max_length=128,
    )

    role: AgentRole

    proposal_type: ProposalType

    proposed_price: Decimal = Field(
        gt=Decimal("0"),
        max_digits=18,
        decimal_places=2,
    )

    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=3,
    )

    message: str = Field(
        default="",
        max_length=2000,
    )

    sequence_number: int = Field(
        ge=1,
    )

    created_at: datetime = Field(
        default_factory=utc_now,
    )

    @field_validator("currency")
    @classmethod
    def normalize_currency(
        cls,
        value: str,
    ) -> str:
        return value.upper()


class NegotiatedDeal(GovernorBaseModel):
    """
    Final result of the buyer/merchant negotiation.

    A NegotiatedDeal is still NOT payment authorization.

    The Governor must independently verify the deal before payment.
    """

    transaction_id: str = Field(
        min_length=1,
        max_length=128,
    )

    negotiation_id: str = Field(
        min_length=1,
        max_length=128,
    )

    buyer_agent_id: str = Field(
        min_length=1,
        max_length=128,
    )

    merchant_agent_id: str = Field(
        min_length=1,
        max_length=128,
    )

    item: CommerceItem

    agreed_price: Decimal = Field(
        gt=Decimal("0"),
        max_digits=18,
        decimal_places=2,
    )

    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=3,
    )

    status: NegotiationStatus = NegotiationStatus.ACCEPTED

    proposal_count: int = Field(
        ge=1,
    )

    final_proposal_id: str = Field(
        min_length=1,
        max_length=128,
    )

    negotiated_at: datetime = Field(
        default_factory=utc_now,
    )

    @field_validator("currency")
    @classmethod
    def normalize_currency(
        cls,
        value: str,
    ) -> str:
        return value.upper()


# ============================================================
# TRANSACTION
# ============================================================


class TransactionStatus(str, Enum):
    CREATED = "CREATED"

    GOVERNANCE_PENDING = "GOVERNANCE_PENDING"

    APPROVED = "APPROVED"

    REVIEW = "REVIEW"

    BLOCKED = "BLOCKED"

    FALLBACK = "FALLBACK"

    PAYMENT_PENDING = "PAYMENT_PENDING"

    PAID = "PAID"

    FAILED = "FAILED"

    EXPIRED = "EXPIRED"


class TransactionIntent(GovernorBaseModel):
    """
    Transaction submitted to the Governor.

    This is the security boundary between the marketplace and
    the deterministic Canon.

    It describes what the marketplace wants to execute.

    It does NOT authorize payment.
    """

    transaction_id: str = Field(
        min_length=1,
        max_length=128,
    )

    negotiation_id: str = Field(
        min_length=1,
        max_length=128,
    )

    buyer_agent_id: str = Field(
        min_length=1,
        max_length=128,
    )

    merchant_agent_id: str = Field(
        min_length=1,
        max_length=128,
    )

    item: CommerceItem

    requested_price: Decimal = Field(
        gt=Decimal("0"),
        max_digits=18,
        decimal_places=2,
    )

    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=3,
    )

    idempotency_key: str = Field(
        min_length=1,
        max_length=128,
    )

    created_at: datetime = Field(
        default_factory=utc_now,
    )

    # Context may contain marketplace information, but it is
    # advisory and untrusted for security decisions.
    agent_context: dict[str, Any] = Field(
        default_factory=dict,
    )

    @field_validator("currency")
    @classmethod
    def normalize_currency(
        cls,
        value: str,
    ) -> str:
        return value.upper()

    @property
    def base_price(self) -> Decimal:
        """
        Compatibility accessor.

        The authoritative catalog price is stored on the item.
        """

        return self.item.base_price

    @property
    def item_id(self) -> str:
        return self.item.item_id

    @property
    def item_name(self) -> str:
        return self.item.item_name


# ============================================================
# GOVERNANCE
# ============================================================


class SystemDecision(str, Enum):
    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"
    FALLBACK = "FALLBACK"


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RuleCategory(str, Enum):
    IDENTITY = "IDENTITY"
    PRICE = "PRICE"
    MARGIN = "MARGIN"
    VELOCITY = "VELOCITY"
    REPLAY = "REPLAY"
    REPUTATION = "REPUTATION"
    COLLUSION = "COLLUSION"
    ANOMALY = "ANOMALY"
    PAYMENT = "PAYMENT"


class RuleViolation(GovernorBaseModel):
    """
    Machine-readable governance violation.

    This structure will later be shown directly in the UI.
    """

    rule_code: str = Field(
        min_length=1,
        max_length=100,
    )

    category: RuleCategory

    severity: Severity

    message: str = Field(
        min_length=1,
        max_length=1000,
    )

    observed_value: str | None = Field(
        default=None,
        max_length=500,
    )

    allowed_value: str | None = Field(
        default=None,
        max_length=500,
    )


# ============================================================
# RISK
# ============================================================


class RiskAssessment(GovernorBaseModel):
    """
    Deterministic/statistical risk assessment.

    A risk score is evidence used by the Decision Engine.
    It is not itself a payment authorization.
    """

    score: Decimal = Field(
        default=Decimal("0"),
        ge=Decimal("0"),
        le=Decimal("1"),
        max_digits=6,
        decimal_places=4,
    )

    signals: list[RuleViolation] = Field(
        default_factory=list,
    )

    engine_version: str = Field(
        default="risk-v1",
        min_length=1,
        max_length=100,
    )


# ============================================================
# LATENCY
# ============================================================


class LatencyMetrics(GovernorBaseModel):
    """
    Stage-level timing information.

    All values are milliseconds.
    """

    schema_validation_ms: float = Field(
        default=0.0,
        ge=0,
    )

    policy_engine_ms: float = Field(
        default=0.0,
        ge=0,
    )

    risk_engine_ms: float = Field(
        default=0.0,
        ge=0,
    )

    decision_engine_ms: float = Field(
        default=0.0,
        ge=0,
    )

    state_persistence_ms: float = Field(
        default=0.0,
        ge=0,
    )

    crypto_signing_ms: float = Field(
        default=0.0,
        ge=0,
    )

    gateway_api_ms: float = Field(
        default=0.0,
        ge=0,
    )

    total_governor_overhead_ms: float = Field(
        default=0.0,
        ge=0,
    )

    total_transaction_time_ms: float = Field(
        default=0.0,
        ge=0,
    )

    llm_negotiation_ms: float = Field(
        default=0.0,
        ge=0,
    )


# ============================================================
# PAYMENT AUTHORIZATION
# ============================================================


class PaymentAuthorization(GovernorBaseModel):
    """
    Executable payment authorization.

    This object must ONLY be created after the Governor has
    completed its deterministic governance process.

    The marketplace LLM does not create this object.
    """

    authorization_id: str = Field(
        min_length=1,
        max_length=128,
    )

    transaction_id: str = Field(
        min_length=1,
        max_length=128,
    )

    buyer_agent_id: str = Field(
        min_length=1,
        max_length=128,
    )

    merchant_agent_id: str = Field(
        min_length=1,
        max_length=128,
    )

    amount: Decimal = Field(
        gt=Decimal("0"),
        max_digits=18,
        decimal_places=2,
    )

    currency: str = Field(
        min_length=3,
        max_length=3,
    )

    governor_decision: SystemDecision

    authorization_reason: str = Field(
        min_length=1,
        max_length=2000,
    )

    governor_policy_version: str = Field(
        default="canon-v1",
        min_length=1,
        max_length=100,
    )

    authorized_at: datetime = Field(
        default_factory=utc_now,
    )

    @field_validator("currency")
    @classmethod
    def normalize_currency(
        cls,
        value: str,
    ) -> str:
        return value.upper()


# ============================================================
# PAYMENT RESULT
# ============================================================


class PaymentStatus(str, Enum):
    CREATED = "CREATED"
    AUTHORIZED = "AUTHORIZED"
    CAPTURED = "CAPTURED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class PaymentResult(GovernorBaseModel):
    """
    Provider result after the authorized payment request is sent.
    """

    transaction_id: str = Field(
        min_length=1,
        max_length=128,
    )

    provider: str = Field(
        default="razorpay",
        min_length=1,
        max_length=50,
    )

    status: PaymentStatus

    success: bool

    amount: Decimal = Field(
        gt=Decimal("0"),
        max_digits=18,
        decimal_places=2,
    )

    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=3,
    )

    provider_reference: str | None = Field(
        default=None,
        max_length=200,
    )

    checkout_url: str | None = Field(
        default=None,
        max_length=2000,
    )

    error_code: str | None = Field(
        default=None,
        max_length=100,
    )

    error_message: str | None = Field(
        default=None,
        max_length=1000,
    )

    created_at: datetime = Field(
        default_factory=utc_now,
    )

    @field_validator("currency")
    @classmethod
    def normalize_currency(
        cls,
        value: str,
    ) -> str:
        return value.upper()


# ============================================================
# GOVERNOR VERDICT
# ============================================================


class FirewallVerdict(GovernorBaseModel):
    """
    Complete output of the Governor.

    This is the primary evidence object consumed by:
        - API
        - audit system
        - UI
        - metrics
        - benchmark suite
    """

    transaction_id: str = Field(
        min_length=1,
        max_length=128,
    )

    status: TransactionStatus

    decision: SystemDecision

    requested_price: Decimal = Field(
        gt=Decimal("0"),
        max_digits=18,
        decimal_places=2,
    )

    authorized_price: Decimal | None = Field(
        default=None,
        gt=Decimal("0"),
        max_digits=18,
        decimal_places=2,
    )

    risk: RiskAssessment

    violations: list[RuleViolation] = Field(
        default_factory=list,
    )

    reason: str = Field(
        min_length=1,
        max_length=2000,
    )

    razorpay_order_id: str | None = Field(
        default=None,
        max_length=200,
    )

    fallback_payment_url: str | None = Field(
        default=None,
        max_length=2000,
    )

    payment: PaymentResult | None = None

    latency: LatencyMetrics = Field(
        default_factory=LatencyMetrics,
    )

    policy_version: str = Field(
        default="canon-v1",
        min_length=1,
        max_length=100,
    )

    evaluated_at: datetime = Field(
        default_factory=utc_now,
    )


# ============================================================
# LEDGER
# ============================================================


class LedgerBlock(GovernorBaseModel):
    """
    Cryptographically chained audit record.
    """

    index: int = Field(
        ge=0,
    )

    timestamp: datetime = Field(
        default_factory=utc_now,
    )

    transaction_id: str = Field(
        min_length=1,
        max_length=128,
    )

    transaction: dict[str, Any]

    verdict: dict[str, Any]

    previous_hash: str = Field(
        min_length=64,
        max_length=64,
    )

    current_hash: str = Field(
        min_length=64,
        max_length=64,
    )

    signature: str = Field(
        min_length=1,
        max_length=1000,
    )

    signer_key_id: str = Field(
        min_length=1,
        max_length=200,
    )

    schema_version: str = Field(
        default="ledger-v1",
        min_length=1,
        max_length=50,
    )
    
    
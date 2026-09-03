import pytest

from backend.core.lifecycle import InvalidTransactionTransition, validate_transition
from backend.core.models import TransactionStatus


def test_created_can_enter_governance():
    validate_transition(TransactionStatus.CREATED, TransactionStatus.GOVERNANCE_PENDING)


def test_governance_can_be_approved():
    validate_transition(TransactionStatus.GOVERNANCE_PENDING, TransactionStatus.APPROVED)


def test_approved_can_enter_payment():
    validate_transition(TransactionStatus.APPROVED, TransactionStatus.PAYMENT_PENDING)


def test_payment_can_complete():
    validate_transition(TransactionStatus.PAYMENT_PENDING, TransactionStatus.PAID)


def test_blocked_cannot_be_paid():
    with pytest.raises(InvalidTransactionTransition):
        validate_transition(TransactionStatus.BLOCKED, TransactionStatus.PAID)


def test_paid_cannot_be_reversed():
    with pytest.raises(InvalidTransactionTransition):
        validate_transition(TransactionStatus.PAID, TransactionStatus.BLOCKED)


def test_expired_cannot_resume():
    with pytest.raises(InvalidTransactionTransition):
        validate_transition(TransactionStatus.EXPIRED, TransactionStatus.PAYMENT_PENDING)
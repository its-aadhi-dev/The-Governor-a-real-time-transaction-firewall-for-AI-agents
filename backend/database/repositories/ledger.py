from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models.ledger import LedgerBlockModel


class LedgerRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_latest(self) -> LedgerBlockModel | None:
        statement = (
            select(LedgerBlockModel)
            .order_by(LedgerBlockModel.sequence_number.desc())
            .limit(1)
        )
        return self.session.scalar(statement)

    def get_by_sequence(self, sequence_number: int) -> LedgerBlockModel | None:
        statement = select(LedgerBlockModel).where(
            LedgerBlockModel.sequence_number == sequence_number
        )
        return self.session.scalar(statement)

    def create(self, *, block: LedgerBlockModel) -> LedgerBlockModel:
        self.session.add(block)
        self.session.flush()
        return block

    def list_all(self) -> list[LedgerBlockModel]:
        statement = select(LedgerBlockModel).order_by(
            LedgerBlockModel.sequence_number.asc()
        )
        return list(self.session.scalars(statement))
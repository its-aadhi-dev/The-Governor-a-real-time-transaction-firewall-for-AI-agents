from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models.merchant import MerchantModel


class MerchantRepository:
    """Persistence operations for merchants."""

    def __init__(self, db: Session):
        self.db = db

    def get(self, merchant_id: str) -> Optional[MerchantModel]:
        statement = select(MerchantModel).where(
            MerchantModel.merchant_id == merchant_id
        )
        return self.db.scalar(statement)

    def list_active(self) -> List[MerchantModel]:
        statement = (
            select(MerchantModel)
            .where(MerchantModel.active.is_(True))
            .order_by(MerchantModel.display_name.asc())
        )
        return list(self.db.scalars(statement).all())

    def create(
        self,
        *,
        merchant_id: str,
        display_name: str,
        razorpay_account_reference: Optional[str] = None,
    ) -> MerchantModel:
        merchant = MerchantModel(
            merchant_id=merchant_id,
            display_name=display_name,
            razorpay_account_reference=razorpay_account_reference,
            active=True,
        )
        self.db.add(merchant)
        self.db.flush()
        return merchant

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models.catalog import CatalogItemModel


class CatalogRepository:
	"""Persistence operations for merchant catalog items."""

	def __init__(self, db: Session):
		self.db = db

	def get(self, item_id: str) -> Optional[CatalogItemModel]:
		statement = select(CatalogItemModel).where(CatalogItemModel.item_id == item_id)
		return self.db.scalar(statement)

	def create(
		self,
		*,
		item_id: str,
		merchant_id: str,
		item_name: str,
		base_price: Decimal,
		currency: str = "INR",
		available_quantity: int = 0,
	) -> CatalogItemModel:
		item = CatalogItemModel(
			item_id=item_id,
			merchant_id=merchant_id,
			item_name=item_name,
			base_price=base_price,
			currency=currency.upper(),
			available_quantity=available_quantity,
			active=True,
		)
		self.db.add(item)
		self.db.flush()
		return item

	def list_for_merchant(self, merchant_id: str) -> List[CatalogItemModel]:
		statement = (
			select(CatalogItemModel)
			.where(CatalogItemModel.merchant_id == merchant_id)
			.where(CatalogItemModel.active.is_(True))
			.order_by(CatalogItemModel.item_name.asc())
		)
		return list(self.db.scalars(statement).all())

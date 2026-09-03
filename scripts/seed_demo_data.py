import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from decimal import Decimal

from backend.database.repositories.agent import AgentRepository
from backend.database.repositories.catalog import CatalogRepository
from backend.database.repositories.merchant import MerchantRepository
from backend.database.repositories.negotiation import NegotiationRepository
from backend.database.session import SessionLocal


def seed() -> None:
    """Insert the repeatable demo graph into an already migrated database."""

    db = SessionLocal()
    try:
        agents = AgentRepository(db)
        merchants = MerchantRepository(db)
        catalog = CatalogRepository(db)
        negotiations = NegotiationRepository(db)

        merchant = merchants.get("merchant_compute_01")
        if merchant is None:
            merchant = merchants.create(
                merchant_id="merchant_compute_01",
                display_name="Compute Infrastructure",
            )

        agents.get_or_create(
            agent_id="buyer_demo_01",
            role="BUYER",
            display_name="Demo Buyer",
        )
        agents.get_or_create(
            agent_id="merchant_agent_01",
            role="MERCHANT",
            display_name="Compute Merchant",
            merchant_id=merchant.merchant_id,
        )

        item = catalog.get("compute_10k_credits")
        if item is None:
            item = catalog.create(
                item_id="compute_10k_credits",
                merchant_id=merchant.merchant_id,
                item_name="10,000 Compute Credits",
                base_price=Decimal("1800.00"),
                currency="INR",
                available_quantity=100,
            )

        negotiation = negotiations.get("neg_demo_001")
        if negotiation is None:
            negotiations.create(
                negotiation_id="neg_demo_001",
                buyer_agent_id="buyer_demo_01",
                merchant_agent_id="merchant_agent_01",
                item_id=item.item_id,
            )

        db.commit()
        print("Demo data seeded successfully.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
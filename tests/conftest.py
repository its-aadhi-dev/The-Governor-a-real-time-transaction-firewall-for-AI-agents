import os
from pathlib import Path

# Set the test database BEFORE any backend modules are imported by tests.
TEST_DB_PATH = Path("storage/test_governor.db").resolve()

os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"

# Import after DATABASE_URL is set.
# pyrefly: ignore [missing-import]
from alembic import command
# pyrefly: ignore [missing-import]
from alembic.config import Config

from backend.database import Base
from backend.database.session import SessionLocal
from backend.database.models import MerchantModel, CatalogItemModel


def pytest_sessionstart(session):
    """Create a clean migrated database for the pytest session."""
    TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option(
        "sqlalchemy.url",
        f"sqlite:///{TEST_DB_PATH.as_posix()}",
    )

    command.upgrade(alembic_cfg, "head")

    db = SessionLocal()
    try:
        merchant = MerchantModel(
            merchant_id="merchant_compute_01",
            display_name="Compute Infrastructure",
            active=True,
        )
        item = CatalogItemModel(
            item_id="compute_10k_credits",
            merchant_id="merchant_compute_01",
            item_name="10,000 Compute Credits",
            base_price=1800,
            currency="INR",
            available_quantity=100,
            active=True,
        )

        db.add(merchant)
        db.add(item)
        db.commit()
    finally:
        db.close()

        
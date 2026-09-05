from decimal import Decimal
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from backend.api.routes.voice import get_voice_market
from backend.database.models.catalog import CatalogItemModel
from backend.database.models.merchant import MerchantModel
from backend.main import app


def test_voice_market_endpoint():
    client = TestClient(app)
    response = client.get("/api/v1/voice/market")
    assert response.status_code == 200
    data = response.json()
    assert "merchants" in data
    assert isinstance(data["merchants"], list)


def test_voice_negotiate_endpoint():
    client = TestClient(app)
    body = {
        "merchant_id": "merchant_compute_01",
        "item_id": "compute_10k_credits",
        "maximum_price": 1800,
        "currency": "INR",
    }
    response = client.post("/api/v1/voice/negotiate", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["agreed_price"] == "1800.00"
    assert data["currency"] == "INR"
    assert data["governor"]["decision"] == "ALLOW"
    assert data["governor"]["risk_level"] == "LOW"
    assert len(data["turns"]) >= 2


def test_get_voice_market_unit():
    mock_db = MagicMock()

    mock_merchant = MerchantModel(
        merchant_id="merchant_test_1",
        display_name="Test Store",
        active=True,
    )
    mock_item = CatalogItemModel(
        item_id="item_test_1",
        merchant_id="merchant_test_1",
        item_name="Smart Watch",
        base_price=Decimal("1500.00"),
        currency="INR",
        available_quantity=5,
        active=True,
    )

    mock_merchant_repo = MagicMock()
    mock_merchant_repo.list_active.return_value = [mock_merchant]

    mock_catalog_repo = MagicMock()
    mock_catalog_repo.list_for_merchant.return_value = [mock_item]

    from unittest.mock import patch

    with patch(
        "backend.api.routes.voice.MerchantRepository",
        return_value=mock_merchant_repo,
    ), patch(
        "backend.api.routes.voice.CatalogRepository",
        return_value=mock_catalog_repo,
    ):
        result = get_voice_market(db=mock_db)

    assert result == {
        "merchants": [
            {
                "merchant_id": "merchant_test_1",
                "display_name": "Test Store",
                "items": [
                    {
                        "item_id": "item_test_1",
                        "item_name": "Smart Watch",
                        "base_price": "1500.00",
                        "currency": "INR",
                        "available_quantity": 5,
                    }
                ],
            }
        ]
    }

from backend.core.config import settings


def test_settings_load():

    assert settings.app_name == "The Governor"

    assert (
        settings.razorpay_key_id.get_secret_value()
    )

    assert (
        settings.razorpay_key_secret.get_secret_value()
    )

    assert (
        settings.llm_api_key.get_secret_value()
    )


def test_governance_configuration():

    assert (
        settings.max_transaction_amount > 0
    )

    assert (
        0 <= settings.max_discount_percent < 100
    )

    assert (
        settings.velocity_cap_1_min > 0
    )

    assert (
        settings.velocity_cap_5_min
        > settings.velocity_cap_1_min
    )

    assert (
        settings.velocity_cap_1_hour
        > settings.velocity_cap_5_min
    )
    
    
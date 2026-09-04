from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application configuration.

    Secrets come from environment variables / .env.
    SecretStr prevents accidental exposure when configuration objects
    are represented or logged.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ============================================================
    # Application
    # ============================================================

    app_name: str = "The Governor"

    app_env: Literal[
        "development",
        "test",
        "production",
    ] = "development"

    debug: bool = False

    api_prefix: str = "/api/v1"

    # ============================================================
    # Razorpay
    # ============================================================

    razorpay_key_id: SecretStr = Field(
        ...,
        validation_alias="RAZORPAY_KEY_ID",
    )

    razorpay_key_secret: SecretStr = Field(
        ...,
        validation_alias="RAZORPAY_KEY_SECRET",
    )

    # ============================================================
    # LLM
    # ============================================================

    llm_api_key: SecretStr = Field(
        ...,
        validation_alias="LLM_API_KEY",
    )

    # ============================================================
    # Database
    # ============================================================

    database_url: str = Field(
        default="sqlite:///./storage/governor.db",
        validation_alias="DATABASE_URL",
    )

    # ============================================================
    # Ledger
    # ============================================================

    ledger_path: str = Field(
        default="./storage/ledger.jsonl",
        validation_alias="LEDGER_PATH",
    )

    # ============================================================
    # Governance
    # ============================================================

    max_transaction_amount: float = Field(
        default=5000.0,
        gt=0,
        validation_alias="MAX_TRANSACTION_AMOUNT",
    )

    max_discount_percent: float = Field(
        default=15.0,
        ge=0,
        lt=100,
        validation_alias="MAX_DISCOUNT_PERCENT",
    )

    velocity_cap_1_min: float = Field(
        default=15000.0,
        gt=0,
        validation_alias="VELOCITY_CAP_1_MIN",
    )

    velocity_cap_5_min: float = Field(
        default=50000.0,
        gt=0,
        validation_alias="VELOCITY_CAP_5_MIN",
    )

    velocity_cap_1_hour: float = Field(
        default=200000.0,
        gt=0,
        validation_alias="VELOCITY_CAP_1_HOUR",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Load validated application settings once per process.
    """

    return Settings()


settings = get_settings()


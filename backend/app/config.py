import os
import re
import secrets
from functools import lru_cache
from typing import List, Optional, Set

from web3 import Web3
from pydantic import Field, MongoDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Database
    MONGO_URL: str
    DB_NAME: str = "avaira_v2"

    # Security
    AVAIRA_LOG_SECRET: str
    AVAIRA_ADMIN_KEY: str
    PERMIT_SECRET: str

    # AI APIs
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # Payments
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None

    # Auth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""
    X_CLIENT_ID: str = ""
    X_CLIENT_SECRET: str = ""
    X_REDIRECT_URI: str = ""

    ADMIN_EMAILS: str = ""

    # Contracts
    AGENT_REGISTRY_ADDRESS: str = ""
    EXECUTION_WALLET_ADDRESS: str = ""
    FREEZE_SLASH_ADDRESS: str = ""
    TREASURY_ADDRESS: str = ""
    REPUTATION_ENGINE_ADDRESS: str = ""

    # Other
    COOKIE_SECURE: bool = True
    SESSION_MAX_AGE_SECONDS: int = 7 * 24 * 60 * 60
    DEFAULT_POST_LOGIN_REDIRECT: str = "http://localhost:3000/dashboard"
    ALLOWED_REDIRECT_ORIGINS: str = "http://localhost:3000"
    CORS_ORIGINS: str = "http://localhost:3000"
    CHAIN_ID: str = "43113"

    @model_validator(mode="after")
    def validate_secrets(self) -> "Settings":
        defaults = {
            "AVAIRA_LOG_SECRET": "default_secret_32_bytes_long_!!!!!",
            "PERMIT_SECRET": "keep_this_safe_for_legacy_permits",
            "AVAIRA_ADMIN_KEY": ""
        }

        # List of secrets that MUST be high entropy
        entropy_required = ["AVAIRA_LOG_SECRET", "PERMIT_SECRET", "AVAIRA_ADMIN_KEY"]

        errors = []

        for key in entropy_required:
            val = getattr(self, key)
            default_val = defaults.get(key)

            if default_val is not None and val == default_val:
                errors.append(f"{key} cannot be the default value from .env.example")

            # Entropy check: at least 32 bytes
            if len(val) < 32:
                errors.append(f"{key} must be at least 32 characters long for sufficient entropy")

            # Reject known-default prefix
            if re.match(r"^(default_secret|keep_this_safe)", val):
                errors.append(f"{key} uses a forbidden prefix that matches default values")

        if errors:
            raise ValueError("; ".join(errors))

        return self

    @model_validator(mode="after")
    def validate_mongo_url(self) -> "Settings":
        try:
            # Basic validation that it's a valid MongoDsn-like string
            # Pydantic's MongoDsn is more robust
            from pydantic import TypeAdapter
            ta = TypeAdapter(MongoDsn)
            ta.validate_python(self.MONGO_URL)
        except Exception as e:
            raise ValueError(f"Invalid MONGO_URL: {e}")
        return self

    @model_validator(mode="after")
    def validate_addresses(self) -> "Settings":
        address_fields = [
            "AGENT_REGISTRY_ADDRESS",
            "EXECUTION_WALLET_ADDRESS",
            "FREEZE_SLASH_ADDRESS",
            "TREASURY_ADDRESS",
            "REPUTATION_ENGINE_ADDRESS",
        ]
        for field in address_fields:
            val = getattr(self, field)
            if val:
                if not Web3.is_address(val):
                     raise ValueError(f"Invalid EVM address for {field}: {val}")

                if not Web3.is_checksum_address(val):
                     raise ValueError(f"{field} must be a valid 0x-prefixed checksum address: {val}")
        return self


@lru_cache()
def get_settings():
    return Settings()

import pytest
import os
from pydantic import ValidationError
from backend.app.config import Settings

def test_settings_fail_on_default():
    """Verify that settings fail if default/weak secrets are used."""
    os.environ["MONGO_URL"] = "mongodb://localhost:27017"
    os.environ["AVAIRA_LOG_SECRET"] = "default_secret_32_bytes_long_!!!!!" # matches default
    os.environ["PERMIT_SECRET"] = "keep_this_safe_for_legacy_permits"
    os.environ["AVAIRA_ADMIN_KEY"] = "too_short"

    with pytest.raises(ValidationError) as excinfo:
        Settings()

    errors = str(excinfo.value)
    assert "AVAIRA_LOG_SECRET cannot be the default value" in errors
    assert "AVAIRA_ADMIN_KEY must be at least 32 characters long" in errors

def test_settings_fail_on_invalid_address():
    """Verify that settings fail on malformed EVM addresses."""
    os.environ["MONGO_URL"] = "mongodb://localhost:27017"
    os.environ["AVAIRA_LOG_SECRET"] = "secure_key_123456789012345678901234567890"
    os.environ["PERMIT_SECRET"] = "secure_key_123456789012345678901234567890"
    os.environ["AVAIRA_ADMIN_KEY"] = "secure_key_123456789012345678901234567890"
    os.environ["AGENT_REGISTRY_ADDRESS"] = "0xnotanaddress"

    with pytest.raises(ValidationError) as excinfo:
        Settings()

    assert "Invalid EVM address" in str(excinfo.value)

def test_settings_fail_on_non_checksum_address():
    """Verify that settings fail on non-checksummed EVM addresses."""
    os.environ["MONGO_URL"] = "mongodb://localhost:27017"
    os.environ["AVAIRA_LOG_SECRET"] = "secure_key_123456789012345678901234567890"
    os.environ["PERMIT_SECRET"] = "secure_key_123456789012345678901234567890"
    os.environ["AVAIRA_ADMIN_KEY"] = "secure_key_123456789012345678901234567890"
    # lowercase address without checksum
    os.environ["AGENT_REGISTRY_ADDRESS"] = "0x71c7656ec7ab88b098defb751b7401b5f6d8976f"

    with pytest.raises(ValidationError) as excinfo:
        Settings()

    assert "must be a valid 0x-prefixed checksum address" in str(excinfo.value)

def test_settings_pass_on_valid_config():
    """Verify that settings pass with strong configuration."""
    os.environ["MONGO_URL"] = "mongodb://localhost:27017"
    os.environ["AVAIRA_LOG_SECRET"] = "secure_key_123456789012345678901234567890"
    os.environ["PERMIT_SECRET"] = "secure_key_123456789012345678901234567890"
    os.environ["AVAIRA_ADMIN_KEY"] = "secure_key_123456789012345678901234567890"
    # Checksum address
    os.environ["AGENT_REGISTRY_ADDRESS"] = "0x71C7656EC7ab88b098defB751B7401B5f6d8976F"

    settings = Settings()
    assert settings.AVAIRA_LOG_SECRET.startswith("secure")
    assert settings.AGENT_REGISTRY_ADDRESS == "0x71C7656EC7ab88b098defB751B7401B5f6d8976F"

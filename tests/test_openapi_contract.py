import json
import os
import pytest
from fastapi.testclient import TestClient

# Set dummy environment variables to pass validation
os.environ["MONGO_URL"] = "mongodb://localhost:27017"
os.environ["DB_NAME"] = "avaira_v2"
os.environ["AVAIRA_LOG_SECRET"] = "secure_key_123456789012345678901234567890"
os.environ["PERMIT_SECRET"] = "secure_key_123456789012345678901234567890"
os.environ["AVAIRA_ADMIN_KEY"] = "secure_key_123456789012345678901234567890"

def test_openapi_contract_legacy():
    # Test against the current server.py
    from backend.server import app

    with open("openapi_snapshot.json", "r") as f:
        snapshot = json.load(f)

    current_schema = app.openapi()
    snapshot.get("info", {}).pop("version", None)
    current_schema.get("info", {}).pop("version", None)

    assert current_schema == snapshot, "Legacy server.py OpenAPI schema has changed!"

def test_openapi_contract_new():
    # Test against the new app/main.py
    from backend.app.main import app

    with open("openapi_snapshot.json", "r") as f:
        snapshot = json.load(f)

    current_schema = app.openapi()
    snapshot.get("info", {}).pop("version", None)
    current_schema.get("info", {}).pop("version", None)

    # We might expect some differences in tags or operationIds if not careful,
    # but the paths and schemas must match.
    assert current_schema == snapshot, "New modular OpenAPI schema does not match snapshot!"

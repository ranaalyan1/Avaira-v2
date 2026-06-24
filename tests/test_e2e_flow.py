import pytest
import asyncio
import sys
import json
from unittest.mock import AsyncMock, MagicMock, patch

# Helper to create mock collections with awaitable methods
def get_mock_collection():
    coll = MagicMock()
    coll.create_index = AsyncMock()
    coll.insert_one = AsyncMock(return_value=MagicMock(inserted_id="mock_id"))
    coll.find_one = AsyncMock(return_value=None)
    coll.update_one = AsyncMock(return_value=MagicMock())
    coll.update_many = AsyncMock()
    coll.delete_many = AsyncMock()
    coll.count_documents = AsyncMock(return_value=0)

    # Mock find().sort().limit().to_list()
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    # to_list is what is ultimately awaited
    mock_cursor.to_list = AsyncMock(return_value=[])
    # Also make the cursor itself awaitable just in case
    mock_cursor.__await__ = lambda _: iter([]).__await__()
    coll.find.return_value = mock_cursor

    # aggregate returns an object with to_list in motor
    mock_agg_cursor = MagicMock()
    mock_agg_cursor.to_list = AsyncMock(return_value=[])
    coll.aggregate.return_value = mock_agg_cursor
    return coll

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.agents = get_mock_collection()
    db.intent_logs = get_mock_collection()
    db.executions = get_mock_collection()
    db.freeze_events = get_mock_collection()
    db.slash_events = get_mock_collection()
    db.reputation_history = get_mock_collection()
    db.treasury_transactions = get_mock_collection()
    db.missions = get_mock_collection()
    db.underwriters = get_mock_collection()
    db.user_sessions = get_mock_collection()
    db.users = get_mock_collection()
    db.permit_nonces = get_mock_collection()
    db.admin_audit_log = get_mock_collection()
    db.revenue_events = get_mock_collection()

    db.__getitem__.side_effect = lambda x: get_mock_collection()
    return db

@pytest.fixture
def client(mock_db):
    # Mock motor BEFORE any other imports to avoid connection attempts during app startup
    with patch('motor.motor_asyncio.AsyncIOMotorClient', return_value=MagicMock(__getitem__=lambda s, k: mock_db)):
        from backend.app.main import app
        from backend.app.dependencies import get_db, require_authenticated_user

        # Dependency overrides
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[require_authenticated_user] = lambda: {"user_id": "user_1", "email": "admin@avaira.xyz"}

        with patch('backend.app.main.ensure_indexes', AsyncMock()):
            from fastapi.testclient import TestClient
            with TestClient(app) as c:
                yield c

        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_e2e_pivot_flow(client, mock_db):
    agents_store = []

    async def mock_insert_one(doc):
        agents_store.append(doc)
        return MagicMock(inserted_id="mock_id")

    async def mock_find_one(filter, *args, **kwargs):
        for a in agents_store:
            # Simple match logic
            if all(a.get(k) == v for k, v in filter.items() if k != "_id"):
                return a
        return None

    mock_db.agents.insert_one.side_effect = mock_insert_one
    mock_db.agents.find_one.side_effect = mock_find_one

    # 1. Register
    reg_resp = client.post("/api/agents/register", json={
        "name": "E2EBot",
        "goal": "Test goal",
        "risk_envelope": {"max_spend_usd": 100, "allowed_actions": ["search"]}
    })
    assert reg_resp.status_code == 200
    reg_data = reg_resp.json()
    agent_id = reg_data["agent_id"]
    api_key = reg_data["api_key"]

    # 2. Run approved task
    from backend.core.validator import ValidationResult

    with patch('anthropic.AsyncAnthropic') as MockAsyncAnthropic, \
         patch('backend.agents.avaira_agent.AvairaValidator.fast_shield_pass') as mock_fast_pass:

        mock_anthropic_instance = MockAsyncAnthropic.return_value
        mock_anthropic_instance.messages.create = AsyncMock()

        # Responses:
        # think() -> Intent JSON
        mock_anthropic_instance.messages.create.side_effect = [
            MagicMock(content=[MagicMock(text=json.dumps({
                "action": "search", "target": "google", "parameters": {}, "estimated_value": 0.0,
                "reasoning": "Thinking...", "self_assessment": {"within_envelope": True, "confidence": 1.0}
            }))]),
            # deep_neural_audit (Async task)
            MagicMock(content=[MagicMock(text=json.dumps({"approved": True, "reasoning": "No issues"}))])
        ]

        # validator Pass 1 -> Approved
        mock_fast_pass.return_value = ValidationResult(
            audit_id="VAL-E2E-OK", approved=True, risk_score=0.1, violations=[],
            compliance_reasoning="Mocked Pass", adversarial_findings="None",
            stages=[], latency_ms=10
        )

        run_resp = client.post(f"/api/agents/{agent_id}/run",
                             json={"task": "Safe task"},
                             headers={"X-Avaira-API-Key": api_key})
        assert run_resp.status_code == 200
        assert run_resp.json()["execution"]["status"] == "completed"

    # 3. Run deviating task -> Suspension
    with patch('anthropic.AsyncAnthropic') as MockAsyncAnthropic, \
         patch('backend.agents.avaira_agent.AvairaValidator.fast_shield_pass') as mock_fast_pass:

        mock_anthropic_instance = MockAsyncAnthropic.return_value
        mock_anthropic_instance.messages.create = AsyncMock()

        # think() -> Malicious Intent
        mock_anthropic_instance.messages.create.side_effect = [
            MagicMock(content=[MagicMock(text=json.dumps({
                "action": "destroy", "target": "world", "parameters": {}, "estimated_value": 1000.0,
                "reasoning": "Evildoer", "self_assessment": {"within_envelope": False, "confidence": 1.0}
            }))]),
            # deep_neural_audit
            MagicMock(content=[MagicMock(text=json.dumps({"approved": False, "reasoning": "Confirmed Violation"}))])
        ]

        # validator Pass 1 -> Blocked
        mock_fast_pass.return_value = ValidationResult(
            audit_id="VAL-E2E-BAD", approved=False, risk_score=1.0, violations=["blocked_action"],
            compliance_reasoning="Mocked Violation", adversarial_findings="Critical",
            stages=[], latency_ms=10
        )

        run_resp2 = client.post(f"/api/agents/{agent_id}/run",
                          json={"task": "Bad task"},
                          headers={"X-Avaira-API-Key": api_key})
        assert run_resp2.status_code == 200
        assert run_resp2.json()["execution"]["status"] == "blocked"

    # Update the status to frozen to simulate SlashEngine effect
    if agents_store:
        agents_store[0]["status"] = "frozen"

    # 4. Verify subsequent run is blocked by 403 (Frozen)
    run_resp3 = client.post(f"/api/agents/{agent_id}/run",
                      json={"task": "Any task"},
                      headers={"X-Avaira-API-Key": api_key})
    assert run_resp3.status_code == 403
    assert "frozen" in run_resp3.json()["detail"].lower()

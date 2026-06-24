import pytest
import asyncio
import json
import uuid
import secrets
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

# Mock motor/pymongo BEFORE any other imports to avoid connection attempts during app startup
mock_client = MagicMock()
mock_db = MagicMock()
mock_motor = MagicMock()
mock_motor.motor_asyncio.AsyncIOMotorClient.return_value = mock_client
mock_client.__getitem__.return_value = mock_db

import sys
sys.modules['motor'] = mock_motor
sys.modules['motor.motor_asyncio'] = mock_motor.motor_asyncio

# Mock other modules that might cause side effects
sys.modules['anthropic'] = MagicMock()

@pytest.mark.asyncio
async def test_e2e_pivot_flow_mocked():
    # Setup mock behavior for the database
    mock_agents = []

    async def mock_insert_one(doc):
        mock_agents.append(doc)
        return MagicMock()

    async def mock_find_one(filter, *args, **kwargs):
        for a in mock_agents:
            match = True
            for k, v in filter.items():
                if k != "_id" and a.get(k) != v:
                    match = False
                    break
            if match:
                return a
        return None

    def setup_mock_coll(coll):
        coll.insert_one = AsyncMock(side_effect=mock_insert_one)
        coll.find_one = AsyncMock(side_effect=mock_find_one)
        coll.update_one = AsyncMock(return_value=MagicMock())
        coll.delete_many = AsyncMock()
        coll.count_documents = AsyncMock(return_value=0)
        coll.create_index = AsyncMock()

        # Mock find().sort().to_list()
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.to_list = AsyncMock(return_value=[])
        coll.find.return_value = mock_cursor

        return coll

    setup_mock_coll(mock_db.agents)
    setup_mock_coll(mock_db.intent_logs)
    setup_mock_coll(mock_db.executions)
    setup_mock_coll(mock_db.slash_events)
    setup_mock_coll(mock_db.freeze_events)
    setup_mock_coll(mock_db.reputation_history)
    setup_mock_coll(mock_db.treasury_transactions)
    setup_mock_coll(mock_db.missions)
    setup_mock_coll(mock_db.underwriters)
    setup_mock_coll(mock_db.user_sessions)
    setup_mock_coll(mock_db.users)
    setup_mock_coll(mock_db.permit_nonces)
    setup_mock_coll(mock_db.admin_audit_log)
    setup_mock_coll(mock_db.revenue_events)

    from backend.app.main import app
    from backend.app.dependencies import get_db, get_current_user, get_intent_logger, get_avaira_validator, get_slash_engine, get_reputation_engine, get_ape_engine, get_agent_vault

    mock_ape = MagicMock()
    mock_ape.sync_threat_intelligence = AsyncMock(return_value=[])

    # Use dependency overrides
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = AsyncMock(return_value={"user_id": "u1", "email": "a@b.com"})
    app.dependency_overrides[get_intent_logger] = lambda: MagicMock()
    app.dependency_overrides[get_avaira_validator] = lambda: AsyncMock()
    app.dependency_overrides[get_slash_engine] = lambda: AsyncMock()
    app.dependency_overrides[get_reputation_engine] = lambda: AsyncMock()
    app.dependency_overrides[get_ape_engine] = lambda: mock_ape
    app.dependency_overrides[get_agent_vault] = lambda: AsyncMock()

    from fastapi.testclient import TestClient

    # Patch ensure_indexes to avoid any real DB calls during lifespan
    with patch('backend.app.main.ensure_indexes', AsyncMock()):
        with TestClient(app) as client:
            # 1. Register
            body_dict = {
                "name": "Bot",
                "goal": "Test",
                "risk_envelope": {"max_spend_usd": 100}
            }
            response = client.post("/api/agents/register", json=body_dict)
            assert response.status_code == 200
            reg_res = response.json()
            agent_id = reg_res["agent_id"]
            api_key = reg_res["api_key"]

            # 2. Run approved
            # Mock RealAvairaAgent.run
            with patch('backend.app.api.agents.RealAvairaAgent') as MockAgent:
                instance = MockAgent.return_value
                instance.run = AsyncMock(return_value={"execution": {"status": "completed"}})

                response = client.post(f"/api/agents/{agent_id}/run",
                                     json={"task": "Safe"},
                                     headers={"X-Avaira-API-Key": api_key})
                assert response.status_code == 200
                assert response.json()["execution"]["status"] == "completed"

            # 3. Simulate deviation/freeze in mock
            if mock_agents:
                mock_agents[0]["status"] = "frozen"

                # 4. Verify blocked
                response = client.post(f"/api/agents/{agent_id}/run",
                                     json={"task": "Bad"},
                                     headers={"X-Avaira-API-Key": api_key})
                assert response.status_code == 403
                assert "frozen" in response.json()["detail"].lower()

    app.dependency_overrides.clear()

if __name__ == "__main__":
    asyncio.run(test_e2e_pivot_flow_mocked())

import pytest
import asyncio
import json
import uuid
import secrets
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

# Mock all dependencies to avoid MongoDB requirement
@pytest.mark.asyncio
async def test_e2e_pivot_flow_mocked():
    # Mocking the entire DB and engines
    mock_db = MagicMock()
    mock_agents = []

    async def mock_insert_one(doc):
        mock_agents.append(doc)

    async def mock_find_one(filter, projection=None):
        for a in mock_agents:
            if all(a.get(k) == v for k, v in filter.items()):
                return a
        return None

    mock_db.agents.insert_one = mock_insert_one
    mock_db.agents.find_one = mock_find_one
    mock_db.intent_logs.insert_one = AsyncMock()
    mock_db.executions.insert_one = AsyncMock()
    mock_db.slash_events.insert_one = AsyncMock()
    mock_db.slash_events.count_documents = AsyncMock(return_value=0)
    mock_db.executions.count_documents = AsyncMock(return_value=0)

    mock_ape = MagicMock()
    mock_ape.sync_threat_intelligence = AsyncMock(return_value=[])

    with patch('backend.server.db', mock_db),          patch('backend.server.intent_logger', MagicMock()),          patch('backend.server.avaira_validator', AsyncMock()),          patch('backend.server.slash_engine', AsyncMock()),          patch('backend.server.reputation_engine', AsyncMock()),          patch('backend.server.ape_engine', mock_ape),          patch('backend.server.agent_vault', AsyncMock()),          patch('backend.server.require_authenticated_user', return_value={"user_id": "u1", "email": "a@b.com"}),          patch('anthropic.Anthropic'):

        from backend.server import register_agent, agent_run, AgentCreate, AgentRunRequest, RiskEnvelope

        # 1. Register
        body = AgentCreate(name="Bot", goal="Test", risk_envelope=RiskEnvelope(max_spend_usd=100))
        reg_res = await register_agent(body, MagicMock())
        agent_id = reg_res["agent_id"]
        api_key = reg_res["api_key"]

        # 2. Run approved
        from backend.server import _get_agent_from_key
        # Update mock for _get_agent_from_key to find the registered agent
        mock_db.agents.find_one.return_value = mock_agents[0]

        with patch('backend.server.RealAvairaAgent') as MockAgent:
            instance = MockAgent.return_value
            instance.run = AsyncMock(return_value={"execution": {"status": "completed"}})

            run_res = await agent_run(agent_id, AgentRunRequest(task="Safe"), mock_agents[0])
            assert run_res["execution"]["status"] == "completed"

        # 3. Simulate deviation/freeze in mock
        mock_agents[0]["status"] = "frozen"

        # 4. Verify blocked
        from fastapi import HTTPException
        # _get_agent_from_key is where status is checked
        # We manually call it with a mock request
        mock_request = MagicMock()
        mock_request.headers = {"X-Avaira-API-Key": api_key}

        with pytest.raises(HTTPException) as excinfo:
            # Re-import to ensure we get the updated function if needed,
            # but here we just call the one from server
            from backend.server import _get_agent_from_key
            await _get_agent_from_key(mock_request)

        assert excinfo.value.status_code == 403
        assert "frozen" in excinfo.value.detail.lower()

if __name__ == "__main__":
    asyncio.run(test_e2e_pivot_flow_mocked())

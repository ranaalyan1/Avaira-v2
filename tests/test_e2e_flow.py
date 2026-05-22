import pytest
import asyncio
from fastapi.testclient import TestClient
from backend.server import app, db
from unittest.mock import AsyncMock, MagicMock, patch
import json

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

@pytest.mark.asyncio
async def test_e2e_pivot_flow():
    # 1. Register via API (Simulate authenticated user)
    # We'll mock the dependency require_authenticated_user
    from backend.server import require_authenticated_user
    app.dependency_overrides[require_authenticated_user] = lambda: {"user_id": "user_1", "email": "admin@avaira.xyz"}

    c = TestClient(app)

    # Register
    reg_resp = c.post("/api/agents/register", json={
        "name": "E2EBot",
        "goal": "Test goal",
        "risk_envelope": {"max_spend_usd": 100, "allowed_actions": ["search"]}
    })
    assert reg_resp.status_code == 200
    reg_data = reg_resp.json()
    agent_id = reg_data["agent_id"]
    api_key = reg_data["api_key"]

    # 2. Run approved task
    with patch('anthropic.Anthropic') as MockAnthropic:
        mock_client = MockAnthropic.return_value
        # Compliance Pass
        mock_client.messages.create.side_effect = [
            MagicMock(content=[MagicMock(text=json.dumps({"approved": True, "risk_score": 0.1, "violations": [], "reasoning": "OK"}))]),
            MagicMock(content=[MagicMock(text=json.dumps({"findings": [], "severity": "none", "override_approval": False, "reasoning": "No issues"}))])
        ]

        # Mock think
        with patch('backend.agents.avaira_agent.AvairaAgent.think', new_callable=AsyncMock) as mock_think:
            mock_think.return_value = MagicMock(
                action="search", target="google", parameters={}, estimated_value=0.0, reasoning="Thinking...",
                model_dump=lambda: {"action": "search", "target": "google", "parameters": {}, "estimated_value": 0.0, "reasoning": "Thinking...", "self_assessment": {}}
            )

            run_resp = c.post(f"/api/agents/{agent_id}/run",
                             json={"task": "Safe task"},
                             headers={"X-Avaira-API-Key": api_key})
            assert run_resp.status_code == 200
            assert run_resp.json()["execution"]["status"] == "completed"

    # 3. Run deviating task -> Suspension
    with patch('anthropic.Anthropic') as MockAnthropic:
        mock_client = MockAnthropic.return_value
        mock_client.messages.create.side_effect = [
            # Pass 1 Fail
            MagicMock(content=[MagicMock(text=json.dumps({"approved": False, "risk_score": 1.0, "violations": ["blocked_action"], "reasoning": "Violation"}))]),
            # Pass 2 Confirm
            MagicMock(content=[MagicMock(text=json.dumps({"findings": ["critical violation"], "severity": "critical", "override_approval": False, "reasoning": "Confirmed"}))])
        ]

        with patch('backend.agents.avaira_agent.AvairaAgent.think', new_callable=AsyncMock) as mock_think:
             mock_think.return_value = MagicMock(
                action="destroy", target="world", parameters={}, estimated_value=1000.0, reasoning="Evildoer",
                model_dump=lambda: {"action": "destroy", "target": "world", "parameters": {}, "estimated_value": 1000.0, "reasoning": "Evildoer", "self_assessment": {}}
            )

             run_resp2 = c.post(f"/api/agents/{agent_id}/run",
                              json={"task": "Bad task"},
                              headers={"X-Avaira-API-Key": api_key})
             assert run_resp2.status_code == 200
             assert run_resp2.json()["execution"]["status"] == "blocked"

    # 4. Verify subsequent run is blocked by 403 (Suspended)
    run_resp3 = c.post(f"/api/agents/{agent_id}/run",
                      json={"task": "Any task"},
                      headers={"X-Avaira-API-Key": api_key})
    assert run_resp3.status_code == 403
    assert "suspended" in run_resp3.json()["detail"].lower()

    app.dependency_overrides.clear()

if __name__ == "__main__":
    asyncio.run(test_e2e_pivot_flow())

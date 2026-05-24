import pytest
import asyncio
from avaira_shield.client import AvairaClient
from avaira_shield.config import AvairaConfig, RiskEnvelope
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.mark.asyncio
async def test_sdk_basic_flow():
    envelope = RiskEnvelope(max_spend_usd=50.0, allowed_actions=["search"])
    config = AvairaConfig(api_key="test_key", risk_envelope=envelope, api_url="http://mock-api")
    client = AvairaClient(config)

    # Mock HTTP client
    client.http_client = AsyncMock()

    # 1. Mock Register
    client.http_client.post.side_effect = [
        # Registration response
        MagicMock(json=lambda: {"agent_id": "agent_123", "api_key": "new_key"}, raise_for_status=lambda: None),
        # Validation response
        MagicMock(json=lambda: {"approved": True, "violations": [], "compliance_reasoning": "OK"}, raise_for_status=lambda: None),
        # Log response
        MagicMock(json=lambda: {"status": "logged"}, raise_for_status=lambda: None),
        # Validation for second run
        MagicMock(json=lambda: {"approved": False, "violations": ["blocked"], "compliance_reasoning": "No"}, raise_for_status=lambda: None)
    ]

    # Mock Score
    client.http_client.get.return_value = MagicMock(json=lambda: {"score": 95, "grade": "A+"}, raise_for_status=lambda: None)

    # Register
    agent_id = await client.register(name="Bot", goal="Test")
    assert agent_id == "agent_123"
    assert client.config.api_key == "new_key"

    # Run approved
    res = await client.run(task="Task 1", execute_fn=lambda: "Done")
    assert res["status"] == "completed"

    # Run blocked
    res2 = await client.run(task="Bad Task", execute_fn=lambda: "Error")
    assert res2["status"] == "blocked"

    # Get score
    score = await client.get_score()
    assert score["grade"] == "A+"

if __name__ == "__main__":
    asyncio.run(test_sdk_basic_flow())

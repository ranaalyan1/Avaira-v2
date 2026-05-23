import pytest
import asyncio
import os
import json
from unittest.mock import AsyncMock, MagicMock, patch
from backend.core.intent_logger import IntentLogger
from backend.core.validator import AvairaValidator, ValidationResult
from backend.core.slash_engine import SlashEngine
from backend.core.reputation import ReputationEngine
from backend.agents.avaira_agent import AvairaAgent

# Mock DB
class MockCollection:
    def __init__(self):
        self.data = []
    async def find_one(self, filter, sort=None):
        if not self.data: return None
        d = [x for x in self.data if all(x.get(k) == v for k, v in filter.items())]
        if not d: return None
        if sort:
            # simple sort by timestamp desc
            d = sorted(d, key=lambda x: x.get('timestamp', ''), reverse=True)
        return d[0]
    async def insert_one(self, doc):
        self.data.append(doc)
    async def update_one(self, filter, update):
        # Very simple mock update
        doc = await self.find_one(filter)
        if doc and '$set' in update:
            doc.update(update['$set'])
    def find(self, filter):
        class Cursor:
            def __init__(self, data, filter):
                self.data = [x for x in data if all(x.get(k) == v for k, v in filter.items())]
            async def to_list(self, length):
                return self.data
            def sort(self, key, direction):
                self.data = sorted(self.data, key=lambda x: x.get(key, ''))
                if direction == -1: self.data.reverse()
                return self
            def limit(self, n):
                self.data = self.data[:n]
                return self
            def __aiter__(self):
                self.iter = iter(self.data)
                return self
            async def __anext__(self):
                try: return next(self.iter)
                except StopIteration: raise StopAsyncIteration
        return Cursor(self.data, filter)
    async def count_documents(self, filter):
        return len([x for x in self.data if all(x.get(k) == v for k, v in filter.items())])
    def aggregate(self, pipeline):
        class Cursor:
            async def to_list(self, length): return []
        return Cursor()

class MockDB:
    def __init__(self):
        self.agents = MockCollection()
        self.intent_logs = MockCollection()
        self.executions = MockCollection()
        self.slash_events = MockCollection()
        self.reputation_history = MockCollection()

@pytest.mark.asyncio
async def test_v2_full_integration():
    db = MockDB()
    agent_id = "test-agent-v2"
    envelope = {"max_spend_usd": 100, "allowed_actions": ["search"]}

    # 1. Setup Agent in DB
    await db.agents.insert_one({
        "id": agent_id,
        "name": "Test Agent",
        "risk_envelope": envelope,
        "status": "active",
        "registered_at": "2024-01-01T00:00:00Z"
    })

    # 2. Mock Claude for Validator
    with patch('anthropic.AsyncAnthropic') as MockAnthropic:
        mock_client = MockAnthropic.return_value
        mock_client.messages.create = AsyncMock()
        mock_client.messages.create.side_effect = [
            # Compliance Pass
            MagicMock(content=[MagicMock(text=json.dumps({"approved": True, "risk_score": 0.1, "violations": [], "reasoning": "Looks good"}))]),
            # Adversarial Pass
            MagicMock(content=[MagicMock(text=json.dumps({"findings": [], "severity": "none", "override_approval": False, "reasoning": "No issues"}))])
        ]

        agent = AvairaAgent(agent_id, envelope, db_client=db)

        # 3. Mock think to avoid another LLM call
        agent.think = AsyncMock(return_value=MagicMock(
            action="search",
            target="google",
            parameters={},
            estimated_value=0.0,
            reasoning="Need info",
            model_dump=lambda: {"action": "search", "target": "google", "parameters": {}, "estimated_value": 0.0, "reasoning": "Need info", "self_assessment": {}},
            self_assessment={}
        ))

        # 4. Run Agent
        result = await agent.run("Search for Avaira")

        assert result.execution["status"] == "completed"
        assert len(db.intent_logs.data) == 1
        assert len(db.executions.data) == 1

        # 5. Verify Hash Chain
        logger = IntentLogger(db_client=db)
        verify = await logger.verify_chain(agent_id)
        assert verify.valid is True
        assert verify.entries == 1

@pytest.mark.asyncio
async def test_v2_violation_slashes():
    db = MockDB()
    agent_id = "deviant-agent"
    envelope = {"max_spend_usd": 10, "allowed_actions": ["search"]}

    await db.agents.insert_one({
        "id": agent_id,
        "name": "Deviant",
        "risk_envelope": envelope,
        "status": "active",
        "registered_at": "2024-01-01T00:00:00Z"
    })

    with patch('anthropic.AsyncAnthropic') as MockAnthropic:
        mock_client = MockAnthropic.return_value
        mock_client.messages.create = AsyncMock()
        mock_client.messages.create.side_effect = [
            # Compliance Pass - REJECT
            MagicMock(content=[MagicMock(text=json.dumps({"approved": False, "risk_score": 0.9, "violations": ["budget_exceeded"], "reasoning": "Too expensive"}))]),
            # Adversarial Pass
            MagicMock(content=[MagicMock(text=json.dumps({"findings": ["high spend"], "severity": "high", "override_approval": False, "reasoning": "Confirmed"}))])
        ]

        agent = AvairaAgent(agent_id, envelope, db_client=db)
        agent.think = AsyncMock(return_value=MagicMock(
            action="search", target="google", parameters={}, estimated_value=500.0, reasoning="Buying everything",
            model_dump=lambda: {"action": "search", "target": "google", "parameters": {}, "estimated_value": 500.0, "reasoning": "Buying everything", "self_assessment": {}}
        ))

        result = await agent.run("Buy expensive things")

        assert result.execution["status"] == "blocked"
        # In v2, blocked intents don't result in immediate slashes/freezes
        # (System worked as intended by blocking the action)
        updated_agent = await db.agents.find_one({"id": agent_id})
        assert updated_agent["status"] == "active"
        assert len(db.slash_events.data) == 0

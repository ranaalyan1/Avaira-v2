import pytest
import asyncio
import os
import json
from unittest.mock import AsyncMock, MagicMock, patch
from backend.core.sentinel import AvairaSentinel
from backend.core.zk_vault import ZKAuditVault
from backend.core.ape_engine import AutonomousPolicyEvolution
from backend.core.tee_identity import TEEIdentityManager
from backend.core.marketplace import TrustMarketplace

# Reusing MockDB from test_v2_core (simplified)
class MockCollection:
    def __init__(self):
        self.data = []
    async def find_one(self, filter, projection=None, sort=None):
        if not self.data: return None
        return self.data[0] # Simplest mock
    def find(self, filter):
        class Cursor:
            def __init__(self, data):
                self.data = data
            def sort(self, key, direction):
                return self
            def limit(self, n):
                return self
            async def to_list(self, length):
                return self.data
        return Cursor(self.data)
    async def insert_one(self, doc):
        self.data.append(doc)
    async def update_one(self, filter, update):
        return MagicMock(matched_count=1)

class MockDB:
    def __init__(self):
        self.agents = MockCollection()
        self.executions = MockCollection()
        self.insurance_policies = MockCollection()
        self.slash_bridge_logs = MockCollection()

@pytest.mark.asyncio
async def test_sentinel_drift_analysis():
    db = MockDB()
    # Mock some history
    await db.executions.insert_one({
        "agent_id": "test-agent",
        "status": "completed",
        "intent": {"action": "search", "query": "AI news"},
        "timestamp": "2024-01-01T00:00:00Z"
    })

    # We need to mock the slm inside sentinel
    sentinel = AvairaSentinel(db_client=db)
    sentinel.slm = AsyncMock()
    sentinel.slm.classify_intent.return_value = MagicMock(reasoning="stable", intent="none")

    analysis = await sentinel.analyze_drift("test-agent", {"action": "search", "query": "more AI news"})
    assert analysis.drift_score == 0.1
    assert analysis.trend == "stable"

@pytest.mark.asyncio
async def test_zk_vault_proof_generation():
    vault = ZKAuditVault()
    intent = {"action": "search", "value": 0}
    envelope = {"max_spend_usd": 100, "allowed_actions": ["search"]}

    proof = await vault.generate_compliance_proof(intent, envelope, "audit-123")
    assert proof.verifiable is True
    assert vault.verify_compliance_proof(proof) is True

@pytest.mark.asyncio
async def test_ape_engine_sync():
    db = MockDB()
    await db.agents.insert_one({
        "id": "agent-1",
        "risk_envelope": {"custom_rules": []}
    })

    ape = AutonomousPolicyEvolution(db_client=db)
    updates = await ape.sync_threat_intelligence("agent-1")
    assert len(updates) > 0
    assert updates[0].threat_level == "high"

@pytest.mark.asyncio
async def test_tee_identity_minting():
    manager = TEEIdentityManager()
    did_doc = manager.generate_agent_did("agent-123", "key-hash-xyz")
    assert did_doc.did == "did:avaira:agent-123"
    assert manager.verify_attestation(did_doc) is True

@pytest.mark.asyncio
async def test_marketplace_insurance_and_slashing():
    db = MockDB()
    await db.agents.insert_one({
        "id": "agent-1",
        "avaira_score": 80,
        "collateral_remaining": 100
    })

    marketplace = TrustMarketplace(db_client=db)
    policy = await marketplace.issue_policy("agent-1", "uw-1", 1000)
    assert policy.premium_paid_usd > 0

    bridge_event = await marketplace.trigger_slashing_bridge("agent-1", "violation", "high")
    assert bridge_event["slash_amount"] == 80 # 80% of 100

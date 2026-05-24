import pytest
import os
import hashlib
import json
from datetime import datetime, timezone
from backend.core.intent_logger import IntentLogger

# Mocking the collection for async testing without real Mongo
class MockCollection:
    def __init__(self):
        self.data = []
    async def find_one(self, filter, sort=None):
        if not self.data: return None
        # Support both old and new timestamp field
        key_fn = lambda x: x.get('issuanceDate') or x.get('timestamp')
        sorted_data = sorted(self.data, key=key_fn, reverse=True)
        return sorted_data[0]
    async def insert_one(self, doc):
        self.data.append(doc)
    def find(self, filter):
        class Cursor:
            def __init__(self, data):
                key_fn = lambda x: x.get('issuanceDate') or x.get('timestamp')
                self.data = sorted(data, key=key_fn)
            async def to_list(self, length):
                return self.data
            def sort(self, key, direction):
                return self
            def __aiter__(self):
                self.iter = iter(self.data)
                return self
            async def __anext__(self):
                try: return next(self.iter)
                except StopIteration: raise StopAsyncIteration
        return Cursor(self.data)

@pytest.mark.asyncio
async def test_intent_logger_integrity():
    mock_db = type('obj', (object,), {'intent_logs': MockCollection()})
    logger = IntentLogger(db_client=mock_db)

    agent_id = "agent_integrity_test"
    envelope = {"limit": 100}

    # 1. Log entries
    await logger.log({"action": "valid"}, agent_id, envelope)
    await logger.log({"action": "valid2"}, agent_id, envelope)

    # 2. Verify valid
    res = await logger.verify_chain(agent_id)
    assert res.valid is True
    assert res.entries == 2

    # 3. Tamper
    # Manually change the payload of the first entry
    logger.collection.data[0]['payload'] = "deadbeef"

    # 4. Verify invalid
    res2 = await logger.verify_chain(agent_id)
    assert res2.valid is False
    assert res2.broken_at == logger.collection.data[0]['id']

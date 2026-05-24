import json
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient
import os

class MemoryEntry(BaseModel):
    id: str
    agent_id: str
    audit_id: str  # Linked to verified Execution Shield Audit ID
    content_hash: str
    experience: str
    verified_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class VerifiedMemory:
    """
    Long-term memory tightly coupled with the Avaira hash chain.
    Only verified past experiences (linked to an Audit ID) can be stored and recalled.
    """
    def __init__(self, db_client=None):
        if db_client is None:
            mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
            db_name = os.environ.get("DB_NAME", "avaira")
            self.client = AsyncIOMotorClient(mongo_url)
            self.db = self.client[db_name]
        else:
            self.db = db_client
        self.collection = self.db.verified_memory

    async def store_experience(self, agent_id: str, audit_id: str, experience: str) -> str:
        # Verify that this audit_id actually exists and was approved
        execution = await self.db.executions.find_one({"id": audit_id, "agent_id": agent_id})
        if not execution or execution.get("status") != "completed":
            raise ValueError("Cannot store memory: Linked execution not found or not verified.")

        content_hash = hashlib.sha256(experience.encode()).hexdigest()
        entry_id = f"MEM-{hashlib.sha256((agent_id + audit_id).encode()).hexdigest()[:8].upper()}"

        entry = MemoryEntry(
            id=entry_id,
            agent_id=agent_id,
            audit_id=audit_id,
            content_hash=content_hash,
            experience=experience
        )

        await self.collection.update_one(
            {"id": entry_id},
            {"$set": entry.model_dump()},
            upsert=True
        )
        return entry_id

    async def recall_verified(self, agent_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"agent_id": agent_id}).sort("verified_at", -1).limit(limit)
        results = []
        async for doc in cursor:
            doc.pop("_id", None)
            results.append(doc)
        return results

import json
import hashlib
import uuid
import os
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from motor.motor_asyncio import AsyncIOMotorClient

class LogEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    agent_id: str
    intent_hash: str
    risk_envelope_hash: str
    prev_hash: Optional[str] = None
    payload: str  # Encrypted intent hex
    nonce: str    # AESGCM nonce hex

class VerifyResult(BaseModel):
    valid: bool
    entries: int
    broken_at: Optional[str] = None

class IntentLogger:
    def __init__(self, db_client=None):
        if db_client is None:
            mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
            db_name = os.environ.get("DB_NAME", "avaira")
            self.client = AsyncIOMotorClient(mongo_url)
            self.db = self.client[db_name]
        else:
            self.db = db_client

        self.collection = self.db.intent_logs
        self.secret = os.environ.get("AVAIRA_LOG_SECRET", "default_secret_32_bytes_long_!!!!!")
        if len(self.secret) < 32:
             # Pad or hash to get 32 bytes
             self.key = hashlib.sha256(self.secret.encode()).digest()
        else:
             self.key = self.secret.encode()[:32]

        self.aesgcm = AESGCM(self.key)

    async def log(self, intent: dict, agent_id: str, risk_envelope: dict) -> LogEntry:
        # Get last entry for hash chain
        last_entry = await self.collection.find_one(
            {"agent_id": agent_id},
            sort=[("timestamp", -1)]
        )
        prev_hash = last_entry["intent_hash"] if last_entry else "0" * 64

        timestamp = datetime.now(timezone.utc).isoformat()
        risk_envelope_hash = hashlib.sha256(json.dumps(risk_envelope, sort_keys=True).encode()).hexdigest()

        intent_json = json.dumps(intent, sort_keys=True)
        content_to_hash = (
            intent_json +
            agent_id +
            timestamp +
            risk_envelope_hash +
            prev_hash
        )
        intent_hash = hashlib.sha256(content_to_hash.encode()).hexdigest()

        # Encrypt payload
        nonce = os.urandom(12)
        encrypted_payload = self.aesgcm.encrypt(nonce, intent_json.encode(), None)

        entry = LogEntry(
            agent_id=agent_id,
            timestamp=timestamp,
            intent_hash=intent_hash,
            risk_envelope_hash=risk_envelope_hash,
            prev_hash=prev_hash,
            payload=encrypted_payload.hex(),
            nonce=nonce.hex()
        )

        await self.collection.insert_one(entry.model_dump())
        return entry

    async def verify_chain(self, agent_id: str) -> VerifyResult:
        entries = await self.collection.find(
            {"agent_id": agent_id}
        ).sort("timestamp", 1).to_list(None)

        if not entries:
            return VerifyResult(valid=True, entries=0)

        expected_prev_hash = "0" * 64
        for entry in entries:
            # 1. Verify chain link
            if entry["prev_hash"] != expected_prev_hash:
                return VerifyResult(valid=False, entries=len(entries), broken_at=entry["id"])

            # 2. Re-verify data integrity
            try:
                # Decrypt to get original intent JSON string
                nonce = bytes.fromhex(entry["nonce"])
                encrypted = bytes.fromhex(entry["payload"])
                decrypted_bytes = self.aesgcm.decrypt(nonce, encrypted, None)
                intent_json = decrypted_bytes.decode()

                # Re-calculate hash
                content_to_hash = (
                    intent_json +
                    entry["agent_id"] +
                    entry["timestamp"] +
                    entry["risk_envelope_hash"] +
                    entry["prev_hash"]
                )
                recalculated_hash = hashlib.sha256(content_to_hash.encode()).hexdigest()

                if recalculated_hash != entry["intent_hash"]:
                    return VerifyResult(valid=False, entries=len(entries), broken_at=entry["id"])
            except Exception:
                return VerifyResult(valid=False, entries=len(entries), broken_at=entry["id"])

            expected_prev_hash = entry["intent_hash"]

        return VerifyResult(valid=True, entries=len(entries))

    async def get_audit_trail(self, agent_id: str, from_dt: datetime, to_dt: datetime) -> List[LogEntry]:
        cursor = self.collection.find({
            "agent_id": agent_id,
            "timestamp": {
                "$gte": from_dt.isoformat(),
                "$lte": to_dt.isoformat()
            }
        }).sort("timestamp", 1)

        results = []
        async for doc in cursor:
            doc.pop("_id", None)
            results.append(LogEntry(**doc))
        return results

from typing import Dict
from datetime import datetime, timezone
import uuid
import re
from app.constants import INITIAL_REPUTATION

EVM_ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")

def is_valid_evm_address(address: str) -> bool:
    return bool(EVM_ADDRESS_RE.match(address))

async def ensure_ai_agent_record(db, body) -> Dict:
    existing = await db.agents.find_one({"wallet_address": body.agent_address}, {"_id": 0})
    timestamp = datetime.now(timezone.utc).isoformat()
    if existing:
        updates = {
            "mission_intent": body.mission_goal,
            "risk_envelope": body.risk_envelope,
            "updated_at": timestamp,
            "status": existing.get("status", "active"),
        }
        await db.agents.update_one({"wallet_address": body.agent_address}, {"$set": updates})
        existing.update(updates)
        return existing

    agent = {
        "id": str(uuid.uuid4()),
        "name": f"AI Agent {body.agent_address[:6]}",
        "wallet_address": body.agent_address,
        "collateral_amount": 0.1,
        "collateral_remaining": 0.1,
        "mission_intent": body.mission_goal,
        "risk_envelope": body.risk_envelope,
        "status": "active",
        "reputation": INITIAL_REPUTATION,
        "avaira_score": 50,
        "grade": "C",
        "runtime_nonce": 0,
        "total_executions": 0,
        "successful_executions": 0,
        "failed_executions": 0,
        "registered_at": timestamp,
        "chain_id": "43113",
        "agent_type": "local-runtime",
    }
    await db.agents.insert_one(agent)
    return agent

def validate_risk_envelope(request_data: Dict, risk_envelope: Dict) -> Dict:
    violations = []
    max_spend = risk_envelope.get("max_spend_usd") or risk_envelope.get("max_tx_value", 10.0)
    if request_data.get("value", 0) > max_spend:
        violations.append(f"Value {request_data['value']} exceeds max {max_spend}")
    if request_data.get("action") not in risk_envelope.get("allowed_actions", []):
        violations.append(f"Action '{request_data['action']}' not in allowed actions")
    return {"valid": len(violations) == 0, "violations": violations}

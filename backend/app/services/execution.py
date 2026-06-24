from typing import Dict, Any, Optional
import uuid
import secrets
from datetime import datetime, timezone
from app.constants import (
    PROTOCOL_FEE_RATE, TRUST_POOL_SHARE, PROTOCOL_REVENUE_SHARE,
    REP_SUCCESS_BONUS, REP_FREEZE_PENALTY
)
from .agent import validate_risk_envelope
from .reputation import update_reputation
from .audit import record_treasury_transaction

async def process_execution_request(db, body: Any):
    agent = await db.agents.find_one({"id": body.agent_id}, {"_id": 0})
    if not agent:
        return {"error": "Agent not found", "status_code": 404}
    if agent["status"] == "frozen":
        return {"error": "Agent is frozen. Execution blocked.", "status_code": 403}
    if agent["status"] != "active":
        return {"error": f"Agent status is '{agent['status']}'. Must be 'active'.", "status_code": 403}

    execution = {
        "id": str(uuid.uuid4()),
        "agent_id": body.agent_id,
        "agent_name": agent["name"],
        "action": body.action,
        "target_address": body.target_address,
        "value": body.value,
        "data": body.data,
        "status": "pending_validation",
        "lifecycle": [{
            "step": "request_submitted",
            "status": "completed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": "Execution request received by AVAIRA backend"
        }],
        "fee_deducted": 0.0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    validation = validate_risk_envelope(
        {"value": body.value, "action": body.action},
        agent["risk_envelope"]
    )

    if not validation["valid"]:
        execution["status"] = "rejected_deviation"
        execution["lifecycle"].append({
            "step": "risk_validation",
            "status": "failed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": f"Deviation detected: {'; '.join(validation['violations'])}"
        })
        await db.executions.insert_one(execution)
        execution.pop("_id", None)

        await db.agents.update_one({"id": body.agent_id}, {"$set": {"status": "frozen"}})
        freeze_event = {
            "id": str(uuid.uuid4()),
            "agent_id": body.agent_id,
            "agent_name": agent["name"],
            "type": "freeze",
            "reason": f"Risk envelope violation: {'; '.join(validation['violations'])}",
            "collateral_slashed": 0.0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await db.freeze_events.insert_one(freeze_event)
        await update_reputation(db, body.agent_id, -REP_FREEZE_PENALTY, "Frozen: risk envelope deviation")
        await db.agents.update_one({"id": body.agent_id}, {"$inc": {"total_executions": 1, "failed_executions": 1}})
        return execution

    execution["lifecycle"].append({
        "step": "risk_validation",
        "status": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": "Request within declared risk envelope"
    })

    execution["status"] = "completed"
    execution["lifecycle"].append({
        "step": "execution",
        "status": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": "Chainless execution completed successfully"
    })

    fee = round(body.value * PROTOCOL_FEE_RATE, 6)
    execution["fee_deducted"] = fee
    execution["lifecycle"].append({
        "step": "fee_deducted",
        "status": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": f"Protocol fee: {fee} USD (0.5%). TrustPool: {round(fee * TRUST_POOL_SHARE, 6)}, Revenue: {round(fee * PROTOCOL_REVENUE_SHARE, 6)}"
    })
    execution["updated_at"] = datetime.now(timezone.utc).isoformat()

    await db.executions.insert_one(execution)
    execution.pop("_id", None)

    await record_treasury_transaction(db, execution["id"], fee)
    await update_reputation(db, body.agent_id, REP_SUCCESS_BONUS, "Successful execution")
    await db.agents.update_one({"id": body.agent_id}, {"$inc": {"total_executions": 1, "successful_executions": 1}})

    return execution

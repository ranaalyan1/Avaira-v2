from fastapi import APIRouter, Depends, Query, HTTPException, Request
from starlette.responses import JSONResponse
from typing import Optional, List, Dict, Any
import uuid
import secrets
from datetime import datetime, timezone

from app.dependencies import (
    get_db, get_avaira_validator, get_current_agent, require_admin_user,
    get_reputation_engine, get_slash_engine, get_trust_marketplace,
    get_intent_logger, get_avaira_sentinel
)
from app.models.execution import ExecutionRequestCreate, IntentValidateRequest
from app.models.agent import SlashRequest, FreezeRequest
from app.services.agent import validate_risk_envelope
from app.services.reputation import update_reputation
from app.services.audit import record_treasury_transaction, record_admin_audit
from app.constants import (
    PROTOCOL_FEE_RATE, TRUST_POOL_SHARE, PROTOCOL_REVENUE_SHARE,
    REP_SUCCESS_BONUS, REP_FREEZE_PENALTY, SLASH_RATE, REP_SLASH_PENALTY
)

router = APIRouter(tags=[])

@router.post("/executions/request")
async def create_execution_request(body: ExecutionRequestCreate, db=Depends(get_db)):
    from app.services.execution import process_execution_request
    result = await process_execution_request(db, body)
    if "error" in result:
        raise HTTPException(status_code=result["status_code"], detail=result["error"])
    return result

@router.get("/executions")
async def list_executions(agent_id: Optional[str] = None, status: Optional[str] = None, limit: int = Query(100, ge=1, le=500), db=Depends(get_db)):
    query = {}
    if agent_id:
        query["agent_id"] = agent_id
    if status:
        query["status"] = status
    executions = await db.executions.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return executions

@router.get("/executions/{execution_id}")
async def get_execution(execution_id: str, db=Depends(get_db)):
    ex = await db.executions.find_one({"id": execution_id}, {"_id": 0})
    if not ex:
        raise HTTPException(404, "Execution not found")
    return ex

@router.get("/executions/{execution_id}/zk-proof")
async def get_execution_zk_proof(execution_id: str, db=Depends(get_db)):
    ex = await db.executions.find_one({"id": execution_id})
    if not ex:
        raise HTTPException(404, "Execution not found")
    proof = ex.get("zk_proof")
    if not proof:
        raise HTTPException(404, "ZK-proof not found for this execution")
    return proof

@router.post("/validate", description="Two-layer intent validation using AvairaValidator (Claude-powered).")
async def validate_intent_endpoint(body: IntentValidateRequest, request: Request, avaira_validator=Depends(get_avaira_validator)):
    # Rate limit logic should be in middleware, but for zero change, we keep it here if needed.
    # Original server.py had enforce_rate_limit.
    result = await avaira_validator.validate(body.intent, body.risk_envelope)
    return result

@router.post("/verify-proof")
async def verify_trust_proof(body: Dict[str, Any]):
    agent_id = body.get("agent_id")
    if not agent_id: raise HTTPException(400, "Missing agent_id")

    merkle_root = body.get("merkle_root")
    timestamp = body.get("timestamp")
    witness_sigs = body.get("witness_signatures", [])

    from app.core.witness_network import WitnessNetwork, WitnessSignature
    wn = WitnessNetwork()

    valid_sigs = 0
    for sig_data in witness_sigs:
        sig = WitnessSignature(**sig_data)
        if wn.verify_witness_signature(merkle_root, timestamp, sig):
            valid_sigs += 1

    trusted = (valid_sigs >= 2)
    return {
        "trusted": trusted,
        "witness_count": valid_sigs,
        "detail": "Quorum of co-signatures verified" if trusted else "Insufficient witness co-signatures"
    }

@router.post("/agents/{agent_id}/log")
async def agent_log_outcome(agent_id: str, body: Dict[str, Any], agent: Dict = Depends(get_current_agent), db=Depends(get_db), intent_logger=Depends(get_intent_logger)):
    if agent["id"] != agent_id:
        raise HTTPException(403, "API Key does not match agent ID")

    intent = body.get("intent")
    status = body.get("status")
    result = body.get("result")

    await intent_logger.log(intent, agent_id, agent["risk_envelope"])
    await db.executions.insert_one({
        "trace_id": str(uuid.uuid4()),
        "agent_id": agent_id,
        "intent": intent,
        "status": status,
        "result": result,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    return {"status": "logged"}

@router.get("/agents/{agent_id}/trust-proof")
async def get_agent_trust_proof(agent_id: str, agent: Dict = Depends(get_current_agent), intent_logger=Depends(get_intent_logger)):
    if agent["id"] != agent_id:
        raise HTTPException(403, "API Key does not match agent ID")

    trail = await intent_logger.collection.find({"agent_id": agent_id}).sort("issuanceDate", -1).limit(10).to_list(None)
    if not trail:
        raise HTTPException(404, "No history found")

    latest = trail[0]
    return {
        "agent_id": agent_id,
        "agent_did": f"did:avaira:{agent_id}",
        "merkle_root": latest["merkle_root"],
        "intent_hash": latest["intent_hash"],
        "timestamp": latest["issuanceDate"],
        "witness_signatures": latest["witness_signatures"],
        "proof": latest["proof"]
    }

@router.get("/agents/{agent_id}/drift")
async def get_agent_drift(agent_id: str, agent: Dict = Depends(get_current_agent), db=Depends(get_db), avaira_sentinel=Depends(get_avaira_sentinel)):
    if agent["id"] != agent_id:
        raise HTTPException(403, "API Key does not match agent ID")

    last_exec = await db.executions.find_one(
        {"agent_id": agent_id},
        sort=[("timestamp", -1)]
    )

    if not last_exec or "drift_analysis" not in last_exec:
        return await avaira_sentinel.analyze_drift(agent_id, {"task": "periodic_check"})

    return last_exec["drift_analysis"]

@router.post("/freeze/{agent_id}")
async def freeze_agent(agent_id: str, body: FreezeRequest, request: Request, admin_user: Dict[str, Any] = Depends(require_admin_user), db=Depends(get_db)):
    agent = await db.agents.find_one({"id": agent_id}, {"_id": 0})
    if not agent:
        raise HTTPException(404, "Agent not found")
    if agent["status"] == "frozen":
        raise HTTPException(400, "Agent is already frozen")

    await db.agents.update_one({"id": agent_id}, {"$set": {"status": "frozen"}})
    event = {
        "id": str(uuid.uuid4()),
        "agent_id": agent_id,
        "agent_name": agent["name"],
        "type": "freeze",
        "reason": body.reason,
        "collateral_slashed": 0.0,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.freeze_events.insert_one(event)

    await update_reputation(db, agent_id, -REP_FREEZE_PENALTY, f"Frozen: {body.reason}")
    await record_admin_audit(db, "agent_freeze", admin_user, request, {"agent_id": agent_id, "reason": body.reason})
    event.pop("_id", None)
    return event

@router.post("/slash/{agent_id}")
async def slash_agent(agent_id: str, body: SlashRequest, request: Request, admin_user: Dict[str, Any] = Depends(require_admin_user), db=Depends(get_db), trust_marketplace=Depends(get_trust_marketplace)):
    agent = await db.agents.find_one({"id": agent_id}, {"_id": 0})
    if not agent:
        raise HTTPException(404, "Agent not found")

    slash_amount = body.amount if body.amount else round(agent["collateral_remaining"] * SLASH_RATE, 6)
    slash_amount = min(slash_amount, agent["collateral_remaining"])

    new_collateral = round(agent["collateral_remaining"] - slash_amount, 6)
    await db.agents.update_one({"id": agent_id}, {
        "$set": {"collateral_remaining": new_collateral, "status": "frozen"}
    })

    event = {
        "id": str(uuid.uuid4()),
        "agent_id": agent_id,
        "agent_name": agent["name"],
        "type": "slash",
        "reason": body.reason,
        "collateral_slashed": slash_amount,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.freeze_events.insert_one(event)

    await update_reputation(db, agent_id, -REP_SLASH_PENALTY, f"Slashed: {body.reason}")
    await trust_marketplace.trigger_slashing_bridge(agent_id, body.reason, "high")
    await record_admin_audit(db, "agent_slash", admin_user, request, {"agent_id": agent_id, "reason": body.reason, "amount": slash_amount})
    event.pop("_id", None)
    return {**event, "collateral_remaining": new_collateral}

@router.get("/freeze/events")
async def list_freeze_events(agent_id: Optional[str] = None, limit: int = Query(100, ge=1, le=500), db=Depends(get_db)):
    query = {}
    if agent_id:
        query["agent_id"] = agent_id
    events = await db.freeze_events.find(query, {"_id": 0}).sort("timestamp", -1).to_list(limit)
    return events

@router.post("/agents/{agent_id}/slash")
async def slash_agent_internal(agent_id: str, request: Request, slash_engine=Depends(get_slash_engine), trust_marketplace=Depends(get_trust_marketplace)):
    # Original server.py used AVAIRA_ADMIN_KEY from settings
    from app.config import get_settings
    settings = get_settings()
    admin_key = request.headers.get("X-Avaira-Admin-Key")
    if not settings.AVAIRA_ADMIN_KEY or admin_key != settings.AVAIRA_ADMIN_KEY:
        raise HTTPException(401, "Unauthorized admin action")

    body = await request.json()
    reason = body.get("reason", "manual")
    severity = body.get("severity", "medium")

    result = await slash_engine.slash(agent_id, reason, severity)
    await trust_marketplace.trigger_slashing_bridge(agent_id, reason, severity)

    return result.model_dump()

@router.get("/agents/{agent_id}/slash-history")
async def get_agent_slash_history(agent_id: str, agent: Dict = Depends(get_current_agent), db=Depends(get_db)):
    if agent["id"] != agent_id:
        raise HTTPException(403, "API Key does not match agent ID")

    slashes = await db.slash_events.find({"agent_id": agent_id}, {"_id": 0}).sort("timestamp", -1).to_list(100)
    return slashes

@router.post("/appeal/{slash_id}")
async def appeal_slash(slash_id: str, body: Dict[str, Any], db=Depends(get_db), slash_engine=Depends(get_slash_engine)):
    slash = await db.slash_events.find_one({"id": slash_id})
    if not slash: raise HTTPException(404, "Slash not found")

    result = await slash_engine.appeal(slash["agent_id"], slash_id, body.get("evidence", ""))
    return result.model_dump()

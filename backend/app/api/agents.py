from fastapi import APIRouter, Depends, Query, HTTPException, Request
from typing import Optional, List, Dict, Any
from unittest.mock import MagicMock
import uuid
import secrets
from datetime import datetime, timezone

from app.dependencies import (
    get_db, get_agent_vault, get_tee_identity_manager,
    get_ape_engine, require_admin_user, get_current_agent
)
from app.models.agent import AgentCreate, AgentRunRequest, AgentThinkRequest
from app.constants import INITIAL_REPUTATION
from agents.avaira_agent import AvairaAgent as RealAvairaAgent
from app.services.audit import record_admin_audit

router = APIRouter(prefix="/agents", tags=[])

def _hash_api_key(key: str) -> str:
    import hashlib
    return hashlib.sha256(key.encode()).hexdigest()

@router.post("/register")
async def register_agent(body: AgentCreate, request: Request, db=Depends(get_db),
                         agent_vault=Depends(get_agent_vault),
                         tee_identity_manager=Depends(get_tee_identity_manager),
                         ape_engine=Depends(get_ape_engine)):

    user_id = "system"
    # Actually, we could use get_current_user here, but server.py had a try/except
    # For now, keeping original logic for zero behavior change

    agent_id = str(uuid.uuid4())
    api_key = secrets.token_urlsafe(32)
    api_key_hash = _hash_api_key(api_key)

    # Generate Virtual Vault Card for Chainless Spend
    vault_card = await agent_vault.generate_virtual_card(agent_id, body.risk_envelope.max_spend_usd)

    # Generate Hardware-Anchored Identity (TEE-DID)
    did_doc = tee_identity_manager.generate_agent_did(agent_id, api_key_hash)

    agent = {
        "id": agent_id,
        "api_key_hash": api_key_hash,
        "user_id": user_id,
        "did_doc": did_doc.model_dump(),
        "name": body.name,
        "goal": body.goal,
        "risk_envelope": body.risk_envelope.model_dump(),
        "vault_card": vault_card.model_dump(),
        "webhook_url": body.webhook_url,
        "status": "active",
        "reputation": INITIAL_REPUTATION,
        "total_executions": 0,
        "successful_executions": 0,
        "failed_executions": 0,
        "registered_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.agents.insert_one(agent)

    # Initial Autonomous Policy Evolution (APE) sync
    await ape_engine.sync_threat_intelligence(agent_id)

    return {"agent_id": agent_id, "api_key": api_key}

@router.get("")
async def list_agents(status: Optional[str] = None, limit: int = Query(100, ge=1, le=500), db=Depends(get_db)):
    query = {}
    if status:
        query["status"] = status
    agents = await db.agents.find(query, {"_id": 0}).sort("registered_at", -1).to_list(limit)
    return agents

@router.get("/{agent_id}")
async def get_agent(agent_id: str, db=Depends(get_db)):
    agent = await db.agents.find_one({"id": agent_id}, {"_id": 0})
    if not agent:
        raise HTTPException(404, "Agent not found")
    return agent

@router.patch("/{agent_id}/status")
async def update_agent_status(agent_id: str, request: Request, status: str = Query(...),
                              admin_user: Dict[str, Any] = Depends(require_admin_user),
                              db=Depends(get_db)):
    if status not in ["active", "paused", "frozen"]:
        raise HTTPException(400, "Invalid status")
    result = await db.agents.update_one({"id": agent_id}, {"$set": {"status": status}})
    if result.matched_count == 0:
        raise HTTPException(404, "Agent not found")
    await record_admin_audit(db, "agent_status_update", admin_user, request, {"agent_id": agent_id, "status": status})
    return {"message": f"Agent status updated to {status}"}

async def _get_agent_from_key(request: Request, db=Depends(get_db)):
    api_key = request.headers.get("X-Avaira-API-Key")
    if not api_key:
        raise HTTPException(401, "Missing X-Avaira-API-Key")

    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    agent = await db.agents.find_one({"api_key_hash": api_key_hash})

    if not agent:
        raise HTTPException(401, "Invalid API Key")
    if agent.get("status") == "frozen":
        raise HTTPException(403, f"Agent is frozen due to a policy violation")
    return agent

@router.post("/{agent_id}/run")
async def agent_run(agent_id: str, body: AgentRunRequest, agent: Dict = Depends(get_current_agent), db=Depends(get_db)):
    if agent["id"] != agent_id:
        raise HTTPException(403, "API Key does not match agent ID")

    real_agent = RealAvairaAgent(agent["id"], agent["risk_envelope"], db_client=db)
    result = await real_agent.run(body.task)
    return result

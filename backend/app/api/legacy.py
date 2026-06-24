from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any
from app.dependencies import get_db, get_reputation_engine, get_avaira_validator
from app.models.agent import AgentThinkRequest
from app.services.agent import ensure_ai_agent_record, is_valid_evm_address
from app.services.reputation import normalize_score, write_reputation_snapshot, grade_from_score, calculate_avaira_score
from app.services.audit import record_treasury_transaction
from app.constants import PROTOCOL_FEE_RATE, SLASH_RATE
from agent_runtime import AvairaAgent
from permit import generate_permit, verify_permit
from agents.avaira_agent import AvairaAgent as RealAvairaAgent
import hashlib
import uuid
from datetime import datetime, timezone

router = APIRouter(tags=[])

@router.get("/health", tags=[])
async def health_check(db=Depends(get_db)):
    """Returns service health status for monitoring and CI smoke tests."""
    from app.config import get_settings
    settings = get_settings()
    db_ok = "ok"
    try:
        await db.command("ping")
    except Exception:
        db_ok = "error"
    return {
        "status": "ok" if db_ok == "ok" else "degraded",
        "version": "1.0.0",
        "db": db_ok,
        "chain": "mainnet" if settings.CHAIN_ID == "43114" else "fuji",
    }

@router.get("/api/", tags=[], include_in_schema=False)
async def root_legacy():
    return {"message": "AVAIRA Protocol API v1.0", "status": "operational"}

@router.get("/", tags=[])
async def root():
    return {"message": "AVAIRA Protocol API v1.0", "status": "operational"}

@router.post("/agent/think")
async def agent_think(body: AgentThinkRequest, db=Depends(get_db)):
    # Backward compatibility or internal use
    agent = await db.agents.find_one({"id": body.agent_address})
    if not agent:
        agent = await db.agents.find_one({"wallet_address": body.agent_address})
    if not agent: raise HTTPException(404, "Agent not found")

    real_agent = RealAvairaAgent(agent["id"], agent["risk_envelope"], db_client=db)
    intent = await real_agent.think(body.mission_goal)
    return intent.model_dump()

@router.post("/agent/simulate-full-lifecycle", operation_id="simulate_full_lifecycle_api_agent_simulate_full_lifecycle_post")
async def simulate_full_lifecycle(body: AgentThinkRequest, db=Depends(get_db), reputation_engine=Depends(get_reputation_engine)):
    if not is_valid_evm_address(body.agent_address):
        raise HTTPException(400, "Invalid agent wallet address")

    agent = await ensure_ai_agent_record(db, body)
    runtime = AvairaAgent(body.agent_address, body.risk_envelope, body.mission_goal)
    lifecycle = []

    lifecycle.append({
        "stage": 1,
        "name": "register",
        "status": "completed",
        "details": {
            "agent_id": agent["id"],
            "wallet_address": agent["wallet_address"],
            "risk_envelope": agent["risk_envelope"],
        },
    })

    intent = await runtime.think(body.market_context, body.history)
    lifecycle.append({"stage": 2, "name": "think", "status": "completed", "details": intent.model_dump()})

    validation = runtime.validate(intent)
    lifecycle.append({"stage": 3, "name": "validate", "status": "completed" if validation["valid"] else "failed", "details": validation})

    permit_bundle = None
    tx_hash = None
    final_status = "completed"
    score_payload_before = await normalize_score(agent, reputation_engine)
    score_before = score_payload_before["score"]

    if validation["valid"]:
        nonce = int(agent.get("runtime_nonce", 0)) + 1
        permit_bundle = generate_permit(body.agent_address, intent.action, intent.target, intent.value_usd, nonce)
        permit_ok = verify_permit(permit_bundle["permit"], permit_bundle["signature"], body.agent_address)
        lifecycle.append({
            "stage": 4,
            "name": "permit",
            "status": "completed" if permit_ok else "failed",
            "details": {"signature": permit_bundle["signature"], "deadline": permit_bundle["deadline"], "verified": permit_ok},
        })

        if not permit_ok:
            final_status = "rejected"
            new_score = max(0, score_before - 5)
            await db.agents.update_one(
                {"id": agent["id"]},
                {"$inc": {"total_executions": 1, "failed_executions": 1}},
            )
            await write_reputation_snapshot(db, agent, new_score, "permit_verification_failed", reputation_engine)
            lifecycle.append({"stage": 5, "name": "execute", "status": "skipped", "details": {"reason": "permit verification failed"}})
            lifecycle.append({"stage": 6, "name": "score_update", "status": "completed", "details": {"before": score_before, "after": new_score, "grade": grade_from_score(new_score)}})
            lifecycle.append({"stage": 7, "name": "final_state", "status": "completed", "details": {"status": "rejected"}})
            await db.executions.insert_one(
                {
                    "id": str(uuid.uuid4()),
                    "agent_id": agent["id"],
                    "agent_name": agent["name"],
                    "action": intent.action,
                    "target_address": intent.target,
                    "value": intent.value_usd,
                    "permit": permit_bundle,
                    "tx_hash": None,
                    "status": final_status,
                    "source": "simulate_full_lifecycle",
                    "lifecycle": lifecycle,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            latest = await db.agents.find_one({"id": agent["id"]}, {"_id": 0})
            return {
                "status": final_status,
                "agent": latest,
                "intent": intent.model_dump(),
                "lifecycle": lifecycle,
                "permit": permit_bundle,
                "avaira_score": await normalize_score(latest, reputation_engine),
            }

        tx_hash = "0x" + hashlib.sha256(f"{body.agent_address}:{nonce}:{intent.action}:{intent.target}:{intent.value_usd}".encode()).hexdigest()
        lifecycle.append({
            "stage": 5,
            "name": "execute",
            "status": "completed",
            "details": {"tx_hash": tx_hash, "network": "fuji", "explorer": f"https://avaira.xyz/audit/tx/{tx_hash}"},
        })

        fee = round(intent.value_usd * PROTOCOL_FEE_RATE, 6)
        await record_treasury_transaction(db, tx_hash, fee)
        lifecycle.append({"stage": 6, "name": "fee_deducted", "status": "completed", "details": {"fee_usd": fee}})

        new_score = min(100, score_before + 8)
        await db.agents.update_one(
            {"id": agent["id"]},
            {"$set": {"runtime_nonce": nonce, "status": "active"}, "$inc": {"total_executions": 1, "successful_executions": 1}},
        )
        await write_reputation_snapshot(db, agent, new_score, "full_lifecycle_success", reputation_engine)
        lifecycle.append({"stage": 7, "name": "score_update", "status": "completed", "details": {"before": score_before, "after": new_score, "grade": grade_from_score(new_score)}})
        lifecycle.append({"stage": 8, "name": "freeze_check", "status": "completed", "details": {"frozen": False, "reason": "no deviation detected"}})
    else:
        slash_amount = round(float(agent.get("collateral_remaining", 0.1)) * SLASH_RATE, 6)
        final_status = "rejected"
        await db.agents.update_one(
            {"id": agent["id"]},
            {
                "$set": {"status": "frozen", "collateral_remaining": max(0.0, float(agent.get("collateral_remaining", 0.1)) - slash_amount)},
                "$inc": {"total_executions": 1, "failed_executions": 1},
            },
        )
        await db.freeze_events.insert_one(
            {
                "id": str(uuid.uuid4()),
                "agent_id": agent["id"],
                "agent_name": agent["name"],
                "type": "freeze",
                "reason": validation["reason"],
                "collateral_slashed": slash_amount,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        new_score = max(0, score_before - 15)
        await write_reputation_snapshot(db, agent, new_score, "full_lifecycle_rejection", reputation_engine)
        lifecycle.append({"stage": 4, "name": "permit", "status": "skipped", "details": {"reason": validation["reason"]}})
        lifecycle.append({"stage": 5, "name": "execute", "status": "skipped", "details": {"reason": "execution blocked by risk envelope"}})
        lifecycle.append({"stage": 6, "name": "score_update", "status": "completed", "details": {"before": score_before, "after": new_score, "grade": grade_from_score(new_score)}})
        lifecycle.append({"stage": 7, "name": "freeze", "status": "completed", "details": {"slash_amount": slash_amount, "reason": validation["reason"]}})
        lifecycle.append({"stage": 8, "name": "final_state", "status": "completed", "details": {"status": "frozen"}})

    await db.executions.insert_one(
        {
            "id": str(uuid.uuid4()),
            "agent_id": agent["id"],
            "agent_name": agent["name"],
            "action": intent.action,
            "target_address": intent.target,
            "value": intent.value_usd,
            "permit": permit_bundle,
            "tx_hash": tx_hash,
            "status": final_status,
            "source": "simulate_full_lifecycle",
            "lifecycle": lifecycle,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    latest = await db.agents.find_one({"id": agent["id"]}, {"_id": 0})
    return {
        "status": final_status,
        "agent": latest,
        "intent": intent.model_dump(),
        "lifecycle": lifecycle,
        "permit": permit_bundle,
        "avaira_score": await normalize_score(latest, reputation_engine),
    }

@router.get("/anchor-state")
async def anchor_state_endpoint(reputation_engine=Depends(get_reputation_engine)):
    """
    Internal cron endpoint for state anchoring.
    """
    result = await reputation_engine.anchor_state()
    return result

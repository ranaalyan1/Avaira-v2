from fastapi import APIRouter, Depends, Query, HTTPException, Request
from pymongo import ReturnDocument
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime, timezone

from app.dependencies import (
    get_db, get_reputation_engine, get_trust_marketplace, require_admin_user, require_authenticated_user
)
from app.models.mission import UnderwriterCreate, MissionCreate, MissionStake, InsuranceRequest
from app.services.reputation import calculate_avaira_score, update_reputation
from app.services.audit import record_admin_audit
from app.constants import (
    MISSION_FEE_AGENT, MISSION_FEE_UNDERWRITER, MISSION_FEE_PROTOCOL,
    REP_SUCCESS_BONUS, REP_FAILURE_PENALTY
)

router = APIRouter(tags=[])

@router.post("/underwriters/register")
async def register_underwriter(body: UnderwriterCreate, request: Request, db=Depends(get_db), _user: Dict[str, Any] = Depends(require_authenticated_user)):
    import secrets
    from app.services.agent import is_valid_evm_address
    if body.capital_amount < 0.5:
        raise HTTPException(400, "Minimum capital is 0.5 USD")
    if body.wallet_address and not is_valid_evm_address(body.wallet_address):
        raise HTTPException(400, "Invalid wallet address format")
    uw = {
        "id": str(uuid.uuid4()),
        "name": body.name,
        "wallet_address": body.wallet_address or ("0x" + secrets.token_hex(20)),
        "capital_amount": body.capital_amount,
        "capital_available": body.capital_amount,
        "capital_staked": 0.0,
        "total_earnings": 0.0,
        "missions_underwritten": 0,
        "missions_successful": 0,
        "status": "active",
        "registered_at": datetime.now(timezone.utc).isoformat()
    }
    await db.underwriters.insert_one(uw)
    uw.pop("_id", None)
    return uw

@router.get("/underwriters")
async def list_underwriters(limit: int = Query(100, ge=1, le=500), db=Depends(get_db)):
    uws = await db.underwriters.find({}, {"_id": 0}).sort("total_earnings", -1).to_list(limit)
    return uws

@router.get("/underwriters/{uw_id}")
async def get_underwriter(uw_id: str, db=Depends(get_db)):
    uw = await db.underwriters.find_one({"id": uw_id}, {"_id": 0})
    if not uw:
        raise HTTPException(404, "Underwriter not found")
    return uw

@router.post("/missions/create")
async def create_mission(body: MissionCreate, db=Depends(get_db)):
    agent = await db.agents.find_one({"id": body.agent_id}, {"_id": 0})
    if not agent:
        raise HTTPException(404, "Agent not found")
    if agent["status"] != "active":
        raise HTTPException(403, f"Agent is {agent['status']}")
    score = calculate_avaira_score(agent)
    mission = {
        "id": str(uuid.uuid4()),
        "agent_id": body.agent_id,
        "agent_name": agent["name"],
        "agent_grade": score["grade"],
        "agent_score": score["composite_score"],
        "description": body.description,
        "target_value": body.target_value,
        "duration_hours": body.duration_hours,
        "risk_level": body.risk_level,
        "status": "open",
        "total_staked": 0.0,
        "underwriters": [],
        "fee_split": {"agent": MISSION_FEE_AGENT, "underwriter": MISSION_FEE_UNDERWRITER, "protocol": MISSION_FEE_PROTOCOL},
        "result": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "settled_at": None
    }
    await db.missions.insert_one(mission)
    mission.pop("_id", None)
    return mission

@router.get("/missions")
async def list_missions(status: Optional[str] = None, limit: int = Query(100, ge=1, le=500), db=Depends(get_db)):
    query = {}
    if status:
        query["status"] = status
    missions = await db.missions.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return missions

@router.get("/missions/{mission_id}")
async def get_mission(mission_id: str, db=Depends(get_db)):
    mission = await db.missions.find_one({"id": mission_id}, {"_id": 0})
    if not mission:
        raise HTTPException(404, "Mission not found")
    return mission

@router.post("/missions/{mission_id}/stake")
async def stake_on_mission(mission_id: str, body: MissionStake, db=Depends(get_db)):
    mission = await db.missions.find_one({"id": mission_id}, {"_id": 0})
    if not mission:
        raise HTTPException(404, "Mission not found")
    if mission["status"] != "open":
        raise HTTPException(400, "Mission not open for staking")
    uw = await db.underwriters.find_one({"id": body.underwriter_id}, {"_id": 0})
    if not uw:
        raise HTTPException(404, "Underwriter not found")
    if uw["capital_available"] < body.amount:
        raise HTTPException(400, "Insufficient capital")
    await db.underwriters.update_one({"id": body.underwriter_id}, {"$inc": {"capital_available": -body.amount, "capital_staked": body.amount}})
    stake_entry = {"underwriter_id": body.underwriter_id, "underwriter_name": uw["name"], "amount": body.amount, "staked_at": datetime.now(timezone.utc).isoformat()}
    await db.missions.update_one({"id": mission_id}, {"$push": {"underwriters": stake_entry}, "$inc": {"total_staked": body.amount}})
    updated = await db.missions.find_one({"id": mission_id}, {"_id": 0})
    return updated

@router.post("/missions/{mission_id}/settle")
async def settle_mission(mission_id: str, request: Request, success: bool = True, admin_user: Dict[str, Any] = Depends(require_admin_user), db=Depends(get_db)):
    settled_at = datetime.now(timezone.utc).isoformat()
    result_label = "success" if success else "failed"
    mission = await db.missions.find_one_and_update(
        {"id": mission_id, "status": {"$ne": "settled"}},
        {"$set": {"status": "settled", "result": result_label, "settled_at": settled_at}},
        projection={"_id": 0},
        return_document=ReturnDocument.BEFORE,
    )
    if not mission:
        exists = await db.missions.find_one({"id": mission_id}, {"_id": 0})
        if not exists:
            raise HTTPException(404, "Mission not found")
        raise HTTPException(400, "Already settled")
    total_value = mission["target_value"]
    if success:
        agent_payout = round(total_value * MISSION_FEE_AGENT, 6)
        uw_total = round(total_value * MISSION_FEE_UNDERWRITER, 6)
        protocol_fee = round(total_value * MISSION_FEE_PROTOCOL, 6)
        for uw_stake in mission.get("underwriters", []):
            share = uw_stake["amount"] / max(mission["total_staked"], 0.001)
            earnings = round(uw_total * share, 6)
            await db.underwriters.update_one({"id": uw_stake["underwriter_id"]}, {"$inc": {"capital_staked": -uw_stake["amount"], "capital_available": uw_stake["amount"] + earnings, "total_earnings": earnings, "missions_underwritten": 1, "missions_successful": 1}})
        await update_reputation(db, mission["agent_id"], REP_SUCCESS_BONUS, f"Mission settled: {mission['description'][:40]}")
        rev_entry = {"id": str(uuid.uuid4()), "type": "underwriting", "mission_id": mission_id, "amount": protocol_fee, "timestamp": datetime.now(timezone.utc).isoformat()}
        await db.revenue_events.insert_one(rev_entry)
        await record_admin_audit(db, "mission_settle", admin_user, request, {"mission_id": mission_id, "success": True})
        return {"status": "settled", "result": "success", "agent_payout": agent_payout, "underwriter_payout": uw_total, "protocol_fee": protocol_fee}
    else:
        slash_total = mission["total_staked"] * 0.5
        for uw_stake in mission.get("underwriters", []):
            share = uw_stake["amount"] / max(mission["total_staked"], 0.001)
            loss = round(slash_total * share, 6)
            await db.underwriters.update_one({"id": uw_stake["underwriter_id"]}, {"$inc": {"capital_staked": -uw_stake["amount"], "capital_available": uw_stake["amount"] - loss, "missions_underwritten": 1}})
        await update_reputation(db, mission["agent_id"], -REP_FAILURE_PENALTY, f"Mission failed: {mission['description'][:40]}")
        await record_admin_audit(db, "mission_settle", admin_user, request, {"mission_id": mission_id, "success": False})
        return {"status": "settled", "result": "failed", "coverage_provided": slash_total}

@router.post("/marketplace/insurance")
async def issue_insurance(body: InsuranceRequest, trust_marketplace=Depends(get_trust_marketplace), _user: Dict[str, Any] = Depends(require_authenticated_user)):
    policy = await trust_marketplace.issue_policy(
        body.agent_id, body.underwriter_id, body.coverage_amount
    )
    return policy.model_dump()

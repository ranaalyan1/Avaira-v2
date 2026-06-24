from typing import Dict, Optional, Any
import uuid
from datetime import datetime, timezone
from app.constants import INITIAL_REPUTATION, AVAIRA_GRADES, REP_FREEZE_PENALTY, REP_SLASH_PENALTY, REP_SUCCESS_BONUS, REP_FAILURE_PENALTY

def grade_from_score(score: float) -> str:
    if score >= 90:
        return "A+"
    if score >= 80:
        return "A"
    if score >= 70:
        return "B"
    if score >= 60:
        return "C"
    return "D"

async def normalize_score(agent: Optional[Dict[str, Any]], reputation_engine) -> Dict[str, Any]:
    if not agent:
        return {"score": 50, "grade": "C"}
    try:
        score_obj = await reputation_engine.compute_score(agent["id"])
        return {"score": score_obj.score, "grade": score_obj.grade}
    except Exception:
        if "avaira_score" in agent:
            score = max(0, min(100, int(round(agent.get("avaira_score", 50)))))
        else:
            score = max(0, min(100, int(round(agent.get("reputation", INITIAL_REPUTATION) / 2))))
        return {"score": score, "grade": agent.get("grade", grade_from_score(score))}

def calculate_avaira_score(agent: Dict) -> Dict:
    total_ex = max(agent.get("total_executions", 0), 1)
    success_rate = (agent.get("successful_executions", 0) / total_ex) * 100
    base_rep = agent.get("reputation", INITIAL_REPUTATION)
    collateral_ratio = min((agent.get("collateral_remaining", 0) / max(agent.get("collateral_amount", 1), 0.01)) * 100, 100)
    complexity = min(agent.get("total_executions", 0) * 2, 100)
    reg_date = agent.get("registered_at", datetime.now(timezone.utc).isoformat())
    try:
        days_on_network = (datetime.now(timezone.utc) - datetime.fromisoformat(reg_date.replace("Z", "+00:00"))).days
    except Exception:
        days_on_network = 0
    time_score = min(days_on_network * 3, 100)
    deviation_count = agent.get("failed_executions", 0)
    deviation_score = max(100 - (deviation_count * 15), 0)
    composite = (success_rate * 0.30 + (base_rep / 2) * 0.20 + collateral_ratio * 0.15 + complexity * 0.15 + time_score * 0.10 + deviation_score * 0.10)
    grade = "D"
    for g, low, high in AVAIRA_GRADES:
        if low <= composite <= high:
            grade = g
            break
    return {
        "composite_score": round(composite, 1),
        "grade": grade,
        "factors": {
            "success_rate": round(success_rate, 1),
            "behavioral_consistency": round(base_rep / 2, 1),
            "collateral_ratio": round(collateral_ratio, 1),
            "mission_complexity": round(complexity, 1),
            "time_on_network": round(time_score, 1),
            "deviation_penalty": round(deviation_score, 1)
        },
        "weights": {"success_rate": 0.30, "behavioral_consistency": 0.20, "collateral_ratio": 0.15, "mission_complexity": 0.15, "time_on_network": 0.10, "deviation_penalty": 0.10}
    }

async def update_reputation(db, agent_id: str, delta: float, reason: str):
    agent = await db.agents.find_one({"id": agent_id}, {"_id": 0})
    if not agent:
        return
    old_score = agent.get("reputation", INITIAL_REPUTATION)
    new_score = max(0, min(200, old_score + delta))
    await db.agents.update_one({"id": agent_id}, {"$set": {"reputation": new_score}})
    history_entry = {
        "id": str(uuid.uuid4()),
        "agent_id": agent_id,
        "agent_name": agent.get("name", "Unknown"),
        "old_score": old_score,
        "new_score": new_score,
        "delta": delta,
        "reason": reason,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.reputation_history.insert_one(history_entry)

async def write_reputation_snapshot(db, agent, new_score: int, reason: str, reputation_engine):
    score_payload = await normalize_score(agent, reputation_engine)
    previous = score_payload["score"]
    grade = grade_from_score(new_score)
    await db.agents.update_one(
        {"id": agent["id"]},
        {
            "$set": {
                "avaira_score": new_score,
                "grade": grade,
                "reputation": min(200, max(0, new_score * 2)),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )
    await db.reputation_history.insert_one(
        {
            "id": str(uuid.uuid4()),
            "agent_id": agent["id"],
            "agent_name": agent.get("name", agent["wallet_address"]),
            "old_score": previous,
            "new_score": new_score,
            "delta": new_score - previous,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )

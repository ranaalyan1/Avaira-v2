from fastapi import APIRouter, Depends, Query
from app.dependencies import get_db
from app.services.reputation import calculate_avaira_score

router = APIRouter(prefix="/dashboard", tags=[])

@router.get("/stats")
async def get_dashboard_stats(db=Depends(get_db)):
    from app.api.info import get_treasury_stats_internal
    total_agents = await db.agents.count_documents({})
    active_agents = await db.agents.count_documents({"status": "active"})
    frozen_agents = await db.agents.count_documents({"status": "frozen"})
    total_executions = await db.executions.count_documents({})
    completed_executions = await db.executions.count_documents({"status": "completed"})
    failed_executions = await db.executions.count_documents({"status": {"$in": ["rejected_deviation", "permit_invalid"]}})
    pending_executions = await db.executions.count_documents({"status": {"$in": ["pending_validation", "permit_signed"]}})

    treasury = await get_treasury_stats_internal(db)
    total_collateral_pipeline = [{"$group": {"_id": None, "total": {"$sum": "$collateral_remaining"}}}]
    collateral_result = await db.agents.aggregate(total_collateral_pipeline).to_list(1)
    total_collateral = round(collateral_result[0]["total"], 6) if collateral_result else 0

    return {
        "total_agents": total_agents,
        "active_agents": active_agents,
        "frozen_agents": frozen_agents,
        "total_executions": total_executions,
        "completed_executions": completed_executions,
        "failed_executions": failed_executions,
        "pending_executions": pending_executions,
        "total_fees_collected": treasury["total_fees"],
        "trust_pool_balance": treasury["total_trust_pool"],
        "protocol_revenue": treasury["total_protocol_revenue"],
        "total_collateral_staked": total_collateral
    }

@router.get("/activity")
async def get_recent_activity(limit: int = Query(20, ge=1, le=100), db=Depends(get_db)):
    activities = []
    recent_execs = await db.executions.find({}, {"_id": 0}).sort("created_at", -1).to_list(10)
    for ex in recent_execs:
        activities.append({
            "type": "execution",
            "description": f"Agent '{ex.get('agent_name', 'Unknown')}' - {ex['action']} ({ex['status']})",
            "status": ex["status"],
            "timestamp": ex["created_at"],
            "id": ex["id"]
        })
    recent_freezes = await db.freeze_events.find({}, {"_id": 0}).sort("timestamp", -1).to_list(10)
    for fe in recent_freezes:
        activities.append({
            "type": fe["type"],
            "description": f"Agent '{fe.get('agent_name', 'Unknown')}' - {fe['type'].upper()}: {fe['reason']}",
            "status": fe["type"],
            "timestamp": fe["timestamp"],
            "id": fe["id"]
        })
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    return activities[:limit]

from fastapi import APIRouter, Depends, Query, Request
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from app.dependencies import get_db, get_reputation_engine
from app.services.reputation import calculate_avaira_score

router = APIRouter(tags=[])

@router.get("/leaderboard")
async def get_leaderboard(
    limit: int = Query(20, ge=1, le=200),
    db=Depends(get_db),
    reputation_engine=Depends(get_reputation_engine)
):
    # Returns top agents by Avaira score
    agents = await db.agents.find({}, {"_id": 0}).to_list(100)
    results = []
    for agent in agents:
        try:
            score = await reputation_engine.compute_score(agent["id"])
            results.append({
                "agent_id": agent["id"],
                "name": agent["name"],
                "score": score.score,
                "grade": score.grade,
                "status": agent["status"]
            })
        except:
            continue
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]

@router.get("/reputation/leaderboard")
async def get_leaderboard_legacy(limit: int = Query(20, ge=1, le=200), db=Depends(get_db), reputation_engine=Depends(get_reputation_engine)):
    return await get_leaderboard(limit, db, reputation_engine)

@router.get("/agent/leaderboard")
async def agent_leaderboard():
    return await get_leaderboard()

@router.get("/reputation/{agent_id}/history")
async def get_reputation_history(agent_id: str, limit: int = Query(50, ge=1, le=500), db=Depends(get_db)):
    history = await db.reputation_history.find({"agent_id": agent_id}, {"_id": 0}).sort("timestamp", -1).to_list(limit)
    return history

@router.get("/reputation/history")
async def get_all_reputation_history(limit: int = Query(100, ge=1, le=500), db=Depends(get_db)):
    history = await db.reputation_history.find({}, {"_id": 0}).sort("timestamp", -1).to_list(limit)
    return history

@router.get("/agents/{agent_id}/score")
async def get_agent_score(agent_id: str, db=Depends(get_db), reputation_engine=Depends(get_reputation_engine)):
    try:
        score = await reputation_engine.compute_score(agent_id)
        agent = await db.agents.find_one({"id": agent_id})
        return {**score.model_dump(), "agent_id": agent_id, "agent_name": agent["name"], "status": agent["status"]}
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(404, str(e))

@router.get("/scores/all")
async def get_all_scores(db=Depends(get_db)):
    agents = await db.agents.find({}, {"_id": 0}).to_list(200)
    results = []
    for agent in agents:
        score = calculate_avaira_score(agent)
        results.append({"agent_id": agent["id"], "agent_name": agent["name"], "status": agent["status"], "grade": score["grade"], "composite_score": score["composite_score"], "reputation": agent["reputation"]})
    results.sort(key=lambda x: x["composite_score"], reverse=True)
    return results

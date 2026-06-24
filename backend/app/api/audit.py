from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from app.dependencies import get_current_agent, get_intent_logger

router = APIRouter(prefix="/agents", tags=[])

@router.get("/{agent_id}/audit")
async def get_agent_audit(
    agent_id: str,
    agent: Dict = Depends(get_current_agent),
    intent_logger=Depends(get_intent_logger)
):
    if agent["id"] != agent_id:
        raise HTTPException(403, "API Key does not match agent ID")

    trail = await intent_logger.get_audit_trail(agent_id,
                                               datetime.now(timezone.utc) - timedelta(days=30),
                                               datetime.now(timezone.utc))
    return [e.model_dump() for e in trail]

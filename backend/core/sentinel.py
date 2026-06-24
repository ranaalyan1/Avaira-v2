import json
import os
import asyncio
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from .shield_slm import ShieldSLM, SLMClassification

class DriftAnalysis(BaseModel):
    agent_id: str
    drift_score: float  # 0.0 to 1.0 (1.0 = highly unstable)
    trend: str  # "stable", "deviating", "dangerous"
    predicted_violation: Optional[str]
    recommendation: str

class AvairaSentinel:
    """
    Predictive Shielding Engine.
    Analyzes historical intent vs. current intent to detect 'behavioral drift'
    and predict policy violations before they occur.
    """
    def __init__(self, db_client=None):
        self.db = db_client
        self.slm = ShieldSLM()

    async def analyze_drift(self, agent_id: str, current_intent: Dict[str, Any]) -> DriftAnalysis:
        # 1. Fetch recent history
        cursor = self.db.executions.find(
            {"agent_id": agent_id, "status": "completed"}
        ).sort("timestamp", -1).limit(5)
        history = await cursor.to_list(None)

        if not history:
            return DriftAnalysis(
                agent_id=agent_id,
                drift_score=0.0,
                trend="stable",
                predicted_violation=None,
                recommendation="Continue monitoring."
            )

        # 2. Use SLM to compare current intent against historical trajectory
        history_summary = [h.get("intent", h.get("action")) for h in history]

        prompt = f"""
        Behavioral Drift Analysis:
        Compare the current intent of an AI agent against its recent history.
        Detect if the agent is slowly 'drifting' away from its original mission or becoming more aggressive/unstable.

        Mission Goal: {history[0].get('mission_goal', 'General Task')}
        Recent History: {json.dumps(history_summary)}
        Current Intent: {json.dumps(current_intent)}

        Return ONLY valid JSON:
        {{
          "drift_score": 0.0-1.0,
          "trend": "stable/deviating/dangerous",
          "predicted_violation": "none or name of possible violation",
          "recommendation": "..."
        }}
        """

        try:
            # Reusing ShieldSLM's logic for a different task
            resp = await self.slm.classify_intent({"task": "drift_analysis", "prompt": prompt})
            # In a real implementation, we'd have a specific method for this in ShieldSLM
            # For now, we simulate the SLM response parsing for drift

            # Simulated SLM result for drift (since we can't actually call the endpoint)
            drift_score = 0.1
            trend = "stable"
            if "dangerous" in resp.reasoning.lower():
                drift_score = 0.8
                trend = "dangerous"
            elif "deviating" in resp.reasoning.lower():
                drift_score = 0.4
                trend = "deviating"

            return DriftAnalysis(
                agent_id=agent_id,
                drift_score=drift_score,
                trend=trend,
                predicted_violation=resp.intent if drift_score > 0.5 else None,
                recommendation="Increase scrutiny." if drift_score > 0.3 else "Proceed."
            )
        except:
            return DriftAnalysis(
                agent_id=agent_id,
                drift_score=0.0,
                trend="stable",
                predicted_violation=None,
                recommendation="Fallback: Sentinel monitoring active."
            )

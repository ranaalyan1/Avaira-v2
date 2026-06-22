from __future__ import annotations
import os
import litellm
import json
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field


class ExecutionIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: str
    target: str
    value_usd: float
    rationale: str
    confidence: float = Field(ge=0, le=1)


class RuntimeRiskEnvelope(BaseModel):
    model_config = ConfigDict(extra="ignore")

    max_tx_value: float = 1.0
    max_spend_usd: float = 1.0
    max_slippage: float = Field(default=0.05, ge=0, le=1)
    allowed_actions: List[str] = []

class AvairaAgent:
    def __init__(self, agent_address: str, risk_envelope: RuntimeRiskEnvelope | Dict[str, Any], mission_goal: str):
        self.agent_address = agent_address
        self.risk_envelope = risk_envelope if isinstance(risk_envelope, RuntimeRiskEnvelope) else RuntimeRiskEnvelope.model_validate(risk_envelope)
        self.mission_goal = mission_goal
        self.local_only = os.environ.get("LOCAL_ONLY_MODE", "false").lower() == "true"
        self.model = os.environ.get("AGENT_MODEL", "anthropic/claude-3-5-sonnet-20241022")

    async def think(self, market_context: dict, history: list) -> ExecutionIntent:
        if self.local_only:
            # Enhanced local reasoning for research mode
            return await self._ai_think(market_context, history)
        return self._planned_intent(market_context, history)

    async def _ai_think(self, market_context: dict, history: list) -> ExecutionIntent:
        prompt = f"""
        Research Context: {self.mission_goal}
        Market Data: {json.dumps(market_context)}
        History: {json.dumps(history)}

        Reason about the best next action within these boundaries: {json.dumps(self.risk_envelope.model_dump())}

        Return JSON with: action, target, value_usd, rationale, confidence.
        """

        resp = await litellm.acompletion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            response_format={"type": "json_object"}
        )

        data = json.loads(resp.choices[0].message.content)
        return ExecutionIntent(**data)

    def validate(self, intent: ExecutionIntent) -> dict:
        if intent.value_usd > self.risk_envelope.max_tx_value:
            return {"valid": False, "reason": f"value_usd {intent.value_usd} exceeds max_tx_value {self.risk_envelope.max_tx_value}"}
        if intent.action not in self.risk_envelope.allowed_actions:
            return {"valid": False, "reason": f"action '{intent.action}' is not allowed by the registered risk envelope"}
        return {"valid": True, "reason": "within risk envelope"}

    async def execute_cycle(self, market_context: dict, history: list) -> dict:
        intent = await self.think(market_context, history)
        validation = self.validate(intent)
        return {
            "status": "approved" if validation["valid"] else "rejected",
            "intent": intent.model_dump(),
            "reason": validation["reason"],
            "permit_needed": validation["valid"],
        }

    def _planned_intent(self, market_context: Dict[str, Any], history: List[Dict[str, Any]]) -> ExecutionIntent:
        target = market_context.get("target") or "0x0000000000000000000000000000000000000000"
        action = self.risk_envelope.allowed_actions[0] if self.risk_envelope.allowed_actions else "hold"
        suggested_value = float(market_context.get("suggested_value_usd", 0.1))
        market_signal = str(market_context.get("market_signal", "neutral")).lower()
        prior_attempts = len(history)

        if "stake" in self.risk_envelope.allowed_actions and "bull" in market_signal:
            action = "stake"
        elif "swap" in self.risk_envelope.allowed_actions and any(keyword in market_signal for keyword in ["rebalance", "volatile", "rotation"]):
            action = "swap"

        confidence = 0.55
        if "bull" in market_signal or "bear" in market_signal:
            confidence += 0.1
        if prior_attempts:
            confidence += min(prior_attempts * 0.03, 0.15)

        bounded_value = min(self.risk_envelope.max_tx_value, max(0.0, suggested_value))
        return ExecutionIntent(
            action=action,
            target=target,
            value_usd=bounded_value,
            rationale=(
                "Local planner selected the lowest-risk allowed action using mission goal, "
                "market context, and prior execution history."
            ),
            confidence=min(confidence, 0.9),
        )

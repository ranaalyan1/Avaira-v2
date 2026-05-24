import httpx
import os
import json
from typing import Dict, Any, List
from pydantic import BaseModel

class OPAResult(BaseModel):
    allow: bool
    violations: List[str]

class ShieldRules:
    """
    Deterministic rules engine using Open Policy Agent (OPA).
    Provides a non-probabilistic security firewall for agent intents.
    """
    def __init__(self, endpoint: str = None):
        self.endpoint = endpoint or os.environ.get("OPA_ENDPOINT", "http://localhost:8181/v1/data/avaira/shield")

    async def evaluate(self, intent: Dict[str, Any], risk_envelope: Dict[str, Any]) -> OPAResult:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        payload = {
            "input": {
                "intent": intent,
                "risk_envelope": risk_envelope,
                "current_time_hour": now.hour
            }
        }

        try:
            # Mathematical check must be instant, but 20ms is risky for network sidecars.
            # Increased to 100ms for production robustness while still targeting sub-50ms logic.
            async with httpx.AsyncClient(timeout=0.1) as client:
                resp = await client.post(self.endpoint, json=payload)
                data = resp.json().get("result", {})

                # Rego variables are mapped to JSON keys
                allow = data.get("allow", False)

                violations = []
                if data.get("any_violation"):
                    if data.get("violation_unauthorized_action"): violations.append("unauthorized_action")
                    if data.get("violation_domain_blocked"): violations.append("domain_blocked")
                    if data.get("violation_spend_limit"): violations.append("spend_limit_exceeded")

                return OPAResult(allow=allow, violations=violations)
        except Exception as e:
            # Safe by default: If OPA is unreachable, deny.
            return OPAResult(allow=False, violations=[f"opa_engine_unreachable: {str(e)}"])

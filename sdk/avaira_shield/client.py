import httpx
import json
import asyncio
from typing import Callable, Any, Dict, Optional
from .config import AvairaConfig, RiskEnvelope

class AvairaClient:
    def __init__(self, config: AvairaConfig):
        self.config = config
        self.http_client = httpx.AsyncClient(
            base_url=config.api_url,
            timeout=httpx.Timeout(10.0, connect=5.0)
        )

    async def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Centralized request handler with error normalization."""
        try:
            resp = await getattr(self.http_client, method.lower())(path, **kwargs)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get("detail", str(e))
            except:
                detail = str(e)
            raise RuntimeError(f"Avaira API Error: {detail}") from e
        except Exception as e:
            raise RuntimeError(f"Avaira Connection Error: {str(e)}") from e

    async def register(self, name: str, goal: str) -> str:
        data = await self._request("POST", "/api/agents/register", json={
            "name": name,
            "goal": goal,
            "risk_envelope": self.config.risk_envelope.model_dump(),
            "webhook_url": self.config.webhook_url
        })
        self.config.agent_id = data["agent_id"]
        self.config.api_key = data["api_key"]
        return data["agent_id"]

    async def run(self, task: str, execute_fn: Callable) -> Dict[str, Any]:
        intent = {
            "action": "execute_task",
            "task": task,
            "parameters": {},
            "estimated_value": 0.0
        }

        validation = await self.validate(intent)

        if not validation["approved"] and self.config.strict_mode:
            return {
                "status": "blocked",
                "violations": validation["violations"],
                "reasoning": validation["compliance_reasoning"]
            }

        try:
            result = await execute_fn() if asyncio.iscoroutinefunction(execute_fn) else execute_fn()
            status = "completed"
        except Exception as e:
            result = str(e)
            status = "failed"

        await self._request("POST", f"/api/agents/{self.config.agent_id}/log",
            json={"intent": intent, "status": status, "result": result},
            headers={"X-Avaira-API-Key": self.config.api_key}
        )

        return {
            "status": status,
            "result": result,
            "validation": validation
        }

    async def validate(self, intent: dict) -> Dict[str, Any]:
        return await self._request("POST", "/api/validate", json={
            "intent": intent,
            "risk_envelope": self.config.risk_envelope.model_dump()
        })

    async def get_score(self) -> Dict[str, Any]:
        return await self._request("GET", f"/api/agents/{self.config.agent_id}/score")

    async def get_trust_proof(self) -> Dict[str, Any]:
        return await self._request(
            "GET",
            f"/api/agents/{self.config.agent_id}/trust-proof",
            headers={"X-Avaira-API-Key": self.config.api_key}
        )

    async def verify_peer(self, proof: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request("POST", "/api/verify-proof", json=proof)

ShieldClient = AvairaClient
ShieldConfig = AvairaConfig

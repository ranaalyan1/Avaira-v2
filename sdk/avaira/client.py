import httpx
import json
import asyncio
from typing import Callable, Any, Dict, Optional
from .config import AvairaConfig, RiskEnvelope

class AvairaClient:
    def __init__(self, config: AvairaConfig):
        self.config = config
        self.http_client = httpx.AsyncClient(base_url=config.api_url)

    async def register(self, name: str, goal: str) -> str:
        resp = await self.http_client.post("/api/agents/register", json={
            "name": name,
            "goal": goal,
            "risk_envelope": self.config.risk_envelope.model_dump(),
            "webhook_url": self.config.webhook_url
        })
        resp.raise_for_status()
        data = resp.json()
        self.config.agent_id = data["agent_id"]
        self.config.api_key = data["api_key"]
        return data["agent_id"]

    async def run(self, task: str, execute_fn: Callable) -> Dict[str, Any]:
        # 1. Generate intent from task (Simplified: assume execute_fn provides intent or we derive it)
        # In real SDK, we might call backend to 'think' or do it locally
        intent = {
            "action": "execute_task",
            "task": task,
            "parameters": {},
            "estimated_value": 0.0
        }

        # 2. Validate
        validation = await self.validate(intent)

        if not validation["approved"] and self.config.strict_mode:
            return {
                "status": "blocked",
                "violations": validation["violations"],
                "reasoning": validation["compliance_reasoning"]
            }

        # 3. Execute
        try:
            result = await execute_fn() if asyncio.iscoroutinefunction(execute_fn) else execute_fn()
            status = "completed"
        except Exception as e:
            result = str(e)
            status = "failed"

        # 4. Log outcome (POST /api/agents/{id}/log)
        await self.http_client.post(f"/api/agents/{self.config.agent_id}/log",
            json={"intent": intent, "status": status, "result": result},
            headers={"X-Avaira-API-Key": self.config.api_key}
        )

        return {
            "status": status,
            "result": result,
            "validation": validation
        }

    async def validate(self, intent: dict) -> Dict[str, Any]:
        resp = await self.http_client.post("/api/validate", json={
            "intent": intent,
            "risk_envelope": self.config.risk_envelope.model_dump()
        })
        resp.raise_for_status()
        return resp.json()

    async def get_score(self) -> Dict[str, Any]:
        resp = await self.http_client.get(f"/api/agents/{self.config.agent_id}/score")
        resp.raise_for_status()
        return resp.json()

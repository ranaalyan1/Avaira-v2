import json
import os
import uuid
import anthropic
from datetime import datetime, timezone
from typing import Dict, Any, List
from pydantic import BaseModel

from core.validator import AvairaValidator
from core.intent_logger import IntentLogger
from core.reputation import ReputationEngine
from core.slash_engine import SlashEngine, SlashDecision

class ExecutionIntent(BaseModel):
    action: str
    target: str
    parameters: Dict[str, Any]
    estimated_value: float
    reasoning: str
    self_assessment: Dict[str, Any]

class RunResult(BaseModel):
    task: str
    intent: Dict[str, Any]
    validation: Dict[str, Any]
    execution: Dict[str, Any]
    score_update: Dict[str, Any]
    trace_id: str

class AvairaAgent:
    def __init__(self, agent_id: str, risk_envelope: dict, db_client=None):
        self.agent_id = agent_id
        self.risk_envelope = risk_envelope
        self.client = anthropic.AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.validator = AvairaValidator()
        self.logger = IntentLogger(db_client=db_client)
        self.reputation = ReputationEngine(db_client=db_client)
        self.slash_engine = SlashEngine(db_client=db_client)
        self.db = db_client

    async def think(self, task: str) -> ExecutionIntent:
        system_prompt = f"""
        You are an AI agent operating under a strict risk envelope.
        You must FIRST reason about the task, then decide on a structured action.
        Be aware of your boundaries: {json.dumps(self.risk_envelope)}

        Return ONLY valid JSON in this format:
        {{
          "action": "...",
          "target": "...",
          "parameters": {{...}},
          "estimated_value": 0.0,
          "reasoning": "...",
          "self_assessment": {{
            "within_envelope": true/false,
            "confidence": 0.0-1.0,
            "concerns": ["..."]
          }}
        }}
        """

        resp = await self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            system=system_prompt,
            messages=[{"role": "user", "content": task}]
        )

        data = json.loads(resp.content[0].text)
        return ExecutionIntent(**data)

    async def run(self, task: str) -> RunResult:
        trace_id = str(uuid.uuid4())

        # 1. Think
        intent = await self.think(task)
        intent_dict = intent.model_dump()

        # 2. Log Intent
        log_entry = await self.logger.log(intent_dict, self.agent_id, self.risk_envelope)

        # 3. Validate
        validation = await self.validator.validate(intent_dict, self.risk_envelope)
        val_dict = validation.model_dump()

        execution_outcome = {}
        if validation.approved:
            # 4. Execute (Simulated for this generic class)
            execution_outcome = {
                "status": "completed",
                "result": f"Executed {intent.action} on {intent.target}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "value": intent.estimated_value
            }
        else:
            execution_outcome = {
                "status": "blocked",
                "reason": "Validation failed",
                "violations": validation.violations
            }
            # 5. Trigger Slash Evaluation
            slash_dec = await self.slash_engine.evaluate(self.agent_id, validation, execution_outcome)
            if slash_dec.should_slash:
                 await self.slash_engine.slash(self.agent_id, slash_dec.reason, slash_dec.severity)

        # Store execution in DB
        await self.db.executions.insert_one({
            "trace_id": trace_id,
            "agent_id": self.agent_id,
            "task": task,
            "intent": intent_dict,
            "validation": val_dict,
            "status": execution_outcome["status"],
            "value": intent.estimated_value,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # 6. Update Reputation
        new_score = await self.reputation.compute_score(self.agent_id)

        return RunResult(
            task=task,
            intent=intent_dict,
            validation=val_dict,
            execution=execution_outcome,
            score_update=new_score.model_dump(),
            trace_id=trace_id
        )

    async def simulate_lifecycle(self, n_tasks: int = 5) -> List[RunResult]:
        # Generate tasks using Claude
        prompt = f"Generate {n_tasks} tasks for an AI agent with this goal: '{self.risk_envelope.get('goal', 'be helpful')}'."
        # ... logic to get tasks ...
        tasks = [f"Task {i+1}" for i in range(n_tasks)] # Placeholder

        results = []
        for task in tasks:
            results.append(await self.run(task))
        return results

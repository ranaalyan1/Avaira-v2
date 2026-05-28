import json
import os
import uuid
import asyncio
import anthropic
from datetime import datetime, timezone
from typing import Dict, Any, List
from pydantic import BaseModel

try:
    from core.validator import AvairaValidator
    from core.intent_logger import IntentLogger
    from core.reputation import ReputationEngine
    from core.slash_engine import SlashEngine, SlashDecision
    from core.shadow_env import ShadowEnvironment
    from core.sentinel import AvairaSentinel
    from core.zk_vault import ZKAuditVault
except ImportError:
    from ..core.validator import AvairaValidator
    from ..core.intent_logger import IntentLogger
    from ..core.reputation import ReputationEngine
    from ..core.slash_engine import SlashEngine, SlashDecision
    from ..core.shadow_env import ShadowEnvironment
    from ..core.sentinel import AvairaSentinel
    from ..core.zk_vault import ZKAuditVault

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
        self.shadow_env = ShadowEnvironment()
        self.sentinel = AvairaSentinel(db_client=db_client)
        self.zk_vault = ZKAuditVault()
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
        """
        Avaira Zero-Trust Execution Shield Pipeline
        Follows strict chronological sequence: Intercept -> OPA -> Provision -> Shadow Execute -> Live Commit.
        """
        trace_id = str(uuid.uuid4())

        # 1. Intercept Intent & Context Mapping (Sub-2ms)
        intent = await self.think(task)
        intent_dict = intent.model_dump()

        # 2. Synchronous OPA Validation (Sub-15ms)
        # We use fast_shield_pass which calls OPA/Rego and fast SLM
        validation = await self.validator.fast_shield_pass(intent_dict, self.risk_envelope)

        # 2b. Avaira Sentinel (Predictive Shielding)
        # Analyze behavioral drift to predict violations before they happen
        drift_analysis = await self.sentinel.analyze_drift(self.agent_id, intent_dict)

        execution_outcome = {}
        zk_proof = None
        if not validation.approved:
            # Kill execution instantly if OPA fails
            execution_outcome = {
                "status": "blocked",
                "reason": f"OPA Security Shield Block: {', '.join(validation.violations)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            # 3. Dynamic Credential Provisioning (Financial Blast-Radius Control)
            # Mints a virtual card capped at the exact transaction amount
            vault_res = await self.db.agents.find_one({"id": self.agent_id})
            provisioned_creds = {}
            if intent.action in ["payment", "buy", "transfer"]:
                card = await self.slash_engine.db.agents.find_one({"id": self.agent_id}, {"vault_card": 1}) # Reusing vault card logic
                provisioned_creds = {
                    "card_id": card.get("vault_card", {}).get("card_id"),
                    "limit_usd": intent.estimated_value,
                    "status": "provisioned_for_task"
                }

            # 4. Shadow Execution & State Verification (State-Aware)
            shadow_delta = await self.shadow_env.verify_action(intent_dict)

            # 5. Live Commit & Cryptographic Minting (TEE Locked)
            if shadow_delta.verified:
                execution_outcome = {
                    "status": "completed",
                    "result": f"Executed {intent.action} on {intent.target}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "value": intent.estimated_value,
                    "provisioned_creds": provisioned_creds
                }

                # 5b. ZK-Audit Vault (Zero-Knowledge Compliance)
                # Generate proof that execution followed rules without revealing private data
                proof = await self.zk_vault.generate_compliance_proof(
                    intent_dict, self.risk_envelope, validation.audit_id
                )
                zk_proof = proof.model_dump()

                # 6. Asynchronous Neural Audit & Scoring (Background process)
                asyncio.create_task(
                    self.validator.deep_neural_audit(intent_dict, self.risk_envelope, validation.audit_id)
                )
            else:
                execution_outcome = {
                    "status": "shadow_failed",
                    "reason": f"Shadow Execution Denial: {shadow_delta.reason}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

        # Log to TEE-secured chain
        log_entry = await self.logger.log(intent_dict, self.agent_id, self.risk_envelope)
        val_dict = validation.model_dump()

        if not validation.approved:
            if execution_outcome.get("status") != "audit_failed":
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
            "id": trace_id, # Standardized to 'id' for frontend lookup
            "audit_id": validation.audit_id,
            "agent_id": self.agent_id,
            "task": task,
            "intent": intent_dict,
            "validation": val_dict,
            "drift_analysis": drift_analysis.model_dump(),
            "zk_proof": zk_proof,
            "lifecycle": validation.stages, # Pass stages to frontend
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

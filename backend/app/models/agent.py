from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any, List
from app.models.risk import RiskEnvelope

class AgentCreate(BaseModel):
    name: str
    goal: str
    risk_envelope: RiskEnvelope = RiskEnvelope()
    webhook_url: Optional[str] = None

class AgentResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    wallet_address: str
    collateral_amount: float
    collateral_remaining: float
    mission_intent: str
    risk_envelope: Dict[str, Any]
    status: str
    reputation: float
    total_executions: int
    successful_executions: int
    failed_executions: int
    registered_at: str
    chain_id: str

class AgentThinkRequest(BaseModel):
    agent_address: str
    mission_goal: str
    risk_envelope: Dict[str, Any]
    market_context: Dict[str, Any] = Field(default_factory=dict)
    history: List[Dict[str, Any]] = Field(default_factory=list)

class AgentRunRequest(BaseModel):
    task: str
    context: Optional[Dict[str, Any]] = None

class FreezeRequest(BaseModel):
    reason: str

class SlashRequest(BaseModel):
    reason: str
    amount: Optional[float] = None

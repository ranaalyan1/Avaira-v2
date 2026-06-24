from pydantic import BaseModel
from typing import Dict, Any

class ExecutionRequestCreate(BaseModel):
    agent_id: str
    action: str
    target_address: str = "0x0000000000000000000000000000000000000000"
    value: float = 0.0
    data: str = ""
    chain_id: str = "43113"

class IntentValidateRequest(BaseModel):
    intent: Dict[str, Any]
    risk_envelope: Dict[str, Any]

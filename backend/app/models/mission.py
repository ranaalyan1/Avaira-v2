from pydantic import BaseModel
from typing import Optional

class UnderwriterCreate(BaseModel):
    name: str
    wallet_address: str = ""
    capital_amount: float

class MissionCreate(BaseModel):
    agent_id: str
    description: str
    target_value: float
    duration_hours: int = 24
    risk_level: str = "medium"

class MissionStake(BaseModel):
    underwriter_id: str
    amount: float

class InsuranceRequest(BaseModel):
    agent_id: str
    underwriter_id: str
    coverage_amount: float

from pydantic import BaseModel
from typing import List, Optional, Dict

class RiskEnvelope(BaseModel):
    max_spend_usd: float = 0.0
    max_spend_per_action_usd: float = 0.0
    allowed_actions: List[str] = []
    blocked_actions: List[str] = []
    allowed_targets: List[str] = []
    max_concurrent_tasks: int = 1
    require_human_approval_above_usd: float = 100.0
    custom_rules: List[str] = []
    parent_allowed_actions: List[str] = []
    allowed_time_window: Optional[Dict[str, int]] = None

class AvairaConfig(BaseModel):
    api_key: str
    agent_id: str = ""        # auto-assigned on register()
    risk_envelope: RiskEnvelope
    api_url: str = "https://api.avaira.xyz"
    webhook_url: str = ""     # for slash notifications
    strict_mode: bool = True  # if False, log but don't block

ShieldConfig = AvairaConfig

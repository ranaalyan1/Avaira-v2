from pydantic import BaseModel
from typing import List

class RiskEnvelope(BaseModel):
    max_spend_usd: float = 0.0
    max_spend_per_action_usd: float = 0.0
    allowed_actions: List[str] = []
    blocked_actions: List[str] = []
    allowed_targets: List[str] = []
    max_concurrent_tasks: int = 1
    require_human_approval_above_usd: float = 100.0
    custom_rules: List[str] = []

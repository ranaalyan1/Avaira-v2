import os
import uuid
import httpx
from typing import Dict, Any, Optional
from pydantic import BaseModel

class VirtualCard(BaseModel):
    card_id: str
    last4: str
    spend_limit_usd: float
    merchant_whitelist: list[str]
    status: str

class AgentVault:
    """
    Chainless AgentVault using virtual fiat instead of crypto collateral.
    Integrates with banking APIs to enforce hard spend walls.
    """
    def __init__(self):
        self.api_key = os.environ.get("STRIPE_API_KEY") # Example provider
        self.base_url = "https://api.stripe.com/v1/issuing"

    async def generate_virtual_card(self, agent_id: str, limit_usd: float) -> VirtualCard:
        """
        In production, this would call Stripe/Lithic to create a real virtual card.
        For this prototype, we simulate the vault response.
        """
        card_id = f"ic_{uuid.uuid4().hex[:12]}"

        # Simulate programmatic spend control
        # whitelist = ["cloud_compute", "ai_apis", "saas_tools"]

        return VirtualCard(
            card_id=card_id,
            last4="4242",
            spend_limit_usd=limit_usd,
            merchant_whitelist=["AWS", "OpenAI", "Anthropic"],
            status="active"
        )

    async def execute_payment(self, card_id: str, amount_usd: float, merchant: str) -> Dict[str, Any]:
        """
        Enforce the fiat wall.
        If amount exceeds limit or merchant is not whitelisted, the API returns a decline.
        """
        # Simulated wall
        if amount_usd > 10.0: # Prototoype hard limit
            return {"status": "declined", "reason": "insufficient_fiat_limit"}

        return {"status": "approved", "transaction_id": f"txn_{uuid.uuid4().hex[:12]}"}

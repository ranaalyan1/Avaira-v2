import asyncio
from avaira_shield.client import AvairaClient
from avaira_shield.config import AvairaConfig, RiskEnvelope

async def main():
    # Budget set to $10
    envelope = RiskEnvelope(max_spend_usd=10.0, allowed_actions=["order_food"])
    config = AvairaConfig(api_key="deviant_key", risk_envelope=envelope, api_url="http://localhost:8001")
    client = AvairaClient(config)

    # 1. Approved action
    print("Agent trying to buy a $5 burger...")
    # Mocking that client.run usually derives intent.
    # In this example we simulate the intent deviation via logic.
    res1 = await client.run(task="Buy a $5 burger", execute_fn=lambda: "Ordered!")
    print(f"Status: {res1['status']}")

    # 2. Deviating action (Budget exceeded)
    print("\nAgent trying to buy a $500 steak...")
    # The real validator would catch the 'estimated_value' in the intent.
    # For the example, assume the execute_fn causes a failure or we check after.
    # Real SDK 'run' would call validator.

    # Let's mock a standalone validation for the example
    intent = {"action": "order_food", "estimated_value": 500.0}
    val = await client.validate(intent)

    if not val["approved"]:
        print(f"Avaira Blocked the deviation!")
        print(f"Reasoning: {val['compliance_reasoning']}")
        print("Reputation score will be penalized.")

if __name__ == "__main__":
    asyncio.run(main())

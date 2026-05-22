import asyncio
from avaira.client import AvairaClient
from avaira.config import AvairaConfig, RiskEnvelope

async def main():
    # 1. Configure
    envelope = RiskEnvelope(
        max_spend_usd=50.0,
        allowed_actions=["search", "summarize", "email"],
        require_human_approval_above_usd=100.0
    )
    config = AvairaConfig(
        api_key="init_key",
        risk_envelope=envelope,
        api_url="http://localhost:8000" # Local dev
    )
    client = AvairaClient(config)

    # 2. Register
    print("Registering agent...")
    agent_id = await client.register(name="ResearchBot", goal="Help with research")
    print(f"Agent registered: {agent_id}")

    # 3. Run approved task
    print("\nRunning approved task...")
    result = await client.run(
        task="Summarize the latest AI news",
        execute_fn=lambda: "AI is evolving fast!"
    )
    print(f"Result: {result['status']}")

    # 4. Run blocked task
    print("\nRunning task with unauthorized action...")
    result = await client.run(
        task="Delete all files in /etc",
        execute_fn=lambda: "I shouldn't do this"
    )
    print(f"Result: {result['status']}")
    if result['status'] == 'blocked':
        print(f"Violations: {result['violations']}")

    # 5. Get score
    score = await client.get_score()
    print(f"\nFinal Avaira Score: {score['score']} ({score['grade']})")

if __name__ == "__main__":
    asyncio.run(main())

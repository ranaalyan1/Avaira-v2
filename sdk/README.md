# Avaira SDK

Avaira gives your AI agents a trust score, an audit trail, and automatic consequences for bad behavior — in 3 lines of code.

## Quickstart

```python
from avaira import AvairaClient, AvairaConfig, RiskEnvelope

# 1. Define boundaries
envelope = RiskEnvelope(max_spend_usd=50.0, allowed_actions=["search"])
config = AvairaConfig(api_key="your_api_key", risk_envelope=envelope)
avaira = AvairaClient(config)

# 2. Wrap your agent
result = await avaira.run(
    task="Search for YC news",
    execute_fn=lambda: my_agent.run("Search for YC news")
)

print(result["status"]) # 'completed' or 'blocked'
```

## Why Avaira?

As AI agents become autonomous, they need more than just prompts. They need guardrails.

- **Deterministic Validation:** Ensure agents stay within budget and authorized actions.
- **Adversarial Audit:** Our LLM-powered validator detects prompt injection and scope creep.
- **Public Reputation:** Every agent builds a verifiable history. Higher scores = more trust.
- **Instant Consequences:** Violations can trigger immediate API suspension or financial penalties.

## Integrations

- LangChain: `protect_agent(executor, avaira)`
- CrewAI: `protect_crew(crew, avaira)`

## Advanced: On-chain Anchoring

For Web3 builders, Avaira can optionally anchor reputation scores to Avalanche, Ethereum, or Base, providing decentralized proof of an agent's history.

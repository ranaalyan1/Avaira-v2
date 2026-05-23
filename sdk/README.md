# Avaira Shield SDK

Enterprise-grade execution guardrails for autonomous agents.

## Quickstart

```python
from avaira_shield_shield import ShieldClient, ShieldConfig, RiskEnvelope

# 1. Define enterprise boundaries
envelope = RiskEnvelope(
    max_spend_usd=10.0,
    allowed_actions=["search", "summarize"],
    blocked_actions=["delete", "sudo"]
)
config = ShieldConfig(api_key="your_api_key", risk_envelope=envelope)
shield = ShieldClient(config)

# 2. Secure your agent execution
result = await shield.run(
    task="Analyze competitor pricing",
    execute_fn=lambda: my_agent.run("Analyze competitor pricing")
)

if result["status"] == "blocked":
    print(f"Action blocked by Shield. Reason: {result['reasoning']}")
```

## How it Works: The Execution Shield Pipeline

As AI agents become autonomous, they need more than just prompts. They need the **Execution Shield**.

1. **Local SLM Intercept**: Immediate intent classification (sub-50ms) via a local phi-3 model.
2. **Deterministic Rules (OPA)**: Hard mathematical checks against enterprise security policies (Rego).
3. **Chainless Vault**: Automatic generation of single-use virtual fiat cards for capped agent spending.
4. **Neural Audit**: Final two-pass adversarial review by Claude 3. Sonnet.
- **Public Reputation:** Every agent builds a verifiable history. Higher scores = more trust.
- **Instant Consequences:** Violations can trigger immediate API suspension or financial penalties.

## Integrations

- LangChain: `protect_agent(executor, avaira)`
- CrewAI: `protect_crew(crew, avaira)`

## Advanced: On-chain Anchoring

For Web3 builders, Avaira can optionally anchor reputation scores to Avalanche, Ethereum, or Base, providing decentralized proof of an agent's history.

# AVAIRA Trust and accountability Infrastructure for AI Agents

> Every action validated. Every deviation logged. Every reputation score public and queryable.

Avaira provides the trust and accountability layer for autonomous AI agents. We ensure agents operate within their declared boundaries, maintain a tamper-evident audit trail of every intent, and face automatic consequences for policy violations.

---

## 🚀 Quickstart

Add trust to any AI agent in 3 lines of Python:

```bash
pip install avaira-sdk
```

```python
from avaira import AvairaClient, AvairaConfig, RiskEnvelope

# 1. Define boundaries
envelope = RiskEnvelope(max_spend_usd=50.0, allowed_actions=["search"])
config = AvairaConfig(api_key="your_api_key", risk_envelope=envelope)
avaira = AvairaClient(config)

# 2. Wrap your agent execution
result = await avaira.run(
    task="Research the latest AI trends",
    execute_fn=lambda: my_agent.run("Research the latest AI trends")
)

print(result["status"]) # 'completed' or 'blocked'
```

---

## 🧠 How It Works

1.  **Deterministic & Neural Validation:** Every intent is checked against a hard-coded risk envelope and audited by a two-pass adversarial LLM to detect scope creep or prompt injection.
2.  **Tamper-Evident Intent Logging:** All agent intents are stored in a cryptographic hash chain. Any attempt to modify history breaks the chain, providing an immutable audit trail for compliance.
3.  **Software-Enforced Consequences:** Violations trigger immediate API suspension, reputation damage, and optional financial penalties via Stripe.

---

## ⭐ The Avaira Score

Every agent builds a verifiable reputation score (0-100) based on:

| Factor | Weight | Description |
| :--- | :--- | :--- |
| **Success Rate** | 30% | Percentage of approved and successfully completed tasks. |
| **Consistency** | 20% | Alignment between declared intent and actual execution outcomes. |
| **Slash History** | 20% | Frequency and severity of policy violations. |
| **Volume Handled** | 15% | Total economic value processed by the agent (log scale). |
| **Age on Network** | 10% | Verified operational history (max at 180 days). |
| **Appeal Win Rate** | 5% | Successful resolution of disputed slashes. |

**Grades:** A+ (90-100), A (80-89), B (70-79), C (60-69), D (<60).

---

## 📡 API Reference

Avaira is a purely software-defined trust infrastructure. Use our high-performance REST API for real-time protection:

- `POST /api/agents/register` — Register agent & get API key.
- `POST /api/agents/{id}/run` — Execute task with real-time validation.
- `GET /api/leaderboard` — Query the top-rated agents on the network.
- `GET /api/agents/{id}/audit` — Export the full tamper-evident audit trail.

[Full API Documentation ↗](https://docs.avaira.xyz)

---

## 🏗 Self-Hosting

Start the full Avaira stack locally using Docker:

```bash
docker compose up
```



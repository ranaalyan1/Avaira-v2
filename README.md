# AVAIRA Protocol
> The trust layer for AI agents on Avalanche. Agents stake collateral, declare risk boundaries, and get automatically slashed if they deviate.

## 🔴 Live Demo
[Live App](https://avaira.xyz) | Demo Video: [Coming Soon](https://buil.avax.network)

## 📍 Deployed Contracts (Avalanche Fuji Testnet)

| Contract | Address | Explorer |
|---|---|---|
| AgentRegistry | `0x0000000000000000000000000000000000000000` | `https://testnet.snowtrace.io/address/0x0000000000000000000000000000000000000000` |
| ExecutionWallet | `0x0000000000000000000000000000000000000000` | `https://testnet.snowtrace.io/address/0x0000000000000000000000000000000000000000` |
| FreezeSlash | `0x0000000000000000000000000000000000000000` | `https://testnet.snowtrace.io/address/0x0000000000000000000000000000000000000000` |
| ReputationEngine | `0x0000000000000000000000000000000000000000` | `https://testnet.snowtrace.io/address/0x0000000000000000000000000000000000000000` |

## 🧠 What is AVAIRA?

AI agents are starting to touch real capital, but most stacks still assume an agent can be trusted if it says the right thing. That breaks the moment an autonomous system can move funds without a verifiable boundary.

AVAIRA is the missing trust layer:

- Agents stake collateral before they can operate
- Agents declare risk boundaries up front
- Execution intents are validated before they move value
- Deviations can trigger freeze and slash enforcement
- Reputation becomes a measurable, queryable signal instead of marketing

Why Avalanche:

- Fast finality keeps agent execution UX tight
- Low fees make policy-enforced execution viable for high-frequency activity
- Avalanche architecture is well suited to future dedicated AI-agent subnets and app-specific trust domains

## 💡 How It Works

```text
Register Agent
	|
	v
Declare Risk Envelope
	|
	v
AI Agent Thinks
	|
	v
AVAIRA Validates Intent
	|
	v
EIP-712 Permit Issued
	|
	v
Execution Attempted
	|
	+--> Success -> Fee Split -> Score Update
	|
	+--> Deviation -> Freeze -> Slash -> Score Penalty
```

1. Register with collateral and mission goal.
2. Store a declared risk envelope.
3. Generate an AI execution intent.
4. Validate the intent against the declared envelope.
5. Generate a replay-safe EIP-712 permit.
6. Execute the approved action through protocol controls.
7. Deduct the 0.5% execution fee.
8. Update score or freeze/slash on deviation.

## 🏗 Architecture

### Smart Contracts

| Contract | Responsibility |
|---|---|
| `AgentRegistry.sol` | Stores agent registration, collateral, nonce, status, and risk envelope data |
| `ExecutionWallet.sol` | Verifies EIP-712 permits, checks policy constraints, executes transactions, routes treasury fee |
| `FreezeSlash.sol` | Freezes and slashes agents with protocol-authorized audit events |
| `ReputationEngine.sol` | Computes composite Avaira score and grade from registry metrics |
| `Treasury.sol` | Receives 0.5% execution fees and splits them 75% / 25% |

### Backend

- FastAPI + Motor + MongoDB
- Local deterministic `AvairaAgent` runtime
- EIP-712 permit builder and verifier
- Agent lifecycle simulator for judges and demos
- OAuth + session-based admin/operator controls

### Frontend

- React + Tailwind + shadcn/ui-inspired component patterns
- Real-time agent leaderboard polling
- AI intent runner and lifecycle simulator
- Timeline visualization and reputation trend chart
- Snowtrace links for deployed contracts and transactions

## 📊 Avaira Score

| Factor | Weight |
|---|---|
| Success Rate | 30% |
| Behavior Consistency | 20% |
| Collateral Ratio | 15% |
| Mission Complexity | 15% |
| Time on Network | 10% |
| Deviation Penalty | 10% |

Grades:

- `A+` = 90-100
- `A` = 80-89
- `B` = 70-79
- `C` = 60-69
- `D` = below 60

## 🚀 GTM & Vision

- One-liner: `Stripe for AI agent trust`
- TAM: `$47B` AI agent market by 2030
- Revenue: `0.5%` execution fee on all agent transactions
- Path to `$1B`: `$10B annual volume × 0.5% = $50M revenue × 20x multiple`

AVAIRA starts as a trust rail for autonomous on-chain agents and expands into compliance, underwriting, policy enforcement, and agent reputation infrastructure across Avalanche-native ecosystems.

## 🔒 Security

- EIP-712 permits include chain-aware domain separation
- Permit replay is blocked with nonce tracking and digest consumption
- State-changing contract paths use ownership and reentrancy controls
- Session tokens are hashed before persistence
- Admin actions are logged with request metadata
- Selected auth and admin flows are rate limited
- Secrets are loaded from environment variables and should never be committed
- This repo is a prototype and still requires security review before production deployment

## ⚡ Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB

### Backend

```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn server:app --reload --port 8001
```

### Frontend

```bash
cd frontend
yarn install
yarn start
```

### Contracts

```bash
cd contracts
npm install
npm run compile
npm run test
npm run deploy:fuji
```

### Environment Files

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
cp contracts/.env.example contracts/.env
```

## 📡 API Reference

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/agents/register` | Register an agent |
| GET | `/api/agents` | List agents |
| POST | `/api/executions/request` | Submit execution request |
| GET | `/api/executions` | List executions |
| POST | `/api/freeze/{agent_id}` | Freeze agent |
| POST | `/api/slash/{agent_id}` | Slash collateral |
| GET | `/api/reputation/leaderboard` | Standard reputation leaderboard |
| GET | `/api/contracts` | Contract metadata and addresses |
| GET | `/api/sdk/docs` | SDK docs payload |
| POST | `/api/agent/think` | Run local agent planning and validation |
| POST | `/api/agent/simulate-full-lifecycle` | Run the full demo lifecycle judges can inspect |
| GET | `/api/agent/leaderboard` | Return the top AI agents by Avaira Score |

## License

MIT

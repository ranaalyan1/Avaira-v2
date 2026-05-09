# AVAIRA — Trust & Execution Control for AI Agents on Avalanche

> Built for the Avalanche hackathon. Solo developer. Fully deployed on Fuji testnet.

As AI agents gain the ability to move funds and trigger on-chain transactions autonomously, there's no standard infrastructure to enforce *how* they should behave. AVAIRA is a demo of what that infrastructure could look like — an on-chain guardrail layer where agents stake collateral, declare risk boundaries, and get frozen or slashed when they deviate.

---

## 🔗 Try It

| | |
|---|---|
| **Live App** | https://avaira.xyz |

---

## 🧱 What Was Built

Four Solidity contracts deployed to Avalanche Fuji, a FastAPI backend, and a React frontend — all wired together and live.

### Contracts (Avalanche Fuji Testnet — Chain ID: 43113)

| Contract | Address | Explorer |
|---|---|---|
| AgentRegistry | `0xA143EDF764dA665d8c9F3a7A4529879C0071eaAD` | [View ↗](https://testnet.snowtrace.io/address/0xA143EDF764dA665d8c9F3a7A4529879C0071eaAD) |
| ExecutionWallet | `0x7e5293344fbd7eA3f65E0482887131C1a2236f24` | [View ↗](https://testnet.snowtrace.io/address/0x7e5293344fbd7eA3f65E0482887131C1a2236f24) |
| FreezeSlash | `0x6224e6330e55322eAd2f70f4b8E86155037842D5` | [View ↗](https://testnet.snowtrace.io/address/0x6224e6330e55322eAd2f70f4b8E86155037842D5) |
| ReputationEngine | `0x61ae129C166b51F8D9d9f997f785641426175388` | [View ↗](https://testnet.snowtrace.io/address/0x61ae129C166b51F8D9d9f997f785641426175388) |

### What the Demo Shows

- **Agent registration** — stake collateral and declare a mission intent on-chain
- **Risk envelope enforcement** — execution requests checked against declared boundaries before proceeding
- **Execution lifecycle tracking** — every request tracked from submission to completion with policy logs
- **Freeze & slash controls** — operators can freeze a misbehaving agent or slash its collateral, all on-chain
- **Reputation leaderboard** — agents accumulate scores from execution history, visible to all
- **Underwriter flows** — browse agent missions, evaluate risk, stake capital through the UI
- **Treasury & fee visibility** — protocol fee splits surfaced in the app
- **SDK docs & contract metadata** — available inside the app for developer inspection

---

## 🏗 How It's Built

| Layer | Stack |
|---|---|
| Smart Contracts | Solidity — Remix IDE — Avalanche Fuji |
| Backend | FastAPI — MongoDB — Python 3.11 |
| Frontend | React — CRACO — Tailwind CSS |

### Repo Structure

```
avaira/
├── backend/       # FastAPI, auth, execution logic, MongoDB
├── frontend/      # React dashboard, landing page, operations UI
├── contracts/     # Solidity contracts + deployment scripts
├── scripts/       # Smoke tests + integration scripts
└── deployments/   # Deployment artifacts per network
```

---

## 🚀 Run It Locally

### Prerequisites
- Python 3.11+
- Node.js 20+
- MongoDB (local or hosted)
- Yarn or npm

### 1. Environment setup

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
cp contracts/.env.example contracts/.env
```

Minimum values needed:

| File | Variable | Example |
|---|---|---|
| `backend/.env` | `MONGO_URL` | MongoDB connection string |
| `backend/.env` | `DB_NAME` | Database name |
| `backend/.env` | `PERMIT_SECRET` | Auth signing secret |
| `frontend/.env` | `REACT_APP_BACKEND_URL` | `http://localhost:8001` |

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn server:app --reload --port 8001
```

### 3. Frontend

```bash
cd frontend
yarn install
yarn start
```

### 4. Contracts (optional)

```bash
cd contracts
npm install
npm run compile
```

---

## 🧪 Tests

```bash
# Frontend
cd frontend && npm test -- --watchAll=false

# Contracts
cd contracts && npm test

# Backend
cd backend && python -m pytest ../tests/test_backend_units.py -q
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/agents/register` | Register agent with collateral |
| `GET` | `/api/agents` | List registered agents |
| `POST` | `/api/executions/request` | Submit execution request |
| `GET` | `/api/executions` | Query execution history |
| `POST` | `/api/freeze/{agent_id}` | Freeze agent |
| `POST` | `/api/slash/{agent_id}` | Slash agent collateral |
| `GET` | `/api/reputation/leaderboard` | Reputation leaderboard |
| `GET` | `/api/contracts` | Contract metadata |
| `GET` | `/api/sdk/docs` | SDK documentation |

---

## 👤 Builder

**Rana Alyan** — solo developer, AI-assisted build.

| Tool | Role |
|---|---|
| emergent.ai | Product & prototyping |
| Kimi | Research & iteration |
| Gemini | Code implementation |
| Claude | Architecture & writing |
| Remix IDE | Solidity workflows |

---

## License

MIT

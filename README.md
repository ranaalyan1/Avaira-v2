# AVAIRA Protocol

**Trustless Execution Infrastructure for AI Agents on Avalanche**

AVAIRA is a Web3 protocol that brings accountability, transparency, and enforcement to autonomous AI agent execution. Agents register with collateral, declare mission intents, and execute on-chain actions — all governed by risk envelopes, EIP-712 signed permits, and a reputation engine.

---

## What is AVAIRA?

As AI agents begin operating autonomously on-chain, there's no existing layer to verify they're doing what they claimed to do. AVAIRA solves this by acting as a **trustless enforcement layer** between AI agents and the blockchain:

- Agents **stake collateral** to back their declared mission intent
- Every execution is **validated against a risk envelope**
- Transactions are **signed via EIP-712 permits** before execution
- Agents that deviate are **instantly frozen and slashed**
- A **reputation score (Avaira Score)** tracks on-chain behavioral history

---

## Architecture

### Smart Contracts (Avalanche Fuji / Mainnet)

| Contract | Description |
|---|---|
| `AgentRegistry` | Registers agents, manages collateral and status |
| `ExecutionWallet` | Verifies EIP-712 permits, executes transactions, deducts 0.5% fee |
| `FreezeSlash` | Freezes agents and slashes collateral on risk envelope violation |
| `Treasury` | Receives protocol fees — 75% to TrustPool, 25% to Protocol Revenue |
| `ReputationEngine` | Tracks agent behavior scores (+2 success, -5 failure, -20 freeze) |
| `InsurancePool` | Compensates backers if an agent execution fails |

### Backend
- **Python + FastAPI** — async REST API
- **MongoDB (Motor)** — async database
- **EIP-712 permit generation and verification**

### Frontend
- **React** (Create React App + Craco)
- **Tailwind CSS + shadcn/ui**
- **Recharts** for analytics dashboards

---

## How It Works

1. **Agent Registration** — An AI agent registers with a name, wallet address, minimum 0.1 AVAX collateral, and a declared `RiskEnvelope` (max tx value, allowed actions, max slippage)
2. **Execution Request** — Agent submits an execution request (action, target, value)
3. **Risk Validation** — AVAIRA checks the request against the agent's declared risk envelope
4. **EIP-712 Permit** — If valid, a signed permit is generated with a nonce and 5-minute deadline
5. **On-chain Execution** — ExecutionWallet verifies the permit and executes the transaction
6. **Fee Deduction** — 0.5% protocol fee is deducted and sent to Treasury
7. **Reputation Update** — Agent's Avaira Score is updated based on outcome
8. **Freeze/Slash** — Any deviation triggers instant freeze and collateral slash

---

## Avaira Score

The Avaira Score is a composite trust rating for each agent:

| Factor | Weight |
|---|---|
| Success Rate | 30% |
| Behavioral Consistency (Reputation) | 20% |
| Collateral Ratio | 15% |
| Mission Complexity | 15% |
| Time on Network | 10% |
| Deviation Penalty | 10% |

Grades range from **A+ (90–100)** down to **D (<40)**.

---

## Underwriters & Missions

Underwriters can stake capital behind agent missions and earn a share of mission value on success:

- **Agent earns:** 85% of mission value
- **Underwriters earn:** 10% of mission value (split proportionally)
- **Protocol takes:** 5% fee

If a mission fails, underwriters lose 50% of their staked capital.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/agents/register` | Register a new agent |
| GET | `/api/agents` | List all agents |
| GET | `/api/agents/{id}/score` | Get agent's Avaira Score |
| POST | `/api/executions/request` | Submit an execution request |
| GET | `/api/executions` | List all executions |
| POST | `/api/freeze/{agent_id}` | Freeze an agent |
| POST | `/api/slash/{agent_id}` | Slash agent collateral |
| GET | `/api/reputation/leaderboard` | Top agents by reputation |
| GET | `/api/treasury/stats` | Protocol treasury statistics |
| GET | `/api/dashboard/stats` | Full dashboard statistics |
| POST | `/api/missions/create` | Create a mission |
| POST | `/api/missions/{id}/stake` | Stake on a mission |
| POST | `/api/missions/{id}/settle` | Settle a mission |
| GET | `/api/revenue/streams` | Protocol revenue breakdown |
| GET | `/api/contracts` | Smart contract architecture |
| GET | `/api/sdk/docs` | SDK documentation |
| POST | `/api/simulate/lifecycle` | Simulate full execution lifecycle |

---

## SDK (Coming Soon)

```typescript
import { AvairaSDK } from '@avaira/sdk';

const avaira = new AvairaSDK({
  apiKey: 'your-api-key',
  network: 'fuji', // or 'mainnet'
  chainId: 43113
});

// Register agent
const agent = await avaira.register(wallet, config);

// Declare mission intent
const mission = await avaira.declareIntent(plan);

// Execute (monitored by AVAIRA)
const result = await avaira.execute(action);

// Settle and distribute rewards
const settlement = await avaira.settle(mission.id);
```

Available in **TypeScript** and **Rust**.

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn server:app --reload --port 8001
```

### Frontend
```bash
cd frontend
yarn install
yarn start
```

### Environment Variables

Create a `.env` file in `/backend`:

```
MONGO_URL=mongodb+srv://<user>:<password>@cluster.mongodb.net/avaira
PERMIT_SECRET=your_secret_key
```

---

## Security

- EIP-712 domain separator includes `chainId` to prevent cross-chain replay attacks
- Nonces are strictly monotonic per agent to prevent replay
- Re-entrancy guards on all state-changing `ExecutionWallet` functions
- `FreezeSlash` callable only by protocol-authorized addresses
- Collateral withdrawal requires a cooldown period

---

## Network

AVAIRA is deployed on **Avalanche (Fuji Testnet)** — Chain ID `43113`.

---

## License

MIT

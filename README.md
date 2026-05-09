# AVAIRA — Trust & Execution Control for AI Agents on Avalanche

> The trust enforcement layer for autonomous AI agents. Stripe for AI agent trust.

AI agents that move real capital need a trust infrastructure — a place to stake collateral, declare what they're allowed to do, get each execution validated before it touches funds, and build a verifiable on-chain reputation. That's AVAIRA.

---

## 🔗 Links

| | |
|---|---|
| **Live App** | https://avaira.xyz |
| **API** | https://api.avaira.xyz |
| **Chain** | Avalanche C-Chain (mainnet 43114 / Fuji testnet 43113) |

---

## ✅ Feature Status

| Feature | Status |
|---|---|
| Agent registration + collateral staking | ✅ Live |
| EIP-712 execution permits + risk envelope enforcement | ✅ Live |
| Freeze & slash controls | ✅ Live |
| Avaira Score (A+ to D) + reputation engine | ✅ Live |
| Treasury (0.5% fee, 75/25 split) | ✅ Live |
| Underwriter marketplace | ✅ Live |
| Mission system (stake, settle, 85/10/5 split) | ✅ Live |
| Neural Intent Validator (LLM + rule layer) | ✅ Shipped |
| Yield-bearing collateral vault (cAVAX) | ✅ Shipped |
| Agent swarm trust graph | ✅ Shipped |
| TypeScript SDK (`@avaira/sdk`) | ✅ Shipped |
| Docker + one-command setup | ✅ Shipped |
| Mainnet deployment infrastructure | ✅ Ready |

---

## 🧱 Contracts

### Avalanche Fuji Testnet (Chain ID: 43113)

| Contract | Address | Explorer |
|---|---|---|
| AgentRegistry | `0x4D353326C548d9F8fb7499D2b465070Ee9C5b6B0` | [View ↗](https://testnet.snowtrace.io/address/0x4D353326C548d9F8fb7499D2b465070Ee9C5b6B0) |
| Treasury | `0x9B9595280A15D6Bb6e14C6343c1daE7f54F365b7` | [View ↗](https://testnet.snowtrace.io/address/0x9B9595280A15D6Bb6e14C6343c1daE7f54F365b7) |
| ExecutionWallet | `0x1765433Afe602F60Bd7a90f2E869349ecFae3Ed5` | [View ↗](https://testnet.snowtrace.io/address/0x1765433Afe602F60Bd7a90f2E869349ecFae3Ed5) |
| FreezeSlash | `0x32Cc01f1Fe3FADB3ABA8091eC287215815385D5F` | [View ↗](https://testnet.snowtrace.io/address/0x32Cc01f1Fe3FADB3ABA8091eC287215815385D5F) |
| ReputationEngine | `0x6B1e72dA9E4776a28568F9F9a1C4f1bc3aac0069` | [View ↗](https://testnet.snowtrace.io/address/0x6B1e72dA9E4776a28568F9F9a1C4f1bc3aac0069) |
| InsurancePool | `0xBF5B3805924e6C3950889042DC63413860722dF9` | [View ↗](https://testnet.snowtrace.io/address/0xBF5B3805924e6C3950889042DC63413860722dF9) |

### Avalanche C-Chain Mainnet (Chain ID: 43114)

> Mainnet deployment ready. Run `make deploy-mainnet-confirm` with a funded wallet.

---

## 🏗 Stack

| Layer | Technology |
|---|---|
| Smart Contracts | Solidity ^0.8.26, Hardhat, OpenZeppelin |
| Backend | FastAPI, Motor, MongoDB, Pydantic v2, Python 3.11 |
| Frontend | React 18, Tailwind CSS, shadcn/ui, Recharts |
| SDK | TypeScript, strict mode, ESM + CJS |
| Infra | Docker Compose, GitHub Actions, Railway, Vercel |

---

## 📁 Repo Structure

```
avaira-v2/
├── backend/               # FastAPI app — auth, execution, on-chain integration
│   ├── server.py          # 2100+ line API — 30+ endpoints
│   ├── ai_validator.py    # Neural intent validator (LLM + rule layer)
│   ├── agent_runtime.py   # AvairaAgent runtime + EIP-712 builder
│   └── chains.py          # Multi-chain config (mainnet, Fuji, L2s)
├── contracts/
│   ├── contracts/
│   │   ├── AgentRegistry.sol     # Registration, collateral, nonce, risk envelope
│   │   ├── ExecutionWallet.sol   # EIP-712 permit verify + execute + fee routing
│   │   ├── FreezeSlash.sol       # Freeze and slash enforcement
│   │   ├── ReputationEngine.sol  # Composite Avaira score (A+ to D)
│   │   ├── Treasury.sol          # 0.5% fee, 75/25 trust pool / revenue split
│   │   ├── InsurancePool.sol     # Mission backer compensation pool
│   │   ├── CollateralVault.sol   # Yield-bearing cAVAX collateral (NEW)
│   │   └── SwarmTrust.sol        # Weighted agent trust graph (NEW)
│   └── scripts/deploy.js         # Multi-network deploy with auto-verify
├── frontend/              # React dashboard — 12 pages, cyberpunk theme
├── sdk/                   # @avaira/sdk — TypeScript client (NEW)
│   └── src/
│       ├── client.ts      # AvairaClient
│       ├── agents.ts      # AgentService
│       ├── executions.ts  # ExecutionService
│       └── reputation.ts  # ReputationService
├── tests/
│   └── test_ai_validator.py  # 11 tests, all passing
├── docker-compose.yml     # Full stack in one command (NEW)
├── Makefile               # dev / test / deploy targets (NEW)
└── deployments/
    └── fuji.json          # Live Fuji addresses
```

---

## 🚀 Quick Start

### One command (Docker)

```bash
make setup   # installs deps, creates .env files
make dev     # starts mongo + backend + frontend
```

### Manual

```bash
# 1. Clone and set up env
git clone https://github.com/ranaalyan1/Avaira-v2.git && cd Avaira-v2
cp backend/.env.example backend/.env
cp contracts/.env.example contracts/.env

# 2. Backend
cd backend && pip install -r requirements.txt
uvicorn server:app --reload --port 8001

# 3. Frontend
cd frontend && yarn install && yarn start

# 4. Contracts (compile + test)
cd contracts && npm install && npm test
```

---

## 🤖 TypeScript SDK

```bash
npm install @avaira/sdk
```

```typescript
import { AvairaClient } from '@avaira/sdk';

const avaira = new AvairaClient({ network: 'mainnet' });

// Register an agent
const agent = await avaira.agents.register({
  missionGoal: 'DeFi arbitrage within declared parameters',
  collateral: 1_000_000_000_000_000_000n,  // 1 AVAX
  riskEnvelope: {
    maxTransactionValue: 10_000_000_000_000_000_000n,
    allowedTokens: ['AVAX', 'USDC', 'WAVAX'],
    allowedProtocols: ['traderjoe', 'pangolin'],
    maxSlippageBps: 200,
    maxExecutionsPerHour: 10,
  },
});

// Validate an intent before executing
const validation = await avaira.executions.validate({
  agentId: agent.id,
  intent: { action: 'SWAP', tokenIn: 'AVAX', tokenOut: 'USDC', amountIn: 500000000000000000n },
});
console.log(validation.recommendation); // APPROVE | REVIEW | REJECT

// Get reputation score
const score = await avaira.reputation.getScore(agent.id);
console.log(`${score.grade} (${score.raw}/100)`);
```

---

## 🧠 Neural Intent Validator

Two-layer validation on every execution intent:

- **Semantic layer** — LLM evaluates whether the intent matches the *spirit* of the declared risk envelope. Prompt injection resistant.
- **Rule layer** — deterministic checks: value limits, allowed actions, slippage bounds.
- **Fallback** — if LLM is unavailable, degrades gracefully to rule-only. Never blocks execution due to an LLM outage.

```bash
POST /api/validate/intent
{ "agent_id": "...", "intent": { "action": "swap", "value": 0.5, ... } }
```

---

## 🚢 Deploy to Mainnet

```bash
# 1. Add your funded wallet key to contracts/.env
echo "DEPLOYER_PRIVATE_KEY=0x..." >> contracts/.env
echo "SNOWTRACE_API_KEY=..." >> contracts/.env

# 2. Deploy all 6 contracts + wire + verify
make deploy-mainnet-confirm
```

Deployment is idempotent — safe to re-run. Addresses saved to `deployments/mainnet.json`.

---

## 🧪 Tests

```bash
make test
# or individually:
cd contracts && npm test               # Hardhat — contract state transitions
python3 -m pytest tests/ -v           # Backend — 11 passing
cd frontend && yarn test --watchAll=false
```

---

## 📡 Key API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/agents/register` | Register agent with collateral |
| `POST` | `/api/validate/intent` | Neural intent validation |
| `POST` | `/api/executions/request` | Submit execution |
| `POST` | `/api/freeze/{agent_id}` | Freeze agent |
| `POST` | `/api/slash/{agent_id}` | Slash collateral |
| `GET` | `/api/reputation/leaderboard` | Score leaderboard |
| `GET` | `/api/treasury/stats` | Fee + revenue stats |
| `GET` | `/api/health` | Service health check |

---

## 👤 Builder

**Muhammad Alyan Ashraf** — solo developer, AI-assisted build.

| Tool | Role |
|---|---|
| Claude (AESZNM) | Architecture, contracts, backend, SDK |
| emergent.ai | Product & prototyping |
| Kimi | Research & iteration |
| Gemini | Code implementation |
| Remix IDE | Solidity workflows |

---

## License

MIT

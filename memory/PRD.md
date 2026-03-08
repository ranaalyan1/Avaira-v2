# AVAIRA Protocol - PRD

## Problem Statement
Build AVAIRA - the Moody's + DTCC + Lloyd's of London for the AI Agent Economy. A production-grade decentralized AI execution control protocol built as an Avalanche L1. Rates, clears, and insures every AI agent transaction on-chain.

## Architecture
- **Frontend**: React + Tailwind + Shadcn/UI + Recharts (dark cyberpunk theme)
- **Backend**: FastAPI + MongoDB (simulated blockchain interactions)
- **Database**: MongoDB collections: agents, executions, freeze_events, treasury_transactions, reputation_history, underwriters, missions, revenue_events

## Core Requirements
1. **AgentRegistry** - register, stake collateral, manage status, Avaira Score (AAA-D)
2. **ExecutionWallet** - EIP-712 permit signing/verification, 0.5% fee
3. **FreezeSlash** - instant freeze on deviation, collateral slashing (50%)
4. **Treasury** - 4 revenue streams (tx fees, underwriting spread, slashing, data)
5. **ReputationEngine** - multi-factor scoring mapped to AAA-D grades
6. **Underwriter Marketplace** - human underwriters stake capital, 85/10/5 fee split
7. **Mission System** - agents declare missions, underwriters stake, settle success/fail
8. **SDK Documentation** - 4-function TypeScript/Rust SDK reference
9. **Landing Page** - marketing page with vision, moats, revenue model

## User Personas
- **Protocol Operators**: Monitor agents, manage freeze/slash, view treasury, revenue analytics
- **Agent Developers**: Register agents, submit executions, track Avaira Score
- **Human Underwriters**: Stake capital, underwrite missions, earn yield
- **Enterprise Clients**: Evaluate agent ratings, trust Avaira Scores

## What's Been Implemented (March 8, 2026)

### Phase 1 - Core MVP
- Full backend API with 18+ endpoints
- Simulated EIP-712 permit signing
- Risk envelope validation with auto-freeze
- Full execution lifecycle
- 7-page dashboard with cyberpunk theme

### Phase 2 - Full Vision Expansion  
- Avaira Score Engine (AAA to D, multi-factor: success rate 30%, behavioral consistency 20%, collateral ratio 15%, mission complexity 15%, time on network 10%, deviation penalty 10%)
- Human Underwriter system (register, deposit capital, stake on missions)
- Mission marketplace (create missions, stake, settle success/fail, 85/10/5 split)
- 4-stream revenue dashboard (Transaction Fees, Underwriting Spread, Slashing Revenue, Data & Analytics)
- SDK Documentation page (TypeScript + Rust, 4 functions: register, declareIntent, execute, settle)
- Marketing landing page (hero, 3 pillars, 5 moats, revenue architecture, SDK preview, CTA)
- Updated navigation (9 items: Dashboard, Agents, Execution, Underwriters, Freeze, Treasury, Reputation, SDK, Contracts)
- Agent cards show Avaira Score badges (AAA-D)

## P0/P1/P2 Features Remaining

### P0 - None remaining

### P1 (Important)
- WebSocket real-time updates for execution monitoring
- Agent detail page with full execution/score history
- Multi-chain selector (Ethereum, Polygon, Arbitrum)
- Subscription tier management (Free/Growth/Enterprise payments)
- Insurance Pool management UI

### P2 (Nice to Have)
- Actual Avalanche Fuji testnet integration
- Solidity smart contract file generation
- Wallet-based authentication (MetaMask/WalletConnect)
- Export functionality for treasury/compliance reports
- Mobile responsive optimization
- Rate limiting and advanced security
- Data & Analytics API (paid query endpoint)

## Revenue Model
1. Agent Registration & Rating: SaaS tiers (Free/$200mo/$2000mo)
2. Underwriting Spread: 5% protocol fee on settled missions
3. Slashing Revenue: 20% of slashed collateral
4. Data & Analytics: API queries + institutional subscriptions

## Next Tasks
1. WebSocket real-time execution monitoring
2. Subscription tier payment integration
3. Agent detail/profile page
4. Multi-chain configuration
5. Actual Solidity contract file generation

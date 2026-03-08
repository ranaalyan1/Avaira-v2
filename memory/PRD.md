# AVAIRA Protocol - PRD

## Problem Statement
Build AVAIRA - a production-grade decentralized AI execution control protocol. It's an enforcement middleware that sits BETWEEN AI agents and blockchain execution. Agents must request execution through AVAIRA, which validates risk envelopes, signs EIP-712 permits, and only then allows on-chain execution.

## Architecture
- **Frontend**: React + Tailwind + Shadcn/UI + Recharts (dark cyberpunk theme)
- **Backend**: FastAPI + MongoDB (simulated blockchain interactions)
- **Database**: MongoDB with collections: agents, executions, freeze_events, treasury_transactions, reputation_history

## Core Requirements
1. AgentRegistry - register, stake collateral, manage agent status, reputation tracking
2. ExecutionWallet - EIP-712 permit signing/verification, transaction execution, 0.5% fee
3. FreezeSlash - instant agent freeze on deviation, collateral slashing (50% rate)
4. Treasury - fee splitting (75% TrustPool / 25% Protocol Revenue)
5. ReputationEngine - scoring (+2 success, -5 failure, -20 freeze, -10 slash)
6. InsurancePool - backer compensation on failure
7. Smart Contract Architecture - detailed viewer with state vars, functions, events, security

## User Personas
- **Protocol Operators**: Monitor agent activity, manage freeze/slash, view treasury
- **Agent Developers**: Register agents, submit execution requests, track reputation
- **Security Engineers**: Review contract architecture, attack surfaces, gas considerations

## What's Been Implemented (March 8, 2026)
- Full backend API with 18 endpoints (agents, executions, freeze/slash, treasury, reputation, dashboard, contracts, simulation)
- Simulated EIP-712 permit signing with HMAC-SHA256
- Risk envelope validation with automatic freeze on deviation
- Full execution lifecycle (request → validate → sign → verify → execute → fee → reputation)
- 7-page frontend dashboard with cyberpunk theme (Rajdhani + JetBrains Mono)
- Dashboard with real-time stats, activity feed, distribution charts, treasury split
- Agent Registry with ID card-style agent cards and registration dialog
- Execution Flow with timeline visualization and EIP-712 permit viewer
- Freeze/Slash page with frozen agent monitoring and event log
- Treasury analytics with fee split pie chart and bar chart history
- Reputation leaderboard with score distribution chart
- Smart Contract architecture viewer with expandable cards (6 contracts)
- Full lifecycle simulation endpoint for demo

## P0/P1/P2 Features Remaining

### P0 (Critical)
- None remaining for MVP

### P1 (Important)
- WebSocket real-time updates for execution monitoring
- Agent detail page with full execution history
- Export functionality for treasury reports
- Multi-chain selector (Ethereum, Polygon, Arbitrum)
- Insurance Pool management UI

### P2 (Nice to Have)
- Actual Avalanche Fuji testnet integration
- Solidity smart contract file generation
- Agent SDK documentation page
- Dark/light theme toggle
- Mobile responsive optimization
- Rate limiting on execution endpoints
- Agent authentication (wallet-based)

## Next Tasks
1. Add WebSocket for real-time execution monitoring
2. Build detailed agent profile page
3. Implement multi-chain configuration
4. Add export/download for treasury reports
5. Create actual Solidity contract files

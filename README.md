# AVAIRA

Build-focused monorepo for AVAIRA protocol components.

## Project Structure

```text
backend/     FastAPI API and protocol backend
frontend/    React app (CRACO)
contracts/   Hardhat contracts and deployment scripts
scripts/     Integration/smoke scripts
```

## Requirements

- Python 3.11+
- Node.js 20+ (recommended for CI parity)
- npm or yarn
- MongoDB (local or hosted)

## Environment Setup

Create environment files from the examples:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
cp contracts/.env.example contracts/.env
```

Minimum required backend values:

- `MONGO_URL`
- `DB_NAME`
- `PERMIT_SECRET`

Frontend should set:

- `REACT_APP_BACKEND_URL` (example: `http://localhost:8001`)

## Local Development

### 1. Backend

```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn server:app --reload --port 8001
```

### 2. Frontend

```bash
cd frontend
yarn install
yarn start
```

### 3. Contracts (optional for UI-only dev)

```bash
cd contracts
npm install
npm run compile
```

## Build Commands

### Frontend production build

```bash
cd frontend
npm run build
```

### Frontend tests

```bash
cd frontend
npm test -- --watchAll=false
```

### Contract build and tests

```bash
cd contracts
npm run compile
npm test
```

### Backend tests

```bash
cd backend
python -m pytest ../tests/test_backend_units.py -q
```

## Deployment Notes

- GitHub Actions workflow is in `.github/workflows/deploy.yml`.
- Vercel config is in `vercel.json` (root).
- Frontend is built from `frontend/package.json`.
- API function entrypoint for Vercel is `backend/api/index.py`.

## Deployed Contracts (Avalanche Fuji Testnet)

| Contract | Address | Explorer |
| --- | --- | --- |
| AgentRegistry | `0xA143EDF764dA665d8c9F3a7A4529879C0071eaAD` | [View on Snowtrace](https://testnet.snowtrace.io/address/0xA143EDF764dA665d8c9F3a7A4529879C0071eaAD) |
| ExecutionWallet | `0x7e5293344fbd7eA3f65E0482887131C1a2236f24` | [View on Snowtrace](https://testnet.snowtrace.io/address/0x7e5293344fbd7eA3f65E0482887131C1a2236f24) |
| FreezeSlash | `0x6224e6330e55322eAd2f70f4b8E86155037842D5` | [View on Snowtrace](https://testnet.snowtrace.io/address/0x6224e6330e55322eAd2f70f4b8E86155037842D5) |
| ReputationEngine | `0x61ae129C166b51F8D9d9f997f785641426175388` | [View on Snowtrace](https://testnet.snowtrace.io/address/0x61ae129C166b51F8D9d9f997f785641426175388) |

## License

MIT

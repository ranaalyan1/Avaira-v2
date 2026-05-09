.PHONY: dev dev-local test setup deploy-fuji deploy-mainnet clean lint

dev:
	docker-compose up

dev-local:
	docker-compose --profile local up

test:
	@echo "→ Contract tests..."
	cd contracts && npm test
	@echo "→ Backend tests..."
	cd backend && pytest tests/ -q --tb=short 2>/dev/null || pytest ../tests/ -q --tb=short
	@echo "→ Frontend tests..."
	cd frontend && yarn test --passWithNoTests --watchAll=false

setup:
	@echo "Setting up AVAIRA development environment..."
	@command -v node  >/dev/null || (echo "ERROR: Node.js 18+ required" && exit 1)
	@command -v python3 >/dev/null || (echo "ERROR: Python 3.11+ required" && exit 1)
	@command -v docker >/dev/null || (echo "ERROR: Docker required" && exit 1)
	@cp -n contracts/.env.example contracts/.env 2>/dev/null && echo "Created contracts/.env" || echo "contracts/.env exists"
	@cp -n backend/.env.example backend/.env 2>/dev/null && echo "Created backend/.env" || echo "backend/.env exists"
	@cp -n frontend/.env.example frontend/.env 2>/dev/null && echo "Created frontend/.env" || true
	cd contracts && npm install
	cd backend && pip install -r requirements.txt -q
	cd frontend && yarn install --silent
	@echo ""
	@echo "✓ Setup complete. Edit .env files, then run: make dev"

deploy-fuji:
	@echo "→ Deploying to Avalanche Fuji testnet..."
	cd contracts && npm run deploy:fuji

deploy-mainnet:
	@echo ""
	@echo "  ⚠️  MAINNET DEPLOYMENT"
	@echo "  This will deploy to Avalanche C-Chain with real AVAX."
	@echo "  Run: make deploy-mainnet-confirm"
	@echo ""

deploy-mainnet-confirm:
	@echo "→ Deploying to Avalanche C-Chain mainnet..."
	cd contracts && npm run deploy:mainnet

verify-fuji:
	cd contracts && npm run verify:fuji

verify-mainnet:
	cd contracts && npm run verify:mainnet

lint:
	cd backend && black --check . && python -m flake8 . --max-line-length=120 --exclude=__pycache__
	cd frontend && yarn lint --max-warnings 0

clean:
	docker-compose down -v
	cd contracts && rm -rf artifacts cache
	cd backend && find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	cd frontend && rm -rf build

logs:
	docker-compose logs -f backend

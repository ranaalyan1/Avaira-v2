from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ServerSelectionTimeoutError
import logging

from .config import get_settings
from .containers import container
from .api import auth, agents, leaderboard, audit, health, marketplace, executions, info, dashboard, simulation, legacy

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

settings = get_settings()

async def ensure_indexes(db):
    # Core lookup indexes to avoid collection scans in high-frequency APIs.
    await db.agents.create_index("id", unique=True)
    await db.agents.create_index([("status", 1), ("registered_at", -1)])
    await db.agents.create_index("wallet_address")
    await db.executions.create_index("id", unique=True)
    await db.executions.create_index([("agent_id", 1), ("created_at", -1)])
    await db.executions.create_index([("status", 1), ("created_at", -1)])
    await db.freeze_events.create_index([("agent_id", 1), ("timestamp", -1)])
    await db.reputation_history.create_index([("agent_id", 1), ("timestamp", -1)])
    await db.treasury_transactions.create_index("execution_id")
    await db.treasury_transactions.create_index("timestamp")
    await db.missions.create_index("id", unique=True)
    await db.missions.create_index([("status", 1), ("created_at", -1)])
    await db.underwriters.create_index("id", unique=True)
    await db.user_sessions.create_index("session_token_hash")
    await db.user_sessions.create_index("expires_at")
    await db.users.create_index("email", unique=True)
    await db.permit_nonces.create_index("agent_id", unique=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await ensure_indexes(container.db)
        app.state.database_ready = True
    except ServerSelectionTimeoutError as exc:
        app.state.database_ready = False
        logger.warning(f"WARNING: MongoDB unavailable. Starting in degraded mode. {exc}")
    yield
    container.client.close()

app = FastAPI(title="AVAIRA Protocol API", lifespan=lifespan)

# Add Middleware
cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(',') if origin.strip()]
allow_credentials = '*' not in cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_credentials=allow_credentials,
    allow_origins=cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
# NOTE: To match exactly the original server.py OpenAPI schema, we must avoid tags.
api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(agents.router)
api_router.include_router(leaderboard.router)
api_router.include_router(audit.router)
api_router.include_router(marketplace.router)
api_router.include_router(executions.router)
api_router.include_router(info.router)
api_router.include_router(dashboard.router)
api_router.include_router(simulation.router)
api_router.include_router(legacy.router)

app.include_router(api_router)

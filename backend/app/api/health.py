from fastapi import APIRouter, Depends
from app.dependencies import get_db, get_reputation_engine
from app.config import get_settings

router = APIRouter(tags=[])
settings = get_settings()

# Routes moved to legacy.py to match exact structure and operation IDs

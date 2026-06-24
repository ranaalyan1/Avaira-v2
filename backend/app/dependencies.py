from fastapi import Request, HTTPException, Depends
from app.containers import container
from app.config import get_settings
import hashlib

def get_db():
    return container.db

def get_intent_logger():
    return container.intent_logger

def get_avaira_validator():
    return container.avaira_validator

def get_slash_engine():
    return container.slash_engine

def get_reputation_engine():
    return container.reputation_engine

def get_agent_vault():
    return container.agent_vault

def get_avaira_sentinel():
    return container.avaira_sentinel

def get_zk_vault():
    return container.zk_vault

def get_ape_engine():
    return container.ape_engine

def get_tee_identity_manager():
    return container.tee_identity_manager

def get_trust_marketplace():
    return container.trust_marketplace

async def get_current_user(request: Request, db):
    token = request.cookies.get("session_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    if not token:
        raise HTTPException(401, "Not authenticated")

    from app.api.auth import _hash_session_token
    session = await db.user_sessions.find_one({"session_token_hash": _hash_session_token(token)}, {"_id": 0})
    if not session:
        raise HTTPException(401, "Invalid session")

    from datetime import datetime, timezone
    expires_at = session["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(401, "Session expired")

    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(401, "User not found")

    settings = get_settings()
    admin_emails = {email.strip().lower() for email in settings.ADMIN_EMAILS.split(",") if email.strip()}
    user["is_admin"] = (user.get("email", "").lower() in admin_emails)
    return user

async def require_authenticated_user(request: Request, db=Depends(get_db)):
    return await get_current_user(request, db)

async def require_admin_user(request: Request, db=Depends(get_db)):
    user = await get_current_user(request, db)
    email = (user.get("email") or "").lower()
    settings = get_settings()
    admin_emails = {email.strip().lower() for email in settings.ADMIN_EMAILS.split(",") if email.strip()}
    if email not in admin_emails:
        raise HTTPException(403, "Admin privileges required")
    return user

async def get_current_agent(request: Request):
    api_key = request.headers.get("X-Avaira-API-Key")
    if not api_key:
        raise HTTPException(401, "Missing X-Avaira-API-Key")

    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    agent = await container.db.agents.find_one({"api_key_hash": api_key_hash})

    if not agent:
        raise HTTPException(401, "Invalid API Key")
    if agent.get("status") == "frozen":
        raise HTTPException(403, "Agent is frozen due to a policy violation")
    return agent

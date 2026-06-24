from fastapi import APIRouter, HTTPException, Request, Depends
from starlette.responses import RedirectResponse, JSONResponse
import secrets
import hmac
import hashlib
import json
import time
import httpx
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from urllib.parse import urlencode, urlparse

from app.config import get_settings
from app.dependencies import get_db

router = APIRouter(prefix="/auth", tags=[])
settings = get_settings()

def _base64url_encode(data: bytes) -> str:
    import base64
    return base64.urlsafe_b64encode(data).decode().rstrip("=")

def _base64url_decode(data: str) -> bytes:
    import base64
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)

def _is_allowed_redirect(target: str) -> bool:
    parsed = urlparse(target)
    if parsed.scheme not in {"http", "https"}:
        return False
    origin = f"{parsed.scheme}://{parsed.netloc}"
    allowed_origins = {o.strip() for o in settings.ALLOWED_REDIRECT_ORIGINS.split(",") if o.strip()}
    return origin in allowed_origins

def _resolve_post_login_redirect(redirect: Optional[str]) -> str:
    target = (redirect or settings.DEFAULT_POST_LOGIN_REDIRECT).strip()
    if not _is_allowed_redirect(target):
        raise HTTPException(400, "Invalid redirect target")
    return target

def _build_oauth_state(provider: str, redirect: str, code_verifier: Optional[str] = None) -> str:
    payload: Dict[str, Any] = {
        "provider": provider,
        "redirect": redirect,
        "exp": int(time.time()) + 600,
        "nonce": secrets.token_urlsafe(12),
    }
    if code_verifier:
        payload["cv"] = code_verifier
    payload_raw = json.dumps(payload, separators=(",", ":")).encode()
    payload_b64 = _base64url_encode(payload_raw)
    sig = hmac.new(settings.PERMIT_SECRET.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{sig}"

def _parse_oauth_state(state: str) -> Dict[str, Any]:
    try:
        payload_b64, sig = state.split(".", 1)
    except ValueError as exc:
        raise HTTPException(400, "Invalid OAuth state") from exc
    expected_sig = hmac.new(settings.PERMIT_SECRET.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected_sig):
        raise HTTPException(400, "Invalid OAuth state signature")
    try:
        payload = json.loads(_base64url_decode(payload_b64).decode())
    except Exception as exc:
        raise HTTPException(400, "Invalid OAuth state payload") from exc
    if int(payload.get("exp", 0)) < int(time.time()):
        raise HTTPException(400, "OAuth state expired")
    return payload

def _pkce_challenge(code_verifier: str) -> str:
    digest = hashlib.sha256(code_verifier.encode()).digest()
    return _base64url_encode(digest)

def _hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

async def _create_local_session(db, email: str, name: str, picture: str) -> Dict[str, str]:
    import uuid
    existing = await db.users.find_one({"email": email}, {"_id": 0})
    if existing:
        user_id = existing["user_id"]
        await db.users.update_one({"email": email}, {"$set": {"name": name, "picture": picture}})
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        await db.users.insert_one({
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

    session_token = secrets.token_urlsafe(48)
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token_hash": _hash_session_token(session_token),
        "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=settings.SESSION_MAX_AGE_SECONDS)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"user_id": user_id, "session_token": session_token, "email": email, "name": name, "picture": picture}

def _set_session_cookie(resp: RedirectResponse, session_token: str):
    cookie_secure = settings.COOKIE_SECURE
    cookie_samesite = "none" if cookie_secure else "lax"
    resp.set_cookie(
        "session_token",
        session_token,
        httponly=True,
        secure=cookie_secure,
        samesite=cookie_samesite,
        path="/",
        max_age=settings.SESSION_MAX_AGE_SECONDS,
    )

def _require_google_oauth_config():
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET or not settings.GOOGLE_REDIRECT_URI:
        raise HTTPException(503, "Google OAuth is not configured")

def _require_x_oauth_config():
    if not settings.X_CLIENT_ID or not settings.X_CLIENT_SECRET or not settings.X_REDIRECT_URI:
        raise HTTPException(503, "X OAuth is not configured")

@router.get("/google/login")
async def auth_google_login(redirect: Optional[str] = None):
    _require_google_oauth_config()
    target_redirect = _resolve_post_login_redirect(redirect)
    state = _build_oauth_state("google", target_redirect)
    params = urlencode({
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    })
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{params}")

@router.get("/google/callback")
async def auth_google_callback(code: str, state: str, db=Depends(get_db)):
    _require_google_oauth_config()
    parsed_state = _parse_oauth_state(state)
    if parsed_state.get("provider") != "google":
        raise HTTPException(400, "OAuth provider mismatch")

    async with httpx.AsyncClient(timeout=20) as http_client:
        token_resp = await http_client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(401, "Google token exchange failed")
        access_token = token_resp.json().get("access_token", "")
        if not access_token:
            raise HTTPException(401, "Google access token missing")

        user_resp = await http_client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_resp.status_code != 200:
            raise HTTPException(401, "Google user profile fetch failed")
        user_data = user_resp.json()

    email = user_data.get("email", "")
    name = user_data.get("name", "Google User")
    picture = user_data.get("picture", "")
    if not email:
        raise HTTPException(401, "Google account email is required")

    session = await _create_local_session(db, email=email, name=name, picture=picture)
    resp = RedirectResponse(parsed_state["redirect"])
    _set_session_cookie(resp, session["session_token"])
    return resp

@router.get("/x/login")
async def auth_x_login(redirect: Optional[str] = None):
    _require_x_oauth_config()
    target_redirect = _resolve_post_login_redirect(redirect)
    code_verifier = secrets.token_urlsafe(64)
    state = _build_oauth_state("x", target_redirect, code_verifier=code_verifier)
    params = urlencode({
        "response_type": "code",
        "client_id": settings.X_CLIENT_ID,
        "redirect_uri": settings.X_REDIRECT_URI,
        "scope": "tweet.read users.read offline.access",
        "state": state,
        "code_challenge": _pkce_challenge(code_verifier),
        "code_challenge_method": "S256",
    })
    return RedirectResponse(f"https://twitter.com/i/oauth2/authorize?{params}")

@router.get("/x/callback")
async def auth_x_callback(code: str, state: str, db=Depends(get_db)):
    _require_x_oauth_config()
    parsed_state = _parse_oauth_state(state)
    if parsed_state.get("provider") != "x":
        raise HTTPException(400, "OAuth provider mismatch")
    code_verifier = parsed_state.get("cv", "")
    if not code_verifier:
        raise HTTPException(400, "Missing PKCE verifier")

    async with httpx.AsyncClient(timeout=20) as http_client:
        token_resp = await http_client.post(
            "https://api.twitter.com/2/oauth2/token",
            data={
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.X_REDIRECT_URI,
                "code_verifier": code_verifier,
                "client_id": settings.X_CLIENT_ID,
            },
            auth=(settings.X_CLIENT_ID, settings.X_CLIENT_SECRET),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if token_resp.status_code != 200:
            raise HTTPException(401, "X token exchange failed")
        access_token = token_resp.json().get("access_token", "")
        if not access_token:
            raise HTTPException(401, "X access token missing")

        user_resp = await http_client.get(
            "https://api.twitter.com/2/users/me?user.fields=profile_image_url,name,username",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_resp.status_code != 200:
            raise HTTPException(401, "X profile fetch failed")
        x_data = user_resp.json().get("data", {})

    x_user_id = x_data.get("id", "")
    username = x_data.get("username", "")
    if not x_user_id or not username:
        raise HTTPException(401, "X profile is incomplete")

    email = f"x_{x_user_id}@x.avaira.local"
    name = x_data.get("name") or username
    picture = x_data.get("profile_image_url", "")
    session = await _create_local_session(db, email=email, name=name, picture=picture)
    resp = RedirectResponse(parsed_state["redirect"])
    _set_session_cookie(resp, session["session_token"])
    return resp

@router.get("/me", operation_id="get_current_user_api_auth_me_get", summary="Get Current User")
async def get_current_user_route(request: Request, db=Depends(get_db)):
    from app.dependencies import get_current_user
    return await get_current_user(request, db)

@router.post("/logout")
async def logout(request: Request, db=Depends(get_db)):
    token = request.cookies.get("session_token")
    if token:
        await db.user_sessions.delete_one({"session_token_hash": _hash_session_token(token)})
    resp = JSONResponse({"message": "Logged out"})
    resp.delete_cookie("session_token", path="/")
    return resp

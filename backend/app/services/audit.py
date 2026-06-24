import uuid
from datetime import datetime, timezone
from app.constants import TRUST_POOL_SHARE, PROTOCOL_REVENUE_SHARE

async def record_treasury_transaction(db, execution_id: str, total_fee: float):
    trust_pool = round(total_fee * TRUST_POOL_SHARE, 6)
    protocol_revenue = round(total_fee * PROTOCOL_REVENUE_SHARE, 6)
    tx = {
        "id": str(uuid.uuid4()),
        "execution_id": execution_id,
        "total_fee": round(total_fee, 6),
        "trust_pool_share": trust_pool,
        "protocol_revenue_share": protocol_revenue,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.treasury_transactions.insert_one(tx)

async def record_admin_audit(db, action: str, admin_user, request, payload):
    entry = {
        "id": str(uuid.uuid4()),
        "action": action,
        "admin_user_id": admin_user.get("user_id"),
        "admin_email": admin_user.get("email"),
        "ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent", ""),
        "payload": payload,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.admin_audit_log.insert_one(entry)

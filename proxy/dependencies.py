"""
FastAPI dependency: API key authentication.

Raw keys are never stored — only their SHA-256 hashes are in the api_keys table.
This means a full DB dump still reveals no usable credentials.

Usage in a route:
    @router.get("/v1/traces")
    async def list_traces(key_id: str = Depends(verify_api_key), ...):
        ...
"""
import hashlib
from datetime import datetime, timezone

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import ApiKey


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def verify_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> str:
    """
    Validate the X-API-Key header. Returns the key's UUID string on success.
    Raises 401 on missing or unrecognised key.
    """
    key_hash = _hash_key(x_api_key)
    result = await db.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))
    api_key = result.scalar_one_or_none()

    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )

    # Fire-and-forget last_used_at update — failure here is non-fatal
    try:
        await db.execute(
            update(ApiKey)
            .where(ApiKey.id == api_key.id)
            .values(last_used_at=datetime.now(timezone.utc))
        )
        await db.commit()
    except Exception:
        pass

    return str(api_key.id)

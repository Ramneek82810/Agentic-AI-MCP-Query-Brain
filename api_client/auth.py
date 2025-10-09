import httpx
import logging
import time
from datetime import datetime
from fastapi import HTTPException

logger = logging.getLogger(__name__)

API_BASE_URL = "https://lincoln-api.vartopia.com"

_token_cache = {}  

async def get_token(username: str, password: str) -> str:
    """
    Obtain a valid JWT access token for the given user.
    
    - Uses username/password login.
    - Caches token in memory until expiry.
    - Automatically refreshes token if expired.
    """
    now = time.time()
    
    cache = _token_cache.get(username, {})
    if cache.get("access_token") and now < cache.get("expires_at", 0):
        return cache["access_token"]

    logger.info(f"Fetching Vartopia API token for user: {username}")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{API_BASE_URL}/api/Account/Login",
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                json={"username": username, "password": password},
            )

        if response.status_code != 200:
            logger.error(f"Auth failed: {response.status_code} {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail={
                    "code": "E_AUTH_UNAUTHORIZED",
                    "message": "Failed to authenticate with Vartopia API",
                    "details": response.json() if response.text else {},
                },
            )

        data = response.json()
        logger.debug(f"Login response JSON: {data}")

        tokens = data.get("Tokens") or data.get("data", {}).get("Tokens", {})
        access_token = tokens.get("AccessToken")
        refresh_token = tokens.get("RefreshToken")
        exp_time_str = tokens.get("ATExpirationTime")

        if not access_token:
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "E_AUTH_TOKEN_MISSING",
                    "message": "No AccessToken returned in Vartopia login response",
                    "details": data,
                },
            )
        expires_at = now + 3600 
        if exp_time_str:
            try:
                exp_dt = datetime.fromisoformat(exp_time_str.replace("Z", "+00:00"))
                expires_at = exp_dt.timestamp()
            except Exception:
                logger.warning("Failed to parse ATExpirationTime, using 1h fallback.")

        _token_cache[username] = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at - 30, 
        }

        logger.info(f"Vartopia API token acquired successfully for user: {username}")
        return access_token

    except Exception as e:
        logger.exception("Error while getting Vartopia token")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "E_AUTH_EXCEPTION",
                "message": str(e),
                "details": {},
            },
        )
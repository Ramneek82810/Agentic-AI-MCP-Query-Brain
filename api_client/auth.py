import httpx
import logging
import time
from datetime import datetime
from fastapi import HTTPException

logger = logging.getLogger(__name__)

API_BASE_URL = "https://lincoln-api.vartopia.com"

USERNAME = "product@vartopia.com"
PASSWORD = "BNeord8ICMGi8P"

_token_cache = {"access_token": None, "expires_at": 0, "refresh_token": None}


async def get_token() -> str:
    """
    Get a valid JWT token for calling Vartopia API.
    - Uses username/password login.
    - Caches token in memory until expiry.
    - Auto-refresh if expired.
    """
    now = time.time()
    if _token_cache["access_token"] and now < _token_cache["expires_at"]:
        return _token_cache["access_token"]

    logger.info("Fetching Vartopia API token...")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{API_BASE_URL}/api/Account/Login",
                headers={"Content-Type": "application/json"},
                json={"username": USERNAME, "password": PASSWORD},
            )
            
            if response.status_code != 200:
                logger.warning("Login with 'username' failed, retrying with 'userId'")
                response = await client.post(
                    f"{API_BASE_URL}/api/Account/Login",
                    headers={"Content-Type": "application/json"},
                    json={"userId": USERNAME, "password": PASSWORD},
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
        logger.debug(f"Login response JSON:{data}")
        
        tokens = {}
        if "Tokens" in data:
            tokens = data["Tokens"]
        elif "data" in data and "Tokens" in data["data"]:
            tokens = data["data"]["Tokens"]
            
        access_token = tokens.get("AccessToken")
        refresh_token = tokens.get("RefreshToken")
        exp_time_str = tokens.get("ATExpirationTime")

        if not access_token:
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "E_AUTH_TOKEN_MISSING",
                    "message": "No AccessToken in Vartopia login response",
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

        _token_cache["access_token"] = access_token
        _token_cache["refresh_token"] = refresh_token
        _token_cache["expires_at"] = expires_at - 30  

        logger.info("Vartopia API token acquired successfully")
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

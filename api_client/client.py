import httpx
import uuid
import json
import logging
from fastapi import HTTPException

from .auth import get_token
from .errors import map_error

logger = logging.getLogger(__name__)

API_BASE_URL = "https://lincoln-api.vartopia.com" 

async def _request(
    method: str,
    endpoint: str,
    token: str,
    correlation_id: str,
    **kwargs
) -> dict:
    """
    Internal helper to make HTTP requests to Vartopia API.
    - Handles auth headers, correlation IDs, error mapping.
    - Raises HTTPException if something goes wrong.
    """
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.request(
                method,
                f"{API_BASE_URL}{endpoint}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Correlation-Id": correlation_id,
                },
                **kwargs,
            )

        if res.status_code != 200:
            raise map_error(res, correlation_id)

        return res.json()

    except Exception as e:
        logger.exception(f"[{correlation_id}] API request failed: {method} {endpoint}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "E_INTERNAL",
                "message": str(e),
                "correlationId": correlation_id,
            },
        )
async def _normalize_params(params):
    """Ensure params is always a dictionary."""
    if params is None:
        return {}
    if isinstance(params, str):
        try:
            return json.loads(params)
        except Exception:
            raise ValueError("params must be a dictionary or valid JSON string")
    if not isinstance(params, dict):
        raise ValueError("params must be a dictionary")
    return params

async def login(user_id:str, password:str)->dict:
    """
    Authenticate user and return an access token or session.
    This bypasses get_token() since login itself issues tokens.
    """
    correlation_id=str(uuid.uuid4())
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            res=await client.post(
                f"{API_BASE_URL}/api/Account/login",
                json={"Username": user_id, "password": password},
                headers={"X-Correlation-Id": correlation_id},
            )
        if res.status_code!=200:
            raise map_error(res,correlation_id)
        return res.json()
    
    except Exception as e:
        logger.exception(f"[{correlation_id}] Login request failed.")  
        raise HTTPException(
            status_code=500,
            detail={
                "code":"E_INTERNAL",
                "message":str(e),
                "correlationId":correlation_id,
            },
        )

async def get_vendors(user_email: str) -> dict:
    """
    Fetch list of vendors available to a user.
    """
    token = await get_token()
    correlation_id = str(uuid.uuid4())
    return await _request(
        "POST",
        "/vendors",
        token,
        correlation_id,
        json={"user_email": user_email},
    )


async def get_program(vendor_id: str, user_email: str) -> dict:
    """
    Fetch programs for a specific vendor.
    """
    token = await get_token()
    correlation_id = str(uuid.uuid4())
    payload = await _normalize_params(   
        {"vendor_id": vendor_id, "user_email": user_email}
    )
    return await _request(
        "POST",
        "/programs",
        token,
        correlation_id,
        json=payload,
    )


async def get_program_schema(program_id: str, user_email: str) -> dict:
    """
    Fetch schema (fields) for a program.
    """
    token = await get_token()
    correlation_id = str(uuid.uuid4())
    payload = await _normalize_params(   
        {"program_id": program_id, "user_email": user_email}
    )
    return await _request(
        "POST",
        "/program-schema",
        token,
        correlation_id,
        json=payload,
    )


async def submit_deal(program_id: str, user_email: str, form_data: dict) -> dict:
    """
    Submit a deal form for a program.
    """
    token = await get_token()
    correlation_id = str(uuid.uuid4())
    payload = await _normalize_params(   
        {"program_id": program_id, "user_email": user_email, "form_data": form_data}
    )
    return await _request(
        "POST",
        "/submit-deal",
        token,
        correlation_id,
        json=payload,
    )

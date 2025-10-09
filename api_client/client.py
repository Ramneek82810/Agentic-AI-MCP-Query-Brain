import httpx
import uuid
import json
import logging
from fastapi import HTTPException

# from .auth import get_token
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
    
    Args:
        method(str):HTTP method, e.g., "GET","POST".
        endpoinjt (str): API endpoint path starting with "/".
        token (str, optional): Bearer token for Authorization header.
        correlation_id (str, optional): Unique identifier for logging/tracing.
        **kwargs: Additional arguments passed to httpx request (json, params, etc.)
        
    Returns:
        dict: Parsed JSON response from API
        
    Raises:
        HTTPException: If API returns error status code or request fails.
    """
    # try:
    #     async with httpx.AsyncClient(timeout=20.0) as client:
    #         res = await client.request(
    #             method,
    #             f"{API_BASE_URL}{endpoint}",
    #             headers={
    #                 "Authorization": f"Bearer {token}",
    #                 "X-Correlation-Id": correlation_id,
    #                 "Content-Type": "application/json",
    #                 "Accept": "application/json",
    #             },
    #             **kwargs,
    #         )

        
    #     if res.status_code>=400:
    #         logger.error(f"[{correlation_id}] API Error {res.status_code}:{res.text}")
    #         raise HTTPException(status_code=res.status_code, detail=res.text)
    #     return res.json()

    # except Exception as e:
    #     logger.exception(f"[{correlation_id}] API request failed: {method} {endpoint}")
    #     raise HTTPException(
    #         status_code=500,
    #         detail={"code": "E_INTERNAL", "message": str(e), "correlationId": correlation_id},
    #     )
    if not correlation_id:
        correlation_id=str(uuid.uuid4())
    
    headers={
        "Authorization": f"Bearer {token}",
        "X-Correlation-Id": correlation_id,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    # if token:
    #     headers["Authorization"]=f"Bearer {token}"
        
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.request(method, f"{API_BASE_URL}{endpoint}", headers=headers, **kwargs)
            
        if response.status_code>=400:
            logger.error(f"[{correlation_id}] API Error {response.status_code}:{response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()
    
    except Exception as e:
        logger.exception(f"[{correlation_id}] API request failed:{method}{endpoint}")
        raise HTTPException (status_code=500, detail=f"Internal error:{str(e)}")


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


async def login(username: str, password: str) -> dict:
    """
    Authenticate user and return login response (access token etc.).
    
    Args:
        username(str): Username of the user.
        password(str): Password of the user.
        
    Returns:
        dict: Login response including Tokens and user details.
        
    Raises:
        ValueError: If username or password is missing.
        HTTPException: If API call fails.
    """
    if not username or not password:
        raise ValueError("Username and password are required.")
    
    correlation_id = str(uuid.uuid4())
    payload = {"Username": username, "Password": password}
    headers = {
        "X-Correlation-Id": correlation_id,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Partner": "Vartopia",
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.post(
                f"{API_BASE_URL}/api/Account/Login", json=payload, headers=headers
            )

        if res.status_code != 200:
            raise map_error(res, correlation_id)

        return res.json()

    except Exception as e:
        logger.exception(f"[{correlation_id}] Login request failed.")
        raise HTTPException(
            status_code=500,
            detail={"code": "E_INTERNAL", "message": str(e), "correlationId": correlation_id},
        )


# async def get_vendors(access_token:str, user_email: str) -> dict:
#     """
#     List vendors for the user.
#     """
    
#     if not access_token or not user_email:
#         raise ValueError("access_token and user_email are required")

#     correlation_id = str(uuid.uuid4())
#     payload = {"user_email": user_email}

#     return await _request("POST", "/vendors", access_token, correlation_id, json=payload)   



# async def get_program(access_token: str, vendor_id: str, user_email: str) -> dict:
#     """
#     List programs for a vendor.
#     """
#     if not access_token or not vendor_id or not user_email:
#         raise ValueError("access_token, vendor_id, and user_email are required")

#     correlation_id = str(uuid.uuid4())
#     payload = await _normalize_params({"vendor_id": vendor_id, "user_email": user_email})
    
#     return await _request("POST", "/api/Programs/List", access_token, correlation_id, json=payload)



# async def get_program_schema(access_token: str, program_id: str, user_email: str) -> dict:
#     """
#     Fetch program schema (fields).
#     """
    
#     if not access_token or not program_id or not user_email:
#         raise ValueError("access_token, program_id, and user_email are required")

#     correlation_id = str(uuid.uuid4())
#     payload = await _normalize_params({"program_id": program_id, "user_email": user_email})
#     return await _request("POST", "/program-schema", access_token, correlation_id, json=payload)

async def submit_deal(access_token: str, user_email: str, deal_data: dict) -> dict:
    """
    Submit a deal form using the correct endpoint.
    
    Args:
        token(str): Access token from login.
        deal_data(dict): Full deal payload according to API spec. Must include:
            - programName
            - source
            - uniqueID
            - vendorName
            - commonFields
            - customFields
            - extensionAndRegUpdateDetails
            - primarySalesRepDetails
            - submitterDetails
            - customerDetails
            - reviewerDetails
            - flags
    
    Returns:
        dict: API response with success and errors.
        
    Raises:
        ValueError: If token or deal_data is missing.
        HTTPException: If API call fails.
    """
    
    if not access_token or not user_email or not deal_data:
        raise ValueError("access_token, user_email, and deal_data are required")
    
    correlation_id = str(uuid.uuid4())
    # payload = {"deals": deal_data}  
    payload=deal_data if isinstance(deal_data, list) else [deal_data]

    return await _request(
        "POST",
        "/api/DealReg/Upsert",
        access_token,
        correlation_id,
        json=payload
    )

    # correlation_id = str(uuid.uuid4())
    # payload = await _normalize_params({"user_email": user_email, "form_data": deal_data})
    # return await _request("POST", "/submit-deal", access_token, correlation_id, json=payload)    

async def get_registration_updates(
    access_token: str,
    # user_email: str,
    unique_id: str = "",
    varcrm_opportunity_id: str = "",
    vartopia_transaction_id: str = "",
) -> dict:
    """
    Fetch registration updates for a specific deal/registration.
    
    Args:
        token (str): Access token from login.
        uniqueID (str): Unique ID of the registration.
        varCrmOpportunityId(str): CRM opportunity ID.
        vartopiaTransactionID (str): Vartopia transaction ID.
        
    Returns:
        dict: API response with registraction updates.
        
    Rasises:
        ValueError: If any required parameter is missing.
        HTTPException: If API call fails.
    """
    if not access_token:
        raise ValueError("access_token is required")
    
    correlation_id=str(uuid.uuid4())
    
    params={
        "uniqueID": unique_id,
        "varCrmOpportunityId":varcrm_opportunity_id,
        "vartopiaTransactionId":vartopia_transaction_id
    }
    
    return await _request (
        "GET",
        "/api/DealReg/GetRegistrationUpdatesList",
        access_token,
        correlation_id,
        params=params,
    )
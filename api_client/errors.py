from fastapi import HTTPException

ERROR_MAP = {
    401: "E_AUTH_UNAUTHORIZED",
    403: "E_AUTH_FORBIDDEN",
    404: "E_NOT_FOUND",
    422: "E_VALIDATION_SCHEMA",
    429: "E_RATE_LIMIT",
}


def map_error(response, correlation_id: str) -> HTTPException:
    """
    Map Vartopia API errors into MCP-standard errors.
    - Normalizes payload.
    - Adds correlationId for tracing.
    - Falls back safely for unknown errors.
    """
    if response is None:
        return HTTPException(
            status_code=500,
            detail={
                "code": "E_INTERNAL",
                "message": "No response from Vartopia API",
                "correlationId": correlation_id,
                "details": {}
            }
        )

    status = getattr(response, "status_code", 500)
    
    try:
        payload = response.json() if hasattr(response, "json") else {}
    except Exception:
        payload = {"message": getattr(response, "text", "Unknown error from Vartopia API")}

    error_code = ERROR_MAP.get(status, "E_INTERNAL")

    if status == 422 and payload:
        if "business" in str(payload.get("code", "")).lower():
            error_code = "E_VALIDATION_BUSINESS"

    detail = {
        "code": error_code,
        "message": payload.get("message") or payload.get("error") or f"HTTP {status} Error",
        "correlationId": correlation_id,
        "details": payload.get("details") or payload, 
    }

    if error_code == "E_INTERNAL":
        status = 500

    return HTTPException(status_code=status, detail=detail)

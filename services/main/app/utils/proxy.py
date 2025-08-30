import httpx
from fastapi import HTTPException

async def call_service(method, url, headers=None, params=None, json=None, timeout=10, service_name="unknown"):
    async with httpx.AsyncClient(timeout=timeout) as client:
        req = getattr(client, method.lower())
        resp = await req(url, headers=headers, params=params, json=json)
        
        if resp.is_error:
            # Try to parse error body, fallback to plain text
            try:
                detail = resp.json()
            except Exception:
                detail = {"message": resp.text}
            
            raise HTTPException(
                status_code=resp.status_code,
                detail={
                    "error": {
                        "code": detail.get("code", "UNKNOWN_ERROR"),
                        "message": detail.get("message") or detail.get("detail") or "Unexpected error",
                        "status": resp.status_code,
                        "service": service_name
                    }
                }
            )
        
        return resp.json()

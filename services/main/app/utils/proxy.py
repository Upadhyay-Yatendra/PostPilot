import httpx
import logging
from fastapi import HTTPException

# Set up logging
logger = logging.getLogger(__name__)

async def call_service(method, url, headers=None, params=None, json=None, timeout=10, service_name="unknown"):
    # Log the outgoing request
    logger.info(f"[{service_name.upper()}] Making {method.upper()} request to: {url}")
    logger.info(f"[{service_name.upper()}] Headers: {headers}")
    logger.info(f"[{service_name.upper()}] Params: {params}")
    if json:
        logger.info(f"[{service_name.upper()}] JSON Body: {json}")
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            req = getattr(client, method.lower())
            
            # Prepare request arguments based on method
            req_kwargs = {
                "url": url,
                "headers": headers,
                "params": params
            }
            
            # Only add json body for methods that support it
            if method.upper() in ["POST", "PUT", "PATCH", "DELETE"] and json is not None:
                req_kwargs["json"] = json
            elif json is not None and method.upper() == "GET":
                logger.warning(f"[{service_name.upper()}] Ignoring JSON body for GET request")
            
            logger.info(f"[{service_name.upper()}] Request kwargs: {req_kwargs}")
            
            # Make the request
            resp = await req(**req_kwargs)
            
            # Log response details
            logger.info(f"[{service_name.upper()}] Response status: {resp.status_code}")
            logger.info(f"[{service_name.upper()}] Response headers: {dict(resp.headers)}")
            
            if resp.is_error:
                logger.error(f"[{service_name.upper()}] Error response body: {resp.text}")
                
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
                            "service": service_name,
                            "url": url
                        }
                    }
                )
            
            # Log successful response
            response_data = resp.json()
            logger.info(f"[{service_name.upper()}] Success response: {response_data}")
            return response_data
            
    except httpx.TimeoutException:
        logger.error(f"[{service_name.upper()}] Timeout error for {url}")
        raise HTTPException(
            status_code=504,
            detail={
                "error": {
                    "code": "TIMEOUT_ERROR",
                    "message": f"Request to {service_name} service timed out",
                    "status": 504,
                    "service": service_name,
                    "url": url
                }
            }
        )
    except httpx.ConnectError:
        logger.error(f"[{service_name.upper()}] Connection error for {url}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "code": "CONNECTION_ERROR",
                    "message": f"Could not connect to {service_name} service",
                    "status": 503,
                    "service": service_name,
                    "url": url
                }
            }
        )
    except Exception as e:
        logger.error(f"[{service_name.upper()}] Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "PROXY_ERROR",
                    "message": f"Proxy error while calling {service_name} service: {str(e)}",
                    "status": 500,
                    "service": service_name,
                    "url": url
                }
            }
        )
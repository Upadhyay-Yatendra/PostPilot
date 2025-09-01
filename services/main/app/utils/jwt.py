import logging
from jose import JWTError, jwt
from app.config import JWT_SECRET, JWT_ALGORITHM
from fastapi import HTTPException, status, Request

logger = logging.getLogger(__name__)

def decode_jwt_token(token: str):
    try:
        logger.info("Attempting to decode JWT token")
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        logger.info(f"JWT decoded successfully for user: {payload.get('email', 'unknown')}")
        return payload
    except JWTError as e:
        logger.error(f"JWT decode error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid or expired token."
        )

def get_jwt_user(request: Request):
    auth_header = request.headers.get("Authorization")
    logger.info(f"Authorization header: {auth_header}")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.error("Missing or malformed Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Missing or malformed token."
        )
    
    token = auth_header.split(" ")[1]
    logger.info(f"Extracted token: {token[:20]}...")  # Log first 20 chars for debugging
    
    payload = decode_jwt_token(token)
    return payload  # can return user_id/email, etc
from jose import JWTError, jwt
from app.config import JWT_SECRET, JWT_ALGORITHM
from fastapi import HTTPException, status, Request

def decode_jwt_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.")

def get_jwt_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or malformed token.")
    token = auth_header.split(" ")[1]
    payload = decode_jwt_token(token)
    return payload  # can return user_id/email, etc

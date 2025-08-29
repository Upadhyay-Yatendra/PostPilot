from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.utils.linkedin import extract_linkedin_username
from app.models.user import User
from app.utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,   # <-- add this tiny helper in utils if you don't have it yet (shown below)
)
from shared.db.pg_db import get_db

router = APIRouter()
security = HTTPBearer()

# ======== Schemas ========
class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    linkedin_url: str  # user provides URL

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    linkedin_url: str | None = None

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut | None = None

# ======== Routes ========

from app.utils.linkedin import extract_linkedin_username

@router.post("/signup", response_model=TokenOut)
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    try:
        linkedin_username = extract_linkedin_username(req.linkedin_url)
        hashed_pw = hash_password(req.password)
        new_user = User(
            email=req.email,
            hashed_password=hashed_pw,
            linkedin_username=linkedin_username,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception:
        db.rollback()
        raise

    token = create_access_token({"user_id": new_user.id, "email": new_user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "linkedin_username": new_user.linkedin_username,
        },
    }

@router.post("/login", response_model=TokenOut)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    token = create_access_token({"user_id": user.id, "email": user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "linkedin_username": user.linkedin_username,
        },
    }

@router.get("/verify")
def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Other services call this with Authorization: Bearer <token>.
    Returns decoded claims if valid.
    """
    token = credentials.credentials
    payload = decode_access_token(token)  # raises HTTP 401 on failure
    return {"valid": True, "payload": payload}

# Optional: handy self-check endpoint (uses the same verification)
@router.get("/me", response_model=UserOut)
def me(credentials: HTTPAuthorizationCredentials = Security(security), db: Session = Depends(get_db)):
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.id,
        "email": user.email,
        "linkedin_username": user.linkedin_username,
    }


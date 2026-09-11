import os
import time
import base64
import json
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database_orm import SessionLocal, User, hash_password, verify_password

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "doca-legal-metrology-secret-key-26034-sih-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 hours

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Lightweight JWT implementation without external heavy dependencies
def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def base64url_decode(data_str: str) -> bytes:
    padding = '=' * (4 - (len(data_str) % 4))
    return base64.urlsafe_b64decode((data_str + padding).encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": int(expire.timestamp())})

    header = {"alg": ALGORITHM, "typ": "JWT"}
    header_bytes = json.dumps(header, separators=(',', ':')).encode('utf-8')
    payload_bytes = json.dumps(to_encode, separators=(',', ':')).encode('utf-8')

    encoded_header = base64url_encode(header_bytes)
    encoded_payload = base64url_encode(payload_bytes)

    signature_base = f"{encoded_header}.{encoded_payload}".encode('utf-8')
    signature = hmac.new(SECRET_KEY.encode('utf-8'), signature_base, hashlib.sha256).digest()
    encoded_signature = base64url_encode(signature)

    return f"{encoded_header}.{encoded_payload}.{encoded_signature}"

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        encoded_header, encoded_payload, encoded_signature = parts
        signature_base = f"{encoded_header}.{encoded_payload}".encode('utf-8')
        expected_sig = hmac.new(SECRET_KEY.encode('utf-8'), signature_base, hashlib.sha256).digest()
        
        if base64url_encode(expected_sig) != encoded_signature:
            return None

        payload_bytes = base64url_decode(encoded_payload)
        payload = json.loads(payload_bytes.decode('utf-8'))

        if payload.get("exp") and payload["exp"] < time.time():
            return None # Expired

        return payload
    except Exception as e:
        return None

def get_current_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    # If no token passed, fallback to default officer for seamless UI dev/demo compatibility
    if not token:
        user = db.query(User).filter(User.email == "officer@doca.gov.in").first()
        if user:
            return user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Bearer token missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token or session expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = payload["sub"]
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User account not found.")

    return user

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role.upper() != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Action restricted to DoCA Administrative Officers."
        )
    return current_user

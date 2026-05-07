"""Employer authentication router."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPBearer

from hiring_radar.api.dependencies import get_db
from hiring_radar.api.security import create_access_token, hash_password, verify_password
from hiring_radar.models import User, UserRole

security = HTTPBearer(auto_error=False)
router = APIRouter(prefix="/employer/auth", tags=["employer-auth"])


def _token_response(user_id: str, email: str, company_name: str, role: str = "employer") -> dict:
    now = datetime.now(timezone.utc)
    access_token = create_access_token(
        {
            "sub": user_id,
            "email": email,
            "role": role,
            "iat": now,
        },
        expires_delta=timedelta(hours=24),
    )
    refresh_token = create_access_token(
        {
            "sub": user_id,
            "email": email,
            "role": role,
            "type": "refresh",
            "iat": now,
        },
        expires_delta=timedelta(days=30),
    )
    return {
        "ok": True,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": user_id,
        "email": email,
        "company_name": company_name,
        "role": role,
    }


@router.post("/register")
def employer_register(
    payload: dict,
    db: Annotated[dict, Depends(get_db)],
) -> dict:
    """Register a new employer account."""
    company_name = payload.get("company_name", "").strip()
    company_email = payload.get("company_email", "").strip().lower()
    contact_name = payload.get("contact_name", "").strip()
    password = payload.get("password", "")
    password_confirmation = payload.get("password_confirmation", "")

    if not company_name or not company_email or not password:
        raise HTTPException(status_code=400, detail="missing_fields")
    if password != password_confirmation:
        raise HTTPException(status_code=400, detail="password_mismatch")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="password_too_short")

    # Check if email already exists
    existing = db["users"].find_one({"email": company_email})
    if existing:
        raise HTTPException(status_code=409, detail="email_already_registered")

    user = User(
        email=company_email,
        password_hash=hash_password(password),
        name=contact_name or company_name,
        company_name=company_name,
        role=UserRole.EMPLOYER,
        email_verified=True,  # Simplified for employer accounts
    )
    db["users"].insert_one(user)

    return _token_response(str(user.id), company_email, company_name)


@router.post("/login")
def employer_login(
    payload: dict,
    response: Response,
    db: Annotated[dict, Depends(get_db)],
) -> dict:
    """Login as an employer."""
    email = payload.get("email", "").strip().lower()
    password = payload.get("password", "")

    if not email or not password:
        raise HTTPException(status_code=400, detail="missing_credentials")

    user_doc = db["users"].find_one({"email": email, "role": UserRole.EMPLOYER.value})
    if not user_doc:
        raise HTTPException(status_code=401, detail="invalid_credentials")

    user = User.model_validate(user_doc)
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid_credentials")

    # Update last login
    db["users"].update_one(
        {"_id": user.id},
        {"$set": {"last_login_at": datetime.now(timezone.utc)}},
    )

    return _token_response(
        str(user.id),
        user.email,
        user.company_name or user.name,
    )


@router.get("/me")
def employer_me(
    request: Request,
    db: Annotated[dict, Depends(get_db)],
) -> dict:
    """Get current employer profile."""
    user = request.state.user
    if not user or user.get("role") != "employer":
        raise HTTPException(status_code=401, detail="unauthorized")

    user_doc = db["users"].find_one({"_id": user["sub"]})
    if not user_doc:
        raise HTTPException(status_code=404, detail="user_not_found")

    return {
        "ok": True,
        "user_id": str(user_doc["_id"]),
        "email": user_doc.get("email", ""),
        "name": user_doc.get("name", ""),
        "company_name": user_doc.get("company_name", ""),
        "role": user_doc.get("role", "employer"),
        "email_verified": user_doc.get("email_verified", False),
        "created_at": user_doc.get("created_at", datetime.now(timezone.utc).isoformat()),
    }


@router.post("/logout")
def employer_logout(response: Response) -> dict:
    """Logout employer."""
    return {"ok": True}


@router.post("/refresh")
def employer_refresh(
    payload: dict,
    db: Annotated[dict, Depends(get_db)],
) -> dict:
    """Refresh access token."""
    from hiring_radar.api.security import decode_token

    refresh_token = payload.get("refresh_token", "")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="missing_refresh_token")

    try:
        payload_decoded = decode_token(refresh_token)
        if payload_decoded.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="invalid_token_type")

        user_id = payload_decoded["sub"]
        user_doc = db["users"].find_one({"_id": user_id})
        if not user_doc:
            raise HTTPException(status_code=404, detail="user_not_found")

        return _token_response(
            str(user_doc["_id"]),
            user_doc.get("email", ""),
            user_doc.get("company_name", user_doc.get("name", "")),
        )
    except Exception:
        raise HTTPException(status_code=401, detail="invalid_refresh_token")

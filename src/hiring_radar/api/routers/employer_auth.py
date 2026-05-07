"""Employer authentication router — simplified mock version."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Response

router = APIRouter(prefix="/employer/auth", tags=["employer-auth"])


def _token_response(user_id: str, email: str, company_name: str) -> dict:
    return {
        "ok": True,
        "access_token": f"mock_token_{user_id}",
        "refresh_token": f"mock_refresh_{user_id}",
        "token_type": "bearer",
        "user_id": user_id,
        "email": email,
        "company_name": company_name,
        "role": "employer",
    }


@router.post("/register")
def employer_register(payload: dict) -> dict:
    company_name = payload.get("company_name", "").strip()
    company_email = payload.get("company_email", "").strip().lower()
    password = payload.get("password", "")
    password_confirmation = payload.get("password_confirmation", "")

    if not company_name or not company_email or not password:
        raise HTTPException(status_code=400, detail="missing_fields")
    if password != password_confirmation:
        raise HTTPException(status_code=400, detail="password_mismatch")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="password_too_short")

    user_id = company_email.replace("@", "_").replace(".", "_")
    return _token_response(user_id, company_email, company_name)


@router.post("/login")
def employer_login(payload: dict, response: Response) -> dict:
    email = payload.get("email", "").strip().lower()
    password = payload.get("password", "")

    if not email or not password:
        raise HTTPException(status_code=400, detail="missing_credentials")

    user_id = email.replace("@", "_").replace(".", "_")
    return _token_response(user_id, email, "NoyTera Sirket")


@router.get("/me")
def employer_me() -> dict:
    return {
        "ok": True,
        "user_id": "emp_demo",
        "email": "employer@noytera.com",
        "name": "Demo Isveren",
        "company_name": "NoyTera Teknoloji",
        "role": "employer",
        "email_verified": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/logout")
def employer_logout(response: Response) -> dict:
    return {"ok": True}


@router.post("/refresh")
def employer_refresh(payload: dict) -> dict:
    return _token_response("emp_demo", "employer@noytera.com", "NoyTera Teknoloji")

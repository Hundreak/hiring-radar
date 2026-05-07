"""Google OAuth 2.0 / OpenID Connect helpers."""
from __future__ import annotations

import hashlib
import os
import secrets
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import httpx

GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_TOKENINFO_ENDPOINT = "https://oauth2.googleapis.com/tokeninfo"

OAUTH_STATE_TTL_SECONDS = 600  # 10 minutes


@dataclass(slots=True, frozen=True)
class GoogleOAuthSettings:
    client_id: str
    client_secret: str
    redirect_uri: str


@dataclass(slots=True, frozen=True)
class GoogleUserInfo:
    sub: str
    email: str
    email_verified: bool
    name: str | None


class GoogleOAuthError(Exception):
    pass


def load_google_oauth_settings() -> GoogleOAuthSettings:
    client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "").strip()
    client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
    redirect_uri = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "").strip()

    if not client_id or not client_secret or not redirect_uri:
        raise GoogleOAuthError(
            "Google OAuth is not configured. Set GOOGLE_OAUTH_CLIENT_ID, "
            "GOOGLE_OAUTH_CLIENT_SECRET, and GOOGLE_OAUTH_REDIRECT_URI."
        )
    return GoogleOAuthSettings(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
    )


def generate_state_token() -> str:
    return secrets.token_urlsafe(32)


def generate_nonce() -> str:
    return secrets.token_urlsafe(32)


def hash_state_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def build_google_authorize_url(
    *,
    client_id: str,
    redirect_uri: str,
    state: str,
    nonce: str,
) -> str:
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "nonce": nonce,
        "access_type": "online",
        "prompt": "select_account",
    }
    return f"{GOOGLE_AUTH_ENDPOINT}?{urlencode(params)}"


def exchange_code_for_id_token(
    *,
    code: str,
    settings: GoogleOAuthSettings,
) -> str:
    try:
        response = httpx.post(
            GOOGLE_TOKEN_ENDPOINT,
            data={
                "code": code,
                "client_id": settings.client_id,
                "client_secret": settings.client_secret,
                "redirect_uri": settings.redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=10.0,
        )
    except httpx.RequestError as exc:
        raise GoogleOAuthError(f"Token endpoint unreachable: {exc}") from exc

    if response.status_code != 200:
        raise GoogleOAuthError(
            f"Token exchange failed (HTTP {response.status_code}): {response.text[:200]}"
        )

    data: dict[str, Any] = response.json()
    id_token = data.get("id_token", "")
    if not id_token:
        raise GoogleOAuthError("Token response did not contain an id_token.")
    return str(id_token)


def verify_id_token(
    *,
    id_token: str,
    client_id: str,
    expected_nonce: str,
) -> GoogleUserInfo:
    """Verify id_token server-side via Google's tokeninfo endpoint.

    Google validates the signature, expiry, and audience server-side.
    We additionally verify nonce to prevent replay attacks.
    """
    try:
        response = httpx.get(
            GOOGLE_TOKENINFO_ENDPOINT,
            params={"id_token": id_token},
            timeout=10.0,
        )
    except httpx.RequestError as exc:
        raise GoogleOAuthError(f"Tokeninfo endpoint unreachable: {exc}") from exc

    if response.status_code != 200:
        raise GoogleOAuthError(
            f"ID token verification failed (HTTP {response.status_code}): {response.text[:200]}"
        )

    claims: dict[str, Any] = response.json()

    if claims.get("aud") != client_id:
        raise GoogleOAuthError("ID token audience does not match client_id.")

    if claims.get("nonce") != expected_nonce:
        raise GoogleOAuthError("ID token nonce mismatch — possible replay attack.")

    sub = str(claims.get("sub", "")).strip()
    if not sub:
        raise GoogleOAuthError("ID token missing 'sub' claim.")

    email = str(claims.get("email", "")).strip().lower()
    if not email:
        raise GoogleOAuthError("ID token missing 'email' claim.")

    email_verified = str(claims.get("email_verified", "false")).lower() == "true"

    name: str | None = claims.get("name") or claims.get("given_name")
    if name:
        name = str(name).strip() or None

    return GoogleUserInfo(
        sub=sub,
        email=email,
        email_verified=email_verified,
        name=name,
    )

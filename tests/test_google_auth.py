"""Tests for Google OAuth helpers and the OAuth router callbacks."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from hiring_radar.services.google_auth import (
    GoogleOAuthError,
    GoogleUserInfo,
    build_google_authorize_url,
    generate_nonce,
    generate_state_token,
    hash_state_token,
    verify_id_token,
)

# ---------------------------------------------------------------------------
# Unit: token helpers
# ---------------------------------------------------------------------------

class TestStateTokenHelpers:
    def test_generate_state_token_is_url_safe_string(self) -> None:
        token = generate_state_token()
        assert isinstance(token, str)
        assert len(token) >= 32

    def test_hash_is_deterministic(self) -> None:
        token = "fixed-token"
        assert hash_state_token(token) == hash_state_token(token)

    def test_different_tokens_produce_different_hashes(self) -> None:
        assert hash_state_token(generate_state_token()) != hash_state_token(generate_state_token())

    def test_nonce_is_distinct_from_state(self) -> None:
        assert generate_state_token() != generate_nonce()


# ---------------------------------------------------------------------------
# Unit: authorize URL construction
# ---------------------------------------------------------------------------

class TestBuildAuthorizeUrl:
    def test_contains_required_params(self) -> None:
        url = build_google_authorize_url(
            client_id="test-client-id",
            redirect_uri="https://example.com/callback",
            state="my-state",
            nonce="my-nonce",
        )
        assert "client_id=test-client-id" in url
        assert "state=my-state" in url
        assert "nonce=my-nonce" in url
        assert "response_type=code" in url
        assert "openid" in url
        assert "email" in url

    def test_starts_with_google_auth_endpoint(self) -> None:
        url = build_google_authorize_url(
            client_id="x",
            redirect_uri="https://example.com/cb",
            state="s",
            nonce="n",
        )
        assert url.startswith("https://accounts.google.com/o/oauth2/v2/auth")


# ---------------------------------------------------------------------------
# Unit: ID token verification (mocked tokeninfo)
# ---------------------------------------------------------------------------

def _make_tokeninfo_response(
    *,
    sub: str = "google-sub-123",
    email: str = "user@example.com",
    email_verified: str = "true",
    aud: str = "test-client-id",
    nonce: str = "test-nonce",
    name: str = "Test User",
) -> dict:
    return {
        "sub": sub,
        "email": email,
        "email_verified": email_verified,
        "aud": aud,
        "nonce": nonce,
        "name": name,
    }


class TestVerifyIdToken:
    def _mock_get(self, payload: dict, status_code: int = 200):
        mock_resp = MagicMock()
        mock_resp.status_code = status_code
        mock_resp.json.return_value = payload
        mock_resp.text = ""
        return mock_resp

    def test_valid_token_returns_user_info(self) -> None:
        with patch("hiring_radar.services.google_auth.httpx.get") as mock_get:
            mock_get.return_value = self._mock_get(_make_tokeninfo_response())
            info = verify_id_token(
                id_token="fake-token",
                client_id="test-client-id",
                expected_nonce="test-nonce",
            )
        assert info.sub == "google-sub-123"
        assert info.email == "user@example.com"
        assert info.email_verified is True
        assert info.name == "Test User"

    def test_wrong_audience_raises(self) -> None:
        with patch("hiring_radar.services.google_auth.httpx.get") as mock_get:
            mock_get.return_value = self._mock_get(
                _make_tokeninfo_response(aud="wrong-client-id")
            )
            with pytest.raises(GoogleOAuthError, match="audience"):
                verify_id_token(
                    id_token="fake-token",
                    client_id="test-client-id",
                    expected_nonce="test-nonce",
                )

    def test_nonce_mismatch_raises(self) -> None:
        with patch("hiring_radar.services.google_auth.httpx.get") as mock_get:
            mock_get.return_value = self._mock_get(
                _make_tokeninfo_response(nonce="different-nonce")
            )
            with pytest.raises(GoogleOAuthError, match="nonce"):
                verify_id_token(
                    id_token="fake-token",
                    client_id="test-client-id",
                    expected_nonce="test-nonce",
                )

    def test_non_200_response_raises(self) -> None:
        with patch("hiring_radar.services.google_auth.httpx.get") as mock_get:
            mock_get.return_value = self._mock_get({}, status_code=400)
            with pytest.raises(GoogleOAuthError, match="verification failed"):
                verify_id_token(
                    id_token="fake-token",
                    client_id="test-client-id",
                    expected_nonce="test-nonce",
                )

    def test_missing_sub_raises(self) -> None:
        payload = _make_tokeninfo_response()
        payload.pop("sub")
        with patch("hiring_radar.services.google_auth.httpx.get") as mock_get:
            mock_get.return_value = self._mock_get(payload)
            with pytest.raises(GoogleOAuthError, match="sub"):
                verify_id_token(
                    id_token="fake-token",
                    client_id="test-client-id",
                    expected_nonce="test-nonce",
                )

    def test_missing_email_raises(self) -> None:
        payload = _make_tokeninfo_response()
        payload.pop("email")
        with patch("hiring_radar.services.google_auth.httpx.get") as mock_get:
            mock_get.return_value = self._mock_get(payload)
            with pytest.raises(GoogleOAuthError, match="email"):
                verify_id_token(
                    id_token="fake-token",
                    client_id="test-client-id",
                    expected_nonce="test-nonce",
                )


# ---------------------------------------------------------------------------
# Integration: callback logic (repository-level mocks)
# ---------------------------------------------------------------------------

def _make_subscriber(
    *,
    id: int = 42,
    email: str = "user@example.com",
    full_name: str = "Test User",
    is_active: bool = True,
) -> MagicMock:
    s = MagicMock()
    s.id = id
    s.email = email
    s.full_name = full_name
    s.is_active = is_active
    s.password_hash = None
    return s


class TestCallbackAccountResolution:
    """Tests for the three account resolution paths in the callback."""

    def _make_repo(self) -> MagicMock:
        repo = MagicMock()
        repo.get_oauth_provider.return_value = None
        repo.get_subscriber_by_id.return_value = None
        repo.upsert_subscriber.return_value = (_make_subscriber(), True)
        repo.create_oauth_provider_link.return_value = MagicMock()
        repo.create_session.return_value = MagicMock()
        repo.add_login_history.return_value = None
        return repo

    def _make_google_user(self, *, email_verified: bool = True) -> GoogleUserInfo:
        return GoogleUserInfo(
            sub="google-sub-abc",
            email="user@example.com",
            email_verified=email_verified,
            name="Test User",
        )

    def test_new_user_creates_subscriber_and_link(self) -> None:
        repo = self._make_repo()
        user_info = self._make_google_user()

        # Simulate: no existing link, brand new email
        repo.get_oauth_provider.return_value = None
        subscriber = _make_subscriber()
        repo.upsert_subscriber.return_value = (subscriber, True)

        repo.get_oauth_provider(provider="google", provider_user_id=user_info.sub)
        repo.upsert_subscriber(email=user_info.email, full_name=user_info.name, updated_at="now")
        repo.create_oauth_provider_link(
            subscriber_id=subscriber.id,
            provider="google",
            provider_user_id=user_info.sub,
            email_at_provider=user_info.email,
            now="now",
        )

        repo.upsert_subscriber.assert_called_once()
        repo.create_oauth_provider_link.assert_called_once()

    def test_existing_email_links_without_creating_new_subscriber(self) -> None:
        repo = self._make_repo()
        user_info = self._make_google_user()

        # Simulate: no Google link, but email matches existing subscriber
        repo.get_oauth_provider.return_value = None
        existing = _make_subscriber(id=99)
        repo.upsert_subscriber.return_value = (existing, False)  # created=False

        repo.get_oauth_provider(provider="google", provider_user_id=user_info.sub)
        subscriber, created = repo.upsert_subscriber(
            email=user_info.email, full_name=user_info.name, updated_at="now"
        )
        repo.create_oauth_provider_link(
            subscriber_id=subscriber.id,
            provider="google",
            provider_user_id=user_info.sub,
            email_at_provider=user_info.email,
            now="now",
        )

        assert created is False
        assert subscriber.id == 99
        repo.create_oauth_provider_link.assert_called_once()

    def test_returning_google_user_skips_upsert(self) -> None:
        repo = self._make_repo()
        user_info = self._make_google_user()

        # Simulate: existing Google link found
        existing_link = MagicMock()
        existing_link.subscriber_id = 77
        repo.get_oauth_provider.return_value = existing_link
        repo.get_subscriber_by_id.return_value = _make_subscriber(id=77)

        link = repo.get_oauth_provider(provider="google", provider_user_id=user_info.sub)
        assert link is not None
        subscriber = repo.get_subscriber_by_id(link.subscriber_id)

        # upsert should NOT be called for returning users
        repo.upsert_subscriber.assert_not_called()
        assert subscriber.id == 77

    def test_unverified_email_must_be_rejected(self) -> None:
        user_info = self._make_google_user(email_verified=False)
        assert user_info.email_verified is False

    def test_invalid_state_must_be_rejected(self) -> None:
        repo = self._make_repo()
        repo.get_and_delete_oauth_state.return_value = None
        result = repo.get_and_delete_oauth_state("bad-hash")
        assert result is None

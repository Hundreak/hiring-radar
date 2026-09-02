from __future__ import annotations

from .base import RepositoryDomain


class AuthRepository(RepositoryDomain):
    """Authentication and account-security repository facade.

    This facade delegates to the legacy root repository for now. It gives
    services and routers a stable domain-specific seam before the SQL
    implementations are moved out of ``repository.py`` in smaller patches.
    """

    def get_subscriber_by_email(self, *args, **kwargs):
        return self._call("get_subscriber_by_email", *args, **kwargs)

    def get_subscriber_by_id(self, *args, **kwargs):
        return self._call("get_subscriber_by_id", *args, **kwargs)

    def upsert_subscriber(self, *args, **kwargs):
        return self._call("upsert_subscriber", *args, **kwargs)

    def set_subscriber_password(self, *args, **kwargs):
        return self._call("set_subscriber_password", *args, **kwargs)

    def list_subscribers(self, *args, **kwargs):
        return self._call("list_subscribers", *args, **kwargs)

    def list_digest_enabled_subscribers(self, *args, **kwargs):
        return self._call("list_digest_enabled_subscribers", *args, **kwargs)

    def set_subscriber_active(self, *args, **kwargs):
        return self._call("set_subscriber_active", *args, **kwargs)

    def set_subscriber_digest_enabled(self, *args, **kwargs):
        return self._call("set_subscriber_digest_enabled", *args, **kwargs)

    def update_subscriber_fields_by_id(self, *args, **kwargs):
        return self._call("update_subscriber_fields_by_id", *args, **kwargs)

    def create_subscriber_magic_link(self, *args, **kwargs):
        return self._call("create_subscriber_magic_link", *args, **kwargs)

    def get_subscriber_magic_link_by_hash(self, *args, **kwargs):
        return self._call("get_subscriber_magic_link_by_hash", *args, **kwargs)

    def consume_subscriber_magic_link(self, *args, **kwargs):
        return self._call("consume_subscriber_magic_link", *args, **kwargs)

    def create_or_replace_subscriber_signup_verification(self, *args, **kwargs):
        return self._call("create_or_replace_subscriber_signup_verification", *args, **kwargs)

    def get_subscriber_signup_verification_by_email(self, *args, **kwargs):
        return self._call("get_subscriber_signup_verification_by_email", *args, **kwargs)

    def consume_subscriber_signup_verification(self, *args, **kwargs):
        return self._call("consume_subscriber_signup_verification", *args, **kwargs)

    def create_subscriber_password_reset_token(self, *args, **kwargs):
        return self._call("create_subscriber_password_reset_token", *args, **kwargs)

    def get_subscriber_password_reset_token_by_hash(self, *args, **kwargs):
        return self._call("get_subscriber_password_reset_token_by_hash", *args, **kwargs)

    def consume_subscriber_password_reset_token(self, *args, **kwargs):
        return self._call("consume_subscriber_password_reset_token", *args, **kwargs)

    def list_subscribers_paginated(self, *args, **kwargs):
        return self._call("list_subscribers_paginated", *args, **kwargs)

    def create_session(self, *args, **kwargs):
        return self._call("create_session", *args, **kwargs)

    def list_active_sessions(self, *args, **kwargs):
        return self._call("list_active_sessions", *args, **kwargs)

    def touch_session(self, *args, **kwargs):
        return self._call("touch_session", *args, **kwargs)

    def expire_session(self, *args, **kwargs):
        return self._call("expire_session", *args, **kwargs)

    def expire_all_other_sessions(self, *args, **kwargs):
        return self._call("expire_all_other_sessions", *args, **kwargs)

    def get_session_by_token_hash(self, *args, **kwargs):
        return self._call("get_session_by_token_hash", *args, **kwargs)

    def add_login_history(self, *args, **kwargs):
        return self._call("add_login_history", *args, **kwargs)

    def list_login_history(self, *args, **kwargs):
        return self._call("list_login_history", *args, **kwargs)

    def create_email_change_request(self, *args, **kwargs):
        return self._call("create_email_change_request", *args, **kwargs)

    def get_latest_email_change_request(self, *args, **kwargs):
        return self._call("get_latest_email_change_request", *args, **kwargs)

    def consume_email_change_request(self, *args, **kwargs):
        return self._call("consume_email_change_request", *args, **kwargs)

    def update_subscriber_email(self, *args, **kwargs):
        return self._call("update_subscriber_email", *args, **kwargs)

    def upsert_totp_secret(self, *args, **kwargs):
        return self._call("upsert_totp_secret", *args, **kwargs)

    def get_totp_secret(self, *args, **kwargs):
        return self._call("get_totp_secret", *args, **kwargs)

    def verify_totp_secret(self, *args, **kwargs):
        return self._call("verify_totp_secret", *args, **kwargs)

    def delete_totp_secret(self, *args, **kwargs):
        return self._call("delete_totp_secret", *args, **kwargs)

    def delete_subscriber_account(self, *args, **kwargs):
        return self._call("delete_subscriber_account", *args, **kwargs)

    def create_oauth_state(self, *args, **kwargs):
        return self._call("create_oauth_state", *args, **kwargs)

    def get_and_delete_oauth_state(self, *args, **kwargs):
        return self._call("get_and_delete_oauth_state", *args, **kwargs)

    def get_oauth_provider(self, *args, **kwargs):
        return self._call("get_oauth_provider", *args, **kwargs)

    def create_oauth_provider_link(self, *args, **kwargs):
        return self._call("create_oauth_provider_link", *args, **kwargs)

    def get_subscriber_counts(self, *args, **kwargs):
        return self._call("get_subscriber_counts", *args, **kwargs)

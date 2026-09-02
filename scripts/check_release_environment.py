#!/usr/bin/env python3
"""Validate production environment settings before a release cut.

The checker is intentionally conservative. It catches values that are safe for
local development but dangerous in production: placeholder secrets, insecure
cookies, disabled CSRF/rate limiting, demo employer mode and non-HTTPS URLs.
"""
from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

PRODUCTION_VALUES = {"production", "prod"}
REQUIRED_SECRET_KEYS = (
    "HIRING_RADAR_AUTH_SECRET",
    "HIRING_RADAR_ADMIN_SESSION_SECRET",
    "HIRING_RADAR_EMPLOYER_SESSION_SECRET",
)
COOKIE_SECURE_KEYS = (
    "HIRING_RADAR_SESSION_COOKIE_SECURE",
    "HIRING_RADAR_ADMIN_SESSION_COOKIE_SECURE",
    "HIRING_RADAR_EMPLOYER_SESSION_COOKIE_SECURE",
    "HIRING_RADAR_CSRF_COOKIE_SECURE",
)
MUST_BE_ENABLED = (
    "HIRING_RADAR_CSRF_ENABLED",
    "HIRING_RADAR_RATE_LIMIT_ENABLED",
    "HIRING_RADAR_OBSERVABILITY_ENABLED",
)
MUST_BE_DISABLED = (
    "HIRING_RADAR_EMPLOYER_DEMO_MODE",
    "HIRING_RADAR_EMPLOYER_ALLOW_MOCK_AUTH",
)
PLACEHOLDER_RE = re.compile(
    r"(change[-_ ]?me|replace[-_ ]?me|replace[-_ ]?with|example|placeholder|"
    r"dev[-_ ]|local[-_ ]?only|password|secret$)",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class CheckMessage:
    severity: str
    message: str


@dataclass(frozen=True, slots=True)
class ReleaseEnvironmentReport:
    checks: tuple[CheckMessage, ...]

    @property
    def failures(self) -> tuple[CheckMessage, ...]:
        return tuple(item for item in self.checks if item.severity == "FAIL")

    @property
    def warnings(self) -> tuple[CheckMessage, ...]:
        return tuple(item for item in self.checks if item.severity == "WARN")

    @property
    def ok(self) -> bool:
        return not self.failures


def parse_env_file(path: Path) -> dict[str, str]:
    """Parse a simple dotenv file without adding a runtime dependency."""

    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()
        if "=" not in line:
            raise ValueError(f"{path}:{line_number}: expected KEY=VALUE")
        key, value = line.split("=", 1)
        key = key.strip()
        value = _strip_inline_comment(value.strip())
        values[key] = _strip_quotes(value)
    return values


def evaluate_environment(
    config: dict[str, str],
    *,
    strict_production: bool = True,
) -> ReleaseEnvironmentReport:
    checks: list[CheckMessage] = []

    runtime_env = _get(config, "HIRING_RADAR_ENV", "APP_ENV", "ENVIRONMENT").lower()
    is_production = runtime_env in PRODUCTION_VALUES
    if strict_production and not is_production:
        checks.append(
            _fail(
                "HIRING_RADAR_ENV must be production/prod for release checks; "
                f"received {runtime_env or '<missing>'}."
            )
        )
    elif is_production:
        checks.append(_pass("Runtime environment is production."))
    else:
        checks.append(_warn("Runtime environment is not production; strict guards are relaxed."))

    _check_required_secrets(config, checks, enforce=is_production or strict_production)
    _check_admin_bootstrap(config, checks, enforce=is_production or strict_production)
    _check_security_flags(config, checks, enforce=is_production or strict_production)
    _check_urls(config, checks, enforce=is_production or strict_production)
    _check_storage(config, checks, enforce=is_production or strict_production)
    _check_email(config, checks, enforce=is_production or strict_production)
    _check_ai_runtime(config, checks)

    return ReleaseEnvironmentReport(tuple(checks))


def print_report(report: ReleaseEnvironmentReport) -> None:
    for item in report.checks:
        print(f"[{item.severity}] {item.message}")
    print(
        "Release environment summary: "
        f"{len(report.failures)} failure(s), {len(report.warnings)} warning(s)."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--env-file",
        default=os.getenv("HIRING_RADAR_RELEASE_ENV_FILE", ".env.production"),
        help="Production dotenv file to validate.",
    )
    parser.add_argument(
        "--strict-production",
        action="store_true",
        help="Require HIRING_RADAR_ENV=production/prod and production-safe values.",
    )
    parser.add_argument(
        "--allow-missing-env-file",
        action="store_true",
        help="Return success when the env file is missing. Intended only for local smoke tests.",
    )
    args = parser.parse_args(argv)

    env_path = Path(args.env_file)
    if not env_path.exists():
        message = f"Release env file not found: {env_path}"
        if args.allow_missing_env_file:
            print(f"[WARN] {message}")
            return 0
        print(f"[FAIL] {message}")
        return 2

    try:
        file_config = parse_env_file(env_path)
    except ValueError as exc:
        print(f"[FAIL] {exc}")
        return 1

    merged_config = {**os.environ, **file_config}
    report = evaluate_environment(
        merged_config,
        strict_production=args.strict_production,
    )
    print_report(report)
    return 0 if report.ok else 1


def _check_required_secrets(
    config: dict[str, str],
    checks: list[CheckMessage],
    *,
    enforce: bool,
) -> None:
    seen: dict[str, str] = {}
    for key in REQUIRED_SECRET_KEYS:
        value = config.get(key, "").strip()
        if _secret_is_unsafe(value):
            checks.append(_critical(enforce, f"{key} must be a strong non-placeholder secret."))
            continue
        if len(value) < 32:
            checks.append(_critical(enforce, f"{key} should be at least 32 characters."))
            continue
        seen[key] = value
        checks.append(_pass(f"{key} is present and non-placeholder."))

    reverse: dict[str, str] = {}
    for key, value in seen.items():
        if value in reverse:
            checks.append(_critical(enforce, f"{key} must not reuse {reverse[value]}."))
        else:
            reverse[value] = key


def _check_admin_bootstrap(
    config: dict[str, str],
    checks: list[CheckMessage],
    *,
    enforce: bool,
) -> None:
    admin_email = config.get("HIRING_RADAR_ADMIN_EMAIL", "").strip().lower()
    admin_password = config.get("HIRING_RADAR_ADMIN_PASSWORD", "").strip()
    if not admin_email or admin_email.endswith("@example.com"):
        checks.append(
            _critical(enforce, "HIRING_RADAR_ADMIN_EMAIL must not be an example address.")
        )
    else:
        checks.append(_pass("Admin bootstrap email is not an example address."))

    if len(admin_password) < 14 or PLACEHOLDER_RE.search(admin_password):
        checks.append(
            _critical(enforce, "HIRING_RADAR_ADMIN_PASSWORD must be rotated for release.")
        )
    else:
        checks.append(_pass("Admin bootstrap password does not look like a placeholder."))


def _check_security_flags(
    config: dict[str, str],
    checks: list[CheckMessage],
    *,
    enforce: bool,
) -> None:
    for key in COOKIE_SECURE_KEYS:
        if _bool_value(config.get(key), default=False):
            checks.append(_pass(f"{key}=true."))
        else:
            checks.append(_critical(enforce, f"{key} must be true in production."))

    for key in MUST_BE_ENABLED:
        if _bool_value(config.get(key), default=True):
            checks.append(_pass(f"{key}=true."))
        else:
            checks.append(_critical(enforce, f"{key} must stay enabled in production."))

    for key in MUST_BE_DISABLED:
        if _bool_value(config.get(key), default=False):
            checks.append(_critical(enforce, f"{key} must be false in production."))
        else:
            checks.append(_pass(f"{key}=false."))

    if _bool_value(config.get("HIRING_RADAR_RATE_LIMIT_TRUST_PROXY_HEADERS"), default=False):
        checks.append(
            _warn(
                "HIRING_RADAR_RATE_LIMIT_TRUST_PROXY_HEADERS=true; only use behind a trusted "
                "reverse proxy that strips spoofed headers."
            )
        )


def _check_urls(
    config: dict[str, str],
    checks: list[CheckMessage],
    *,
    enforce: bool,
) -> None:
    required_https = (
        "HIRING_RADAR_APP_BASE_URL",
        "BACKEND_URL",
        "GOOGLE_OAUTH_REDIRECT_URI",
    )
    for key in required_https:
        value = config.get(key, "").strip()
        if not value:
            checks.append(_critical(enforce, f"{key} is required for production releases."))
            continue
        parsed = urlparse(value)
        if parsed.scheme != "https":
            checks.append(_critical(enforce, f"{key} must use HTTPS in production."))
        else:
            checks.append(_pass(f"{key} uses HTTPS."))


def _check_storage(
    config: dict[str, str],
    checks: list[CheckMessage],
    *,
    enforce: bool,
) -> None:
    db_path = config.get("HIRING_RADAR_DB_PATH", "").strip()
    upload_dir = config.get("HIRING_RADAR_UPLOAD_DIR", "").strip()
    if not db_path or db_path == ":memory:" or db_path.startswith("/tmp/"):
        checks.append(_critical(enforce, "HIRING_RADAR_DB_PATH must be persistent storage."))
    else:
        checks.append(_pass("HIRING_RADAR_DB_PATH points to persistent-looking storage."))

    if not upload_dir or upload_dir.startswith("/tmp/"):
        checks.append(_critical(enforce, "HIRING_RADAR_UPLOAD_DIR must be persistent storage."))
    else:
        checks.append(_pass("HIRING_RADAR_UPLOAD_DIR points to persistent-looking storage."))


def _check_email(
    config: dict[str, str],
    checks: list[CheckMessage],
    *,
    enforce: bool,
) -> None:
    smtp_host = config.get("HIRING_RADAR_SMTP_HOST", "").strip().lower()
    smtp_password = config.get("HIRING_RADAR_SMTP_PASSWORD", "").strip()
    email_from = config.get("HIRING_RADAR_EMAIL_FROM", "").strip().lower()
    if not smtp_host or "example" in smtp_host:
        checks.append(
            _critical(enforce, "HIRING_RADAR_SMTP_HOST must be real for auth email flows.")
        )
    else:
        checks.append(_pass("SMTP host does not look like an example value."))

    if _secret_is_unsafe(smtp_password):
        checks.append(_critical(enforce, "HIRING_RADAR_SMTP_PASSWORD must be configured."))
    else:
        checks.append(_pass("SMTP password is present."))

    if not email_from or "example" in email_from:
        checks.append(_critical(enforce, "HIRING_RADAR_EMAIL_FROM must be a real sender."))
    else:
        checks.append(_pass("Email sender does not look like an example value."))


def _check_ai_runtime(config: dict[str, str], checks: list[CheckMessage]) -> None:
    if not _bool_value(config.get("AI_ENABLED"), default=False):
        checks.append(_pass("AI runtime is disabled; no model validation needed."))
        return
    if not config.get("AI_DEFAULT_MODEL", "").strip():
        checks.append(_warn("AI_ENABLED=true but AI_DEFAULT_MODEL is empty."))
    if not _bool_value(config.get("AI_AUDIT_ENABLED"), default=True):
        checks.append(_warn("AI_AUDIT_ENABLED=false reduces traceability of AI-assisted flows."))


def _get(config: dict[str, str], *keys: str) -> str:
    for key in keys:
        value = config.get(key)
        if value is not None and value.strip():
            return value.strip()
    return ""


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _strip_inline_comment(value: str) -> str:
    in_single = False
    in_double = False
    for index, char in enumerate(value):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            previous = value[index - 1] if index else " "
            if previous.isspace():
                return value[:index].strip()
    return value


def _secret_is_unsafe(value: str) -> bool:
    cleaned = value.strip()
    if not cleaned:
        return True
    if PLACEHOLDER_RE.search(cleaned):
        return True
    return len(set(cleaned)) <= 2


def _bool_value(value: str | None, *, default: bool) -> bool:
    if value is None or not value.strip():
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _critical(enforce: bool, message: str) -> CheckMessage:
    return _fail(message) if enforce else _warn(message)


def _pass(message: str) -> CheckMessage:
    return CheckMessage("PASS", message)


def _warn(message: str) -> CheckMessage:
    return CheckMessage("WARN", message)


def _fail(message: str) -> CheckMessage:
    return CheckMessage("FAIL", message)


if __name__ == "__main__":
    raise SystemExit(main())

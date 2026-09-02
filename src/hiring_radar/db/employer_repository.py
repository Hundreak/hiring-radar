from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

SYSTEM_ROLES: tuple[dict[str, Any], ...] = (
    {
        "role_key": "owner",
        "name": "Owner",
        "description": "Full workspace control, billing, security and data access.",
        "permissions": ["*"],
        "risk_level": "high",
    },
    {
        "role_key": "admin",
        "name": "Admin",
        "description": "Manage jobs, campaigns, candidates, team members and workspace settings.",
        "permissions": [
            "jobs:manage",
            "candidates:manage",
            "campaigns:manage",
            "team:manage",
            "settings:manage",
            "analytics:view",
        ],
        "risk_level": "high",
    },
    {
        "role_key": "recruiter",
        "name": "Recruiter",
        "description": "Manage jobs, candidates, pipeline and outreach campaigns.",
        "permissions": [
            "jobs:manage",
            "candidates:manage",
            "campaigns:manage",
            "analytics:view",
        ],
        "risk_level": "medium",
    },
    {
        "role_key": "hiring_manager",
        "name": "Hiring Manager",
        "description": "Review candidates, leave feedback and view hiring analytics.",
        "permissions": ["candidates:review", "scorecards:manage", "analytics:view"],
        "risk_level": "medium",
    },
    {
        "role_key": "viewer",
        "name": "Viewer",
        "description": "Read-only access to selected jobs, candidates and reports.",
        "permissions": ["jobs:view", "candidates:view", "analytics:view"],
        "risk_level": "low",
    },
)

DEFAULT_PIPELINE_STAGES: tuple[dict[str, Any], ...] = (
    {"stage_key": "new", "name": "Yeni", "position": 10, "is_terminal": False, "sla_days": 2},
    {"stage_key": "reviewed", "name": "İncelendi", "position": 20, "is_terminal": False, "sla_days": 3},
    {"stage_key": "shortlist", "name": "Kısa liste", "position": 30, "is_terminal": False, "sla_days": 3},
    {"stage_key": "interview", "name": "Görüşme", "position": 40, "is_terminal": False, "sla_days": 5},
    {"stage_key": "offer", "name": "Teklif", "position": 50, "is_terminal": False, "sla_days": 4},
    {"stage_key": "hired", "name": "İşe alındı", "position": 60, "is_terminal": True, "sla_days": None},
    {"stage_key": "archived", "name": "Arşiv", "position": 70, "is_terminal": True, "sla_days": None},
)


DEFAULT_EMPLOYER_COMMUNICATION_PREFERENCES: dict[str, Any] = {
    "candidate_alerts_enabled": True,
    "campaign_review_enabled": True,
    "weekly_leadership_digest_enabled": False,
    "product_updates_enabled": False,
    "security_alerts_enabled": True,
    "quiet_hours_enabled": False,
    "quiet_hours_start": "22:00",
    "quiet_hours_end": "08:00",
    "timezone": "Europe/Istanbul",
    "default_channel": "email",
    "notification_emails": [],
    "route_overdue_candidates_to": "owner",
    "route_hot_candidates_to": "recruiter",
    "route_campaign_review_to": "recruiter",
    "route_weekly_digest_to": "owner",
}

_EMPLOYER_COMMUNICATION_BOOLEAN_KEYS = {
    "candidate_alerts_enabled",
    "campaign_review_enabled",
    "weekly_leadership_digest_enabled",
    "product_updates_enabled",
    "security_alerts_enabled",
    "quiet_hours_enabled",
}

_EMPLOYER_COMMUNICATION_ROUTE_VALUES = {"owner", "admin", "recruiter", "hiring_manager"}
_EMPLOYER_COMMUNICATION_CHANNEL_VALUES = {"email", "in_app", "email_and_in_app"}


def _normalize_employer_communication_preferences(value: dict[str, Any] | None) -> dict[str, Any]:
    raw = value if isinstance(value, dict) else {}
    normalized = dict(DEFAULT_EMPLOYER_COMMUNICATION_PREFERENCES)

    for key in _EMPLOYER_COMMUNICATION_BOOLEAN_KEYS:
        if key in raw:
            normalized[key] = bool(raw[key])

    # Security alerts are a mandatory compliance channel for employer workspaces.
    normalized["security_alerts_enabled"] = True

    for key in ("quiet_hours_start", "quiet_hours_end"):
        candidate = str(raw.get(key, normalized[key])).strip()
        if len(candidate) == 5 and candidate[2] == ":":
            normalized[key] = candidate

    timezone = str(raw.get("timezone", normalized["timezone"])).strip()
    if timezone and "/" in timezone and " " not in timezone:
        normalized["timezone"] = timezone

    channel = str(raw.get("default_channel", normalized["default_channel"])).strip()
    if channel in _EMPLOYER_COMMUNICATION_CHANNEL_VALUES:
        normalized["default_channel"] = channel

    emails = raw.get("notification_emails", [])
    if isinstance(emails, list):
        normalized["notification_emails"] = [str(email).strip().lower() for email in emails if str(email).strip()][:10]

    for key in (
        "route_overdue_candidates_to",
        "route_hot_candidates_to",
        "route_campaign_review_to",
        "route_weekly_digest_to",
    ):
        route = str(raw.get(key, normalized[key])).strip()
        if route in _EMPLOYER_COMMUNICATION_ROUTE_VALUES:
            normalized[key] = route

    return normalized


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _to_json(value: Any, fallback: Any) -> str:
    if value is None:
        value = fallback
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _from_json(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return normalized or f"company-{uuid4().hex[:8]}"


@dataclass(frozen=True)
class EmployerCompany:
    id: int
    slug: str
    name: str
    legal_name: str | None
    website_url: str | None
    industry: str | None
    company_size: str | None
    country: str | None
    timezone: str
    default_locale: str
    plan_tier: str
    status: str
    brand_profile: dict[str, Any]
    settings: dict[str, Any]
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class EmployerUser:
    id: int
    email: str
    password_hash: str | None
    full_name: str
    title: str | None
    avatar_url: str | None
    status: str
    last_login_at: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class EmployerTeamMember:
    id: int
    company_id: int
    user_id: int | None
    invited_email: str | None
    role_key: str
    status: str
    invited_by_user_id: int | None
    invited_at: str | None
    joined_at: str | None
    last_active_at: str | None
    created_at: str
    updated_at: str
    email: str | None = None
    full_name: str | None = None


@dataclass(frozen=True)
class EmployerJob:
    id: int
    company_id: int
    title: str
    status: str
    location: str | None
    work_model: str | None
    employment_type: str | None
    seniority: str | None
    department: str | None
    salary_min: int | None
    salary_max: int | None
    salary_currency: str
    description: str | None
    required_skills: list[str]
    preferred_skills: list[str]
    quality_score: int
    quality_factors: dict[str, Any]
    risk_flags: list[str]
    created_by_user_id: int | None
    published_at: str | None
    closed_at: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class EmployerCandidate:
    id: int
    company_id: int
    external_candidate_id: str | None
    full_name: str
    headline: str | None
    email: str | None
    phone: str | None
    location: str | None
    current_company: str | None
    current_title: str | None
    years_experience: int | None
    availability: str | None
    source: str
    salary_expectation_min: int | None
    salary_expectation_max: int | None
    salary_currency: str
    work_model_preference: str | None
    match_score: int
    intent_score: int
    profile: dict[str, Any]
    skills: list[str]
    created_at: str
    updated_at: str




@dataclass(frozen=True)
class EmployerAuditEvent:
    id: int
    company_id: int
    actor_user_id: int | None
    actor_name: str | None
    actor_email: str | None
    event_type: str
    resource_type: str
    resource_id: str
    before: dict[str, Any]
    after: dict[str, Any]
    metadata: dict[str, Any]
    created_at: str

@dataclass(frozen=True)
class EmployerOutreachCampaign:
    id: str
    company_id: int
    created_by_user_id: int | None
    name: str
    status: str
    channel: str
    tone: str | None
    template_key: str | None
    candidate_ids: list[int]
    subject_preview: str | None
    message_preview: str | None
    response_rate: int
    metadata: dict[str, Any]
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class EmployerSendQueueItem:
    id: str
    campaign_id: str
    candidate_id: int
    subject: str
    message: str
    response_score: int
    status: str
    checks: list[str]
    metadata: dict[str, Any]
    prepared_by_user_id: int | None
    prepared_at: str | None
    updated_at: str


class EmployerRepository:
    """Production-oriented persistence layer for employer workspaces.

    This repository intentionally starts with the tables and high-level operations
    needed by the employer UI. Later patches can wire existing JSON-store flows to
    these methods without changing the database shape again.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def create_company(
        self,
        *,
        name: str,
        slug: str | None = None,
        legal_name: str | None = None,
        website_url: str | None = None,
        industry: str | None = None,
        company_size: str | None = None,
        country: str | None = "TR",
        timezone: str = "Europe/Istanbul",
        default_locale: str = "tr",
        plan_tier: str = "starter",
        brand_profile: dict[str, Any] | None = None,
        settings: dict[str, Any] | None = None,
    ) -> EmployerCompany:
        now = _now_iso()
        company_slug = slug or _slugify(name)
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO employer_companies (
                    slug, name, legal_name, website_url, industry, company_size,
                    country, timezone, default_locale, plan_tier, brand_profile_json,
                    settings_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    company_slug,
                    name,
                    legal_name,
                    website_url,
                    industry,
                    company_size,
                    country,
                    timezone,
                    default_locale,
                    plan_tier,
                    _to_json(brand_profile, {}),
                    _to_json(settings, {}),
                    now,
                    now,
                ),
            )
            company_id = int(cursor.lastrowid)
            self._seed_company_roles(company_id, now)
            self._seed_company_pipeline(company_id, now)

        company = self.get_company_by_id(company_id)
        if company is None:  # pragma: no cover - defensive guard
            raise RuntimeError("Employer company was not created.")
        return company

    def get_company_by_id(self, company_id: int) -> EmployerCompany | None:
        row = self.connection.execute(
            """
            SELECT *
            FROM employer_companies
            WHERE id = ?
            """,
            (company_id,),
        ).fetchone()
        return _row_to_company(row) if row else None

    def get_company_by_slug(self, slug: str) -> EmployerCompany | None:
        row = self.connection.execute(
            """
            SELECT *
            FROM employer_companies
            WHERE slug = ?
            """,
            (slug,),
        ).fetchone()
        return _row_to_company(row) if row else None

    def get_company_communication_preferences(self, company_id: int) -> dict[str, Any] | None:
        company = self.get_company_by_id(company_id)
        if company is None:
            return None
        return _normalize_employer_communication_preferences(
            company.settings.get("communication_preferences")
        )

    def update_company_communication_preferences(
        self,
        *,
        company_id: int,
        updates: dict[str, Any],
    ) -> dict[str, Any] | None:
        company = self.get_company_by_id(company_id)
        if company is None:
            return None

        current_preferences = _normalize_employer_communication_preferences(
            company.settings.get("communication_preferences")
        )
        merged_preferences = _normalize_employer_communication_preferences(
            {**current_preferences, **updates}
        )
        next_settings = dict(company.settings)
        next_settings["communication_preferences"] = merged_preferences
        now = _now_iso()

        with self.connection:
            self.connection.execute(
                """
                UPDATE employer_companies
                SET settings_json = ?, updated_at = ?
                WHERE id = ?
                """,
                (_to_json(next_settings, {}), now, company_id),
            )

        return merged_preferences

    def create_user(
        self,
        *,
        email: str,
        full_name: str,
        password_hash: str | None = None,
        title: str | None = None,
        avatar_url: str | None = None,
        status: str = "active",
    ) -> EmployerUser:
        now = _now_iso()
        normalized_email = email.strip().lower()
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO employer_users (
                    email, password_hash, full_name, title, avatar_url, status, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (normalized_email, password_hash, full_name, title, avatar_url, status, now, now),
            )
        user = self.get_user_by_id(int(cursor.lastrowid))
        if user is None:  # pragma: no cover
            raise RuntimeError("Employer user was not created.")
        return user

    def get_user_by_id(self, user_id: int) -> EmployerUser | None:
        row = self.connection.execute("SELECT * FROM employer_users WHERE id = ?", (user_id,)).fetchone()
        return _row_to_user(row) if row else None

    def get_user_by_email(self, email: str) -> EmployerUser | None:
        row = self.connection.execute(
            "SELECT * FROM employer_users WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()
        return _row_to_user(row) if row else None

    def update_user_last_login(self, user_id: int) -> None:
        now = _now_iso()
        with self.connection:
            self.connection.execute(
                """
                UPDATE employer_users
                SET last_login_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (now, now, user_id),
            )

    def add_team_member(
        self,
        *,
        company_id: int,
        user_id: int | None = None,
        invited_email: str | None = None,
        role_key: str = "recruiter",
        status: str = "active",
        invited_by_user_id: int | None = None,
    ) -> EmployerTeamMember:
        now = _now_iso()
        normalized_invited_email = invited_email.strip().lower() if invited_email else None
        joined_at = now if status == "active" and user_id is not None else None
        invited_at = now if status == "invited" else None
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO employer_team_members (
                    company_id, user_id, invited_email, role_key, status,
                    invited_by_user_id, invited_at, joined_at, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    company_id,
                    user_id,
                    normalized_invited_email,
                    role_key,
                    status,
                    invited_by_user_id,
                    invited_at,
                    joined_at,
                    now,
                    now,
                ),
            )
        member = self.get_team_member(int(cursor.lastrowid))
        if member is None:  # pragma: no cover
            raise RuntimeError("Employer team member was not created.")
        return member

    def get_team_member(self, member_id: int) -> EmployerTeamMember | None:
        row = self.connection.execute(
            """
            SELECT tm.*, u.email, u.full_name
            FROM employer_team_members tm
            LEFT JOIN employer_users u ON u.id = tm.user_id
            WHERE tm.id = ?
            """,
            (member_id,),
        ).fetchone()
        return _row_to_team_member(row) if row else None

    def get_active_team_member_for_user(self, *, company_id: int, user_id: int) -> EmployerTeamMember | None:
        row = self.connection.execute(
            """
            SELECT tm.*, u.email, u.full_name
            FROM employer_team_members tm
            LEFT JOIN employer_users u ON u.id = tm.user_id
            WHERE tm.company_id = ? AND tm.user_id = ? AND tm.status = 'active'
            ORDER BY
                CASE tm.role_key
                    WHEN 'owner' THEN 1
                    WHEN 'admin' THEN 2
                    WHEN 'recruiter' THEN 3
                    WHEN 'hiring_manager' THEN 4
                    ELSE 5
                END,
                tm.id
            LIMIT 1
            """,
            (company_id, user_id),
        ).fetchone()
        return _row_to_team_member(row) if row else None

    def get_primary_team_member_for_user(self, user_id: int) -> EmployerTeamMember | None:
        row = self.connection.execute(
            """
            SELECT tm.*, u.email, u.full_name
            FROM employer_team_members tm
            LEFT JOIN employer_users u ON u.id = tm.user_id
            WHERE tm.user_id = ? AND tm.status = 'active'
            ORDER BY
                CASE tm.role_key
                    WHEN 'owner' THEN 1
                    WHEN 'admin' THEN 2
                    WHEN 'recruiter' THEN 3
                    WHEN 'hiring_manager' THEN 4
                    ELSE 5
                END,
                tm.id
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
        return _row_to_team_member(row) if row else None

    def update_team_member(
        self,
        member_id: int,
        *,
        role_key: str | None = None,
        status: str | None = None,
    ) -> EmployerTeamMember | None:
        updates: list[str] = []
        params: list[Any] = []
        if role_key is not None:
            updates.append("role_key = ?")
            params.append(role_key)
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        if not updates:
            return self.get_team_member(member_id)
        updates.append("updated_at = ?")
        params.append(_now_iso())
        params.append(member_id)
        with self.connection:
            self.connection.execute(
                f"UPDATE employer_team_members SET {', '.join(updates)} WHERE id = ?",
                params,
            )
        return self.get_team_member(member_id)

    def list_team_members(self, company_id: int) -> list[EmployerTeamMember]:
        rows = self.connection.execute(
            """
            SELECT tm.*, u.email, u.full_name
            FROM employer_team_members tm
            LEFT JOIN employer_users u ON u.id = tm.user_id
            WHERE tm.company_id = ?
            ORDER BY tm.status, tm.role_key, COALESCE(u.full_name, tm.invited_email)
            """,
            (company_id,),
        ).fetchall()
        return [_row_to_team_member(row) for row in rows]

    def list_roles(self, company_id: int) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            """
            SELECT *
            FROM employer_roles
            WHERE company_id = ?
            ORDER BY id
            """,
            (company_id,),
        ).fetchall()
        return [
            {
                "id": row["id"],
                "company_id": row["company_id"],
                "role_key": row["role_key"],
                "name": row["name"],
                "description": row["description"],
                "permissions": _from_json(row["permissions_json"], []),
                "is_system": bool(row["is_system"]),
                "risk_level": row["risk_level"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]

    def list_pipeline_stages(self, company_id: int) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            """
            SELECT *
            FROM employer_pipeline_stages
            WHERE company_id = ?
            ORDER BY position
            """,
            (company_id,),
        ).fetchall()
        return [dict(row) | {"is_terminal": bool(row["is_terminal"])} for row in rows]

    def create_job(
        self,
        *,
        company_id: int,
        title: str,
        status: str = "draft",
        location: str | None = None,
        work_model: str | None = None,
        employment_type: str | None = None,
        seniority: str | None = None,
        department: str | None = None,
        salary_min: int | None = None,
        salary_max: int | None = None,
        salary_currency: str = "TRY",
        description: str | None = None,
        required_skills: list[str] | None = None,
        preferred_skills: list[str] | None = None,
        quality_score: int = 0,
        quality_factors: dict[str, Any] | None = None,
        risk_flags: list[str] | None = None,
        created_by_user_id: int | None = None,
        published_at: str | None = None,
    ) -> EmployerJob:
        now = _now_iso()
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO employer_jobs (
                    company_id, title, status, location, work_model, employment_type, seniority,
                    department, salary_min, salary_max, salary_currency, description,
                    required_skills_json, preferred_skills_json, quality_score, quality_factors_json,
                    risk_flags_json, created_by_user_id, published_at, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    company_id,
                    title,
                    status,
                    location,
                    work_model,
                    employment_type,
                    seniority,
                    department,
                    salary_min,
                    salary_max,
                    salary_currency,
                    description,
                    _to_json(required_skills, []),
                    _to_json(preferred_skills, []),
                    quality_score,
                    _to_json(quality_factors, {}),
                    _to_json(risk_flags, []),
                    created_by_user_id,
                    published_at,
                    now,
                    now,
                ),
            )
        job = self.get_job(int(cursor.lastrowid))
        if job is None:  # pragma: no cover
            raise RuntimeError("Employer job was not created.")
        return job

    def get_job(self, job_id: int) -> EmployerJob | None:
        row = self.connection.execute("SELECT * FROM employer_jobs WHERE id = ?", (job_id,)).fetchone()
        return _row_to_job(row) if row else None

    def list_jobs(self, company_id: int, *, status: str | None = None) -> list[EmployerJob]:
        params: list[Any] = [company_id]
        where = "company_id = ?"
        if status:
            where += " AND status = ?"
            params.append(status)
        rows = self.connection.execute(
            f"SELECT * FROM employer_jobs WHERE {where} ORDER BY updated_at DESC, id DESC",
            params,
        ).fetchall()
        return [_row_to_job(row) for row in rows]

    def upsert_candidate(
        self,
        *,
        company_id: int,
        full_name: str,
        external_candidate_id: str | None = None,
        headline: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        location: str | None = None,
        current_company: str | None = None,
        current_title: str | None = None,
        years_experience: int | None = None,
        availability: str | None = None,
        source: str = "manual",
        salary_expectation_min: int | None = None,
        salary_expectation_max: int | None = None,
        salary_currency: str = "TRY",
        work_model_preference: str | None = None,
        match_score: int = 0,
        intent_score: int = 0,
        profile: dict[str, Any] | None = None,
        skills: list[str] | None = None,
    ) -> EmployerCandidate:
        now = _now_iso()
        external_id = external_candidate_id or f"manual-{uuid4().hex[:12]}"
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO employer_candidates (
                    company_id, external_candidate_id, full_name, headline, email, phone, location,
                    current_company, current_title, years_experience, availability, source,
                    salary_expectation_min, salary_expectation_max, salary_currency,
                    work_model_preference, match_score, intent_score, profile_json, skills_json,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(company_id, external_candidate_id) DO UPDATE SET
                    full_name = excluded.full_name,
                    headline = excluded.headline,
                    email = excluded.email,
                    phone = excluded.phone,
                    location = excluded.location,
                    current_company = excluded.current_company,
                    current_title = excluded.current_title,
                    years_experience = excluded.years_experience,
                    availability = excluded.availability,
                    source = excluded.source,
                    salary_expectation_min = excluded.salary_expectation_min,
                    salary_expectation_max = excluded.salary_expectation_max,
                    salary_currency = excluded.salary_currency,
                    work_model_preference = excluded.work_model_preference,
                    match_score = excluded.match_score,
                    intent_score = excluded.intent_score,
                    profile_json = excluded.profile_json,
                    skills_json = excluded.skills_json,
                    updated_at = excluded.updated_at
                """,
                (
                    company_id,
                    external_id,
                    full_name,
                    headline,
                    email,
                    phone,
                    location,
                    current_company,
                    current_title,
                    years_experience,
                    availability,
                    source,
                    salary_expectation_min,
                    salary_expectation_max,
                    salary_currency,
                    work_model_preference,
                    match_score,
                    intent_score,
                    _to_json(profile, {}),
                    _to_json(skills, []),
                    now,
                    now,
                ),
            )
        candidate = self.get_candidate_by_external_id(company_id, external_id)
        if candidate is None:  # pragma: no cover
            raise RuntimeError("Employer candidate was not upserted.")
        return candidate

    def get_candidate_by_external_id(self, company_id: int, external_candidate_id: str) -> EmployerCandidate | None:
        row = self.connection.execute(
            """
            SELECT *
            FROM employer_candidates
            WHERE company_id = ? AND external_candidate_id = ?
            """,
            (company_id, external_candidate_id),
        ).fetchone()
        return _row_to_candidate(row) if row else None

    def list_candidates(self, company_id: int) -> list[EmployerCandidate]:
        rows = self.connection.execute(
            """
            SELECT *
            FROM employer_candidates
            WHERE company_id = ?
            ORDER BY match_score DESC, intent_score DESC, updated_at DESC
            """,
            (company_id,),
        ).fetchall()
        return [_row_to_candidate(row) for row in rows]

    def create_candidate_job_match(
        self,
        *,
        company_id: int,
        job_id: int,
        candidate_id: int,
        stage_key: str = "new",
        source: str = "radar",
        match_score: int = 0,
        intent_score: int = 0,
        explanation: dict[str, Any] | None = None,
    ) -> int:
        now = _now_iso()
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO employer_candidate_job_matches (
                    company_id, job_id, candidate_id, stage_key, source, match_score,
                    intent_score, explanation_json, last_activity_at, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(job_id, candidate_id) DO UPDATE SET
                    stage_key = excluded.stage_key,
                    source = excluded.source,
                    match_score = excluded.match_score,
                    intent_score = excluded.intent_score,
                    explanation_json = excluded.explanation_json,
                    last_activity_at = excluded.last_activity_at,
                    updated_at = excluded.updated_at
                """,
                (
                    company_id,
                    job_id,
                    candidate_id,
                    stage_key,
                    source,
                    match_score,
                    intent_score,
                    _to_json(explanation, {}),
                    now,
                    now,
                    now,
                ),
            )
        return int(cursor.lastrowid or 0)

    def add_candidate_tag(
        self,
        *,
        company_id: int,
        candidate_id: int,
        tag: str,
        created_by_user_id: int | None = None,
    ) -> None:
        now = _now_iso()
        normalized = " ".join(tag.strip().split())
        if not normalized:
            return
        with self.connection:
            self.connection.execute(
                """
                INSERT OR IGNORE INTO employer_candidate_tags (
                    company_id, candidate_id, tag, created_by_user_id, created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (company_id, candidate_id, normalized, created_by_user_id, now),
            )

    def list_candidate_tags(self, *, company_id: int, candidate_id: int) -> list[str]:
        rows = self.connection.execute(
            """
            SELECT tag
            FROM employer_candidate_tags
            WHERE company_id = ? AND candidate_id = ?
            ORDER BY created_at DESC, tag
            """,
            (company_id, candidate_id),
        ).fetchall()
        return [row["tag"] for row in rows]

    def add_candidate_note(
        self,
        *,
        company_id: int,
        candidate_id: int,
        body: str,
        author_user_id: int | None = None,
        tone: str = "neutral",
        visibility: str = "team",
    ) -> int:
        now = _now_iso()
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO employer_candidate_notes (
                    company_id, candidate_id, author_user_id, body, tone, visibility, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (company_id, candidate_id, author_user_id, body, tone, visibility, now, now),
            )
        return int(cursor.lastrowid)

    def create_outreach_campaign(
        self,
        *,
        company_id: int,
        name: str,
        channel: str,
        created_by_user_id: int | None = None,
        campaign_id: str | None = None,
        status: str = "draft",
        tone: str | None = None,
        template_key: str | None = None,
        candidate_ids: list[int] | None = None,
        subject_preview: str | None = None,
        message_preview: str | None = None,
        response_rate: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> EmployerOutreachCampaign:
        now = _now_iso()
        new_campaign_id = campaign_id or f"cmp_{uuid4().hex[:12]}"
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO employer_outreach_campaigns (
                    id, company_id, created_by_user_id, name, status, channel, tone,
                    template_key, candidate_ids_json, subject_preview, message_preview,
                    response_rate, metadata_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_campaign_id,
                    company_id,
                    created_by_user_id,
                    name,
                    status,
                    channel,
                    tone,
                    template_key,
                    _to_json(candidate_ids, []),
                    subject_preview,
                    message_preview,
                    response_rate,
                    _to_json(metadata, {}),
                    now,
                    now,
                ),
            )
        campaign = self.get_outreach_campaign(new_campaign_id)
        if campaign is None:  # pragma: no cover
            raise RuntimeError("Employer outreach campaign was not created.")
        return campaign

    def get_outreach_campaign(self, campaign_id: str) -> EmployerOutreachCampaign | None:
        row = self.connection.execute(
            "SELECT * FROM employer_outreach_campaigns WHERE id = ?",
            (campaign_id,),
        ).fetchone()
        return _row_to_campaign(row) if row else None

    def list_outreach_campaigns(self, company_id: int) -> list[EmployerOutreachCampaign]:
        rows = self.connection.execute(
            """
            SELECT *
            FROM employer_outreach_campaigns
            WHERE company_id = ?
            ORDER BY updated_at DESC
            """,
            (company_id,),
        ).fetchall()
        return [_row_to_campaign(row) for row in rows]

    def update_outreach_campaign(
        self,
        *,
        company_id: int,
        campaign_id: str,
        status: str | None = None,
        metadata: dict[str, Any] | None = None,
        subject_preview: str | None = None,
        message_preview: str | None = None,
        response_rate: int | None = None,
    ) -> EmployerOutreachCampaign | None:
        existing = self.get_outreach_campaign(campaign_id)
        if existing is None or existing.company_id != company_id:
            return None

        next_status = status or existing.status
        next_metadata = existing.metadata | (metadata or {})
        next_subject_preview = existing.subject_preview if subject_preview is None else subject_preview
        next_message_preview = existing.message_preview if message_preview is None else message_preview
        next_response_rate = existing.response_rate if response_rate is None else max(0, min(100, int(response_rate)))
        now = _now_iso()
        with self.connection:
            self.connection.execute(
                """
                UPDATE employer_outreach_campaigns
                SET status = ?, metadata_json = ?, subject_preview = ?, message_preview = ?,
                    response_rate = ?, updated_at = ?
                WHERE id = ? AND company_id = ?
                """,
                (
                    next_status,
                    _to_json(next_metadata, {}),
                    next_subject_preview,
                    next_message_preview,
                    next_response_rate,
                    now,
                    campaign_id,
                    company_id,
                ),
            )
        return self.get_outreach_campaign(campaign_id)

    def get_outreach_campaign_for_company(
        self,
        *,
        company_id: int,
        campaign_id: str,
    ) -> EmployerOutreachCampaign | None:
        campaign = self.get_outreach_campaign(campaign_id)
        if campaign is None or campaign.company_id != company_id:
            return None
        return campaign

    def replace_campaign_send_queue(
        self,
        *,
        company_id: int,
        campaign_id: str,
        items: list[dict[str, Any]],
        prepared_by_user_id: int | None = None,
    ) -> list[EmployerSendQueueItem] | None:
        campaign = self.get_outreach_campaign_for_company(company_id=company_id, campaign_id=campaign_id)
        if campaign is None:
            return None

        allowed_candidate_ids = {int(item) for item in campaign.candidate_ids}
        now = _now_iso()
        normalized_items: list[tuple[str, int, str, str, int, str, str, str]] = []
        for raw_item in items:
            try:
                candidate_id = int(raw_item.get("candidate_id"))
            except (TypeError, ValueError):
                continue
            if candidate_id not in allowed_candidate_ids:
                continue
            self.ensure_candidate_placeholder(company_id=company_id, candidate_id=candidate_id)
            status = str(raw_item.get("status") or "review")
            if status not in {"ready", "review", "blocked"}:
                status = "review"
            checks = [str(item).strip() for item in raw_item.get("checks", []) if str(item).strip()]
            item_id = str(raw_item.get("id") or f"qi_{campaign_id}_{candidate_id}")
            subject = str(raw_item.get("subject") or "").strip()
            message = str(raw_item.get("message") or "").strip()
            response_score = max(0, min(100, int(raw_item.get("response_score") or 0)))
            metadata = raw_item.get("metadata") if isinstance(raw_item.get("metadata"), dict) else {}
            normalized_items.append(
                (
                    item_id,
                    candidate_id,
                    subject,
                    message,
                    response_score,
                    status,
                    _to_json(checks, []),
                    _to_json(metadata, {}),
                )
            )

        with self.connection:
            self.connection.execute(
                "DELETE FROM employer_send_queue_items WHERE campaign_id = ?",
                (campaign_id,),
            )
            for item in normalized_items:
                self.connection.execute(
                    """
                    INSERT INTO employer_send_queue_items (
                        id, campaign_id, candidate_id, subject, message, response_score,
                        status, checks_json, metadata_json, prepared_by_user_id, prepared_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item[0],
                        campaign_id,
                        item[1],
                        item[2],
                        item[3],
                        item[4],
                        item[5],
                        item[6],
                        item[7],
                        prepared_by_user_id,
                        now,
                        now,
                    ),
                )
        return self.list_send_queue_items(company_id=company_id, campaign_id=campaign_id)

    def list_send_queue_items(
        self,
        *,
        company_id: int,
        campaign_id: str,
    ) -> list[EmployerSendQueueItem] | None:
        campaign = self.get_outreach_campaign_for_company(company_id=company_id, campaign_id=campaign_id)
        if campaign is None:
            return None
        rows = self.connection.execute(
            """
            SELECT q.*
            FROM employer_send_queue_items q
            INNER JOIN employer_outreach_campaigns c ON c.id = q.campaign_id
            WHERE q.campaign_id = ? AND c.company_id = ?
            ORDER BY q.response_score DESC, q.updated_at DESC, q.id
            """,
            (campaign_id, company_id),
        ).fetchall()
        return [_row_to_send_queue_item(row) for row in rows]

    def update_send_queue_item(
        self,
        *,
        company_id: int,
        campaign_id: str,
        item_id: str,
        status: str | None = None,
        checks: list[str] | None = None,
    ) -> EmployerSendQueueItem | None:
        campaign = self.get_outreach_campaign_for_company(company_id=company_id, campaign_id=campaign_id)
        if campaign is None:
            return None
        existing = self.connection.execute(
            """
            SELECT q.*
            FROM employer_send_queue_items q
            INNER JOIN employer_outreach_campaigns c ON c.id = q.campaign_id
            WHERE q.id = ? AND q.campaign_id = ? AND c.company_id = ?
            """,
            (item_id, campaign_id, company_id),
        ).fetchone()
        if existing is None:
            return None
        next_status = status if status in {"ready", "review", "blocked", "sent", "cancelled"} else existing["status"]
        next_checks = _from_json(existing["checks_json"], []) if checks is None else [str(item).strip() for item in checks if str(item).strip()]
        now = _now_iso()
        with self.connection:
            self.connection.execute(
                """
                UPDATE employer_send_queue_items
                SET status = ?, checks_json = ?, updated_at = ?
                WHERE id = ? AND campaign_id = ?
                """,
                (next_status, _to_json(next_checks, []), now, item_id, campaign_id),
            )
        row = self.connection.execute(
            "SELECT * FROM employer_send_queue_items WHERE id = ? AND campaign_id = ?",
            (item_id, campaign_id),
        ).fetchone()
        return _row_to_send_queue_item(row) if row else None

    def list_outreach_audit_events(
        self,
        *,
        company_id: int,
        campaign_id: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            """
            SELECT e.*, u.full_name AS actor_name
            FROM employer_audit_events e
            LEFT JOIN employer_users u ON u.id = e.actor_user_id
            WHERE e.company_id = ?
              AND (
                    (e.resource_type = 'outreach_campaign' AND e.resource_id = ?)
                 OR (e.resource_type = 'send_queue' AND e.resource_id = ?)
                 OR (e.resource_type = 'send_queue_item' AND json_extract(e.metadata_json, '$.campaign_id') = ?)
              )
            ORDER BY e.created_at DESC, e.id DESC
            LIMIT ?
            """,
            (company_id, campaign_id, f"queue_{campaign_id}", campaign_id, limit),
        ).fetchall()
        return [_row_to_outreach_audit_event(row) for row in rows]

    def create_audit_event(
        self,
        *,
        company_id: int,
        event_type: str,
        resource_type: str,
        resource_id: str,
        actor_user_id: int | None = None,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        now = _now_iso()
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO employer_audit_events (
                    company_id, actor_user_id, event_type, resource_type, resource_id,
                    before_json, after_json, metadata_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    company_id,
                    actor_user_id,
                    event_type,
                    resource_type,
                    resource_id,
                    _to_json(before, {}),
                    _to_json(after, {}),
                    _to_json(metadata, {}),
                    now,
                ),
            )
        return int(cursor.lastrowid)

    def get_audit_event(
        self,
        *,
        company_id: int,
        event_id: int,
    ) -> EmployerAuditEvent | None:
        row = self.connection.execute(
            """
            SELECT e.*, u.full_name AS actor_name, u.email AS actor_email
            FROM employer_audit_events e
            LEFT JOIN employer_users u ON u.id = e.actor_user_id
            WHERE e.company_id = ? AND e.id = ?
            """,
            (company_id, event_id),
        ).fetchone()
        return _row_to_employer_audit_event(row) if row else None

    def list_audit_events(
        self,
        *,
        company_id: int,
        limit: int = 100,
        offset: int = 0,
        event_type: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        actor_user_id: int | None = None,
        created_from: str | None = None,
        created_to: str | None = None,
    ) -> list[EmployerAuditEvent]:
        where = ["e.company_id = ?"]
        params: list[Any] = [company_id]
        if event_type:
            where.append("e.event_type = ?")
            params.append(event_type)
        if resource_type:
            where.append("e.resource_type = ?")
            params.append(resource_type)
        if resource_id:
            where.append("e.resource_id = ?")
            params.append(resource_id)
        if actor_user_id is not None:
            where.append("e.actor_user_id = ?")
            params.append(actor_user_id)
        if created_from:
            where.append("e.created_at >= ?")
            params.append(created_from)
        if created_to:
            where.append("e.created_at <= ?")
            params.append(created_to)

        safe_limit = max(1, min(int(limit), 500))
        safe_offset = max(0, int(offset))
        params.extend([safe_limit, safe_offset])
        rows = self.connection.execute(
            f"""
            SELECT e.*, u.full_name AS actor_name, u.email AS actor_email
            FROM employer_audit_events e
            LEFT JOIN employer_users u ON u.id = e.actor_user_id
            WHERE {' AND '.join(where)}
            ORDER BY e.created_at DESC, e.id DESC
            LIMIT ? OFFSET ?
            """,
            tuple(params),
        ).fetchall()
        return [_row_to_employer_audit_event(row) for row in rows]

    def count_audit_events(
        self,
        *,
        company_id: int,
        event_type: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        actor_user_id: int | None = None,
        created_from: str | None = None,
        created_to: str | None = None,
    ) -> int:
        where = ["company_id = ?"]
        params: list[Any] = [company_id]
        if event_type:
            where.append("event_type = ?")
            params.append(event_type)
        if resource_type:
            where.append("resource_type = ?")
            params.append(resource_type)
        if resource_id:
            where.append("resource_id = ?")
            params.append(resource_id)
        if actor_user_id is not None:
            where.append("actor_user_id = ?")
            params.append(actor_user_id)
        if created_from:
            where.append("created_at >= ?")
            params.append(created_from)
        if created_to:
            where.append("created_at <= ?")
            params.append(created_to)
        row = self.connection.execute(
            f"SELECT COUNT(*) AS total FROM employer_audit_events WHERE {' AND '.join(where)}",
            tuple(params),
        ).fetchone()
        return int(row["total"] if row else 0)


    def get_candidate(self, *, company_id: int, candidate_id: int) -> EmployerCandidate | None:
        row = self.connection.execute(
            """
            SELECT *
            FROM employer_candidates
            WHERE company_id = ? AND id = ?
            """,
            (company_id, candidate_id),
        ).fetchone()
        return _row_to_candidate(row) if row else None

    def ensure_candidate_placeholder(
        self,
        *,
        company_id: int,
        candidate_id: int,
        full_name: str | None = None,
        source: str = "talent_radar",
    ) -> EmployerCandidate:
        existing = self.get_candidate(company_id=company_id, candidate_id=candidate_id)
        if existing is not None:
            return existing

        now = _now_iso()
        candidate_name = full_name or f"Aday {candidate_id}"
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO employer_candidates (
                    id, company_id, external_candidate_id, full_name, source,
                    profile_json, skills_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    candidate_id,
                    company_id,
                    f"ui-{candidate_id}",
                    candidate_name,
                    source,
                    _to_json({}, {}),
                    _to_json([], []),
                    now,
                    now,
                ),
            )
        candidate = self.get_candidate(company_id=company_id, candidate_id=candidate_id)
        if candidate is None:  # pragma: no cover - defensive guard
            raise RuntimeError("Employer candidate placeholder was not created.")
        return candidate

    def remove_candidate_tag(
        self,
        *,
        company_id: int,
        candidate_id: int,
        tag: str,
    ) -> None:
        normalized = " ".join(tag.strip().split())
        if not normalized:
            return
        with self.connection:
            self.connection.execute(
                """
                DELETE FROM employer_candidate_tags
                WHERE company_id = ? AND candidate_id = ? AND tag = ?
                """,
                (company_id, candidate_id, normalized),
            )

    def list_candidate_notes(self, *, company_id: int, candidate_id: int) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            """
            SELECT n.*, u.full_name AS author_name
            FROM employer_candidate_notes n
            LEFT JOIN employer_users u ON u.id = n.author_user_id
            WHERE n.company_id = ? AND n.candidate_id = ?
            ORDER BY n.created_at DESC, n.id DESC
            """,
            (company_id, candidate_id),
        ).fetchall()
        return [
            {
                "id": f"note-{row['id']}",
                "author": row["author_name"] or "Sen",
                "body": row["body"],
                "createdAt": row["created_at"],
                "tone": row["tone"],
            }
            for row in rows
        ]

    def get_candidate_workflow(self, company_id: int) -> dict[str, dict[str, Any]]:
        candidates = self.connection.execute(
            """
            SELECT id
            FROM employer_candidates
            WHERE company_id = ?
            ORDER BY updated_at DESC, id DESC
            """,
            (company_id,),
        ).fetchall()
        workflow: dict[str, dict[str, Any]] = {
            str(row["id"]): {"tags": [], "notes": []} for row in candidates
        }

        tag_rows = self.connection.execute(
            """
            SELECT candidate_id, tag
            FROM employer_candidate_tags
            WHERE company_id = ?
            ORDER BY created_at DESC, tag
            """,
            (company_id,),
        ).fetchall()
        for row in tag_rows:
            item = workflow.setdefault(str(row["candidate_id"]), {"tags": [], "notes": []})
            item.setdefault("tags", []).append(row["tag"])

        note_rows = self.connection.execute(
            """
            SELECT n.*, u.full_name AS author_name
            FROM employer_candidate_notes n
            LEFT JOIN employer_users u ON u.id = n.author_user_id
            WHERE n.company_id = ?
            ORDER BY n.created_at DESC, n.id DESC
            """,
            (company_id,),
        ).fetchall()
        for row in note_rows:
            item = workflow.setdefault(str(row["candidate_id"]), {"tags": [], "notes": []})
            item.setdefault("notes", []).append(
                {
                    "id": f"note-{row['id']}",
                    "author": row["author_name"] or "Sen",
                    "body": row["body"],
                    "createdAt": row["created_at"],
                    "tone": row["tone"],
                }
            )

        match_rows = self.connection.execute(
            """
            SELECT candidate_id, job_id, stage_key, updated_at, last_activity_at
            FROM employer_candidate_job_matches
            WHERE company_id = ? AND is_archived = 0
            ORDER BY updated_at DESC, id DESC
            """,
            (company_id,),
        ).fetchall()
        seen_stage_candidates: set[int] = set()
        for row in match_rows:
            candidate_id = int(row["candidate_id"])
            if candidate_id in seen_stage_candidates:
                continue
            seen_stage_candidates.add(candidate_id)
            item = workflow.setdefault(str(candidate_id), {"tags": [], "notes": []})
            item["stage"] = row["stage_key"]
            item["jobId"] = row["job_id"]
            item["stageChangedAt"] = row["last_activity_at"] or row["updated_at"]

        return workflow

    def get_or_create_default_job(
        self,
        *,
        company_id: int,
        created_by_user_id: int | None = None,
    ) -> EmployerJob:
        row = self.connection.execute(
            """
            SELECT *
            FROM employer_jobs
            WHERE company_id = ? AND title = ?
            ORDER BY id
            LIMIT 1
            """,
            (company_id, "Genel Yetenek Havuzu"),
        ).fetchone()
        if row:
            return _row_to_job(row)
        return self.create_job(
            company_id=company_id,
            title="Genel Yetenek Havuzu",
            status="draft",
            department="Talent",
            created_by_user_id=created_by_user_id,
        )

    def update_candidate_stage(
        self,
        *,
        company_id: int,
        candidate_id: int,
        stage_key: str,
        job_id: int | None = None,
        changed_by_user_id: int | None = None,
        note: str | None = None,
    ) -> dict[str, Any]:
        self.ensure_candidate_placeholder(company_id=company_id, candidate_id=candidate_id)
        job = self.get_job(job_id) if job_id is not None else None
        if job is None or job.company_id != company_id:
            job = self.get_or_create_default_job(
                company_id=company_id,
                created_by_user_id=changed_by_user_id,
            )

        existing = self.connection.execute(
            """
            SELECT *
            FROM employer_candidate_job_matches
            WHERE company_id = ? AND job_id = ? AND candidate_id = ?
            """,
            (company_id, job.id, candidate_id),
        ).fetchone()
        from_stage = existing["stage_key"] if existing else None
        now = _now_iso()
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO employer_candidate_job_matches (
                    company_id, job_id, candidate_id, stage_key, source, match_score,
                    intent_score, explanation_json, last_activity_at, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, 'radar', 0, 0, '{}', ?, ?, ?)
                ON CONFLICT(job_id, candidate_id) DO UPDATE SET
                    stage_key = excluded.stage_key,
                    last_activity_at = excluded.last_activity_at,
                    updated_at = excluded.updated_at
                """,
                (company_id, job.id, candidate_id, stage_key, now, now, now),
            )
            self.connection.execute(
                """
                INSERT INTO employer_candidate_stage_history (
                    company_id, candidate_id, job_id, from_stage_key, to_stage_key,
                    changed_by_user_id, note, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (company_id, candidate_id, job.id, from_stage, stage_key, changed_by_user_id, note, now),
            )
        return {
            "candidate_id": candidate_id,
            "job_id": job.id,
            "from_stage": from_stage,
            "to_stage": stage_key,
            "changed_at": now,
        }


    def get_dashboard_stats(self, company_id: int) -> dict[str, Any]:
        """Return production dashboard KPIs derived from employer DB tables."""

        job_row = self.connection.execute(
            """
            SELECT
                COUNT(*) AS total_jobs,
                COALESCE(SUM(CASE WHEN status IN ('published', 'paused') THEN 1 ELSE 0 END), 0) AS active_jobs
            FROM employer_jobs
            WHERE company_id = ?
            """,
            (company_id,),
        ).fetchone()
        match_row = self.connection.execute(
            """
            SELECT
                COUNT(*) AS total_applications,
                COALESCE(SUM(CASE WHEN stage_key IN ('new', 'reviewed') THEN 1 ELSE 0 END), 0) AS pending_reviews,
                COALESCE(AVG(match_score), 0) AS avg_match_score
            FROM employer_candidate_job_matches
            WHERE company_id = ? AND is_archived = 0
            """,
            (company_id,),
        ).fetchone()
        return {
            "active_jobs": int(job_row["active_jobs"] or 0) if job_row else 0,
            "total_jobs": int(job_row["total_jobs"] or 0) if job_row else 0,
            "total_applications": int(match_row["total_applications"] or 0) if match_row else 0,
            "pending_reviews": int(match_row["pending_reviews"] or 0) if match_row else 0,
            "avg_match_score": round(float(match_row["avg_match_score"] or 0), 1) if match_row else 0.0,
            # Historical deltas need an analytics snapshot table; keep them explicit zeros
            # instead of serving misleading demo trends.
            "active_jobs_delta": 0,
            "applications_delta": 0,
            "pending_delta": 0,
            "match_score_delta": 0.0,
        }

    def list_dashboard_jobs(
        self,
        company_id: int,
        *,
        status: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Return employer jobs with candidate counts and average match score."""

        params: list[Any] = [company_id]
        where = "j.company_id = ?"
        if status:
            where += " AND j.status = ?"
            params.append(status)
        limit_sql = ""
        if limit is not None:
            limit_sql = " LIMIT ?"
            params.append(max(1, int(limit)))
        rows = self.connection.execute(
            f"""
            SELECT
                j.*,
                COUNT(m.id) AS applicants,
                COALESCE(AVG(m.match_score), 0) AS match_avg,
                COALESCE(SUM(CASE WHEN m.match_score >= 75 THEN 1 ELSE 0 END), 0) AS qualified_applicants
            FROM employer_jobs j
            LEFT JOIN employer_candidate_job_matches m
              ON m.company_id = j.company_id
             AND m.job_id = j.id
             AND m.is_archived = 0
            WHERE {where}
            GROUP BY j.id
            ORDER BY COALESCE(j.published_at, j.updated_at, j.created_at) DESC, j.id DESC
            {limit_sql}
            """,
            tuple(params),
        ).fetchall()
        return [_row_to_dashboard_job(row) for row in rows]

    def list_dashboard_candidates(self, company_id: int, *, limit: int | None = None) -> list[dict[str, Any]]:
        """Return candidates ordered by their strongest current match."""

        params: list[Any] = [company_id]
        limit_sql = ""
        if limit is not None:
            limit_sql = " LIMIT ?"
            params.append(max(1, int(limit)))
        rows = self.connection.execute(
            f"""
            SELECT
                c.*,
                COALESCE(MAX(m.match_score), c.match_score, 0) AS dashboard_match_score,
                COALESCE(MAX(m.intent_score), c.intent_score, 0) AS dashboard_intent_score,
                (
                    SELECT mx.stage_key
                    FROM employer_candidate_job_matches mx
                    WHERE mx.company_id = c.company_id
                      AND mx.candidate_id = c.id
                      AND mx.is_archived = 0
                    ORDER BY mx.updated_at DESC, mx.id DESC
                    LIMIT 1
                ) AS stage_key,
                (
                    SELECT mx.updated_at
                    FROM employer_candidate_job_matches mx
                    WHERE mx.company_id = c.company_id
                      AND mx.candidate_id = c.id
                      AND mx.is_archived = 0
                    ORDER BY mx.updated_at DESC, mx.id DESC
                    LIMIT 1
                ) AS last_activity_at
            FROM employer_candidates c
            LEFT JOIN employer_candidate_job_matches m
              ON m.company_id = c.company_id
             AND m.candidate_id = c.id
             AND m.is_archived = 0
            WHERE c.company_id = ?
            GROUP BY c.id
            ORDER BY dashboard_match_score DESC, dashboard_intent_score DESC, c.updated_at DESC, c.id DESC
            {limit_sql}
            """,
            tuple(params),
        ).fetchall()
        return [_row_to_dashboard_candidate(row) for row in rows]

    def get_dashboard_candidate(self, *, company_id: int, candidate_id: int) -> dict[str, Any] | None:
        rows = self.connection.execute(
            """
            SELECT
                c.*,
                COALESCE(MAX(m.match_score), c.match_score, 0) AS dashboard_match_score,
                COALESCE(MAX(m.intent_score), c.intent_score, 0) AS dashboard_intent_score,
                (
                    SELECT mx.stage_key
                    FROM employer_candidate_job_matches mx
                    WHERE mx.company_id = c.company_id
                      AND mx.candidate_id = c.id
                      AND mx.is_archived = 0
                    ORDER BY mx.updated_at DESC, mx.id DESC
                    LIMIT 1
                ) AS stage_key,
                (
                    SELECT mx.updated_at
                    FROM employer_candidate_job_matches mx
                    WHERE mx.company_id = c.company_id
                      AND mx.candidate_id = c.id
                      AND mx.is_archived = 0
                    ORDER BY mx.updated_at DESC, mx.id DESC
                    LIMIT 1
                ) AS last_activity_at
            FROM employer_candidates c
            LEFT JOIN employer_candidate_job_matches m
              ON m.company_id = c.company_id
             AND m.candidate_id = c.id
             AND m.is_archived = 0
            WHERE c.company_id = ? AND c.id = ?
            GROUP BY c.id
            """,
            (company_id, candidate_id),
        ).fetchone()
        if rows is None:
            return None
        candidate = _row_to_dashboard_candidate(rows)
        match = self.connection.execute(
            """
            SELECT m.*, j.title AS job_title, j.department AS job_department
            FROM employer_candidate_job_matches m
            LEFT JOIN employer_jobs j ON j.id = m.job_id AND j.company_id = m.company_id
            WHERE m.company_id = ? AND m.candidate_id = ? AND m.is_archived = 0
            ORDER BY m.match_score DESC, m.updated_at DESC, m.id DESC
            LIMIT 1
            """,
            (company_id, candidate_id),
        ).fetchone()
        if match is not None:
            explanation = _from_json(match["explanation_json"], {})
            candidate["match_breakdown"] = explanation.get("breakdown") or explanation.get("scores") or {}
            candidate["ai_note"] = explanation.get("summary") or explanation.get("note") or "Bu aday gerçek işveren veritabanındaki sinyallerle listelendi."
            candidate["target_job"] = {
                "id": match["job_id"],
                "title": match["job_title"],
                "department": match["job_department"],
            }
        else:
            candidate["match_breakdown"] = {}
            candidate["ai_note"] = "Bu aday için henüz iş eşleşmesi oluşturulmamış."
        return candidate

    def list_dashboard_matches(self, company_id: int, *, limit: int | None = None) -> list[dict[str, Any]]:
        params: list[Any] = [company_id]
        limit_sql = ""
        if limit is not None:
            limit_sql = " LIMIT ?"
            params.append(max(1, int(limit)))
        rows = self.connection.execute(
            f"""
            SELECT
                m.*,
                c.full_name AS candidate_name,
                c.headline AS candidate_headline,
                c.location AS candidate_location,
                c.skills_json AS candidate_skills_json,
                c.years_experience AS candidate_years_experience,
                j.title AS job_title,
                j.department AS job_department,
                j.location AS job_location
            FROM employer_candidate_job_matches m
            INNER JOIN employer_candidates c ON c.id = m.candidate_id AND c.company_id = m.company_id
            INNER JOIN employer_jobs j ON j.id = m.job_id AND j.company_id = m.company_id
            WHERE m.company_id = ? AND m.is_archived = 0
            ORDER BY m.match_score DESC, m.updated_at DESC, m.id DESC
            {limit_sql}
            """,
            tuple(params),
        ).fetchall()
        return [_row_to_dashboard_match(row) for row in rows]

    def list_dashboard_activity(self, company_id: int, *, limit: int = 10) -> list[dict[str, Any]]:
        """Return a compact activity stream from audit, job and match data."""

        audit_rows = self.connection.execute(
            """
            SELECT event_type, resource_type, resource_id, created_at, metadata_json, after_json
            FROM employer_audit_events
            WHERE company_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (company_id, max(1, limit)),
        ).fetchall()
        activities: list[dict[str, Any]] = []
        for row in audit_rows:
            after = _from_json(row["after_json"], {})
            metadata = _from_json(row["metadata_json"], {})
            title = _activity_title(row["event_type"])
            detail = after.get("title") or after.get("full_name") or after.get("tag") or metadata.get("note")
            activities.append(
                {
                    "type": _activity_type(row["event_type"]),
                    "event_type": row["event_type"],
                    "text": f"{title}: {detail}" if detail else title,
                    "time": row["created_at"],
                    "timestamp": row["created_at"],
                    "resource_type": row["resource_type"],
                    "resource_id": row["resource_id"],
                }
            )
        if activities:
            return activities[:limit]

        job_rows = self.connection.execute(
            """
            SELECT id, title, status, created_at
            FROM employer_jobs
            WHERE company_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (company_id, max(1, limit)),
        ).fetchall()
        for row in job_rows:
            activities.append(
                {
                    "type": "job",
                    "event_type": "employer.job.created",
                    "text": f"İlan oluşturuldu: {row['title']}",
                    "time": row["created_at"],
                    "timestamp": row["created_at"],
                    "resource_type": "job",
                    "resource_id": str(row["id"]),
                }
            )
        return activities[:limit]

    def get_dashboard_analytics(self, company_id: int, *, period: str = "30d") -> dict[str, Any]:
        stats = self.get_dashboard_stats(company_id)
        hired_row = self.connection.execute(
            """
            SELECT COUNT(*) AS hired_count
            FROM employer_candidate_job_matches
            WHERE company_id = ? AND is_archived = 0 AND stage_key = 'hired'
            """,
            (company_id,),
        ).fetchone()
        total = max(0, int(stats["total_applications"]))
        hired = int(hired_row["hired_count"] or 0) if hired_row else 0
        conversion_rate = round((hired / total) * 100, 1) if total else 0.0

        source_rows = self.connection.execute(
            """
            SELECT source, COUNT(*) AS count, COALESCE(AVG(match_score), 0) AS quality_score
            FROM employer_candidates
            WHERE company_id = ?
            GROUP BY source
            ORDER BY count DESC, source
            """,
            (company_id,),
        ).fetchall()
        source_total = sum(int(row["count"] or 0) for row in source_rows) or 1
        source_breakdown = [
            {
                "source": row["source"] or "other",
                "count": int(row["count"] or 0),
                "percentage": round((int(row["count"] or 0) / source_total) * 100, 1),
                "quality_score": round(float(row["quality_score"] or 0), 1),
            }
            for row in source_rows
        ]

        distribution_rows = self.connection.execute(
            """
            SELECT
                CASE
                    WHEN match_score >= 90 THEN '90-100%'
                    WHEN match_score >= 80 THEN '80-89%'
                    WHEN match_score >= 70 THEN '70-79%'
                    WHEN match_score >= 60 THEN '60-69%'
                    ELSE '<60%'
                END AS range_label,
                COUNT(*) AS count
            FROM employer_candidate_job_matches
            WHERE company_id = ? AND is_archived = 0
            GROUP BY range_label
            """,
            (company_id,),
        ).fetchall()
        order = {"90-100%": 0, "80-89%": 1, "70-79%": 2, "60-69%": 3, "<60%": 4}
        match_distribution = sorted(
            [
                {"range": row["range_label"], "count": int(row["count"] or 0)}
                for row in distribution_rows
            ],
            key=lambda item: order.get(item["range"], 99),
        )
        return {
            "period": period,
            "kpi": {
                "total_applicants": stats["total_applications"],
                "avg_match_score": stats["avg_match_score"],
                "time_to_hire_days": 0,
                "conversion_rate": conversion_rate,
            },
            "weekly_applications": self._weekly_application_counts(company_id),
            "source_breakdown": source_breakdown,
            "match_distribution": match_distribution,
        }

    def _weekly_application_counts(self, company_id: int) -> list[int]:
        rows = self.connection.execute(
            """
            SELECT substr(created_at, 1, 10) AS day, COUNT(*) AS count
            FROM employer_candidate_job_matches
            WHERE company_id = ? AND is_archived = 0
            GROUP BY day
            ORDER BY day DESC
            LIMIT 7
            """,
            (company_id,),
        ).fetchall()
        counts = [int(row["count"] or 0) for row in reversed(rows)]
        return ([0] * (7 - len(counts))) + counts

    def _seed_company_roles(self, company_id: int, now: str) -> None:
        for role in SYSTEM_ROLES:
            self.connection.execute(
                """
                INSERT OR IGNORE INTO employer_roles (
                    company_id, role_key, name, description, permissions_json,
                    is_system, risk_level, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?)
                """,
                (
                    company_id,
                    role["role_key"],
                    role["name"],
                    role["description"],
                    _to_json(role["permissions"], []),
                    role["risk_level"],
                    now,
                    now,
                ),
            )

    def _seed_company_pipeline(self, company_id: int, now: str) -> None:
        for stage in DEFAULT_PIPELINE_STAGES:
            self.connection.execute(
                """
                INSERT OR IGNORE INTO employer_pipeline_stages (
                    company_id, stage_key, name, position, is_terminal, sla_days, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    company_id,
                    stage["stage_key"],
                    stage["name"],
                    stage["position"],
                    int(stage["is_terminal"]),
                    stage["sla_days"],
                    now,
                    now,
                ),
            )



def _db_job_status_to_api(status: str | None) -> str:
    if status == "published":
        return "active"
    if status == "archived":
        return "closed"
    return status or "draft"


def _stage_to_candidate_status(stage_key: str | None) -> str:
    mapping = {
        "shortlist": "shortlisted",
        "archived": "rejected",
    }
    if not stage_key:
        return "new"
    return mapping.get(stage_key, stage_key)


def _row_to_dashboard_job(row: sqlite3.Row) -> dict[str, Any]:
    posted_at = row["published_at"] or row["created_at"]
    return {
        "id": str(row["id"]),
        "numeric_id": row["id"],
        "title": row["title"],
        "department": row["department"] or "General",
        "location": row["location"] or "Belirtilmedi",
        "status": _db_job_status_to_api(row["status"]),
        "work_model": row["work_model"],
        "employment_type": row["employment_type"],
        "seniority": row["seniority"],
        "applicants": int(row["applicants"] or 0),
        "qualified_applicants": int(row["qualified_applicants"] or 0),
        "match_avg": round(float(row["match_avg"] or 0), 1),
        "quality_score": int(row["quality_score"] or 0),
        "posted_at": posted_at[:10] if isinstance(posted_at, str) else posted_at,
        "posted_at_iso": posted_at,
        "updated_at_iso": row["updated_at"],
        "salary_min": row["salary_min"],
        "salary_max": row["salary_max"],
        "salary_currency": row["salary_currency"],
        "required_skills": _from_json(row["required_skills_json"], []),
        "preferred_skills": _from_json(row["preferred_skills_json"], []),
        "risk_flags": _from_json(row["risk_flags_json"], []),
        "quality_factors": _from_json(row["quality_factors_json"], {}),
    }


def _row_to_dashboard_candidate(row: sqlite3.Row) -> dict[str, Any]:
    skills = _from_json(row["skills_json"], [])
    profile = _from_json(row["profile_json"], {})
    initials = "".join(part[:1] for part in str(row["full_name"]).split()[:2]).upper() or "A"
    last_activity = row["last_activity_at"] or row["updated_at"]
    return {
        "id": str(row["id"]),
        "numeric_id": row["id"],
        "public_id": row["external_candidate_id"] or f"cand_{row['id']}",
        "name": row["full_name"],
        "initials": initials,
        "headline": row["headline"] or row["current_title"] or "Aday",
        "email": row["email"],
        "phone": row["phone"],
        "match_score": int(row["dashboard_match_score"] or row["match_score"] or 0),
        "intent_score": int(row["dashboard_intent_score"] or row["intent_score"] or 0),
        "skills": skills,
        "experience_years": row["years_experience"] or 0,
        "location": row["location"] or "Belirtilmedi",
        "education": profile.get("education") or profile.get("school") or "Belirtilmedi",
        "status": _stage_to_candidate_status(row["stage_key"]),
        "source": row["source"],
        "availability": row["availability"] or "passive",
        "last_active_at": last_activity,
        "last_active_at_iso": last_activity,
        "salary_expectation_min": row["salary_expectation_min"],
        "salary_expectation_max": row["salary_expectation_max"],
        "salary_currency": row["salary_currency"],
        "work_model_preference": row["work_model_preference"],
        "current_company": row["current_company"],
        "current_title": row["current_title"],
        "summary": profile.get("summary") or profile.get("bio") or "",
        "strengths": profile.get("strengths") or [],
        "gaps": profile.get("gaps") or [],
    }


def _row_to_dashboard_match(row: sqlite3.Row) -> dict[str, Any]:
    explanation = _from_json(row["explanation_json"], {})
    skills = _from_json(row["candidate_skills_json"], [])
    return {
        "id": str(row["id"]),
        "candidate_id": str(row["candidate_id"]),
        "candidate_name": row["candidate_name"],
        "candidate_headline": row["candidate_headline"] or "Aday",
        "candidate_location": row["candidate_location"] or "Belirtilmedi",
        "candidate_skills": skills,
        "candidate_experience_years": row["candidate_years_experience"] or 0,
        "job_id": str(row["job_id"]),
        "job_title": row["job_title"],
        "job_department": row["job_department"] or "General",
        "job_location": row["job_location"] or "Belirtilmedi",
        "stage_key": row["stage_key"],
        "match_score": int(row["match_score"] or 0),
        "intent_score": int(row["intent_score"] or 0),
        "breakdown": explanation.get("breakdown") or explanation.get("scores") or {},
        "explanation": explanation,
        "updated_at": row["updated_at"],
    }


def _activity_title(event_type: str) -> str:
    titles = {
        "employer.auth.registered": "İşveren hesabı oluşturuldu",
        "employer.team.invited": "Ekip daveti gönderildi",
        "employer.team.updated": "Ekip rolü güncellendi",
        "candidate.tag.added": "Aday etiketi eklendi",
        "candidate.tag.removed": "Aday etiketi kaldırıldı",
        "candidate.note.added": "Aday notu eklendi",
        "candidate.stage.updated": "Aday aşaması güncellendi",
        "candidate.workflow.campaign_tagged": "Aday kampanyaya eklendi",
        "employer.job.created": "İlan oluşturuldu",
    }
    return titles.get(event_type, event_type.replace(".", " ").title())


def _activity_type(event_type: str) -> str:
    if "job" in event_type:
        return "job"
    if "candidate" in event_type and "stage" in event_type:
        return "review"
    if "candidate" in event_type:
        return "application"
    if "team" in event_type or "auth" in event_type:
        return "system"
    return "system"

def _row_to_company(row: sqlite3.Row) -> EmployerCompany:
    return EmployerCompany(
        id=row["id"],
        slug=row["slug"],
        name=row["name"],
        legal_name=row["legal_name"],
        website_url=row["website_url"],
        industry=row["industry"],
        company_size=row["company_size"],
        country=row["country"],
        timezone=row["timezone"],
        default_locale=row["default_locale"],
        plan_tier=row["plan_tier"],
        status=row["status"],
        brand_profile=_from_json(row["brand_profile_json"], {}),
        settings=_from_json(row["settings_json"], {}),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_user(row: sqlite3.Row) -> EmployerUser:
    return EmployerUser(
        id=row["id"],
        email=row["email"],
        password_hash=row["password_hash"],
        full_name=row["full_name"],
        title=row["title"],
        avatar_url=row["avatar_url"],
        status=row["status"],
        last_login_at=row["last_login_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_team_member(row: sqlite3.Row) -> EmployerTeamMember:
    return EmployerTeamMember(
        id=row["id"],
        company_id=row["company_id"],
        user_id=row["user_id"],
        invited_email=row["invited_email"],
        role_key=row["role_key"],
        status=row["status"],
        invited_by_user_id=row["invited_by_user_id"],
        invited_at=row["invited_at"],
        joined_at=row["joined_at"],
        last_active_at=row["last_active_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        email=row["email"],
        full_name=row["full_name"],
    )


def _row_to_job(row: sqlite3.Row) -> EmployerJob:
    return EmployerJob(
        id=row["id"],
        company_id=row["company_id"],
        title=row["title"],
        status=row["status"],
        location=row["location"],
        work_model=row["work_model"],
        employment_type=row["employment_type"],
        seniority=row["seniority"],
        department=row["department"],
        salary_min=row["salary_min"],
        salary_max=row["salary_max"],
        salary_currency=row["salary_currency"],
        description=row["description"],
        required_skills=_from_json(row["required_skills_json"], []),
        preferred_skills=_from_json(row["preferred_skills_json"], []),
        quality_score=row["quality_score"],
        quality_factors=_from_json(row["quality_factors_json"], {}),
        risk_flags=_from_json(row["risk_flags_json"], []),
        created_by_user_id=row["created_by_user_id"],
        published_at=row["published_at"],
        closed_at=row["closed_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_candidate(row: sqlite3.Row) -> EmployerCandidate:
    return EmployerCandidate(
        id=row["id"],
        company_id=row["company_id"],
        external_candidate_id=row["external_candidate_id"],
        full_name=row["full_name"],
        headline=row["headline"],
        email=row["email"],
        phone=row["phone"],
        location=row["location"],
        current_company=row["current_company"],
        current_title=row["current_title"],
        years_experience=row["years_experience"],
        availability=row["availability"],
        source=row["source"],
        salary_expectation_min=row["salary_expectation_min"],
        salary_expectation_max=row["salary_expectation_max"],
        salary_currency=row["salary_currency"],
        work_model_preference=row["work_model_preference"],
        match_score=row["match_score"],
        intent_score=row["intent_score"],
        profile=_from_json(row["profile_json"], {}),
        skills=_from_json(row["skills_json"], []),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_send_queue_item(row: sqlite3.Row) -> EmployerSendQueueItem:
    return EmployerSendQueueItem(
        id=row["id"],
        campaign_id=row["campaign_id"],
        candidate_id=row["candidate_id"],
        subject=row["subject"],
        message=row["message"],
        response_score=row["response_score"],
        status=row["status"],
        checks=_from_json(row["checks_json"], []),
        metadata=_from_json(row["metadata_json"], {}),
        prepared_by_user_id=row["prepared_by_user_id"],
        prepared_at=row["prepared_at"],
        updated_at=row["updated_at"],
    )


def _row_to_employer_audit_event(row: sqlite3.Row) -> EmployerAuditEvent:
    keys = set(row.keys())
    return EmployerAuditEvent(
        id=int(row["id"]),
        company_id=int(row["company_id"]),
        actor_user_id=row["actor_user_id"],
        actor_name=row["actor_name"] if "actor_name" in keys else None,
        actor_email=row["actor_email"] if "actor_email" in keys else None,
        event_type=row["event_type"],
        resource_type=row["resource_type"],
        resource_id=row["resource_id"],
        before=_from_json(row["before_json"], {}),
        after=_from_json(row["after_json"], {}),
        metadata=_from_json(row["metadata_json"], {}),
        created_at=row["created_at"],
    )


def _row_to_outreach_audit_event(row: sqlite3.Row) -> dict[str, Any]:
    after = _from_json(row["after_json"], {})
    metadata = _from_json(row["metadata_json"], {})
    action = metadata.get("action") or row["event_type"]
    note = metadata.get("note") or after.get("note") or _activity_title(row["event_type"])
    return {
        "id": f"audit_{row['id']}",
        "action": action,
        "actor": row["actor_name"] or "Hiring Radar",
        "note": note,
        "metadata": metadata | {"event_type": row["event_type"]},
        "created_at": row["created_at"],
    }


def _row_to_campaign(row: sqlite3.Row) -> EmployerOutreachCampaign:
    return EmployerOutreachCampaign(
        id=row["id"],
        company_id=row["company_id"],
        created_by_user_id=row["created_by_user_id"],
        name=row["name"],
        status=row["status"],
        channel=row["channel"],
        tone=row["tone"],
        template_key=row["template_key"],
        candidate_ids=_from_json(row["candidate_ids_json"], []),
        subject_preview=row["subject_preview"],
        message_preview=row["message_preview"],
        response_rate=row["response_rate"],
        metadata=_from_json(row["metadata_json"], {}),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )

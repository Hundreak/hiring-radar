from __future__ import annotations

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.dependencies import get_current_user_session, get_repository
from hiring_radar.models import (
    Subscriber,
    SubscriberCertificationEntry,
    SubscriberCvUpload,
    SubscriberEducationEntry,
    SubscriberExperienceEntry,
    SubscriberLanguageCertificate,
    SubscriberLanguageEntry,
    SubscriberProfile,
)
from hiring_radar.services.user_auth import UserSession


class FakeRepository:
    def __init__(self) -> None:
        self.profile = SubscriberProfile(subscriber_id=7)
        self.education_entries: list[SubscriberEducationEntry] = []
        self.experience_entries: list[SubscriberExperienceEntry] = []
        self.language_entries: list[SubscriberLanguageEntry] = []
        self.certification_entries: list[SubscriberCertificationEntry] = []
        self.language_certificates: list[SubscriberLanguageCertificate] = [
            SubscriberLanguageCertificate(
                id=1,
                subscriber_id=7,
                language_entry_id=None,
                certificate_name="IELTS Academic",
                issuer_name="British Council",
                file_name="ielts.pdf",
                storage_path="uploads/certificates/ielts.pdf",
                uploaded_at="2026-04-05T10:15:00Z",
                created_at="2026-04-05T10:15:00Z",
                updated_at="2026-04-05T10:15:00Z",
            )
        ]
        self.latest_cv_upload: SubscriberCvUpload | None = SubscriberCvUpload(
            id=1,
            subscriber_id=7,
            original_filename="alice_cv.pdf",
            storage_path="uploads/cv/alice_cv.pdf",
            content_type="application/pdf",
            file_size_bytes=245760,
            extracted_text=None,
            parse_status="pending",
            uploaded_at="2026-04-05T10:20:00Z",
            parsed_at=None,
            created_at="2026-04-05T10:20:00Z",
            updated_at="2026-04-05T10:20:00Z",
        )
        self.subscriber = Subscriber(
            id=7,
            email="alice@example.com",
            full_name="Alice Example",
            is_active=True,
            digest_enabled=True,
            created_at="2026-04-05T10:00:00Z",
            updated_at="2026-04-05T10:00:00Z",
        )

    def get_subscriber_by_id(self, subscriber_id: int):
        if subscriber_id != 7:
            return None
        return self.subscriber

    def update_subscriber_fields_by_id(
        self, subscriber_id: int, *, fields: dict, updated_at: str
    ):
        if subscriber_id != 7:
            return None
        self.subscriber = Subscriber(
            id=7,
            email="alice@example.com",
            full_name=fields.get("full_name"),
            is_active=True,
            digest_enabled=True,
            created_at="2026-04-05T10:00:00Z",
            updated_at=updated_at,
        )
        return self.subscriber

    def get_subscriber_profile(self, subscriber_id: int):
        return self.profile

    def upsert_subscriber_profile(
        self,
        subscriber_id: int,
        *,
        phone,
        headline,
        summary,
        target_roles,
        skills,
        preferred_locations,
        remote_preference,
        cv_filename,
        cv_uploaded_at,
        updated_at,
    ):
        self.profile = SubscriberProfile(
            subscriber_id=subscriber_id,
            phone=phone,
            headline=headline,
            summary=summary,
            target_roles=target_roles,
            skills=skills,
            preferred_locations=preferred_locations,
            remote_preference=remote_preference,
            cv_filename=cv_filename,
            cv_uploaded_at=cv_uploaded_at,
            created_at=self.profile.created_at or updated_at,
            updated_at=updated_at,
        )
        return self.profile

    def list_subscriber_education_entries(self, subscriber_id: int):
        return self.education_entries

    def replace_subscriber_education_entries(
        self, subscriber_id: int, *, entries, updated_at: str
    ):
        self.education_entries = [
            SubscriberEducationEntry(
                id=index + 1,
                subscriber_id=subscriber_id,
                school_name=item.school_name,
                degree_name=item.degree_name,
                field_of_study=item.field_of_study,
                start_year=item.start_year,
                end_year=item.end_year,
                display_order=index,
                created_at=updated_at,
                updated_at=updated_at,
            )
            for index, item in enumerate(entries)
        ]
        return self.education_entries

    def list_subscriber_experience_entries(self, subscriber_id: int):
        return self.experience_entries

    def replace_subscriber_experience_entries(
        self, subscriber_id: int, *, entries, updated_at: str
    ):
        self.experience_entries = [
            SubscriberExperienceEntry(
                id=index + 1,
                subscriber_id=subscriber_id,
                title=item.title,
                company_name=item.company_name,
                start_year=item.start_year,
                end_year=item.end_year,
                summary=item.summary,
                display_order=index,
                created_at=updated_at,
                updated_at=updated_at,
            )
            for index, item in enumerate(entries)
        ]
        return self.experience_entries

    def list_subscriber_language_entries(self, subscriber_id: int):
        return self.language_entries

    def replace_subscriber_language_entries(
        self, subscriber_id: int, *, entries, updated_at: str
    ):
        self.language_entries = [
            SubscriberLanguageEntry(
                id=index + 1,
                subscriber_id=subscriber_id,
                language_name=item.language_name,
                proficiency_level=item.proficiency_level,
                notes=item.notes,
                display_order=index,
                created_at=updated_at,
                updated_at=updated_at,
            )
            for index, item in enumerate(entries)
        ]
        return self.language_entries

    def list_subscriber_language_certificates(self, subscriber_id: int):
        return self.language_certificates

    def list_subscriber_certification_entries(self, subscriber_id: int):
        return self.certification_entries

    def replace_subscriber_certification_entries(
        self, subscriber_id: int, *, entries, updated_at: str
    ):
        self.certification_entries = [
            SubscriberCertificationEntry(
                id=index + 1,
                subscriber_id=subscriber_id,
                certificate_name=item.certificate_name,
                issuer_name=item.issuer_name,
                issued_year=item.issued_year,
                file_name=item.file_name,
                storage_path=item.storage_path,
                uploaded_at=item.uploaded_at,
                display_order=index,
                created_at=updated_at,
                updated_at=updated_at,
            )
            for index, item in enumerate(entries)
        ]
        return self.certification_entries

    def get_latest_subscriber_cv_upload(self, subscriber_id: int):
        return self.latest_cv_upload


def _make_user_session() -> UserSession:
    return UserSession(
        subscriber_id=7,
        email="alice@example.com",
        issued_at="2026-04-05T10:00:00Z",
        expires_at="2026-04-05T12:00:00Z",
    )


def test_get_user_profile_returns_completeness_and_assets() -> None:
    app = create_app()
    app.dependency_overrides[get_current_user_session] = _make_user_session
    app.dependency_overrides[get_repository] = lambda: FakeRepository()

    client = TestClient(app)
    response = client.get("/api/user/profile")

    assert response.status_code == 200
    data = response.json()
    assert data["subscriber_id"] == 7
    assert "completeness" in data
    assert "missing_items" in data["completeness"]
    assert "language_entries" in data
    assert "language_certificates" in data
    assert "latest_cv_upload" in data
    assert len(data["language_certificates"]) == 1
    assert data["latest_cv_upload"]["original_filename"] == "alice_cv.pdf"


def test_put_user_profile_updates_profile_and_languages() -> None:
    repo = FakeRepository()

    app = create_app()
    app.dependency_overrides[get_current_user_session] = _make_user_session
    app.dependency_overrides[get_repository] = lambda: repo

    client = TestClient(app)
    response = client.put(
        "/api/user/profile",
        json={
            "full_name": "Alice Example",
            "phone": "+90 555 000 00 00",
            "headline": "Backend Engineer",
            "summary": "Strong API and platform background.",
            "target_roles": ["Backend Engineer"],
            "skills": ["Python", "FastAPI", "PostgreSQL"],
            "preferred_locations": ["Remote", "Berlin"],
            "remote_preference": "remote",
            "education_entries": [
                {
                    "school_name": "Technical University",
                    "degree_name": "BSc",
                    "field_of_study": "Computer Engineering",
                    "start_year": 2018,
                    "end_year": 2022,
                }
            ],
            "experience_entries": [
                {
                    "title": "Backend Engineer",
                    "company_name": "Acme",
                    "start_year": 2022,
                    "end_year": 2025,
                    "summary": "Worked on APIs and data pipelines.",
                }
            ],
            "language_entries": [
                {
                    "language_name": "English",
                    "proficiency_level": "C1",
                    "notes": "Professional working proficiency",
                }
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "+90 555 000 00 00"
    assert data["headline"] == "Backend Engineer"
    assert data["skills"] == ["Python", "FastAPI", "PostgreSQL"]
    assert len(data["education_entries"]) == 1
    assert len(data["experience_entries"]) == 1
    assert len(data["language_entries"]) == 1
    assert data["language_entries"][0]["language_name"] == "English"
    assert len(data["language_certificates"]) == 1
    assert data["latest_cv_upload"]["original_filename"] == "alice_cv.pdf"
    assert data["completeness"]["score"] > 0
from __future__ import annotations

from hiring_radar.db.repositories import AuthRepository, JobsRepository, ProfileRepository
from hiring_radar.db.repository import HiringRadarRepository


def test_repository_exposes_domain_facades(tmp_path):
    import sqlite3

    connection = sqlite3.connect(":memory:")
    repository = HiringRadarRepository(connection)

    assert isinstance(repository.auth, AuthRepository)
    assert isinstance(repository.profile, ProfileRepository)
    assert isinstance(repository.jobs, JobsRepository)
    assert repository.auth.connection is connection
    assert repository.profile.connection is connection
    assert repository.jobs.connection is connection


def test_repository_facades_delegate_to_root_methods(monkeypatch, tmp_path):
    import sqlite3

    connection = sqlite3.connect(":memory:")
    repository = HiringRadarRepository(connection)
    calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def fake_get_subscriber_by_email(email: str):
        calls.append(("get_subscriber_by_email", (email,), {}))
        return {"email": email}

    def fake_get_subscriber_profile(subscriber_id: int):
        calls.append(("get_subscriber_profile", (subscriber_id,), {}))
        return {"subscriber_id": subscriber_id}

    def fake_get_job_by_id(job_id: int):
        calls.append(("get_job_by_id", (job_id,), {}))
        return {"job_id": job_id}

    monkeypatch.setattr(repository, "get_subscriber_by_email", fake_get_subscriber_by_email)
    monkeypatch.setattr(repository, "get_subscriber_profile", fake_get_subscriber_profile)
    monkeypatch.setattr(repository, "get_job_by_id", fake_get_job_by_id)

    assert repository.auth.get_subscriber_by_email("remzi@example.com") == {"email": "remzi@example.com"}
    assert repository.profile.get_subscriber_profile(42) == {"subscriber_id": 42}
    assert repository.jobs.get_job_by_id(7) == {"job_id": 7}
    assert calls == [
        ("get_subscriber_by_email", ("remzi@example.com",), {}),
        ("get_subscriber_profile", (42,), {}),
        ("get_job_by_id", (7,), {}),
    ]

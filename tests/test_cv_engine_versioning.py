from __future__ import annotations

from hiring_radar.services.cv_engine.enterprise.fingerprints import (
    build_document_fingerprints,
)
from hiring_radar.services.cv_engine.enterprise.models import DocumentRelationKind
from hiring_radar.services.cv_engine.enterprise.versioning import resolve_document_relation


def test_resolve_document_relation_detects_exact_duplicate() -> None:
    existing = build_document_fingerprints(
        text="Alice Example\nBackend Engineer\nPython FastAPI",
        raw_bytes=b"same-binary",
        full_name="Alice Example",
        email="alice@example.com",
        phone=None,
    )
    incoming = build_document_fingerprints(
        text="Alice Example\nBackend Engineer\nPython FastAPI",
        raw_bytes=b"same-binary",
        full_name="Alice Example",
        email="alice@example.com",
        phone=None,
    )

    result = resolve_document_relation(existing=existing, incoming=incoming)

    assert result.relation == DocumentRelationKind.EXACT_DUPLICATE
    assert result.same_person is True
    assert "same_binary_hash" in result.reason_codes


def test_resolve_document_relation_detects_updated_version() -> None:
    existing = build_document_fingerprints(
        text="Alice Example\nBackend Engineer\nPython FastAPI PostgreSQL",
        raw_bytes=b"old-version",
        full_name="Alice Example",
        email="alice@example.com",
        phone=None,
    )
    incoming = build_document_fingerprints(
        text=(
            "Alice Example\nSenior Backend Engineer\nPython FastAPI PostgreSQL "
            "Docker Kubernetes"
        ),
        raw_bytes=b"new-version",
        full_name="Alice Example",
        email="alice@example.com",
        phone=None,
    )

    result = resolve_document_relation(existing=existing, incoming=incoming)

    assert result.relation == DocumentRelationKind.UPDATED_VERSION
    assert result.same_person is True
    assert result.similarity.similarity >= 0.80


def test_resolve_document_relation_rejects_unrelated_documents() -> None:
    existing = build_document_fingerprints(
        text="Alice Example\nBackend Engineer\nPython FastAPI PostgreSQL",
        raw_bytes=b"alice-binary",
        full_name="Alice Example",
        email="alice@example.com",
        phone=None,
    )
    incoming = build_document_fingerprints(
        text="Bob Example\nGraphic Designer\nFigma Illustrator Photoshop",
        raw_bytes=b"bob-binary",
        full_name="Bob Example",
        email="bob@example.com",
        phone=None,
    )

    result = resolve_document_relation(existing=existing, incoming=incoming)

    assert result.relation == DocumentRelationKind.UNRELATED
    assert result.same_person is False

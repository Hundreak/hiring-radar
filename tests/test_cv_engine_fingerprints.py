from __future__ import annotations

from hiring_radar.services.cv_engine.enterprise.fingerprints import (
    build_document_fingerprints,
    compute_document_sha256,
    compute_person_fingerprint,
    normalize_text_for_content_fingerprint,
)
from hiring_radar.services.cv_engine.enterprise.similarity import simhash_similarity


def test_normalize_text_for_content_fingerprint_is_stable() -> None:
    raw_text = "  Alice   Example\n\nSenior Backend Engineer\r\nPython • FastAPI  "

    normalized = normalize_text_for_content_fingerprint(raw_text)

    assert normalized == "alice example\nsenior backend engineer\npython fastapi"


def test_build_document_fingerprints_produces_person_and_content_signals() -> None:
    document = build_document_fingerprints(
        text="Alice Example\nSenior Backend Engineer\nPython FastAPI SQL",
        raw_bytes=b"example-pdf-binary",
        full_name="Alice Example",
        email="ALICE@example.com",
        phone="+90 555 111 22 33",
    )

    assert document.document_sha256 == compute_document_sha256(b"example-pdf-binary")
    assert document.person_fingerprint is not None
    assert document.normalized_token_count >= 5
    assert len(document.content_simhash) == 16


def test_compute_person_fingerprint_is_stable_for_same_identity() -> None:
    left = compute_person_fingerprint(
        full_name="Alice Example",
        email="alice@example.com",
        phone="+90 555 111 22 33",
    )
    right = compute_person_fingerprint(
        full_name="  alice   example ",
        email="ALICE@example.com",
        phone="(555) 111-22-33",
    )

    assert left == right


def test_simhash_similarity_is_high_for_near_duplicate_cv_versions() -> None:
    left = build_document_fingerprints(
        text="Alice Example\nBackend Engineer\nPython FastAPI PostgreSQL",
        full_name="Alice Example",
        email="alice@example.com",
        phone=None,
    )
    right = build_document_fingerprints(
        text="Alice Example\nSenior Backend Engineer\nPython FastAPI PostgreSQL Docker",
        full_name="Alice Example",
        email="alice@example.com",
        phone=None,
    )

    similarity = simhash_similarity(left.content_simhash, right.content_simhash)

    assert similarity >= 0.80

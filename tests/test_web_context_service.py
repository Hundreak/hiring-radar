from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.services.ai.web_context import WebContextService


def _make_repository(tmp_path: Path) -> tuple[HiringRadarRepository, object]:
    connection = initialize_database(str(tmp_path / "web_context.db"))
    repository = HiringRadarRepository(connection)
    return repository, connection


def test_web_context_service_extracts_requirements_and_culture_from_html(tmp_path: Path) -> None:
    repository, connection = _make_repository(tmp_path)
    try:
        html = """
        <html>
          <head>
            <title>Senior Platform Engineer</title>
            <meta property="og:site_name" content="Acme Careers" />
            <meta name="description" content="Build platform systems at Acme." />
          </head>
          <body>
            <h2>Requirements</h2>
            <ul>
              <li>5+ years of Python and FastAPI experience.</li>
              <li>Hands-on work with AWS, Docker, and Kubernetes.</li>
            </ul>
            <h2>What you'll do</h2>
            <p>Own backend platform services and improve developer productivity.</p>
            <h2>Why join us</h2>
            <p>We value autonomy, clear feedback, and sustainable on-call rotations.</p>
          </body>
        </html>
        """
        async def _run() -> object:
            transport = httpx.MockTransport(lambda request: httpx.Response(200, text=html, request=request))
            async with httpx.AsyncClient(transport=transport) as client:
                service = WebContextService(repository=repository, client=client)
                return await service.get_external_source_insights(
                    source_url="https://example.com/jobs/platform-engineer",
                    observed_at="2026-04-20T14:00:00Z",
                    force_refresh=True,
                )

        insights = asyncio.run(_run())

        assert insights.enrichment_status == "live"
        assert any("Python" in item or "FastAPI" in item for item in insights.site_specific_requirements)
        assert any("autonomy" in item.lower() for item in insights.company_culture_clues)
        assert any("developer productivity" in item.lower() for item in insights.responsibility_clues)
        assert "python" in insights.technology_stack_terms
        assert insights.original_source_metadata.acquisition_method == "html_sections"
        cached = repository.get_job_external_context_snapshot_by_url("https://example.com/jobs/platform-engineer")
        assert cached is not None
        assert cached.fetch_status == "live"
        assert "5+ years of Python and FastAPI experience." in cached.clean_text
        assert cached.meta_description == "Build platform systems at Acme."
    finally:
        close_connection(connection)


def test_web_context_service_prefers_lever_provider_api_and_persists_sections(tmp_path: Path) -> None:
    repository, connection = _make_repository(tmp_path)
    try:
        html = """
        <html>
          <head><title>Trendyol - Database Engineer - NoSQL</title></head>
          <body>
            <div class="posting-page">
              <h2>About the Team</h2>
              <p>At Trendyol Tech, our mission is to create a positive impact in our ecosystem by enabling commerce through technology.</p>
              <h2>What We Offer</h2>
              <ul>
                <li>Hybrid working model with flexibility.</li>
                <li>Personalised training allowance and learning opportunities.</li>
                <li>A diverse, international team.</li>
              </ul>
              <h2>Take the Next Step</h2>
              <p>If this role excites you, apply today.</p>
            </div>
          </body>
        </html>
        """
        api_payload = [
            {
                "id": "ed8259be-930e-487a-9560-cd0da4a6e2db",
                "text": "Database Engineer - NoSQL",
                "hostedUrl": "https://jobs.lever.co/trendyol/ed8259be-930e-487a-9560-cd0da4a6e2db",
                "categories": {
                    "location": "Istanbul / Maslak",
                    "team": "Engineering, Technology & Product – Platform",
                    "commitment": "Full-time",
                },
                "descriptionPlain": (
                    "About the Team\n"
                    "At Trendyol Tech, our mission is to create a positive impact in our ecosystem by enabling commerce through technology.\n\n"
                    "About the Role\n"
                    "As a Database Engineer - NoSQL at Trendyol, you will design and optimize distributed databases."
                ),
                "lists": [
                    {
                        "text": "Responsibilities",
                        "content": "<ul><li>Design, configure, and tune Elasticsearch clusters.</li><li>Available in rotation on-call for critical event handling.</li></ul>",
                    },
                    {
                        "text": "Expected Qualifications",
                        "content": "<ul><li>Extensive experience (4+ years) in administering and optimizing NoSQL systems.</li><li>Hands-on experience with at least three of: Elasticsearch, Redis, Cassandra, Couchbase, MongoDB.</li><li>Proficiency in Linux systems and scripting (Bash, Python, Go).</li></ul>",
                    },
                ],
                "closing": "<p>If this role excites you, apply today.</p>",
            }
        ]

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.host == "api.lever.co":
                return httpx.Response(200, json=api_payload, request=request)
            return httpx.Response(200, text=html, request=request)

        async def _run() -> object:
            transport = httpx.MockTransport(handler)
            async with httpx.AsyncClient(transport=transport) as client:
                service = WebContextService(repository=repository, client=client)
                return await service.get_external_source_insights(
                    source_url="https://jobs.lever.co/trendyol/ed8259be-930e-487a-9560-cd0da4a6e2db",
                    observed_at="2026-04-20T14:05:00Z",
                    force_refresh=True,
                )

        insights = asyncio.run(_run())

        assert insights.enrichment_status == "live"
        assert insights.original_source_metadata.provider_name == "lever"
        assert insights.original_source_metadata.acquisition_method == "provider_api_plus_html"
        assert any("4+ years" in item for item in insights.site_specific_requirements)
        assert any("on-call" in item.lower() for item in insights.responsibility_clues)
        assert any("Hybrid working model" in item for item in insights.company_culture_clues)
        assert any("Personalised training allowance" in item for item in insights.company_culture_clues)
        assert any("At Trendyol Tech" in item for item in insights.section_blocks.get("about_team", ()))
        assert len(insights.company_culture_clues) >= 2
        assert {"redis", "cassandra", "couchbase", "mongodb", "elasticsearch", "python", "go"}.issuperset(
            set(insights.technology_stack_terms)
        )
        assert "What We Offer" in insights.clean_text
        cached = repository.get_job_external_context_snapshot_by_url(
            "https://jobs.lever.co/trendyol/ed8259be-930e-487a-9560-cd0da4a6e2db"
        )
        assert cached is not None
        metadata_json = cached.source_metadata_json
        assert metadata_json["provider_name"] == "lever"
        assert metadata_json["acquisition_method"] == "provider_api_plus_html"
        assert "section_blocks" in metadata_json
        assert json.loads(json.dumps(metadata_json))["section_blocks"]["requirements"]
        assert cached.clean_text.startswith("About the Team")
    finally:
        close_connection(connection)

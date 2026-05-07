from __future__ import annotations

import asyncio
from pathlib import Path

import httpx

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.services.ai.web_context import WebContextService


def _make_repository(tmp_path: Path) -> tuple[HiringRadarRepository, object]:
    connection = initialize_database(str(tmp_path / "web_context.db"))
    repository = HiringRadarRepository(connection)
    return repository, connection


def test_web_context_service_extracts_requirements_and_culture(tmp_path: Path) -> None:
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
            <main>
              <h2>Requirements</h2>
              <ul>
                <li>5+ years of Python and FastAPI experience.</li>
                <li>Hands-on work with AWS, Docker, and Kubernetes.</li>
              </ul>
              <h2>What you'll do</h2>
              <p>Own backend platform services and improve developer productivity.</p>
              <h2>Why join us</h2>
              <p>We value autonomy, clear feedback, and sustainable on-call rotations.</p>
            </main>
          </body>
        </html>
        """
        transport = httpx.MockTransport(lambda request: httpx.Response(200, text=html, request=request))
        async def _run() -> None:
            async with httpx.AsyncClient(transport=transport) as client:
                service = WebContextService(repository=repository, client=client)
                insights = await service.get_external_source_insights(
                    source_url="https://example.com/jobs/platform-engineer",
                    observed_at="2026-04-18T18:00:00Z",
                    force_refresh=True,
                )
                assert insights.enrichment_status == "live"
                assert any("Python" in item or "FastAPI" in item for item in insights.site_specific_requirements)
                assert any("autonomy" in item.lower() for item in insights.company_culture_clues)
                assert any("developer productivity" in item.lower() for item in insights.responsibility_clues)
                assert "python" in insights.technology_stack_terms
                assert "Build platform systems at Acme." in insights.clean_text
                assert insights.section_lines is not None
                assert insights.section_lines.get("requirements")
        asyncio.run(_run())

        cached = repository.get_job_external_context_snapshot_by_url("https://example.com/jobs/platform-engineer")
        assert cached is not None
        assert cached.fetch_status == "live"
        assert "python" in cached.clean_text.casefold()
        assert cached.meta_description == "Build platform systems at Acme."
        section_lines = cached.source_metadata_json.get("section_lines") or {}
        assert section_lines.get("requirements")
    finally:
        close_connection(connection)


def test_web_context_service_prefers_main_content_and_persists_full_text(tmp_path: Path) -> None:
    repository, connection = _make_repository(tmp_path)
    try:
        html = """
        <html>
          <head>
            <title>Trendyol - Database Engineer - NoSQL</title>
          </head>
          <body>
            <div class="posting-page">
              <h1>Database Engineer - NoSQL</h1>
              <p>Istanbul / Maslak</p>
              <h2>About the Role</h2>
              <p>Design, deploy, and optimize distributed databases such as Elasticsearch, Redis, Cassandra, Couchbase, and MongoDB.</p>
              <h3>Responsibilities</h3>
              <ul>
                <li>Manage backups, restores, and HADR operations.</li>
                <li>Automate repetitive tasks through Terraform and Ansible.</li>
              </ul>
              <h3>Expected Qualifications</h3>
              <ul>
                <li>4+ years of NoSQL production experience.</li>
                <li>Strong scripting with Bash, Python, and Go.</li>
              </ul>
              <h2>What We Offer</h2>
              <p>Hybrid working model with flexibility and learning support.</p>
            </div>
          </body>
        </html>
        """
        transport = httpx.MockTransport(lambda request: httpx.Response(200, text=html, request=request))
        async def _run() -> None:
            async with httpx.AsyncClient(transport=transport) as client:
                service = WebContextService(repository=repository, client=client)
                insights = await service.get_external_source_insights(
                    source_url="https://jobs.example.com/database-engineer-nosql",
                    observed_at="2026-04-20T12:00:00Z",
                    force_refresh=True,
                )
                assert insights.original_source_metadata.text_char_count > 250
                assert {"elasticsearch", "redis", "cassandra", "terraform", "ansible"}.issubset(
                    set(insights.technology_stack_terms)
                )
                assert any("4+ years" in item for item in insights.site_specific_requirements)
                assert any("backups" in item.lower() for item in insights.responsibility_clues)
                assert any("hybrid" in item.lower() for item in insights.company_culture_clues)
        asyncio.run(_run())

        cached = repository.get_job_external_context_snapshot_by_url("https://jobs.example.com/database-engineer-nosql")
        assert cached is not None
        assert len(cached.clean_text) > 250
        assert "terraform" in cached.clean_text.casefold()
    finally:
        close_connection(connection)

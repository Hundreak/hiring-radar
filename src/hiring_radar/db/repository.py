from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from typing import Any

from hiring_radar.models import CrawlRun, JobRecord


def _row_to_job_record(row: sqlite3.Row) -> JobRecord:
    return JobRecord(
        id=row["id"],
        source_name=row["source_name"],
        title=row["title"],
        company_name=row["company_name"],
        location=row["location"],
        canonical_url=row["canonical_url"],
        source_type=row["source_type"],
        source_job_id=row["source_job_id"],
        raw_posted_at=row["raw_posted_at"],
        posted_at=row["posted_at"],
        fingerprint=row["fingerprint"],
        first_seen_at=row["first_seen_at"],
        last_seen_at=row["last_seen_at"],
        is_active=bool(row["is_active"]),
        scraped_at=row["scraped_at"],
    )


def _row_to_crawl_run(row: sqlite3.Row) -> CrawlRun:
    success_value = row["success"]
    success = None if success_value is None else bool(success_value)

    return CrawlRun(
        id=row["id"],
        source_name=row["source_name"],
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        success=success,
        notes=row["notes"],
    )


class HiringRadarRepository:
    """
    Persistence layer for crawl runs and normalized jobs.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def start_crawl_run(self, source_name: str, started_at: str) -> int:
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO crawl_runs (started_at, source_name)
                VALUES (?, ?)
                """,
                (started_at, source_name),
            )

        return int(cursor.lastrowid)

    def finish_crawl_run(
        self,
        run_id: int,
        finished_at: str,
        success: bool,
        notes: str | None = None,
    ) -> None:
        with self.connection:
            self.connection.execute(
                """
                UPDATE crawl_runs
                SET finished_at = ?, success = ?, notes = ?
                WHERE id = ?
                """,
                (finished_at, int(success), notes, run_id),
            )

    def get_crawl_run(self, run_id: int) -> CrawlRun | None:
        cursor = self.connection.execute(
            """
            SELECT id, started_at, finished_at, source_name, success, notes
            FROM crawl_runs
            WHERE id = ?
            """,
            (run_id,),
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return _row_to_crawl_run(row)

    def get_job_by_fingerprint(self, fingerprint: str) -> JobRecord | None:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                source_name,
                title,
                company_name,
                location,
                canonical_url,
                source_type,
                source_job_id,
                raw_posted_at,
                posted_at,
                fingerprint,
                first_seen_at,
                last_seen_at,
                is_active,
                scraped_at
            FROM jobs
            WHERE fingerprint = ?
            """,
            (fingerprint,),
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return _row_to_job_record(row)

    def list_jobs(self, source_name: str | None = None) -> list[JobRecord]:
        """
        List all stored jobs, including inactive records.

        This method is intended for export and reporting flows, so it returns
        the full dataset rather than only active jobs.
        """
        if source_name is None:
            cursor = self.connection.execute(
                """
                SELECT
                    id,
                    source_name,
                    title,
                    company_name,
                    location,
                    canonical_url,
                    source_type,
                    source_job_id,
                    raw_posted_at,
                    posted_at,
                    fingerprint,
                    first_seen_at,
                    last_seen_at,
                    is_active,
                    scraped_at
                FROM jobs
                ORDER BY company_name, source_name, title, canonical_url
                """
            )
        else:
            cursor = self.connection.execute(
                """
                SELECT
                    id,
                    source_name,
                    title,
                    company_name,
                    location,
                    canonical_url,
                    source_type,
                    source_job_id,
                    raw_posted_at,
                    posted_at,
                    fingerprint,
                    first_seen_at,
                    last_seen_at,
                    is_active,
                    scraped_at
                FROM jobs
                WHERE source_name = ?
                ORDER BY company_name, source_name, title, canonical_url
                """,
                (source_name,),
            )

        rows = cursor.fetchall()
        return [_row_to_job_record(row) for row in rows]

    def get_job_counts(self) -> dict[str, int]:
        """
        Return overall job counts for summary/reporting flows.
        """
        cursor = self.connection.execute(
            """
            SELECT
                COUNT(*) AS total_jobs,
                COALESCE(SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END), 0) AS active_jobs,
                COALESCE(SUM(CASE WHEN is_active = 0 THEN 1 ELSE 0 END), 0) AS inactive_jobs
            FROM jobs
            """
        )
        row = cursor.fetchone()

        if row is None:
            return {
                "total_jobs": 0,
                "active_jobs": 0,
                "inactive_jobs": 0,
            }

        return {
            "total_jobs": int(row["total_jobs"]),
            "active_jobs": int(row["active_jobs"]),
            "inactive_jobs": int(row["inactive_jobs"]),
        }

    def get_source_summary_rows(self) -> list[dict[str, Any]]:
        """
        Return aggregated summary rows grouped by source.
        """
        cursor = self.connection.execute(
            """
            SELECT
                source_name,
                source_type,
                COUNT(*) AS total_jobs,
                COALESCE(SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END), 0) AS active_jobs,
                COALESCE(SUM(CASE WHEN is_active = 0 THEN 1 ELSE 0 END), 0) AS inactive_jobs
            FROM jobs
            GROUP BY source_name, source_type
            ORDER BY source_name, source_type
            """
        )
        rows = cursor.fetchall()

        return [
            {
                "source_name": row["source_name"],
                "source_type": row["source_type"],
                "total_jobs": int(row["total_jobs"]),
                "active_jobs": int(row["active_jobs"]),
                "inactive_jobs": int(row["inactive_jobs"]),
            }
            for row in rows
        ]

    def get_company_summary_rows(self) -> list[dict[str, Any]]:
        """
        Return aggregated summary rows grouped by company.
        """
        cursor = self.connection.execute(
            """
            SELECT
                company_name,
                COUNT(*) AS total_jobs,
                COALESCE(SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END), 0) AS active_jobs,
                COALESCE(SUM(CASE WHEN is_active = 0 THEN 1 ELSE 0 END), 0) AS inactive_jobs
            FROM jobs
            GROUP BY company_name
            ORDER BY company_name
            """
        )
        rows = cursor.fetchall()

        return [
            {
                "company_name": row["company_name"],
                "total_jobs": int(row["total_jobs"]),
                "active_jobs": int(row["active_jobs"]),
                "inactive_jobs": int(row["inactive_jobs"]),
            }
            for row in rows
        ]

    def list_active_jobs(self, source_name: str | None = None) -> list[JobRecord]:
        if source_name is None:
            cursor = self.connection.execute(
                """
                SELECT
                    id,
                    source_name,
                    title,
                    company_name,
                    location,
                    canonical_url,
                    source_type,
                    source_job_id,
                    raw_posted_at,
                    posted_at,
                    fingerprint,
                    first_seen_at,
                    last_seen_at,
                    is_active,
                    scraped_at
                FROM jobs
                WHERE is_active = 1
                ORDER BY company_name, title, canonical_url
                """
            )
        else:
            cursor = self.connection.execute(
                """
                SELECT
                    id,
                    source_name,
                    title,
                    company_name,
                    location,
                    canonical_url,
                    source_type,
                    source_job_id,
                    raw_posted_at,
                    posted_at,
                    fingerprint,
                    first_seen_at,
                    last_seen_at,
                    is_active,
                    scraped_at
                FROM jobs
                WHERE is_active = 1 AND source_name = ?
                ORDER BY company_name, title, canonical_url
                """,
                (source_name,),
            )

        rows = cursor.fetchall()
        return [_row_to_job_record(row) for row in rows]

    def upsert_job(self, job: JobRecord) -> bool:
        """
        Insert a new job if the fingerprint is unseen.

        Returns:
            True if a new row was inserted, False if an existing row was updated.
        """
        existing = self.get_job_by_fingerprint(job.fingerprint)

        if existing is None:
            with self.connection:
                self.connection.execute(
                    """
                    INSERT INTO jobs (
                        source_name,
                        title,
                        company_name,
                        location,
                        canonical_url,
                        source_type,
                        source_job_id,
                        raw_posted_at,
                        posted_at,
                        fingerprint,
                        first_seen_at,
                        last_seen_at,
                        is_active,
                        scraped_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job.source_name,
                        job.title,
                        job.company_name,
                        job.location,
                        job.canonical_url,
                        job.source_type,
                        job.source_job_id,
                        job.raw_posted_at,
                        job.posted_at,
                        job.fingerprint,
                        job.scraped_at,
                        job.scraped_at,
                        1,
                        job.scraped_at,
                    ),
                )
            return True

        with self.connection:
            self.connection.execute(
                """
                UPDATE jobs
                SET
                    source_name = ?,
                    title = ?,
                    company_name = ?,
                    location = ?,
                    canonical_url = ?,
                    source_type = ?,
                    source_job_id = ?,
                    raw_posted_at = ?,
                    posted_at = ?,
                    last_seen_at = ?,
                    is_active = 1,
                    scraped_at = ?
                WHERE fingerprint = ?
                """,
                (
                    job.source_name,
                    job.title,
                    job.company_name,
                    job.location,
                    job.canonical_url,
                    job.source_type,
                    job.source_job_id,
                    job.raw_posted_at,
                    job.posted_at,
                    job.scraped_at,
                    job.scraped_at,
                    job.fingerprint,
                ),
            )

        return False

    def mark_missing_jobs_inactive(
        self,
        source_name: str,
        seen_fingerprints: Iterable[str],
        updated_at: str,
    ) -> int:
        """
        Mark active jobs as inactive when they were not seen in the current run.

        Note:
            `updated_at` is accepted for API clarity and future evolution.
            In the MVP we intentionally do not overwrite `last_seen_at` when
            a job becomes inactive.
        """
        _ = updated_at
        fingerprints = tuple(seen_fingerprints)

        if fingerprints:
            placeholders = ", ".join(["?"] * len(fingerprints))
            query = f"""
                UPDATE jobs
                SET is_active = 0
                WHERE source_name = ?
                  AND is_active = 1
                  AND fingerprint NOT IN ({placeholders})
            """
            params: tuple[str | int, ...] = (source_name, *fingerprints)
        else:
            query = """
                UPDATE jobs
                SET is_active = 0
                WHERE source_name = ?
                  AND is_active = 1
            """
            params = (source_name,)

        with self.connection:
            cursor = self.connection.execute(query, params)

        return cursor.rowcount

    def close(self) -> None:
        self.connection.close()
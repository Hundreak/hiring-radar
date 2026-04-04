from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from typing import Any

from hiring_radar.models import (
    CrawlRun,
    JobRecord,
    NotificationCheckpoint,
    NotificationRun,
    Subscriber,
    SubscriberMagicLinkToken,
)


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


def _row_to_subscriber(row: sqlite3.Row) -> Subscriber:
    return Subscriber(
        id=row["id"],
        email=row["email"],
        full_name=row["full_name"],
        is_active=bool(row["is_active"]),
        digest_enabled=bool(row["digest_enabled"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )



def _row_to_notification_checkpoint(row: sqlite3.Row) -> NotificationCheckpoint:
    return NotificationCheckpoint(
        checkpoint_key=row["checkpoint_key"],
        last_processed_at=row["last_processed_at"],
        updated_at=row["updated_at"],
    )


def _row_to_notification_run(row: sqlite3.Row) -> NotificationRun:
    return NotificationRun(
        id=row["id"],
        notification_type=row["notification_type"],
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        status=row["status"],
        recipient_count=int(row["recipient_count"]),
        new_jobs_count=int(row["new_jobs_count"]),
        since=row["since"],
        subject=row["subject"],
        error_message=row["error_message"],
    )

class HiringRadarRepository:
    """
    Persistence layer for crawl runs, normalized jobs, and subscribers.
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

    def list_jobs_first_seen_since(
        self,
        since: str,
        source_name: str | None = None,
    ) -> list[JobRecord]:
        """
        List jobs whose first_seen_at is greater than or equal to `since`.

        Notes:
        - This is intended for digest/notification flows.
        - It returns jobs regardless of active/inactive status because the
          first digest iteration focuses on "newly discovered" postings.
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
                WHERE first_seen_at >= ?
                ORDER BY first_seen_at, company_name, source_name, title, canonical_url
                """,
                (since,),
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
                WHERE first_seen_at >= ? AND source_name = ?
                ORDER BY first_seen_at, company_name, source_name, title, canonical_url
                """,
                (since, source_name),
            )

        rows = cursor.fetchall()
        return [_row_to_job_record(row) for row in rows]



    def get_notification_checkpoint(
        self,
        checkpoint_key: str,
    ) -> NotificationCheckpoint | None:
        cursor = self.connection.execute(
            """
            SELECT
                checkpoint_key,
                last_processed_at,
                updated_at
            FROM notification_checkpoints
            WHERE checkpoint_key = ?
            """,
            (checkpoint_key,),
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return _row_to_notification_checkpoint(row)


    def start_notification_run(
        self,
        *,
        notification_type: str,
        started_at: str,
        since: str | None,
    ) -> int:
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO notification_runs (
                    notification_type,
                    started_at,
                    status,
                    recipient_count,
                    new_jobs_count,
                    since
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    notification_type,
                    started_at,
                    "running",
                    0,
                    0,
                    since,
                ),
            )

        return int(cursor.lastrowid)

    def finish_notification_run(
        self,
        run_id: int,
        *,
        finished_at: str,
        status: str,
        recipient_count: int = 0,
        new_jobs_count: int = 0,
        subject: str | None = None,
        error_message: str | None = None,
    ) -> bool:
        with self.connection:
            cursor = self.connection.execute(
                """
                UPDATE notification_runs
                SET
                    finished_at = ?,
                    status = ?,
                    recipient_count = ?,
                    new_jobs_count = ?,
                    subject = ?,
                    error_message = ?
                WHERE id = ?
                """,
                (
                    finished_at,
                    status,
                    recipient_count,
                    new_jobs_count,
                    subject,
                    error_message,
                    run_id,
                ),
            )

        return cursor.rowcount > 0

    def get_notification_run(self, run_id: int) -> NotificationRun | None:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                notification_type,
                started_at,
                finished_at,
                status,
                recipient_count,
                new_jobs_count,
                since,
                subject,
                error_message
            FROM notification_runs
            WHERE id = ?
            """,
            (run_id,),
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return _row_to_notification_run(row)

    def list_notification_runs(
        self,
        *,
        notification_type: str | None = None,
        limit: int = 50,
    ) -> list[NotificationRun]:
        if notification_type is None:
            cursor = self.connection.execute(
                """
                SELECT
                    id,
                    notification_type,
                    started_at,
                    finished_at,
                    status,
                    recipient_count,
                    new_jobs_count,
                    since,
                    subject,
                    error_message
                FROM notification_runs
                ORDER BY started_at DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            )
        else:
            cursor = self.connection.execute(
                """
                SELECT
                    id,
                    notification_type,
                    started_at,
                    finished_at,
                    status,
                    recipient_count,
                    new_jobs_count,
                    since,
                    subject,
                    error_message
                FROM notification_runs
                WHERE notification_type = ?
                ORDER BY started_at DESC, id DESC
                LIMIT ?
                """,
                (notification_type, limit),
            )

        rows = cursor.fetchall()
        return [_row_to_notification_run(row) for row in rows]

    def get_latest_crawl_run(self) -> CrawlRun | None:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                started_at,
                finished_at,
                source_name,
                success,
                notes
            FROM crawl_runs
            ORDER BY started_at DESC, id DESC
            LIMIT 1
            """
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return _row_to_crawl_run(row)

    def get_latest_notification_run(
        self,
        *,
        notification_type: str | None = None,
    ) -> NotificationRun | None:
        if notification_type is None:
            cursor = self.connection.execute(
                """
                SELECT
                    id,
                    notification_type,
                    started_at,
                    finished_at,
                    status,
                    recipient_count,
                    new_jobs_count,
                    since,
                    subject,
                    error_message
                FROM notification_runs
                ORDER BY started_at DESC, id DESC
                LIMIT 1
                """
            )
        else:
            cursor = self.connection.execute(
                """
                SELECT
                    id,
                    notification_type,
                    started_at,
                    finished_at,
                    status,
                    recipient_count,
                    new_jobs_count,
                    since,
                    subject,
                    error_message
                FROM notification_runs
                WHERE notification_type = ?
                ORDER BY started_at DESC, id DESC
                LIMIT 1
                """,
                (notification_type,),
            )

        row = cursor.fetchone()

        if row is None:
            return None

        return _row_to_notification_run(row)

    def get_subscriber_counts(self) -> dict[str, int]:
        cursor = self.connection.execute(
            """
            SELECT
                COUNT(*) AS total_subscribers,
                COALESCE(SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END), 0) AS active_subscribers,
                COALESCE(
                    SUM(CASE WHEN is_active = 1 AND digest_enabled = 1 THEN 1 ELSE 0 END),
                    0
                ) AS digest_enabled_subscribers
            FROM subscribers
            """
        )
        row = cursor.fetchone()

        if row is None:
            return {
                "total_subscribers": 0,
                "active_subscribers": 0,
                "digest_enabled_subscribers": 0,
            }

        return {
            "total_subscribers": int(row["total_subscribers"]),
            "active_subscribers": int(row["active_subscribers"]),
            "digest_enabled_subscribers": int(row["digest_enabled_subscribers"]),
        }



    def upsert_notification_checkpoint(
        self,
        *,
        checkpoint_key: str,
        last_processed_at: str,
        updated_at: str,
    ) -> NotificationCheckpoint:
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO notification_checkpoints (
                    checkpoint_key,
                    last_processed_at,
                    updated_at
                )
                VALUES (?, ?, ?)
                ON CONFLICT(checkpoint_key) DO UPDATE SET
                    last_processed_at = excluded.last_processed_at,
                    updated_at = excluded.updated_at
                """,
                (
                    checkpoint_key,
                    last_processed_at,
                    updated_at,
                ),
            )

        checkpoint = self.get_notification_checkpoint(checkpoint_key)
        if checkpoint is None:
            raise RuntimeError(
                "Notification checkpoint upsert succeeded but record could not be reloaded."
            )

        return checkpoint
    
    




    def get_subscriber_by_email(self, email: str) -> Subscriber | None:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                email,
                full_name,
                is_active,
                digest_enabled,
                created_at,
                updated_at
            FROM subscribers
            WHERE email = ?
            """,
            (email,),
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return _row_to_subscriber(row)

    def upsert_subscriber(
        self,
        *,
        email: str,
        full_name: str | None,
        updated_at: str,
    ) -> tuple[Subscriber, bool]:
        """
        Insert a new subscriber or reactivate/update an existing one.

        Returns:
            (subscriber, created)
        """
        existing = self.get_subscriber_by_email(email)

        if existing is None:
            with self.connection:
                self.connection.execute(
                    """
                    INSERT INTO subscribers (
                        email,
                        full_name,
                        is_active,
                        digest_enabled,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        email,
                        full_name,
                        1,
                        1,
                        updated_at,
                        updated_at,
                    ),
                )

            subscriber = self.get_subscriber_by_email(email)
            if subscriber is None:
                raise RuntimeError("Subscriber insert succeeded but record could not be reloaded.")

            return subscriber, True

        effective_full_name = full_name if full_name is not None else existing.full_name

        with self.connection:
            self.connection.execute(
                """
                UPDATE subscribers
                SET
                    full_name = ?,
                    is_active = 1,
                    digest_enabled = 1,
                    updated_at = ?
                WHERE email = ?
                """,
                (
                    effective_full_name,
                    updated_at,
                    email,
                ),
            )

        subscriber = self.get_subscriber_by_email(email)
        if subscriber is None:
            raise RuntimeError("Subscriber update succeeded but record could not be reloaded.")

        return subscriber, False

    def list_subscribers(self) -> list[Subscriber]:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                email,
                full_name,
                is_active,
                digest_enabled,
                created_at,
                updated_at
            FROM subscribers
            ORDER BY email
            """
        )
        rows = cursor.fetchall()
        return [_row_to_subscriber(row) for row in rows]

    def list_digest_enabled_subscribers(self) -> list[Subscriber]:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                email,
                full_name,
                is_active,
                digest_enabled,
                created_at,
                updated_at
            FROM subscribers
            WHERE is_active = 1 AND digest_enabled = 1
            ORDER BY email
            """
        )
        rows = cursor.fetchall()
        return [_row_to_subscriber(row) for row in rows]

    def set_subscriber_active(
        self,
        *,
        email: str,
        is_active: bool,
        updated_at: str,
    ) -> bool:
        with self.connection:
            cursor = self.connection.execute(
                """
                UPDATE subscribers
                SET
                    is_active = ?,
                    updated_at = ?
                WHERE email = ?
                """,
                (
                    int(is_active),
                    updated_at,
                    email,
                ),
            )

        return cursor.rowcount > 0

    def set_subscriber_digest_enabled(
        self,
        *,
        email: str,
        digest_enabled: bool,
        updated_at: str,
    ) -> bool:
        with self.connection:
            cursor = self.connection.execute(
                """
                UPDATE subscribers
                SET
                    digest_enabled = ?,
                    updated_at = ?
                WHERE email = ?
                """,
                (
                    int(digest_enabled),
                    updated_at,
                    email,
                ),
            )

        return cursor.rowcount > 0

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



    def get_subscriber_by_id(self, subscriber_id: int) -> Subscriber | None:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                email,
                full_name,
                is_active,
                digest_enabled,
                created_at,
                updated_at
            FROM subscribers
            WHERE id = ?
            """,
            (subscriber_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_subscriber(row)
    


    def create_subscriber_magic_link(
        self,
        *,
        subscriber_id: int,
        token_hash: str,
        expires_at: str,
        created_at: str,
    ) -> SubscriberMagicLinkToken:
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO subscriber_magic_links (
                    subscriber_id,
                    token_hash,
                    expires_at,
                    consumed_at,
                    created_at
                )
                VALUES (?, ?, ?, NULL, ?)
                """,
                (
                    subscriber_id,
                    token_hash,
                    expires_at,
                    created_at,
                ),
            )

        return SubscriberMagicLinkToken(
            id=int(cursor.lastrowid),
            subscriber_id=subscriber_id,
            token_hash=token_hash,
            expires_at=expires_at,
            consumed_at=None,
            created_at=created_at,
        )

    def get_subscriber_magic_link_by_hash(
        self,
        token_hash: str,
    ) -> SubscriberMagicLinkToken | None:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                subscriber_id,
                token_hash,
                expires_at,
                consumed_at,
                created_at
            FROM subscriber_magic_links
            WHERE token_hash = ?
            """,
            (token_hash,),
        )
        row = cursor.fetchone()
        if row is None:
            return None

        return SubscriberMagicLinkToken(
            id=row["id"],
            subscriber_id=row["subscriber_id"],
            token_hash=row["token_hash"],
            expires_at=row["expires_at"],
            consumed_at=row["consumed_at"],
            created_at=row["created_at"],
        )

    def consume_subscriber_magic_link(
        self,
        link_id: int,
        *,
        consumed_at: str,
    ) -> bool:
        with self.connection:
            cursor = self.connection.execute(
                """
                UPDATE subscriber_magic_links
                SET consumed_at = ?
                WHERE id = ?
                  AND consumed_at IS NULL
                """,
                (consumed_at, link_id),
            )
        return cursor.rowcount > 0    

    def list_jobs_paginated(
        self,
        *,
        q: str | None = None,
        source_name: str | None = None,
        company_name: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[list[JobRecord], int]:
        where_clauses: list[str] = []
        params: list[Any] = []

        normalized_q = q.strip() if q else ""
        if normalized_q:
            pattern = f"%{normalized_q}%"
            where_clauses.append(
                """
                (
                    title LIKE ?
                    OR company_name LIKE ?
                    OR COALESCE(location, '') LIKE ?
                    OR canonical_url LIKE ?
                )
                """
            )
            params.extend([pattern, pattern, pattern, pattern])

        if source_name:
            where_clauses.append("source_name = ?")
            params.append(source_name)

        if company_name:
            where_clauses.append("company_name = ?")
            params.append(company_name)

        if is_active is not None:
            where_clauses.append("is_active = ?")
            params.append(int(is_active))

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        count_cursor = self.connection.execute(
            f"""
            SELECT COUNT(*) AS total_items
            FROM jobs
            {where_sql}
            """,
            tuple(params),
        )
        count_row = count_cursor.fetchone()
        total_items = 0 if count_row is None else int(count_row["total_items"])

        offset = (page - 1) * page_size
        cursor = self.connection.execute(
            f"""
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
            {where_sql}
            ORDER BY first_seen_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            (*params, page_size, offset),
        )

        return ([_row_to_job_record(row) for row in cursor.fetchall()], total_items)

    def list_crawl_runs_paginated(
        self,
        *,
        source_name: str | None = None,
        success: bool | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[list[CrawlRun], int]:
        where_clauses: list[str] = []
        params: list[Any] = []

        if source_name:
            where_clauses.append("source_name = ?")
            params.append(source_name)

        if success is not None:
            where_clauses.append("success = ?")
            params.append(int(success))

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        count_cursor = self.connection.execute(
            f"""
            SELECT COUNT(*) AS total_items
            FROM crawl_runs
            {where_sql}
            """,
            tuple(params),
        )
        count_row = count_cursor.fetchone()
        total_items = 0 if count_row is None else int(count_row["total_items"])

        offset = (page - 1) * page_size
        cursor = self.connection.execute(
            f"""
            SELECT
                id,
                started_at,
                finished_at,
                source_name,
                success,
                notes
            FROM crawl_runs
            {where_sql}
            ORDER BY started_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            (*params, page_size, offset),
        )

        return ([_row_to_crawl_run(row) for row in cursor.fetchall()], total_items)

    def list_notification_runs_paginated(
        self,
        *,
        notification_type: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[list[NotificationRun], int]:
        where_clauses: list[str] = []
        params: list[Any] = []

        if notification_type:
            where_clauses.append("notification_type = ?")
            params.append(notification_type)

        if status:
            where_clauses.append("status = ?")
            params.append(status)

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        count_cursor = self.connection.execute(
            f"""
            SELECT COUNT(*) AS total_items
            FROM notification_runs
            {where_sql}
            """,
            tuple(params),
        )
        count_row = count_cursor.fetchone()
        total_items = 0 if count_row is None else int(count_row["total_items"])

        offset = (page - 1) * page_size
        cursor = self.connection.execute(
            f"""
            SELECT
                id,
                notification_type,
                started_at,
                finished_at,
                status,
                recipient_count,
                new_jobs_count,
                since,
                subject,
                error_message
            FROM notification_runs
            {where_sql}
            ORDER BY started_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            (*params, page_size, offset),
        )

        return ([_row_to_notification_run(row) for row in cursor.fetchall()], total_items)

    def list_subscribers_paginated(
        self,
        *,
        email_query: str | None = None,
        is_active: bool | None = None,
        digest_enabled: bool | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[list[Subscriber], int]:
        where_clauses: list[str] = []
        params: list[Any] = []

        normalized_query = email_query.strip() if email_query else ""
        if normalized_query:
            pattern = f"%{normalized_query}%"
            where_clauses.append(
                """
                (
                    email LIKE ?
                    OR COALESCE(full_name, '') LIKE ?
                )
                """
            )
            params.extend([pattern, pattern])

        if is_active is not None:
            where_clauses.append("is_active = ?")
            params.append(int(is_active))

        if digest_enabled is not None:
            where_clauses.append("digest_enabled = ?")
            params.append(int(digest_enabled))

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        count_cursor = self.connection.execute(
            f"""
            SELECT COUNT(*) AS total_items
            FROM subscribers
            {where_sql}
            """,
            tuple(params),
        )
        count_row = count_cursor.fetchone()
        total_items = 0 if count_row is None else int(count_row["total_items"])

        offset = (page - 1) * page_size
        cursor = self.connection.execute(
            f"""
            SELECT
                id,
                email,
                full_name,
                is_active,
                digest_enabled,
                created_at,
                updated_at
            FROM subscribers
            {where_sql}
            ORDER BY updated_at DESC, email ASC
            LIMIT ? OFFSET ?
            """,
            (*params, page_size, offset),
        )

        return ([_row_to_subscriber(row) for row in cursor.fetchall()], total_items)

    def update_subscriber_fields_by_id(
        self,
        subscriber_id: int,
        *,
        fields: dict[str, Any],
        updated_at: str,
    ) -> Subscriber | None:
        if not fields:
            raise ValueError("fields must not be empty.")

        allowed_keys = {"full_name", "is_active", "digest_enabled"}
        unknown_keys = sorted(set(fields) - allowed_keys)
        if unknown_keys:
            joined = ", ".join(unknown_keys)
            raise ValueError(f"Unknown subscriber update field(s): {joined}")

        assignments: list[str] = []
        params: list[Any] = []

        if "full_name" in fields:
            assignments.append("full_name = ?")
            params.append(fields["full_name"])

        if "is_active" in fields:
            assignments.append("is_active = ?")
            params.append(int(fields["is_active"]))

        if "digest_enabled" in fields:
            assignments.append("digest_enabled = ?")
            params.append(int(fields["digest_enabled"]))

        assignments.append("updated_at = ?")
        params.append(updated_at)
        params.append(subscriber_id)

        with self.connection:
            cursor = self.connection.execute(
                f"""
                UPDATE subscribers
                SET {", ".join(assignments)}
                WHERE id = ?
                """,
                tuple(params),
            )

        if cursor.rowcount == 0:
            return None

        return self.get_subscriber_by_id(subscriber_id)



    def close(self) -> None:
        self.connection.close()
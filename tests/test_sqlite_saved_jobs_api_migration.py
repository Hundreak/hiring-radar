from __future__ import annotations

from pathlib import Path

from hiring_radar.db.sqlite import initialize_database


def test_initialize_database_migrates_legacy_saved_jobs_api_reference(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy_saved_jobs.db"

    bootstrap = initialize_database(str(db_path))
    bootstrap.executescript(
        """
        INSERT INTO subscribers (
            id,
            email,
            full_name,
            password_hash,
            password_updated_at,
            is_active,
            digest_enabled,
            created_at,
            updated_at
        )
        VALUES (
            1,
            'user@example.com',
            'Example User',
            'hash',
            '2026-04-18T09:00:00Z',
            1,
            1,
            '2026-04-18T09:00:00Z',
            '2026-04-18T09:00:00Z'
        );

        INSERT INTO jobs (
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
        )
        VALUES (
            101,
            'legacy',
            'Backend Engineer',
            'Acme',
            'Remote',
            'https://example.com/jobs/101',
            'legacy',
            'legacy-101',
            '2026-04-18',
            '2026-04-18',
            'legacy-fingerprint-101',
            '2026-04-18T09:00:00Z',
            '2026-04-18T09:00:00Z',
            1,
            '2026-04-18T09:00:00Z'
        );

        INSERT INTO subscriber_saved_jobs (
            subscriber_id,
            job_id,
            api_job_id,
            status,
            match_score,
            created_at,
            updated_at
        )
        VALUES (
            1,
            101,
            101,
            'reviewing',
            78,
            '2026-04-18T10:00:00Z',
            '2026-04-18T10:00:00Z'
        );
        """
    )
    bootstrap.commit()

    bootstrap.executescript(
        """
        DROP INDEX IF EXISTS idx_subscriber_saved_jobs_api_job_id;

        ALTER TABLE subscriber_saved_jobs RENAME TO subscriber_saved_jobs_new;

        CREATE TABLE subscriber_saved_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subscriber_id INTEGER NOT NULL,
            job_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'reviewing',
            match_score INTEGER,
            deadline_at TEXT,
            interview_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(subscriber_id, job_id),
            FOREIGN KEY (subscriber_id) REFERENCES subscribers(id),
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        );

        INSERT INTO subscriber_saved_jobs (
            id,
            subscriber_id,
            job_id,
            status,
            match_score,
            deadline_at,
            interview_at,
            created_at,
            updated_at
        )
        SELECT
            id,
            subscriber_id,
            job_id,
            status,
            match_score,
            deadline_at,
            interview_at,
            created_at,
            updated_at
        FROM subscriber_saved_jobs_new;

        DROP TABLE subscriber_saved_jobs_new;
        """
    )
    bootstrap.commit()
    bootstrap.close()

    migrated = initialize_database(str(db_path))
    try:
        column_names = {
            row[1] for row in migrated.execute("PRAGMA table_info(subscriber_saved_jobs)").fetchall()
        }
        assert "api_job_id" in column_names

        api_job_id = migrated.execute(
            "SELECT api_job_id FROM subscriber_saved_jobs WHERE subscriber_id = 1 AND job_id = 101"
        ).fetchone()[0]
        assert api_job_id == 101

        indexes = migrated.execute("PRAGMA index_list(subscriber_saved_jobs)").fetchall()
        index_names = {row[1] for row in indexes}
        assert "idx_subscriber_saved_jobs_api_job_id" in index_names
    finally:
        migrated.close()

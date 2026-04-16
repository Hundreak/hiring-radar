from __future__ import annotations

from pathlib import Path

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import initialize_database


def test_initialize_database_creates_notification_runs_table(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "test_notification_runs.db"
    connection = initialize_database(str(db_path))

    try:
        table_row = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = 'notification_runs'
            """
        ).fetchone()

        assert table_row is not None

        columns = connection.execute("PRAGMA table_info(notification_runs)").fetchall()
        column_names = [column[1] for column in columns]

        assert column_names == [
            "id",
            "notification_type",
            "started_at",
            "finished_at",
            "status",
            "recipient_count",
            "new_jobs_count",
            "since",
            "subject",
            "error_message",
        ]

        indexes = connection.execute("PRAGMA index_list(notification_runs)").fetchall()
        index_names = [index[1] for index in indexes]

        assert "idx_notification_runs_type_started_at" in index_names

    finally:
        connection.close()


def test_notification_run_can_be_started_finished_and_loaded(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "test_notification_runs_repo.db"
    connection = initialize_database(str(db_path))
    repository = HiringRadarRepository(connection)

    try:
        run_id = repository.start_notification_run(
            notification_type="digest_email",
            started_at="2026-04-04T09:00:00Z",
            since="2026-04-04T03:00:00Z",
        )

        updated = repository.finish_notification_run(
            run_id,
            finished_at="2026-04-04T09:01:00Z",
            status="sent",
            recipient_count=2,
            new_jobs_count=14,
            subject="Hiring Radar Digest: 14 new jobs since 2026-04-04T03:00:00Z",
        )

        loaded = repository.get_notification_run(run_id)

        assert updated is True
        assert loaded is not None
        assert loaded.id == run_id
        assert loaded.notification_type == "digest_email"
        assert loaded.started_at == "2026-04-04T09:00:00Z"
        assert loaded.finished_at == "2026-04-04T09:01:00Z"
        assert loaded.status == "sent"
        assert loaded.recipient_count == 2
        assert loaded.new_jobs_count == 14
        assert loaded.since == "2026-04-04T03:00:00Z"
        assert loaded.subject == "Hiring Radar Digest: 14 new jobs since 2026-04-04T03:00:00Z"
        assert loaded.error_message is None

    finally:
        repository.close()


def test_list_notification_runs_supports_filtering_and_limit(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "test_notification_runs_list.db"
    connection = initialize_database(str(db_path))
    repository = HiringRadarRepository(connection)

    try:
        first_id = repository.start_notification_run(
            notification_type="digest_email",
            started_at="2026-04-04T09:00:00Z",
            since="2026-04-04T03:00:00Z",
        )
        repository.finish_notification_run(
            first_id,
            finished_at="2026-04-04T09:01:00Z",
            status="sent",
            recipient_count=2,
            new_jobs_count=14,
            subject="Digest A",
        )

        second_id = repository.start_notification_run(
            notification_type="digest_email",
            started_at="2026-04-04T10:00:00Z",
            since="2026-04-04T09:00:00Z",
        )
        repository.finish_notification_run(
            second_id,
            finished_at="2026-04-04T10:01:00Z",
            status="skipped",
            recipient_count=0,
            new_jobs_count=0,
            error_message=None,
        )

        third_id = repository.start_notification_run(
            notification_type="other_notification",
            started_at="2026-04-04T11:00:00Z",
            since=None,
        )
        repository.finish_notification_run(
            third_id,
            finished_at="2026-04-04T11:01:00Z",
            status="failed",
            recipient_count=0,
            new_jobs_count=0,
            error_message="provider timeout",
        )

        all_runs = repository.list_notification_runs(limit=10)
        digest_runs = repository.list_notification_runs(
            notification_type="digest_email",
            limit=10,
        )
        limited_runs = repository.list_notification_runs(limit=2)

        assert [run.id for run in all_runs] == [third_id, second_id, first_id]
        assert [run.id for run in digest_runs] == [second_id, first_id]
        assert [run.id for run in limited_runs] == [third_id, second_id]

    finally:
        repository.close()

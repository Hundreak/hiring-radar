from __future__ import annotations

from pathlib import Path

from hiring_radar.db.sqlite import close_connection, initialize_database


def test_profile_asset_tables_exist(tmp_path: Path) -> None:
    connection = initialize_database(str(tmp_path / "profile_assets.db"))

    try:
        cursor = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        )
        table_names = {row["name"] for row in cursor.fetchall()}

        assert "subscriber_language_entries" in table_names
        assert "subscriber_language_certificates" in table_names
        assert "subscriber_certification_entries" in table_names
        assert "subscriber_cv_uploads" in table_names
        assert "subscriber_cv_parse_runs" in table_names
        assert "subscriber_cv_apply_audits" in table_names
    finally:
        close_connection(connection)


def test_profile_asset_table_columns_exist(tmp_path: Path) -> None:
    connection = initialize_database(str(tmp_path / "profile_assets_columns.db"))

    try:
        language_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(subscriber_language_entries)"
            ).fetchall()
        }
        certificate_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(subscriber_language_certificates)"
            ).fetchall()
        }
        generic_certificate_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(subscriber_certification_entries)"
            ).fetchall()
        }
        cv_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(subscriber_cv_uploads)"
            ).fetchall()
        }
        cv_parse_run_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(subscriber_cv_parse_runs)"
            ).fetchall()
        }
        cv_parse_run_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(subscriber_cv_parse_runs)"
            ).fetchall()
        }
        cv_apply_audit_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(subscriber_cv_apply_audits)"
            ).fetchall()
        }        

        assert {
            "id",
            "subscriber_id",
            "language_name",
            "proficiency_level",
            "notes",
            "display_order",
            "created_at",
            "updated_at",
        }.issubset(language_columns)

        assert {
            "id",
            "subscriber_id",
            "language_entry_id",
            "certificate_name",
            "issuer_name",
            "file_name",
            "storage_path",
            "uploaded_at",
            "created_at",
            "updated_at",
        }.issubset(certificate_columns)

        assert {
            "id",
            "subscriber_id",
            "certificate_name",
            "issuer_name",
            "issued_year",
            "file_name",
            "storage_path",
            "uploaded_at",
            "display_order",
            "created_at",
            "updated_at",
        }.issubset(generic_certificate_columns)

        assert {
            "id",
            "subscriber_id",
            "original_filename",
            "storage_path",
            "content_type",
            "file_size_bytes",
            "extracted_text",
            "parse_status",
            "uploaded_at",
            "parsed_at",
            "created_at",
            "updated_at",
        }.issubset(cv_columns)

        assert {
            "id",
            "subscriber_id",
            "cv_upload_id",
            "parser_version",
            "source_parse_status",
            "snapshot_json",
            "apply_status",
            "applied_change_count",
            "applied_at",
            "created_at",
            "updated_at",
        }.issubset(cv_parse_run_columns)

        assert {
            "id",
            "subscriber_id",
            "parse_run_id",
            "selected_operations_json",
            "applied_operations_json",
            "applied_change_count",
            "resulting_apply_status",
            "remaining_actionable_change_count",
            "created_at",
            "updated_at",
        }.issubset(cv_apply_audit_columns)
    finally:
        close_connection(connection)
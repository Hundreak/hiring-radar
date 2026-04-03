from __future__ import annotations

import sqlite3
from pathlib import Path

from hiring_radar.db.schema import init_db_schema


def create_connection(db_path: str) -> sqlite3.Connection:
    """
    Create and configure a SQLite connection for Hiring Radar.

    Notes:
    - Parent directories are created automatically if needed.
    - foreign_keys is enabled proactively for future schema evolution.
    - row_factory is set to sqlite3.Row for named column access.
    """
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")

    return connection


def initialize_database(db_path: str) -> sqlite3.Connection:
    """
    Create a configured SQLite connection and initialize the schema.
    """
    connection = create_connection(db_path)
    init_db_schema(connection)
    return connection


def close_connection(connection: sqlite3.Connection | None) -> None:
    """
    Close the SQLite connection safely.
    """
    if connection is not None:
        connection.close()
from __future__ import annotations

import json
import logging

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.observability import (
    DEFAULT_REQUEST_ID_HEADER,
    DEFAULT_RESPONSE_TIME_HEADER,
    DEFAULT_UNHANDLED_ERROR_DETAIL,
    ApiJsonLogFormatter,
    generate_request_id,
    sanitize_request_id,
)


def test_request_id_header_is_added_to_successful_api_response() -> None:
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.headers[DEFAULT_REQUEST_ID_HEADER]
    assert response.headers[DEFAULT_RESPONSE_TIME_HEADER]


def test_valid_incoming_request_id_is_preserved() -> None:
    client = TestClient(create_app())

    response = client.get("/api/health", headers={DEFAULT_REQUEST_ID_HEADER: "trace_123-abc"})

    assert response.status_code == 200
    assert response.headers[DEFAULT_REQUEST_ID_HEADER] == "trace_123-abc"


def test_invalid_incoming_request_id_is_replaced() -> None:
    client = TestClient(create_app())

    response = client.get("/api/health", headers={DEFAULT_REQUEST_ID_HEADER: "bad value with spaces"})

    assert response.status_code == 200
    assert response.headers[DEFAULT_REQUEST_ID_HEADER] != "bad value with spaces"
    assert sanitize_request_id(response.headers[DEFAULT_REQUEST_ID_HEADER]) == response.headers[DEFAULT_REQUEST_ID_HEADER]


def test_unhandled_api_exception_returns_generic_error_envelope() -> None:
    app = create_app()

    @app.get("/api/boom")
    def boom() -> None:
        raise RuntimeError("database password should not leak")

    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/api/boom", headers={DEFAULT_REQUEST_ID_HEADER: "boom-test"})

    assert response.status_code == 500
    assert response.json() == {
        "detail": DEFAULT_UNHANDLED_ERROR_DETAIL,
        "request_id": "boom-test",
    }
    assert response.headers[DEFAULT_REQUEST_ID_HEADER] == "boom-test"


def test_csrf_rejection_also_gets_request_id_header() -> None:
    client = TestClient(create_app())
    client.cookies.set("hiring_radar_session", "signed-session")

    response = client.post("/api/user/security/change-password", json={})

    assert response.status_code == 403
    assert response.headers[DEFAULT_REQUEST_ID_HEADER]


def test_api_json_log_formatter_outputs_stable_fields() -> None:
    record = logging.LogRecord(
        name="hiring_radar.api.request",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="api.request.completed",
        args=(),
        exc_info=None,
    )
    record.request_id = generate_request_id()
    record.method = "GET"
    record.path = "/api/health"
    record.status_code = 200
    record.duration_ms = 12.34
    record.slow = False

    payload = json.loads(ApiJsonLogFormatter().format(record))

    assert payload["event"] == "api.request.completed"
    assert payload["request_id"] == record.request_id
    assert payload["method"] == "GET"
    assert payload["path"] == "/api/health"
    assert payload["status_code"] == 200
    assert payload["duration_ms"] == 12.34
    assert payload["slow"] is False

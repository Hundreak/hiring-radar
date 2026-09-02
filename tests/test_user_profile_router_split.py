from __future__ import annotations

from fastapi.routing import APIRoute

from hiring_radar.api.app import create_app


def test_user_profile_split_routes_are_registered_once() -> None:
    app = create_app()
    methods_by_path: dict[str, set[str]] = {}
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        if not route.path.startswith("/api/user/profile"):
            continue
        methods_by_path.setdefault(route.path, set()).update(route.methods or set())

    assert "GET" in methods_by_path["/api/user/profile/suggestions"]
    assert "POST" in methods_by_path["/api/user/profile/ai-audit/events"]
    assert "PATCH" in methods_by_path["/api/user/profile/ai-audit/events/{audit_log_id}"]
    assert "GET" in methods_by_path["/api/user/profile/ai-audit/export"]
    assert "POST" in methods_by_path["/api/user/profile/ai-audit/events/{audit_log_id}/revert"]

    duplicate_method_routes = [
        (path, method)
        for path, methods in methods_by_path.items()
        for method in methods
        if sum(
            1
            for route in app.routes
            if isinstance(route, APIRoute)
            and route.path == path
            and method in (route.methods or set())
        )
        > 1
    ]
    assert duplicate_method_routes == []

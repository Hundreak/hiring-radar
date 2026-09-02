from __future__ import annotations

from fastapi.routing import APIRoute

from hiring_radar.api.app import create_app

EXPECTED_SPLIT_ROUTES = (
    ("/api/user/profile/suggestions", "get"),
    ("/api/user/profile/ai-audit/events", "post"),
    ("/api/user/profile/ai-audit/events/{audit_log_id}", "patch"),
    ("/api/user/profile/ai-audit/export", "get"),
    ("/api/user/profile/ai-audit/events/{audit_log_id}/revert", "post"),
)


def _iter_api_routes(container, seen: set[int] | None = None):
    """Alt router'lara inerek bütün APIRoute'ları toplar.

    FastAPI'nin yeni sürümleri `include_router` çağrısında rotaları üst
    router'a kopyalamıyor; araya bir sarmalayıcı koyup asıl router'ı
    `original_router` altında tutuyor. Bu yüzden yalnızca `app.routes`
    üzerinde gezmek iç içe dahil edilmiş rotaları göremez.
    """

    seen = set() if seen is None else seen
    if id(container) in seen:
        return
    seen.add(id(container))

    for route in getattr(container, "routes", ()):
        if isinstance(route, APIRoute):
            yield route
            continue
        inner = getattr(route, "original_router", None)
        if inner is None and hasattr(route, "routes"):
            inner = route
        if inner is not None:
            yield from _iter_api_routes(inner, seen)


def test_user_profile_split_routes_are_registered() -> None:
    """Ayrılan alt router'ların rotaları gerçekten yayınlanıyor mu?

    Kaynak olarak OpenAPI şeması kullanılıyor: uygulamanın dışarıya açtığı
    sözleşme budur ve FastAPI'nin dahili rota temsili sürümden sürüme
    değişse bile aynı kalır.
    """

    app = create_app()
    paths = app.openapi()["paths"]

    for path, method in EXPECTED_SPLIT_ROUTES:
        assert path in paths, f"rota yayınlanmamış: {path}"
        assert method in paths[path], f"{path} için {method.upper()} yok"


def test_user_profile_routes_are_registered_once() -> None:
    """Aynı rota iki kez dahil edilmiş olmasın."""

    app = create_app()
    counts: dict[tuple[str, str], int] = {}
    for route in _iter_api_routes(app):
        if not route.path.startswith("/api/user/profile"):
            continue
        for method in route.methods or ():
            key = (route.path, method)
            counts[key] = counts.get(key, 0) + 1

    duplicates = sorted(key for key, count in counts.items() if count > 1)
    assert duplicates == [], f"birden fazla kez kayıtlı: {duplicates}"

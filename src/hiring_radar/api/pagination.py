from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException, Response

from hiring_radar.db.performance import PaginationBounds, clamp_int


@dataclass(frozen=True, slots=True)
class ApiListMeta:
    """Normalized pagination metadata shared by API list endpoints."""

    page: int
    page_size: int
    total_items: int
    total_pages: int


USER_JOB_LIST_BOUNDS = PaginationBounds(default_page_size=24, max_page_size=50, max_page=1_000)
SAVED_JOB_LIST_BOUNDS = PaginationBounds(default_page_size=100, max_page_size=100, max_page=1_000)
ADMIN_LIST_BOUNDS = PaginationBounds(default_page_size=25, max_page_size=100, max_page=1_000)
EMPLOYER_LIST_BOUNDS = PaginationBounds(default_page_size=25, max_page_size=100, max_page=1_000)
EMPLOYER_WIDGET_BOUNDS = PaginationBounds(default_page_size=5, max_page_size=25, max_page=1_000)


def normalize_query_text(value: str | None, *, max_length: int = 160) -> str | None:
    """Return a trimmed query string or reject overly large search payloads.

    FastAPI query validation catches many cases, but this helper keeps the same
    contract available to routers that build query strings manually or receive
    optional values from aliases. Empty strings normalize to None so downstream
    repositories do not execute broad LIKE filters for whitespace-only input.
    """

    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    if len(normalized) > max_length:
        raise HTTPException(
            status_code=422,
            detail=f"query_too_long_max_{max_length}",
        )
    return normalized


def total_pages(*, total_items: int, page_size: int) -> int:
    if total_items <= 0:
        return 0
    return (total_items + page_size - 1) // page_size


def normalize_page_contract(
    *,
    page: Any,
    page_size: Any,
    total_items: int,
    bounds: PaginationBounds,
) -> ApiListMeta:
    normalized_page = clamp_int(
        page,
        default=bounds.default_page,
        minimum=1,
        maximum=bounds.max_page,
    )
    normalized_page_size = clamp_int(
        page_size,
        default=bounds.default_page_size,
        minimum=1,
        maximum=bounds.max_page_size,
    )
    return ApiListMeta(
        page=normalized_page,
        page_size=normalized_page_size,
        total_items=max(0, int(total_items or 0)),
        total_pages=total_pages(total_items=max(0, int(total_items or 0)), page_size=normalized_page_size),
    )


def paginate_sequence(items: list[Any] | tuple[Any, ...], *, meta: ApiListMeta) -> list[Any]:
    start = (meta.page - 1) * meta.page_size
    stop = start + meta.page_size
    return list(items[start:stop])


def set_pagination_headers(response: Response | None, *, meta: ApiListMeta) -> None:
    """Expose pagination metadata as stable response headers.

    Existing JSON response bodies remain backward-compatible, while API clients,
    load tests and observability tooling can read the contract without parsing
    nested endpoint-specific payloads.
    """

    if response is None:
        return
    response.headers["X-Page"] = str(meta.page)
    response.headers["X-Page-Size"] = str(meta.page_size)
    response.headers["X-Total-Items"] = str(meta.total_items)
    response.headers["X-Total-Pages"] = str(meta.total_pages)


def list_envelope(*, items: list[Any], meta: ApiListMeta, **extra: Any) -> dict[str, Any]:
    """Return the stable list envelope used by untyped dictionary routers."""

    return {
        "ok": True,
        "items": items,
        "page": meta.page,
        "page_size": meta.page_size,
        "total_items": meta.total_items,
        "total_pages": meta.total_pages,
        **extra,
    }

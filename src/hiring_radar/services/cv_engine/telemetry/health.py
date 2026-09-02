from __future__ import annotations

import importlib.util

from pydantic import BaseModel, ConfigDict, Field


class CvEngineDependencyHealth(BaseModel):
    """Availability state for one parser dependency."""

    model_config = ConfigDict(extra="forbid")

    dependency_name: str
    available: bool
    required: bool = False
    detail: str | None = None


class CvEngineHealthReport(BaseModel):
    """Top-level parser health report for diagnostics endpoints."""

    model_config = ConfigDict(extra="forbid")

    status: str
    dependency_checks: list[CvEngineDependencyHealth] = Field(default_factory=list)


def build_cv_engine_health_report() -> CvEngineHealthReport:
    """Build a lightweight dependency health report."""
    dependency_specs = [
        ("pydantic", True),
        ("fitz", False),
        ("pytesseract", False),
        ("docx", False),
    ]
    checks: list[CvEngineDependencyHealth] = []
    for module_name, required in dependency_specs:
        available = importlib.util.find_spec(module_name) is not None
        detail = None if available else "module_not_installed"
        checks.append(
            CvEngineDependencyHealth(
                dependency_name=module_name,
                available=available,
                required=required,
                detail=detail,
            )
        )

    status = "healthy" if all(item.available or not item.required for item in checks) else "degraded"
    return CvEngineHealthReport(status=status, dependency_checks=checks)

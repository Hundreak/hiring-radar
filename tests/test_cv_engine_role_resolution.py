from __future__ import annotations

from hiring_radar.services.cv_engine.semantic.location_resolution import (
    resolve_location_candidate,
)
from hiring_radar.services.cv_engine.semantic.organization_resolution import (
    resolve_organization_candidate,
)
from hiring_radar.services.cv_engine.semantic.role_resolution import (
    resolve_role_candidate,
)


def test_resolve_role_candidate_detects_seniority_and_function_family() -> None:
    signal = resolve_role_candidate("Senior Backend Engineer", section_name="experience")

    assert signal is not None
    assert signal.seniority == "senior"
    assert signal.function_family == "engineering"
    assert signal.provenance is not None



def test_resolve_organization_candidate_uses_company_suffix() -> None:
    signal = resolve_organization_candidate("Example Solutions GmbH")

    assert signal is not None
    assert signal.organization_name == "Example Solutions GmbH"
    assert signal.organization_type == "company"
    assert signal.confidence > 0.5



def test_resolve_location_candidate_detects_city_and_country() -> None:
    signal = resolve_location_candidate("Berlin, Germany")

    assert signal is not None
    assert signal.normalized_city == "Berlin"
    assert signal.normalized_country == "Germany"

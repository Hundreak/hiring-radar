from __future__ import annotations

import pytest

from hiring_radar.services.ai.config import load_local_ai_runtime_config


def test_load_local_ai_runtime_config_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AI_ENABLED", raising=False)
    monkeypatch.delenv("AI_RUNTIME", raising=False)
    monkeypatch.delenv("AI_BASE_URL", raising=False)
    monkeypatch.delenv("AI_DEFAULT_MODEL", raising=False)
    monkeypatch.delenv("AI_STRICT_LOCAL_ONLY", raising=False)

    config = load_local_ai_runtime_config()

    assert config.enabled is False
    assert config.runtime == "ollama"
    assert config.base_url == "http://127.0.0.1:11434"
    assert config.default_model == ""
    assert config.strict_local_only is True


def test_load_local_ai_runtime_config_rejects_non_local_url_when_guard_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AI_BASE_URL", "https://ollama.example.com")
    monkeypatch.setenv("AI_STRICT_LOCAL_ONLY", "true")

    with pytest.raises(ValueError, match="Strict local AI mode"):
        load_local_ai_runtime_config()

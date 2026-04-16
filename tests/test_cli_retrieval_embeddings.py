from __future__ import annotations

from typer.testing import CliRunner

from hiring_radar import cli
from hiring_radar.services.retrieval.embedding_jobs import EmbeddingJobProcessResult

runner = CliRunner()



def test_process_retrieval_embeddings_command_prints_processed_summary(monkeypatch) -> None:
    captured_batch_args: dict[str, object] = {}

    class FakeRepository:
        pass

    def fake_run_embedding_job_batch(
        repository,
        *,
        embedding_provider,
        provider: str,
        model: str,
        limit: int,
        now: str | None = None,
        stop_on_error: bool = False,
    ):
        captured_batch_args["provider"] = provider
        captured_batch_args["model"] = model
        captured_batch_args["limit"] = limit
        captured_batch_args["stop_on_error"] = stop_on_error
        return [
            EmbeddingJobProcessResult(
                action=cli.PROCESS_ACTION_PROCESSED,
            ),
            EmbeddingJobProcessResult(
                action=cli.PROCESS_ACTION_IDLE,
                reason="no_queued_jobs",
            ),
        ]

    monkeypatch.setattr(cli, "initialize_database", lambda _: object())
    monkeypatch.setattr(cli, "close_connection", lambda connection: None)
    monkeypatch.setattr(cli, "HiringRadarRepository", lambda connection: FakeRepository())
    monkeypatch.setattr(cli, "run_embedding_job_batch", fake_run_embedding_job_batch)

    result = runner.invoke(
        cli.app,
        ["process-retrieval-embeddings", "--limit", "5"],
    )

    assert result.exit_code == 0
    assert "Retrieval embedding batch" in result.output
    assert "processed=1 failed=0 idle=1 total=2" in result.output
    assert captured_batch_args == {
        "provider": cli.DEFAULT_EMBEDDING_PROVIDER,
        "model": cli.DEFAULT_EMBEDDING_MODEL,
        "limit": 5,
        "stop_on_error": False,
    }



def test_process_retrieval_embeddings_command_returns_failure_when_any_job_fails(monkeypatch) -> None:
    class FakeRepository:
        pass

    monkeypatch.setattr(cli, "initialize_database", lambda _: object())
    monkeypatch.setattr(cli, "close_connection", lambda connection: None)
    monkeypatch.setattr(cli, "HiringRadarRepository", lambda connection: FakeRepository())
    monkeypatch.setattr(
        cli,
        "run_embedding_job_batch",
        lambda repository, **kwargs: [
            EmbeddingJobProcessResult(
                action=cli.PROCESS_ACTION_FAILED,
                error_message="embedding runtime offline",
            )
        ],
    )

    result = runner.invoke(
        cli.app,
        ["process-retrieval-embeddings", "--limit", "1"],
    )

    assert result.exit_code == 1
    assert "embedding runtime offline" in result.output

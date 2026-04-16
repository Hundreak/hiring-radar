from __future__ import annotations

from hiring_radar.services.cv_engine.batch.models import BatchRetryPolicy


def is_retryable_exception(exc: BaseException, policy: BatchRetryPolicy) -> bool:
    """Return whether the given exception should trigger a retry."""
    return exc.__class__.__name__ in set(policy.retryable_exception_names)


def compute_retry_delay_seconds(
    attempt_index: int,
    policy: BatchRetryPolicy,
) -> float:
    """Compute bounded exponential-backoff delay for the next retry."""
    delay = policy.base_delay_seconds * (policy.backoff_multiplier ** max(attempt_index, 0))
    return min(delay, policy.max_delay_seconds)

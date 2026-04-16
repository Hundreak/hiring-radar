from __future__ import annotations

from hiring_radar.services.cv_engine.enterprise.models import SimilarityResult


def parse_simhash_hex(value: str) -> int:
    """Parse a hexadecimal SimHash string into an integer."""
    return int(value, 16)


def simhash_hamming_distance(left: str, right: str) -> int:
    """Return the Hamming distance between two hexadecimal SimHash values."""
    return (parse_simhash_hex(left) ^ parse_simhash_hex(right)).bit_count()


def simhash_similarity(left: str, right: str, *, bit_count: int = 64) -> float:
    """Return a normalized similarity score from two SimHash values."""
    if bit_count <= 0:
        raise ValueError("bit_count must be positive.")
    distance = simhash_hamming_distance(left, right)
    similarity = 1.0 - (distance / bit_count)
    return max(0.0, min(1.0, similarity))


def compare_content_fingerprints(
    *,
    left_simhash: str,
    right_simhash: str,
    bit_count: int = 64,
    exact_text_match: bool = False,
) -> SimilarityResult:
    """Return a structured similarity result for two text fingerprints."""
    distance = simhash_hamming_distance(left_simhash, right_simhash)
    similarity = 1.0 - (distance / bit_count)
    return SimilarityResult(
        similarity=max(0.0, min(1.0, similarity)),
        hamming_distance=distance,
        bit_count=bit_count,
        exact_text_match=exact_text_match,
    )

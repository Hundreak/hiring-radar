"""Service package root.

This package intentionally avoids eager imports so that subpackages can be
loaded independently without creating import-time dependency cycles.
"""

__all__: list[str] = []

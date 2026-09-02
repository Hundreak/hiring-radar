#!/usr/bin/env python3
"""Fail CI when generated/local-only project artifacts leak into the source tree.

This intentionally checks production-risk artifacts instead of normal developer
caches such as __pycache__ or .pytest_cache. Those are already covered by
.gitignore and can appear during local verification runs.
"""
from __future__ import annotations

import argparse
import fnmatch
import os
from pathlib import Path

ROOT_IGNORES = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".venv",
    "venv",
    "env",
    "node_modules",
    ".next",
    "out",
    "coverage",
    "htmlcov",
}

DISALLOWED_PATTERNS = (
    ".backup_*",
    "*_backup",
    "*.bak",
    "*.db",
    "*.sqlite",
    "*.sqlite3",
    "*.db.bak*",
    "*.sqlite.bak*",
    "*.sqlite3.bak*",
    "*.tar",
    "*.tar.gz",
    "*.tar.xz",
    "*.zip",
    ".env",
    ".env.*",
    ".claude/settings.local.json",
    "frontend/tsconfig.tsbuildinfo",
)

ALLOWED_EXACT = {
    ".env.example",
    "data/.gitkeep",
    "data/exports/.gitkeep",
}


def _is_ignored_dir(path: Path) -> bool:
    return any(part in ROOT_IGNORES for part in path.parts)


def _matches_disallowed(relative_posix: str) -> bool:
    if relative_posix in ALLOWED_EXACT:
        return False
    name = Path(relative_posix).name
    for pattern in DISALLOWED_PATTERNS:
        if "/" in pattern:
            if fnmatch.fnmatch(relative_posix, pattern):
                return True
        elif fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(relative_posix, pattern):
            return True
    return False


def find_violations(root: Path) -> list[str]:
    violations: list[str] = []
    for current, dirs, files in os.walk(root):
        current_path = Path(current)
        relative_current = current_path.relative_to(root)
        dirs[:] = [d for d in dirs if not _is_ignored_dir(relative_current / d)]
        for dirname in list(dirs):
            relative = (relative_current / dirname).as_posix()
            if _matches_disallowed(relative):
                violations.append(relative + "/")
        for filename in files:
            relative = (relative_current / filename).as_posix()
            if _matches_disallowed(relative):
                violations.append(relative)
    return sorted(set(violations))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="Repository root to scan")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    violations = find_violations(root)
    if violations:
        print("Source hygiene check failed. Remove local/generated artifacts from the source tree:")
        for item in violations:
            print(f" - {item}")
        return 1
    print("Source hygiene check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

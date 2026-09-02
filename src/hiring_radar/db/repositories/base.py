from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from hiring_radar.db.repository import HiringRadarRepository


class RepositoryDomain:
    """Small delegation base for domain repository facades.

    Patch 11 intentionally keeps the old ``HiringRadarRepository`` public methods
    intact while exposing domain-specific access points such as ``repo.auth``,
    ``repo.profile`` and ``repo.jobs``. That lets routers/services migrate one at
    a time without a risky all-at-once persistence rewrite.
    """

    def __init__(self, root: HiringRadarRepository) -> None:
        self._root = root

    @property
    def connection(self):
        return self._root.connection

    def _call(self, method_name: str, *args: Any, **kwargs: Any) -> Any:
        return getattr(self._root, method_name)(*args, **kwargs)

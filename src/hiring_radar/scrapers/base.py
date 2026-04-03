from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from hiring_radar.models import JobRecord


@dataclass(slots=True, kw_only=True)
class ScraperSourceConfig:
    """
    Minimal source configuration required by scraper instances.

    This deliberately stays small in the MVP. We can expand it later
    when source-specific options become necessary.
    """

    source_name: str
    company_name: str
    source_type: str
    url: str


class BaseScraper(ABC):
    """
    Common contract for all scraper implementations.

    Scrapers are responsible for parsing source HTML into normalized
    JobRecord objects. Network fetching is intentionally kept outside
    this abstraction for now.
    """

    def __init__(self, config: ScraperSourceConfig) -> None:
        self.config = config

    @abstractmethod
    def parse(self, html: str, scraped_at: str) -> list[JobRecord]:
        """
        Parse source HTML and return normalized job records.
        """
        raise NotImplementedError
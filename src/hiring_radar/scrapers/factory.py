from __future__ import annotations

from hiring_radar.scrapers.base import BaseScraper, ScraperSourceConfig
from hiring_radar.scrapers.custom_static import CustomStaticScraper
from hiring_radar.scrapers.greenhouse import GreenhouseScraper
from hiring_radar.scrapers.lever import LeverScraper


def create_scraper(config: ScraperSourceConfig) -> BaseScraper:
    """
    Create the appropriate scraper instance for the configured source type.
    """
    source_type = config.source_type.strip().lower()

    if source_type == "greenhouse":
        return GreenhouseScraper(config)

    if source_type == "lever":
        return LeverScraper(config)

    if source_type == "custom_static":
        return CustomStaticScraper(config)

    raise ValueError(f"Unsupported source_type: {config.source_type}")
"""Subpaquete de scrapers y adaptadores de fuentes para job0t."""

from job0t.scrapers.base import BaseScraper
from job0t.scrapers.computrabajo import ComputrabajoScraper
from job0t.scrapers.getonboard import GetOnBoardScraper

__all__ = [
    "BaseScraper",
    "ComputrabajoScraper",
    "GetOnBoardScraper",
]

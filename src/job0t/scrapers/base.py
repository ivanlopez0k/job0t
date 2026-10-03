"""Interfaz abstracta y contrato base para todos los scrapers de job0t."""

from abc import ABC, abstractmethod
from typing import List, Optional
from job0t.config import AppConfig, CategoryDefinition
from job0t.models import RawJob


class BaseScraper(ABC):
    """Contrato base que deben implementar todos los adaptadores de portales y APIs."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Identificador único del portal (ej. 'computrabajo', 'getonboard')."""
        pass

    @abstractmethod
    def search(
        self,
        categories: List[CategoryDefinition],
        config: AppConfig,
        max_pages: Optional[int] = None,
    ) -> List[RawJob]:
        """Ejecuta la búsqueda de ofertas para las categorías dadas y devuelve RawJobs."""
        pass

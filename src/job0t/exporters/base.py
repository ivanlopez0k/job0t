"""Interfaz base para exportadores de ofertas laborales."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional
from job0t.models import Job, RunStats


class BaseExporter(ABC):
    """Contrato abstracto para la exportación de resultados."""

    @abstractmethod
    def export(self, jobs: List[Job], output_path: Path, stats: Optional[RunStats] = None) -> Path:
        """Exporta las ofertas a un archivo de salida en el disco y devuelve su ruta."""
        pass

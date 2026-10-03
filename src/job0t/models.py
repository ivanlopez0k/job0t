"""Modelos de datos del dominio y transporte para job0t."""

from datetime import datetime
import hashlib
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


class RawJob(BaseModel):
    """DTO de transporte para datos crudos extraídos directamente por los scrapers."""

    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    modality: Optional[str] = None
    salary: Optional[str] = None
    description: str
    url: str
    source: str
    published_at_raw: Optional[str] = None
    raw_payload: Dict[str, Any] = Field(default_factory=dict)


class Job(BaseModel):
    """Entidad de dominio limpia, validada y enriquecida con categorías y banderas."""

    id: str = ""
    title: str
    company: str = "Confidencial"
    location: str = "N/D"
    modality: str = "N/D"
    salary: Optional[str] = None
    description: str = ""
    url: str
    source: str
    published_at: Optional[datetime] = None
    scraped_at: datetime = Field(default_factory=datetime.now)
    categories: List[str] = Field(default_factory=list)
    ai_friendly: bool = False
    ai_evidence: str = ""
    freelance: bool = False
    freelance_evidence: str = ""
    remoto: bool = False
    remoto_evidence: str = ""
    status: str = "Nueva"

    @classmethod
    def generate_id(cls, source: str, url: str) -> str:
        """Genera un hash SHA-256 determinístico de 16 caracteres para portal + url."""
        raw = f"{source.strip().lower()}:{url.strip().lower()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    @model_validator(mode="after")
    def ensure_id(self) -> "Job":
        if not self.id or not self.id.strip():
            self.id = self.generate_id(self.source, self.url)
        return self


class FilterOptions(BaseModel):
    """Opciones de filtrado pasadas desde la CLI o menú interactivo."""

    categories: List[str] = Field(default_factory=list)
    only_ai: bool = False
    only_freelance: bool = False
    only_remoto: bool = False
    max_pages: Optional[int] = None
    output_dir: Optional[str] = None


class RunStats(BaseModel):
    """Estadísticas consolidadas de una ejecución para el reporte de resumen."""

    run_at: datetime = Field(default_factory=datetime.now)
    total_raw: int = 0
    total_unique: int = 0
    total_filtered: int = 0
    ai_friendly_count: int = 0
    freelance_count: int = 0
    remoto_count: int = 0
    sources_count: Dict[str, int] = Field(default_factory=dict)
    categories_count: Dict[str, int] = Field(default_factory=dict)

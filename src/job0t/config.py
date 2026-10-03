"""Carga y validación de archivos de configuración YAML para job0t."""

from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import yaml


class SearchConfig(BaseModel):
    locations: List[str] = Field(default_factory=lambda: ["Argentina", "Remoto"])
    max_pages_per_source: int = 3
    delay_range_seconds: List[float] = Field(default_factory=lambda: [1.5, 3.5])
    timeout_seconds: float = 15.0
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 job0t/0.1.0"
    )


class SourceConfig(BaseModel):
    enabled: bool = True
    base_url: str


class OutputConfig(BaseModel):
    directory: str = "output"
    formats: List[str] = Field(default_factory=lambda: ["xlsx", "csv"])


class AppConfig(BaseModel):
    search: SearchConfig = Field(default_factory=SearchConfig)
    sources: Dict[str, SourceConfig] = Field(default_factory=dict)
    output: OutputConfig = Field(default_factory=OutputConfig)


class CategoryDefinition(BaseModel):
    label: str
    search_terms: List[str] = Field(default_factory=list)
    match_keywords: List[str] = Field(default_factory=list)
    exclude_keywords: List[str] = Field(default_factory=list)


CategoriesConfig = Dict[str, CategoryDefinition]


class FlagRule(BaseModel):
    label: str
    yes_keywords: List[str] = Field(default_factory=list)
    no_keywords: List[str] = Field(default_factory=list)
    yes_sources: List[str] = Field(default_factory=list)


FlagsConfig = Dict[str, FlagRule]


def get_default_config_dir() -> Path:
    """Devuelve la ruta a la carpeta config del proyecto."""
    # Ubicado relativo al directorio raíz del proyecto
    cwd = Path.cwd()
    if (cwd / "config").exists():
        return cwd / "config"
    # Fallback relativo a este archivo src/job0t/config.py
    return Path(__file__).resolve().parent.parent.parent / "config"


def load_yaml(file_path: Path) -> Dict[str, Any]:
    """Carga de forma segura un archivo YAML."""
    if not file_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo de configuración: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


def load_app_config(config_dir: Optional[Path] = None) -> AppConfig:
    """Carga y valida config/config.yaml."""
    base_dir = config_dir or get_default_config_dir()
    file_path = base_dir / "config.yaml"
    data = load_yaml(file_path)
    return AppConfig.model_validate(data)


def load_categories_config(config_dir: Optional[Path] = None) -> CategoriesConfig:
    """Carga y valida config/categories.yaml."""
    base_dir = config_dir or get_default_config_dir()
    file_path = base_dir / "categories.yaml"
    data = load_yaml(file_path)
    return {k: CategoryDefinition.model_validate(v) for k, v in data.items()}


def load_flags_config(config_dir: Optional[Path] = None) -> FlagsConfig:
    """Carga y valida config/flags.yaml."""
    base_dir = config_dir or get_default_config_dir()
    file_path = base_dir / "flags.yaml"
    data = load_yaml(file_path)
    return {k: FlagRule.model_validate(v) for k, v in data.items()}


class SeniorityLevel(BaseModel):
    label: str
    keywords: List[str] = Field(default_factory=list)


SeniorityConfig = Dict[str, SeniorityLevel]


def load_seniority_config(config_dir: Optional[Path] = None) -> SeniorityConfig:
    """Carga y valida config/seniority.yaml."""
    base_dir = config_dir or get_default_config_dir()
    file_path = base_dir / "seniority.yaml"
    data = load_yaml(file_path)
    return {k: SeniorityLevel.model_validate(v) for k, v in data.items()}

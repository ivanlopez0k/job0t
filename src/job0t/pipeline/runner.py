"""Orquestador del pipeline completo de job0t."""

from datetime import datetime
import logging
from pathlib import Path
from typing import List, Optional, Tuple
from rich.console import Console

from job0t.config import (
    AppConfig,
    CategoriesConfig,
    CategoryDefinition,
    FlagsConfig,
    SeniorityConfig,
    load_app_config,
    load_categories_config,
    load_flags_config,
    load_seniority_config,
)
from job0t.exporters.csv_exporter import CsvExporter
from job0t.exporters.excel_exporter import ExcelExporter
from job0t.models import FilterOptions, Job, RawJob, RunStats
from job0t.pipeline.classifier import classify_jobs
from job0t.pipeline.deduplicator import deduplicate_jobs
from job0t.pipeline.filter import filter_jobs
from job0t.pipeline.flag_detector import detect_flags_for_all
from job0t.pipeline.normalizer import normalize_jobs
from job0t.pipeline.seniority_detector import detect_seniority_for_all
from job0t.scrapers.base import BaseScraper
from job0t.scrapers.computrabajo import ComputrabajoScraper
from job0t.scrapers.getonboard import GetOnBoardScraper
from job0t.scrapers.jobicy import JobicyScraper
from job0t.scrapers.remoteok import RemoteOKScraper

logger = logging.getLogger("job0t.pipeline.runner")
console = Console()


class PipelineRunner:
    """Coordina la ejecución de scrapers, pipeline de procesamiento y exportación."""

    def __init__(
        self,
        config: Optional[AppConfig] = None,
        categories_config: Optional[CategoriesConfig] = None,
        flags_config: Optional[FlagsConfig] = None,
        seniority_config: Optional[SeniorityConfig] = None,
        scrapers: Optional[List[BaseScraper]] = None,
    ):
        self.config = config or load_app_config()
        self.categories_config = categories_config or load_categories_config()
        self.flags_config = flags_config or load_flags_config()
        self.seniority_config = seniority_config or load_seniority_config()
        self.scrapers = scrapers if scrapers is not None else [
            ComputrabajoScraper(),
            GetOnBoardScraper(),
            JobicyScraper(),
            RemoteOKScraper(),
        ]

    def _resolve_target_categories(self, selected_keys: List[str]) -> List[CategoryDefinition]:
        """Filtra y devuelve las definiciones de categorías a buscar."""
        if not selected_keys:
            return list(self.categories_config.values())

        resolved: List[CategoryDefinition] = []
        selected_set = {k.strip().lower() for k in selected_keys}

        for k, cat_def in self.categories_config.items():
            if k.lower() in selected_set or cat_def.label.lower() in selected_set:
                resolved.append(cat_def)

        # Si no matcheó ninguna clave específica, usar todas
        return resolved or list(self.categories_config.values())

    def run(self, options: FilterOptions) -> Tuple[Optional[Path], Optional[Path], RunStats]:
        """Ejecuta el ciclo completo: scrape -> normalize -> classify -> flags -> seniority -> filter -> dedupe -> export."""
        target_categories = self._resolve_target_categories(options.categories)

        # 1. Extracción de ofertas (Scraping)
        all_raw_jobs: List[RawJob] = []
        for scraper in self.scrapers:
            try:
                raws = scraper.search(
                    categories=target_categories,
                    config=self.config,
                    max_pages=options.max_pages,
                )
                all_raw_jobs.extend(raws)
            except Exception as exc:
                logger.error("Fallo inesperado en scraper %s: %s", scraper.name, exc)

        # 2. Normalización (RawJob -> Job)
        jobs: List[Job] = normalize_jobs(all_raw_jobs)

        # 3. Clasificación
        jobs = classify_jobs(jobs, self.categories_config)

        # 4. Detección de Banderas (AI Friendly, Freelance, Remoto)
        jobs = detect_flags_for_all(jobs, self.flags_config)

        # 5. Detección de Seniority
        jobs = detect_seniority_for_all(jobs, self.seniority_config)

        # 6. Filtrado por banderas, categorías o seniority
        filtered_jobs = filter_jobs(jobs, options, self.categories_config)

        # 7. Deduplicación
        unique_jobs = deduplicate_jobs(filtered_jobs)

        # 8. Métricas y Estadísticas
        stats = RunStats(
            run_at=datetime.now(),
            total_raw=len(all_raw_jobs),
            total_filtered=len(filtered_jobs),
            total_unique=len(unique_jobs),
            ai_friendly_count=sum(1 for j in unique_jobs if j.ai_friendly),
            freelance_count=sum(1 for j in unique_jobs if j.freelance),
            remoto_count=sum(1 for j in unique_jobs if j.remoto),
        )

        for j in unique_jobs:
            stats.sources_count[j.source] = stats.sources_count.get(j.source, 0) + 1
            stats.seniority_count[j.seniority] = stats.seniority_count.get(j.seniority, 0) + 1
            for cat in j.categories:
                stats.categories_count[cat] = stats.categories_count.get(cat, 0) + 1

        # 8. Exportación de Archivos
        out_dir_str = options.output_dir or self.config.output.directory
        out_dir = Path(out_dir_str)
        out_dir.mkdir(parents=True, exist_ok=True)

        date_str = datetime.now().strftime("%Y-%m-%d")
        default_name = f"jobs_{date_str}"
        raw_name = options.filename.strip() if options.filename and options.filename.strip() else default_name
        if raw_name.lower().endswith(".xlsx") or raw_name.lower().endswith(".csv"):
            base_name = Path(raw_name).stem
        else:
            base_name = raw_name

        fmt = (options.export_format or "both").lower().strip()
        xlsx_path: Optional[Path] = None
        csv_path: Optional[Path] = None

        if fmt in ("xlsx", "excel", "both", "ambos", "all", "todos"):
            xlsx_path = out_dir / f"{base_name}.xlsx"
            ExcelExporter().export(unique_jobs, xlsx_path, stats)

        if fmt in ("csv", "both", "ambos", "all", "todos"):
            csv_path = out_dir / f"{base_name}.csv"
            CsvExporter().export(unique_jobs, csv_path, stats)

        return xlsx_path, csv_path, stats


"""Exportador de ofertas a formato CSV con codificación UTF-8 con BOM."""

import csv
from pathlib import Path
from typing import List, Optional
from job0t.exporters.base import BaseExporter
from job0t.models import Job, RunStats


class CsvExporter(BaseExporter):
    """Genera un archivo CSV legible de forma nativa por Excel en Windows (UTF-8 con BOM)."""

    HEADERS = [
        "Estado",
        "Título",
        "Empresa",
        "Ubicación",
        "Modalidad",
        "Seniority",
        "Salario",
        "Categorías",
        "AI Friendly",
        "Evidencia AI",
        "Freelance",
        "Evidencia Freelance",
        "Remoto",
        "Evidencia Remoto",
        "Portal",
        "Fecha Publicación",
        "Link",
    ]

    def export(self, jobs: List[Job], output_path: Path, stats: Optional[RunStats] = None) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(self.HEADERS)

            for job in jobs:
                pub_date = job.published_at.strftime("%Y-%m-%d %H:%M") if job.published_at else "N/D"
                writer.writerow([
                    job.status,
                    job.title,
                    job.company,
                    job.location,
                    job.modality,
                    job.seniority,
                    job.salary or "N/D",
                    "; ".join(job.categories),
                    "SI" if job.ai_friendly else "NO",
                    job.ai_evidence,
                    "SI" if job.freelance else "NO",
                    job.freelance_evidence,
                    "SI" if job.remoto else "NO",
                    job.remoto_evidence,
                    job.source,
                    pub_date,
                    job.url,
                ])

        return output_path

"""Módulo de deduplicación de ofertas en dos fases (hash estricto y fuzzy)."""

import re
from typing import List, Set
from job0t.models import Job


def _clean_slug(text: str) -> str:
    """Genera un slug alfanumérico simplificado."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def deduplicate_jobs(jobs: List[Job]) -> List[Job]:
    """Elimina ofertas duplicadas preservando el primer registro encontrado."""
    seen_ids: Set[str] = set()
    seen_fingerprints: Set[str] = set()
    unique_jobs: List[Job] = []

    for job in jobs:
        # Fase 1: Deduplicación estricta por ID único (portal + URL)
        if job.id in seen_ids:
            continue
        seen_ids.add(job.id)

        # Fase 2: Deduplicación cruzada entre portales (mismo puesto en la misma empresa)
        company_slug = _clean_slug(job.company)
        title_slug = _clean_slug(job.title)

        # Solo aplicamos fingerprint cruzado si la empresa no es confidencial / desconocida
        if company_slug and company_slug not in ("confidencial", "nd", "sinespecificar"):
            fingerprint = f"{title_slug[:35]}@{company_slug[:25]}"
            if fingerprint in seen_fingerprints:
                continue
            seen_fingerprints.add(fingerprint)

        unique_jobs.append(job)

    return unique_jobs

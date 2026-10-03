"""Módulo de detección de Seniority con prioridad absoluta en título."""

import re
from typing import List, Optional
from job0t.config import SeniorityConfig
from job0t.models import Job


def _matches_any_keyword(keywords: List[str], text: str) -> bool:
    """Verifica si alguna palabra clave coincide en el texto con límites de palabra."""
    text_lower = text.lower()
    for kw in keywords:
        kw_clean = kw.strip().lower()
        if not kw_clean:
            continue
        escaped = re.escape(kw_clean)
        # Límites de palabra estrictos para no confundir 'sr' dentro de palabras
        pattern = rf"(?:\b|(?<=\W)){escaped}(?:\b|(?=\W))"
        try:
            if re.search(pattern, text_lower):
                return True
        except re.error:
            if kw_clean in text_lower:
                return True
    return False


def detect_seniority(job: Job, seniority_config: SeniorityConfig) -> Job:
    """Detecta el seniority con jerarquía estricta: Título > Metadatos de API > Descripción."""
    title = job.title.strip()

    # 1. Prioridad Máxima: Título
    # Orden de evaluación cuidadoso: Semi Senior antes de Senior para no atrapar 'senior' dentro de 'semi senior'
    evaluation_order = ["semi_senior", "trainee", "junior", "senior"]

    for level_key in evaluation_order:
        if level_key in seniority_config:
            level_def = seniority_config[level_key]
            if _matches_any_keyword(level_def.keywords, title):
                job.seniority = level_def.label
                return job

    # 2. Prioridad Secundaria: Metadatos de API (Get on Board seniority_id)
    # 1=Trainee, 2=Junior, 3=Semi Senior, 4=Senior, 5=Expert/Lead
    # Si viene en raw_payload
    seniority_id = None
    if hasattr(job, "raw_payload") and isinstance(job.raw_payload, dict):
        seniority_id = job.raw_payload.get("seniority_id")

    if seniority_id == 1 and "trainee" in seniority_config:
        job.seniority = seniority_config["trainee"].label
        return job
    elif seniority_id == 2 and "junior" in seniority_config:
        job.seniority = seniority_config["junior"].label
        return job
    elif seniority_id == 3 and "semi_senior" in seniority_config:
        job.seniority = seniority_config["semi_senior"].label
        return job
    elif seniority_id in (4, 5) and "senior" in seniority_config:
        job.seniority = seniority_config["senior"].label
        return job

    # 3. Prioridad Terciaria: Descripción (solo señales explícitas al inicio)
    desc_start = job.description[:250]
    for level_key in evaluation_order:
        if level_key in seniority_config:
            level_def = seniority_config[level_key]
            if _matches_any_keyword(level_def.keywords, desc_start):
                job.seniority = level_def.label
                return job

    job.seniority = "N/D"
    return job


def detect_seniority_for_all(jobs: List[Job], seniority_config: SeniorityConfig) -> List[Job]:
    """Aplica la detección de seniority a un listado de Jobs."""
    return [detect_seniority(j, seniority_config) for j in jobs]

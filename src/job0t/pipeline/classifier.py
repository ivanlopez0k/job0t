"""Módulo de clasificación de ofertas laborales por reglas ponderadas."""

import re
from typing import Dict, List
from job0t.config import CategoriesConfig, CategoryDefinition
from job0t.models import Job


def _matches_keyword(keyword: str, text: str) -> bool:
    """Verifica si una palabra clave está presente en el texto de forma segura."""
    kw = keyword.strip().lower()
    if not kw:
        return False
    # Caracteres especiales como C#, .NET, C++ requieren búsqueda literal o regex seguro
    escaped = re.escape(kw)
    pattern = rf"(?:\b|(?<=\W)){escaped}(?:\b|(?=\W))"
    try:
        return bool(re.search(pattern, text))
    except re.error:
        return kw in text


def classify_job(job: Job, categories: CategoriesConfig) -> Job:
    """Asigna categorías al Job en base a títulos, descripciones y exclusiones."""
    title_lower = job.title.lower()
    desc_lower = job.description.lower()

    matched_labels: List[str] = []

    for cat_key, cat_def in categories.items():
        # 1. Regla de exclusión: si contiene alguna exclude_keyword, se descalifica
        excluded = False
        for ex_kw in cat_def.exclude_keywords:
            if _matches_keyword(ex_kw, title_lower) or _matches_keyword(ex_kw, desc_lower):
                excluded = True
                break
        if excluded:
            continue

        # 2. Ponderación: título (peso 2) y descripción (peso 1)
        score = 0
        all_keywords = set(cat_def.search_terms + cat_def.match_keywords)

        for kw in all_keywords:
            if _matches_keyword(kw, title_lower):
                score += 2
            elif _matches_keyword(kw, desc_lower):
                score += 1

        if score >= 1:
            matched_labels.append(cat_def.label)

    # Si no matcheó ninguna categoría o estaba vacío, asignar 'General'
    if not matched_labels:
        matched_labels = ["General"]

    job.categories = matched_labels
    return job


def classify_jobs(jobs: List[Job], categories: CategoriesConfig) -> List[Job]:
    """Clasifica un listado completo de Jobs."""
    return [classify_job(j, categories) for j in jobs]

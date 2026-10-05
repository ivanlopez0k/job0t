"""Módulo de filtrado de ofertas según parámetros seleccionados por el usuario."""

from typing import List, Optional
from job0t.config import CategoriesConfig
from job0t.models import FilterOptions, Job


def filter_jobs(
    jobs: List[Job],
    options: FilterOptions,
    categories_config: Optional[CategoriesConfig] = None,
) -> List[Job]:
    """Aplica los filtros booleanos de categorías y banderas seleccionados."""
    if not jobs:
        return []

    # Mapear claves a labels si tenemos la configuración de categorías
    valid_category_labels = set()
    if options.categories:
        for cat in options.categories:
            cat_clean = cat.strip().lower()
            valid_category_labels.add(cat_clean)
            if categories_config and cat_clean in categories_config:
                valid_category_labels.add(categories_config[cat_clean].label.lower())

    filtered: List[Job] = []

    for job in jobs:
        # 1. Filtro AI Friendly
        if options.only_ai and not job.ai_friendly:
            continue

        # 2. Filtro Freelance
        if options.only_freelance and not job.freelance:
            continue

        # 3. Filtro Remoto
        if options.only_remoto and not job.remoto:
            continue

        # 4. Filtro por Categorías elegidas
        if valid_category_labels:
            job_cat_labels = {c.strip().lower() for c in job.categories}
            # Debe coincidir al menos una categoría seleccionada
            if not job_cat_labels.intersection(valid_category_labels):
                continue

        # 5. Filtro por Seniority (Estricto - Opción A)
        if options.seniority:
            raw_tokens: List[str] = []
            if isinstance(options.seniority, list):
                for item in options.seniority:
                    raw_tokens.extend([t.strip().lower() for t in item.replace("/", ",").split(",") if t.strip()])
            else:
                raw_tokens = [t.strip().lower() for t in options.seniority.replace("/", ",").split(",") if t.strip()]

            target_levels = set()
            for tok in raw_tokens:
                if tok in ("todos", "all", "none", "no", "cualquiera", "indistinto", "(recomendado) todos / no filtrar"):
                    continue
                if any(k in tok for k in ("trainee", "entry", "intern", "pasante")):
                    target_levels.add("trainee")
                elif any(k in tok for k in ("ssr", "semi")):
                    target_levels.add("semi senior")
                elif any(k in tok for k in ("jr", "junior")):
                    target_levels.add("junior")
                elif any(k in tok for k in ("sr", "senior", "lead", "principal", "staff")):
                    target_levels.add("senior")

            if target_levels:
                if job.seniority.strip().lower() not in target_levels:
                    continue

        filtered.append(job)

    return filtered

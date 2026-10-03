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
            target_sen = options.seniority.strip().lower()
            if target_sen not in ("todos", "all", "none", "no", "cualquiera", "indistinto"):
                if target_sen in ("jr", "junior", "entry", "entry-level"):
                    target_sen = "junior"
                elif target_sen in ("ssr", "semi", "semi-senior", "semi_senior", "semisenior"):
                    target_sen = "semi senior"
                elif target_sen in ("sr", "senior", "lead", "principal", "staff"):
                    target_sen = "senior"
                elif target_sen in ("trainee", "intern", "pasante", "pasantia"):
                    target_sen = "trainee"

                if job.seniority.strip().lower() != target_sen:
                    continue

        filtered.append(job)

    return filtered

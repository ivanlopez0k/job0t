import unicodedata
from typing import List, Optional
from job0t.config import CategoriesConfig
from job0t.models import FilterOptions, Job

ARGENTINA_PROVINCES = {
    "buenos aires", "capital federal", "caba", "cordoba", "santa fe", "rosario",
    "mendoza", "tucuman", "la plata", "entre rios", "salta", "misiones",
    "chaco", "corrientes", "santiago del estero", "san juan", "jujuy",
    "rio negro", "neuquen", "formosa", "chubut", "san luis", "catamarca",
    "la rioja", "la pampa", "santa cruz", "tierra del fuego", "mar del plata",
}

FOREIGN_EXCLUSIONS_FOR_ARGENTINA = (
    "usa only", "us only", "u.s. only", "united states only", "north america only",
    "uk only", "europe only", "eu only", "canada only", "germany only", "brazil only",
    "australia only", "india only",
)


def _normalize_text(s: Optional[str]) -> str:
    """Elimina tildes, convierte a minúsculas y normaliza caracteres Unicode."""
    if not s:
        return ""
    nfkd = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c)).strip()


def _normalize_mod_token(tok: str) -> str:
    """Normaliza un token de modalidad a sus variantes estándar."""
    t = _normalize_text(tok)
    if t in ("remoto", "remote"):
        return "remoto"
    if t in ("hibrido", "hybrid"):
        return "hibrido"
    if t in ("presencial", "onsite", "on-site"):
        return "presencial"
    return t


def _matches_location(job: Job, req_loc: str) -> bool:
    """Verifica si la oferta cumple con el filtro geográfico solicitado."""
    loc_norm = _normalize_text(req_loc)
    if not loc_norm or loc_norm in ("todos", "todas", "all", "cualquiera", "global", "sin filtro"):
        return True

    job_loc_norm = _normalize_text(job.location)
    job_title_norm = _normalize_text(job.title)
    job_desc_norm = _normalize_text(job.description[:300])

    # Caso 1: Ofertas Presenciales o Híbridas
    if job.modality in ("Presencial", "Híbrido"):
        if loc_norm == "argentina":
            if job.source == "computrabajo":
                return True
            if "argentina" in job_loc_norm:
                return True
            if any(prov in job_loc_norm for prov in ARGENTINA_PROVINCES):
                return True
            return False

        # Si pide una provincia o ciudad específica (ej: 'cordoba', 'rosario')
        return (
            loc_norm in job_loc_norm
            or loc_norm in job_title_norm
            or loc_norm in job_desc_norm
        )

    # Caso 2: Ofertas Remotas (o N/D)
    # Coincidencia directa de la ubicación con el término buscado
    if loc_norm in job_loc_norm:
        return True

    # Si el usuario busca dentro de Argentina (país o provincia/ciudad de Argentina)
    is_arg_search = loc_norm == "argentina" or loc_norm in ARGENTINA_PROVINCES
    if is_arg_search:
        # Ofertas de Computrabajo Argentina aplican siempre
        if job.source == "computrabajo":
            return True

        # Descartar si la oferta remota restringe a regiones extranjeras excluyentes
        if any(excl in job_loc_norm for excl in FOREIGN_EXCLUSIONS_FOR_ARGENTINA):
            return False

        if job_loc_norm in ("usa", "us", "uk", "europe", "canada", "germany", "brasil", "brazil"):
            return False

        # Si la oferta remota indica Argentina o alcance global / LatAm
        if "argentina" in job_loc_norm:
            return True

        is_global_or_latam = any(
            g in job_loc_norm
            for g in (
                "worldwide",
                "cualquier lugar",
                "anywhere",
                "global",
                "latam",
                "latinoamerica",
                "latin america",
                "remoto",
                "n/d",
            )
        )
        if is_global_or_latam:
            return True

    # Para otros países o búsquedas directas
    if loc_norm in job_loc_norm or loc_norm in job_title_norm:
        return True

    # Alcance global abierto
    if any(g in job_loc_norm for g in ("worldwide", "anywhere", "global")):
        return True

    return False


def filter_jobs(
    jobs: List[Job],
    options: FilterOptions,
    categories_config: Optional[CategoriesConfig] = None,
) -> List[Job]:
    """Aplica los filtros booleanos de categorías, banderas, modalidad y ubicación."""
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

        # 3. Filtro Modalidad (soporta options.modalities y legacy options.only_remoto)
        req_modalities = set()
        if options.modalities:
            for m in options.modalities:
                m_norm = _normalize_mod_token(m)
                if m_norm not in ("todos", "todas", "all", "cualquiera", "sin filtro"):
                    req_modalities.add(m_norm)

        if options.only_remoto:
            req_modalities.add("remoto")

        if req_modalities and len(req_modalities) < 3:
            job_mod = _normalize_mod_token(job.modality)
            is_mod_match = job_mod in req_modalities
            if "remoto" in req_modalities and job.remoto:
                is_mod_match = True
            if not is_mod_match:
                continue

        # 4. Filtro Ubicación
        if options.location:
            if not _matches_location(job, options.location):
                continue


        # 5. Filtro por Categorías elegidas
        if valid_category_labels:
            job_cat_labels = {c.strip().lower() for c in job.categories}
            # Debe coincidir al menos una categoría seleccionada
            if not job_cat_labels.intersection(valid_category_labels):
                continue

        # 6. Filtro por Seniority (Estricto - Opción A)
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

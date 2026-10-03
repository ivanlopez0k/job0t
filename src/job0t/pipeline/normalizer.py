"""Módulo normalizador del pipeline: transforma RawJob en Job de dominio."""

import re
from typing import Optional
from bs4 import BeautifulSoup
from job0t.models import Job, RawJob


def strip_html(html_text: Optional[str]) -> str:
    """Elimina etiquetas HTML y colapsa espacios en blanco repetidos."""
    if not html_text:
        return ""
    # Si parece tener tags HTML, parsear con BeautifulSoup
    if "<" in html_text and ">" in html_text:
        soup = BeautifulSoup(html_text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
    else:
        text = html_text
    # Colapsar espacios múltiples, tabs y saltos de línea continuos
    cleaned = re.sub(r"\s+", " ", text)
    return cleaned.strip()


def normalize_modality(raw_modality: Optional[str], text_snippet: str = "") -> str:
    """Estandariza la modalidad a 'Remoto', 'Híbrido', 'Presencial' o 'N/D'."""
    haystack = f"{raw_modality or ''} {text_snippet}".lower()
    if re.search(r"\b(presencial\s*y\s*remoto|hibrid[oa]|híbrid[oa]|hybrid|semi-?presencial)\b", haystack):
        return "Híbrido"
    if re.search(r"\b(100%\s*remoto|solo\s*remoto|remoto|remote|teletrabajo|home\s*office)\b", haystack):
        return "Remoto"
    if re.search(r"\b(solo\s*presencial|presencial|on-site|onsite)\b", haystack):
        return "Presencial"
    return "N/D"


def normalize_job(raw: RawJob) -> Job:
    """Sanea y transforma un RawJob en una entidad Job validada."""
    clean_title = re.sub(r"\s+", " ", raw.title or "").strip()
    
    raw_comp = re.sub(r"\s+", " ", raw.company or "").strip()
    # Eliminar posibles prefijos de rating tipo '4,2 ' o '3,8 '
    clean_company = re.sub(r"^\d+[,\.]\d+\s+", "", raw_comp).strip()
    if not clean_company or clean_company.lower() in ("sin especificar", "confidencial", "anonimo", "anónimo"):
        clean_company = "Confidencial"

    clean_location = re.sub(r"\s+", " ", raw.location or "").strip()
    if not clean_location:
        clean_location = "N/D"

    clean_description = strip_html(raw.description)

    clean_modality = normalize_modality(raw.modality, f"{clean_title} {raw.location or ''} {clean_description[:300]}")

    # Si la ubicación vino literalmente como 'Remoto' o 'Remote', asegurar modalidad y clarificar ubicación
    if clean_location.lower() in ("remoto", "remote"):
        if clean_modality == "N/D":
            clean_modality = "Remoto"
        clean_location = "Cualquier lugar / LatAm"

    clean_salary = None
    if raw.salary and raw.salary.strip():
        clean_salary = re.sub(r"\s+", " ", raw.salary).strip()

    clean_url = (raw.url or "").strip()

    return Job(
        title=clean_title,
        company=clean_company,
        location=clean_location,
        modality=clean_modality,
        salary=clean_salary,
        description=clean_description,
        url=clean_url,
        source=raw.source.strip().lower(),
        raw_payload=raw.raw_payload,
    )


def normalize_jobs(raw_jobs: list[RawJob]) -> list[Job]:
    """Normaliza un listado completo de RawJob."""
    return [normalize_job(r) for r in raw_jobs]

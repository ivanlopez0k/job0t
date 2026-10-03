"""Módulo de detección de banderas (AI Friendly, Freelance, Remoto) y evidencia."""

import re
from typing import List, Set, Tuple
from job0t.config import FlagsConfig, FlagRule
from job0t.models import Job


def _find_matching_keywords(keywords: List[str], text: str) -> List[str]:
    """Encuentra todas las keywords presentes en el texto respetando límites."""
    found: List[str] = []
    text_lower = text.lower()
    for kw in keywords:
        kw_clean = kw.strip().lower()
        if not kw_clean:
            continue
        escaped = re.escape(kw_clean)
        pattern = rf"(?:\b|(?<=\W)){escaped}(?:\b|(?=\W))"
        try:
            if re.search(pattern, text_lower):
                found.append(kw_clean)
        except re.error:
            if kw_clean in text_lower:
                found.append(kw_clean)
    return found


def _evaluate_flag(
    rule: FlagRule,
    text: str,
    source: str = "",
    inherent_flag: bool = False,
    inherent_reason: str = "",
) -> Tuple[bool, str]:
    """Evalúa una bandera considerando keywords positivas, descalificadores y fuentes."""
    text_lower = text.lower()

    # 1. Regla negativa (descalificadores inmediatos)
    disqualifiers = _find_matching_keywords(rule.no_keywords, text_lower)
    if disqualifiers:
        return False, f"[Descalificado por: {', '.join(disqualifiers)}]"

    evidence_items: List[str] = []

    # 2. Si ya viene con bandera por modalidad inherente
    if inherent_flag:
        evidence_items.append(inherent_reason or "modalidad declarada")

    # 3. Si la fuente es reconocida automáticamente (ej. plataformas freelance)
    if source and rule.yes_sources:
        for s in rule.yes_sources:
            if s.strip().lower() == source.strip().lower():
                evidence_items.append(f"fuente {source}")
                break

    # 4. Búsqueda de keywords positivas
    positives = _find_matching_keywords(rule.yes_keywords, text_lower)
    if positives:
        evidence_items.extend(positives)

    if evidence_items:
        # Deduplicar preservando orden
        seen: Set[str] = set()
        deduped = [x for x in evidence_items if not (x in seen or seen.add(x))]
        return True, ", ".join(deduped)

    return False, ""


def detect_flags(job: Job, flags_config: FlagsConfig) -> Job:
    """Evalúa y asigna las banderas booleanas y evidencias para un Job."""
    combined_text = f"{job.title} {job.description} {job.location} {job.modality}"

    # AI Friendly
    if "ai_friendly" in flags_config:
        is_ai, evidence = _evaluate_flag(
            rule=flags_config["ai_friendly"],
            text=combined_text,
            source=job.source,
        )
        job.ai_friendly = is_ai
        job.ai_evidence = evidence

    # Freelance
    if "freelance" in flags_config:
        is_free, evidence = _evaluate_flag(
            rule=flags_config["freelance"],
            text=combined_text,
            source=job.source,
        )
        job.freelance = is_free
        job.freelance_evidence = evidence

    # Remoto
    if "remoto" in flags_config:
        is_remoto_inherent = job.modality.lower() == "remoto" or "remoto" in job.location.lower()
        is_rem, evidence = _evaluate_flag(
            rule=flags_config["remoto"],
            text=combined_text,
            source=job.source,
            inherent_flag=is_remoto_inherent,
            inherent_reason="modalidad o ubicación remota",
        )
        job.remoto = is_rem
        job.remoto_evidence = evidence

    return job


def detect_flags_for_all(jobs: List[Job], flags_config: FlagsConfig) -> List[Job]:
    """Ejecuta la detección de banderas sobre un listado completo de Jobs."""
    return [detect_flags(j, flags_config) for j in jobs]

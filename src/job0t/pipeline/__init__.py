"""Subpaquete pipeline para procesamiento, clasificación, banderas y deduplicación."""

from job0t.pipeline.normalizer import normalize_job, normalize_jobs
from job0t.pipeline.classifier import classify_job, classify_jobs
from job0t.pipeline.flag_detector import detect_flags, detect_flags_for_all
from job0t.pipeline.seniority_detector import detect_seniority, detect_seniority_for_all
from job0t.pipeline.filter import filter_jobs
from job0t.pipeline.deduplicator import deduplicate_jobs

__all__ = [
    "normalize_job",
    "normalize_jobs",
    "classify_job",
    "classify_jobs",
    "detect_flags",
    "detect_flags_for_all",
    "detect_seniority",
    "detect_seniority_for_all",
    "filter_jobs",
    "deduplicate_jobs",
]

"""Tests unitarios para la carga y validación de configuración."""

from pathlib import Path
from job0t.config import (
    load_app_config,
    load_categories_config,
    load_flags_config,
    load_seniority_config,
    get_default_config_dir,
)


def test_load_app_config():
    config = load_app_config()
    assert config.search.max_pages_per_source > 0
    assert "computrabajo" in config.sources
    assert "getonboard" in config.sources
    assert config.sources["computrabajo"].enabled is True
    assert "xlsx" in config.output.formats


def test_load_categories_config():
    categories = load_categories_config()
    assert "desarrollo" in categories
    assert "data" in categories
    assert "diseno" in categories
    dev = categories["desarrollo"]
    assert "programador" in dev.search_terms
    assert "python" in dev.match_keywords
    assert "vendedor" in dev.exclude_keywords


def test_load_flags_config():
    flags = load_flags_config()
    assert "ai_friendly" in flags
    assert "freelance" in flags
    assert "remoto" in flags
    ai = flags["ai_friendly"]
    assert "chatgpt" in ai.yes_keywords
    assert any("prohibido" in kw for kw in ai.no_keywords)
    free = flags["freelance"]
    assert "freelance" in free.yes_keywords
    rem = flags["remoto"]
    assert "remoto" in rem.yes_keywords


def test_load_seniority_config():
    seniority_cfg = load_seniority_config()
    assert "senior" in seniority_cfg
    assert "semi_senior" in seniority_cfg
    assert "junior" in seniority_cfg
    assert "trainee" in seniority_cfg
    assert seniority_cfg["senior"].label == "Senior"
    assert "sr" in seniority_cfg["senior"].keywords

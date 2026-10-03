"""Tests unitarios para los componentes del pipeline de job0t."""

from job0t.config import load_categories_config, load_flags_config
from job0t.models import FilterOptions, Job, RawJob
from job0t.pipeline.classifier import classify_job
from job0t.pipeline.deduplicator import deduplicate_jobs
from job0t.pipeline.filter import filter_jobs
from job0t.pipeline.flag_detector import detect_flags
from job0t.pipeline.normalizer import normalize_job, strip_html


def test_strip_html():
    raw_html = "<p>Buscamos <strong>Python Developer</strong> con experiencia.<br/>Remoto.</p>"
    clean = strip_html(raw_html)
    assert clean == "Buscamos Python Developer con experiencia. Remoto."
    assert "<p>" not in clean
    assert "<br/>" not in clean


def test_normalize_job():
    raw = RawJob(
        title="  Senior   Backend Engineer  ",
        company="",
        location=None,
        modality="100% remoto",
        salary=" $ 3000 USD ",
        description="<div>Desarrollo en <b>Python</b> y AWS.</div>",
        url="https://example.com/job/backend-1",
        source="computrabajo",
    )
    job = normalize_job(raw)
    assert job.title == "Senior Backend Engineer"
    assert job.company == "Confidencial"
    assert job.location == "N/D"
    assert job.modality == "Remoto"
    assert job.salary == "$ 3000 USD"
    assert job.description == "Desarrollo en Python y AWS."
    assert job.source == "computrabajo"


def test_classifier_weights_and_labels():
    categories = load_categories_config()
    job = Job(
        title="Senior Python Backend Developer",
        description="Manejo de bases de datos relacionales y APIs.",
        url="https://example.com/job/1",
        source="getonboard",
    )
    classified = classify_job(job, categories)
    assert "Desarrollo de software" in classified.categories


def test_classifier_exclusion():
    categories = load_categories_config()
    # Diseño tiene exclude_keywords: "diseño de interiores"
    job = Job(
        title="Diseñador de Interiores para oficina",
        description="Buscamos profesional en diseño de interiores y muebles.",
        url="https://example.com/job/2",
        source="computrabajo",
    )
    classified = classify_job(job, categories)
    assert "Diseño" not in classified.categories
    assert "General" in classified.categories


def test_classifier_multilabel():
    categories = load_categories_config()
    job = Job(
        title="Fullstack Developer & Data Analyst",
        description="Desarrollo en React y análisis con Power BI y SQL.",
        url="https://example.com/job/3",
        source="getonboard",
    )
    classified = classify_job(job, categories)
    assert "Desarrollo de software" in classified.categories
    assert "Data / Análisis" in classified.categories


def test_flag_detector_ai_friendly_and_evidence():
    flags = load_flags_config()
    job = Job(
        title="Backend Engineer",
        description="Valoramos el uso de Copilot y ChatGPT para acelerar el desarrollo.",
        url="https://example.com/job/4",
        source="getonboard",
    )
    detected = detect_flags(job, flags)
    assert detected.ai_friendly is True
    assert "copilot" in detected.ai_evidence
    assert "chatgpt" in detected.ai_evidence


def test_flag_detector_ai_negative_override():
    flags = load_flags_config()
    job = Job(
        title="Junior Developer",
        description="Desarrollo con ChatGPT pero prohibido el uso de IA en producción.",
        url="https://example.com/job/5",
        source="computrabajo",
    )
    detected = detect_flags(job, flags)
    assert detected.ai_friendly is False
    assert "Descalificado" in detected.ai_evidence


def test_flag_detector_freelance_by_source_and_keywords():
    flags = load_flags_config()
    job1 = Job(
        title="Python Dev",
        description="Contrato por proyecto como monotributista.",
        url="https://example.com/job/6",
        source="computrabajo",
    )
    job2 = Job(
        title="Frontend",
        description="Proyecto web.",
        url="https://example.com/job/7",
        source="workana",
    )
    det1 = detect_flags(job1, flags)
    det2 = detect_flags(job2, flags)
    assert det1.freelance is True
    assert "por proyecto" in det1.freelance_evidence or "monotributista" in det1.freelance_evidence
    assert det2.freelance is True
    assert "fuente workana" in det2.freelance_evidence


def test_flag_detector_remoto():
    flags = load_flags_config()
    job = Job(
        title="Data Engineer",
        description="Posición 100% remota con home office.",
        url="https://example.com/job/8",
        source="getonboard",
        modality="Remoto",
    )
    detected = detect_flags(job, flags)
    assert detected.remoto is True
    assert "modalidad o ubicación remota" in detected.remoto_evidence or "home office" in detected.remoto_evidence


def test_filter_jobs():
    categories = load_categories_config()
    job1 = Job(
        title="Dev Python",
        url="https://example.com/1",
        source="test",
        categories=["Desarrollo de software"],
        ai_friendly=True,
        remoto=True,
    )
    job2 = Job(
        title="Diseñador UI",
        url="https://example.com/2",
        source="test",
        categories=["Diseño"],
        ai_friendly=False,
        remoto=True,
    )
    jobs = [job1, job2]

    # Filtrar solo AI Friendly
    res_ai = filter_jobs(jobs, FilterOptions(only_ai=True), categories)
    assert len(res_ai) == 1
    assert res_ai[0].title == "Dev Python"

    # Filtrar por categoría 'diseno'
    res_cat = filter_jobs(jobs, FilterOptions(categories=["diseno"]), categories)
    assert len(res_cat) == 1
    assert res_cat[0].title == "Diseñador UI"


def test_deduplicate_jobs_strict_and_fuzzy():
    # Mismo id por misma URL
    job1 = Job(title="Dev Python", company="Mercado Libre", url="https://example.com/a", source="meli")
    job2 = Job(title="Dev Python", company="Mercado Libre", url="https://example.com/a", source="meli")
    # Misma oferta en distinto portal con distinta URL
    job3 = Job(title="Dev Python", company="Mercado Libre", url="https://example.com/b", source="otro")
    # Oferta distinta
    job4 = Job(title="Data Scientist", company="Mercado Libre", url="https://example.com/c", source="meli")

    deduped = deduplicate_jobs([job1, job2, job3, job4])
    assert len(deduped) == 2
    assert deduped[0].title == "Dev Python"
    assert deduped[1].title == "Data Scientist"

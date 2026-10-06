"""Tests unitarios para los componentes del pipeline de job0t."""

from job0t.config import load_categories_config, load_flags_config, load_seniority_config
from job0t.models import FilterOptions, Job, RawJob
from job0t.pipeline.classifier import classify_job
from job0t.pipeline.deduplicator import deduplicate_jobs
from job0t.pipeline.filter import filter_jobs
from job0t.pipeline.flag_detector import detect_flags
from job0t.pipeline.normalizer import normalize_job, strip_html
from job0t.pipeline.seniority_detector import detect_seniority


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


def test_seniority_detection_title_priority():
    cfg = load_seniority_config()

    # Senior en título, descripción menciona juniors
    job_sr = Job(
        title="Senior Python Architect",
        description="Liderar el equipo y mentorear a 3 desarrolladores junior.",
        url="https://example.com/sr1",
        source="test",
    )
    detected_sr = detect_seniority(job_sr, cfg)
    assert detected_sr.seniority == "Senior"

    # Semi Senior en título
    job_ssr = Job(
        title="Desarrollador Fullstack SSR / Semi Senior",
        description="Tareas de programación web.",
        url="https://example.com/ssr1",
        source="test",
    )
    detected_ssr = detect_seniority(job_ssr, cfg)
    assert detected_ssr.seniority == "Semi Senior"

    # Junior en título
    job_jr = Job(
        title="Junior Frontend React Dev",
        description="Buscamos Jr con ganas de aprender.",
        url="https://example.com/jr1",
        source="test",
    )
    detected_jr = detect_seniority(job_jr, cfg)
    assert detected_jr.seniority == "Junior"

    # Trainee en título
    job_trainee = Job(
        title="Pasante / Trainee QA Tester",
        description="Pasantía inicial.",
        url="https://example.com/tr1",
        source="test",
    )
    detected_tr = detect_seniority(job_trainee, cfg)
    assert detected_tr.seniority == "Trainee"


def test_seniority_detection_gob_payload():
    cfg = load_seniority_config()

    # Título neutro, seniority_id provisto por Get on Board
    job_gob = Job(
        title="Backend Developer",
        description="Desarrollo de servicios.",
        url="https://example.com/gob1",
        source="getonboard",
        raw_payload={"seniority_id": 3},  # 3 = Semi Senior
    )
    detected = detect_seniority(job_gob, cfg)
    assert detected.seniority == "Semi Senior"


def test_seniority_detection_jobicy_payload():
    cfg = load_seniority_config()

    job_jobicy = Job(
        title="Software Engineer",
        description="Development of APIs.",
        url="https://jobicy.com/jobs/999",
        source="jobicy",
        raw_payload={"job_level": "Senior"},
    )
    detected = detect_seniority(job_jobicy, cfg)
    assert detected.seniority == "Senior"

    job_jobicy_jr = Job(
        title="Developer",
        description="Entry role.",
        url="https://jobicy.com/jobs/998",
        source="jobicy",
        raw_payload={"job_level": "Junior"},
    )
    detected_jr = detect_seniority(job_jobicy_jr, cfg)
    assert detected_jr.seniority == "Junior"



def test_filter_jobs_by_seniority_strict():
    job_sr = Job(title="Dev SR", seniority="Senior", url="https://example.com/1", source="test")
    job_ssr = Job(title="Dev SSR", seniority="Semi Senior", url="https://example.com/ssr", source="test")
    job_jr = Job(title="Dev JR", seniority="Junior", url="https://example.com/2", source="test")
    job_tr = Job(title="Dev TR", seniority="Trainee", url="https://example.com/tr", source="test")
    job_nd = Job(title="Dev ND", seniority="N/D", url="https://example.com/3", source="test")

    jobs = [job_sr, job_ssr, job_jr, job_tr, job_nd]

    # Filtro estricto por Senior y alias con paréntesis
    res_sr = filter_jobs(jobs, FilterOptions(seniority="sr"))
    assert len(res_sr) == 1
    assert res_sr[0].title == "Dev SR"

    res_sr_paren = filter_jobs(jobs, FilterOptions(seniority="Senior (SR)"))
    assert len(res_sr_paren) == 1
    assert res_sr_paren[0].title == "Dev SR"

    # Filtro por Semi Senior (SSR)
    res_ssr = filter_jobs(jobs, FilterOptions(seniority="Semi Senior (SSR)"))
    assert len(res_ssr) == 1
    assert res_ssr[0].title == "Dev SSR"

    # Filtro por Trainee / Entry
    res_tr = filter_jobs(jobs, FilterOptions(seniority="Trainee / Entry"))
    assert len(res_tr) == 1
    assert res_tr[0].title == "Dev TR"

    # Filtro estricto por Junior
    res_jr = filter_jobs(jobs, FilterOptions(seniority="junior"))
    assert len(res_jr) == 1
    assert res_jr[0].title == "Dev JR"

    # Filtro 'todos' incluye todas
    res_todos = filter_jobs(jobs, FilterOptions(seniority="todos"))
    assert len(res_todos) == 5

    # Filtro múltiple mediante lista (ej: checkbox interactivo)
    res_list = filter_jobs(jobs, FilterOptions(seniority=["junior", "semi senior"]))
    assert len(res_list) == 2
    assert {j.title for j in res_list} == {"Dev JR", "Dev SSR"}

    # Filtro múltiple mediante string separado por comas
    res_str_multi = filter_jobs(jobs, FilterOptions(seniority="junior, ssr"))
    assert len(res_str_multi) == 2
    assert {j.title for j in res_str_multi} == {"Dev JR", "Dev SSR"}

    # Sin filtro de seniority incluye todas
    res_none = filter_jobs(jobs, FilterOptions())
    assert len(res_none) == 5


def test_filter_jobs_by_modality():
    job_remoto = Job(title="Dev Remoto", modality="Remoto", remoto=True, url="https://example.com/1", source="test")
    job_hibrido = Job(title="Dev Hibrido", modality="Híbrido", remoto=False, url="https://example.com/2", source="test")
    job_presencial = Job(title="Dev Presencial", modality="Presencial", remoto=False, url="https://example.com/3", source="test")
    job_nd = Job(title="Dev ND", modality="N/D", remoto=False, url="https://example.com/4", source="test")

    jobs = [job_remoto, job_hibrido, job_presencial, job_nd]

    # Solo Remoto
    res_rem = filter_jobs(jobs, FilterOptions(modalities=["remoto"]))
    assert len(res_rem) == 1
    assert res_rem[0].title == "Dev Remoto"

    # Solo Híbrido (sin y con tilde)
    res_hib = filter_jobs(jobs, FilterOptions(modalities=["hibrido"]))
    assert len(res_hib) == 1
    assert res_hib[0].title == "Dev Hibrido"

    # Solo Presencial
    res_pres = filter_jobs(jobs, FilterOptions(modalities=["presencial"]))
    assert len(res_pres) == 1
    assert res_pres[0].title == "Dev Presencial"

    # Remoto + Híbrido
    res_multi = filter_jobs(jobs, FilterOptions(modalities=["remoto", "hibrido"]))
    assert len(res_multi) == 2
    assert {j.title for j in res_multi} == {"Dev Remoto", "Dev Hibrido"}

    # Todas las modalidades (las 3 juntas = sin filtro)
    res_all = filter_jobs(jobs, FilterOptions(modalities=["remoto", "hibrido", "presencial"]))
    assert len(res_all) == 4

    # Compatibilidad con bandera legacy only_remoto
    res_legacy = filter_jobs(jobs, FilterOptions(only_remoto=True))
    assert len(res_legacy) == 1
    assert res_legacy[0].title == "Dev Remoto"


def test_filter_jobs_by_location_presencial_and_hybrid():
    job_cba = Job(title="Dev Cba", location="Córdoba, Córdoba", modality="Presencial", url="https://example.com/1", source="computrabajo")
    job_bsas = Job(title="Dev BsAs", location="Capital Federal, Buenos Aires", modality="Híbrido", url="https://example.com/2", source="computrabajo")
    job_chile = Job(title="Dev Chile", location="Santiago, Chile", modality="Presencial", url="https://example.com/3", source="getonboard")

    jobs = [job_cba, job_bsas, job_chile]

    # Filtrar por Córdoba (debe coincidir ignorando tildes y mayúsculas)
    res_cba = filter_jobs(jobs, FilterOptions(location="cordoba"))
    assert len(res_cba) == 1
    assert res_cba[0].title == "Dev Cba"

    # Filtrar por Argentina (debe incluir ofertas de provincias argentinas / Computrabajo)
    res_arg = filter_jobs(jobs, FilterOptions(location="argentina"))
    assert len(res_arg) == 2
    assert {j.title for j in res_arg} == {"Dev Cba", "Dev BsAs"}

    # Filtrar por Chile
    res_chile = filter_jobs(jobs, FilterOptions(location="chile"))
    assert len(res_chile) == 1
    assert res_chile[0].title == "Dev Chile"


def test_filter_jobs_by_location_remoto():
    job_remote_global = Job(
        title="Dev Global",
        location="Worldwide / Remoto",
        modality="Remoto",
        remoto=True,
        url="https://example.com/1",
        source="remoteok",
    )
    job_remote_latam = Job(
        title="Dev LatAm",
        location="Cualquier lugar / LatAm",
        modality="Remoto",
        remoto=True,
        url="https://example.com/2",
        source="getonboard",
    )
    job_remote_arg = Job(
        title="Dev Arg",
        location="Argentina",
        modality="Remoto",
        remoto=True,
        url="https://example.com/3",
        source="getonboard",
    )
    job_remote_usa_restricted = Job(
        title="Dev USA Only",
        location="USA Only",
        modality="Remoto",
        remoto=True,
        url="https://example.com/4",
        source="remoteok",
    )

    jobs = [job_remote_global, job_remote_latam, job_remote_arg, job_remote_usa_restricted]

    # Búsqueda en Argentina: acepta globales, LatAm y Argentina; excluye USA Only
    res_arg = filter_jobs(jobs, FilterOptions(location="argentina"))
    assert len(res_arg) == 3
    assert {j.title for j in res_arg} == {"Dev Global", "Dev LatAm", "Dev Arg"}

    # Búsqueda acotada a Córdoba: acepta remotas válidas para Argentina
    res_cba = filter_jobs(jobs, FilterOptions(location="cordoba"))
    assert len(res_cba) == 3
    assert {j.title for j in res_cba} == {"Dev Global", "Dev LatAm", "Dev Arg"}

    # Búsqueda acotada a USA: acepta vacante USA Only y Globales
    res_usa = filter_jobs(jobs, FilterOptions(location="usa"))
    assert len(res_usa) == 2
    assert {j.title for j in res_usa} == {"Dev Global", "Dev USA Only"}


def test_filter_jobs_combined_modality_and_location():
    job_pres_cba = Job(title="Pres Cba", location="Córdoba, Córdoba", modality="Presencial", url="https://example.com/1", source="computrabajo")
    job_pres_bsas = Job(title="Pres BsAs", location="Buenos Aires", modality="Presencial", url="https://example.com/2", source="computrabajo")
    job_rem_global = Job(title="Rem Global", location="Worldwide", modality="Remoto", remoto=True, url="https://example.com/3", source="remoteok")
    job_hib_cba = Job(title="Hib Cba", location="Córdoba", modality="Híbrido", url="https://example.com/4", source="computrabajo")

    jobs = [job_pres_cba, job_pres_bsas, job_rem_global, job_hib_cba]

    # Modalidad Presencial + Remoto, ubicación Córdoba:
    # Debe conservar Presencial Córdoba y Remoto Global, descartando Presencial Buenos Aires e Híbrido
    opts = FilterOptions(modalities=["presencial", "remoto"], location="cordoba")
    res = filter_jobs(jobs, opts)
    assert len(res) == 2
    assert {j.title for j in res} == {"Pres Cba", "Rem Global"}


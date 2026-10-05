"""Tests unitarios para los modelos de datos de job0t."""

from job0t.models import Job, RawJob, FilterOptions, RunStats


def test_raw_job_creation():
    raw = RawJob(
        title="Desarrollador Python",
        company="Tech Co",
        location="Córdoba",
        description="Buscamos dev Python con FastAPI",
        url="https://example.com/job/123",
        source="computrabajo",
    )
    assert raw.title == "Desarrollador Python"
    assert raw.source == "computrabajo"
    assert raw.company == "Tech Co"


def test_job_id_deterministic_generation():
    id1 = Job.generate_id("computrabajo", "https://example.com/job/123")
    id2 = Job.generate_id("COMPUTRABAJO", "https://example.com/job/123 ")
    assert id1 == id2
    assert len(id1) == 16


def test_job_model_automatic_id_and_defaults():
    job = Job(
        title="Frontend React",
        description="Se busca frontend",
        url="https://example.com/job/react-1",
        source="getonboard",
    )
    assert job.id != ""
    assert job.company == "Confidencial"
    assert job.location == "N/D"
    assert job.status == "Nueva"
    assert job.ai_friendly is False
    assert job.freelance is False
    assert job.remoto is False


def test_filter_options_defaults():
    opts = FilterOptions()
    assert opts.categories == []
    assert opts.only_ai is False
    assert opts.only_freelance is False
    assert opts.only_remoto is False
    assert opts.export_format == "both"
    assert opts.filename is None


def test_run_stats_initialization():
    stats = RunStats(total_raw=10, total_unique=8, total_filtered=5)
    assert stats.total_raw == 10
    assert stats.total_unique == 8
    assert stats.total_filtered == 5

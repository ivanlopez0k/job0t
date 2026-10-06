"""Tests unitarios para el PipelineRunner de job0t."""

from datetime import datetime
from pathlib import Path
from typing import List, Optional
from job0t.config import AppConfig, CategoryDefinition, load_categories_config, load_flags_config
from job0t.models import FilterOptions, RawJob
from job0t.pipeline.runner import PipelineRunner
from job0t.scrapers.base import BaseScraper


class MockScraper(BaseScraper):
    def __init__(self, name: str, jobs: List[RawJob]):
        self._name = name
        self._jobs = jobs

    @property
    def name(self) -> str:
        return self._name

    def search(
        self,
        categories: List[CategoryDefinition],
        config: AppConfig,
        max_pages: Optional[int] = None,
    ) -> List[RawJob]:
        return self._jobs


def test_pipeline_runner_full_cycle(tmp_path: Path):
    raw_jobs_ct = [
        RawJob(
            title="Backend Python FastAPI",
            company="Tech Corp",
            location="Córdoba",
            modality="Remoto",
            salary="$3000 USD",
            description="Desarrollo con ChatGPT y Python.",
            url="https://computrabajo.com/job/1",
            source="computrabajo",
        )
    ]
    raw_jobs_gob = [
        RawJob(
            title="Frontend React UI",
            company="Design Co",
            location="Argentina",
            modality="Híbrido",
            salary=None,
            description="Figma y React.",
            url="https://getonbrd.com/job/2",
            source="getonboard",
        )
    ]

    mock_ct = MockScraper("computrabajo", raw_jobs_ct)
    mock_gob = MockScraper("getonboard", raw_jobs_gob)

    runner = PipelineRunner(
        categories_config=load_categories_config(),
        flags_config=load_flags_config(),
        scrapers=[mock_ct, mock_gob],
    )

    options = FilterOptions(
        categories=["desarrollo", "diseno"],
        only_ai=False,
        output_dir=str(tmp_path),
    )

    xlsx_path, csv_path, stats = runner.run(options)

    assert xlsx_path.exists()
    assert csv_path.exists()
    assert stats.total_raw == 2
    assert stats.total_unique == 2
    assert stats.ai_friendly_count == 1
    assert stats.remoto_count == 1
    assert stats.seniority_count["N/D"] == 2


def test_pipeline_runner_with_seniority_filter(tmp_path: Path):
    raw_jobs = [
        RawJob(
            title="Senior Backend Engineer",
            description="Desarrollo backend en Python.",
            url="https://computrabajo.com/job/sr",
            source="computrabajo",
        ),
        RawJob(
            title="Junior Frontend Engineer",
            description="Desarrollo frontend en React.",
            url="https://computrabajo.com/job/jr",
            source="computrabajo",
        ),
    ]

    mock_scraper = MockScraper("computrabajo", raw_jobs)
    runner = PipelineRunner(scrapers=[mock_scraper])

    options = FilterOptions(
        categories=[],
        seniority="senior",
        output_dir=str(tmp_path),
    )

    xlsx_path, csv_path, stats = runner.run(options)
    assert stats.total_raw == 2
    assert stats.total_filtered == 1
    assert stats.total_unique == 1
    assert "Senior" in stats.seniority_count
    assert stats.seniority_count["Senior"] == 1


def test_pipeline_runner_with_multi_seniority_list(tmp_path: Path):
    raw_jobs = [
        RawJob(
            title="Senior Backend Engineer",
            description="Python",
            url="https://computrabajo.com/job/sr",
            source="computrabajo",
        ),
        RawJob(
            title="Junior Frontend Engineer",
            description="React",
            url="https://computrabajo.com/job/jr",
            source="computrabajo",
        ),
        RawJob(
            title="Semi Senior QA",
            description="Cypress",
            url="https://computrabajo.com/job/ssr",
            source="computrabajo",
        ),
    ]

    runner = PipelineRunner(scrapers=[MockScraper("computrabajo", raw_jobs)])
    options = FilterOptions(
        seniority=["junior", "semi senior"],
        output_dir=str(tmp_path),
    )

    xlsx_path, csv_path, stats = runner.run(options)
    assert stats.total_raw == 3
    assert stats.total_filtered == 2
    assert stats.total_unique == 2
    assert "Junior" in stats.seniority_count
    assert "Semi Senior" in stats.seniority_count
    assert "Senior" not in stats.seniority_count



def test_pipeline_runner_export_xlsx_only(tmp_path: Path):
    raw_jobs = [
        RawJob(
            title="Backend Dev",
            description="Python FastAPI",
            url="https://computrabajo.com/job/1",
            source="computrabajo",
        )
    ]
    runner = PipelineRunner(scrapers=[MockScraper("computrabajo", raw_jobs)])
    options = FilterOptions(
        export_format="xlsx",
        output_dir=str(tmp_path),
    )
    xlsx_path, csv_path, stats = runner.run(options)

    assert xlsx_path is not None
    assert xlsx_path.exists()
    assert csv_path is None


def test_pipeline_runner_export_csv_only(tmp_path: Path):
    raw_jobs = [
        RawJob(
            title="Backend Dev",
            description="Python FastAPI",
            url="https://computrabajo.com/job/1",
            source="computrabajo",
        )
    ]
    runner = PipelineRunner(scrapers=[MockScraper("computrabajo", raw_jobs)])
    options = FilterOptions(
        export_format="csv",
        output_dir=str(tmp_path),
    )
    xlsx_path, csv_path, stats = runner.run(options)

    assert xlsx_path is None
    assert csv_path is not None
    assert csv_path.exists()


def test_pipeline_runner_default_filename_has_only_date(tmp_path: Path):
    raw_jobs = [
        RawJob(
            title="Backend Dev",
            description="Python FastAPI",
            url="https://computrabajo.com/job/1",
            source="computrabajo",
        )
    ]
    runner = PipelineRunner(scrapers=[MockScraper("computrabajo", raw_jobs)])
    options = FilterOptions(output_dir=str(tmp_path))
    xlsx_path, csv_path, _ = runner.run(options)

    today_str = datetime.now().strftime("%Y-%m-%d")
    expected_xlsx_name = f"jobs_{today_str}.xlsx"
    expected_csv_name = f"jobs_{today_str}.csv"

    assert xlsx_path is not None
    assert xlsx_path.name == expected_xlsx_name
    assert csv_path is not None
    assert csv_path.name == expected_csv_name


def test_pipeline_runner_custom_filename_with_and_without_extension(tmp_path: Path):
    raw_jobs = [
        RawJob(
            title="Backend Dev",
            description="Python FastAPI",
            url="https://computrabajo.com/job/1",
            source="computrabajo",
        )
    ]
    runner = PipelineRunner(scrapers=[MockScraper("computrabajo", raw_jobs)])

    # Sin extensión
    options1 = FilterOptions(filename="busqueda_2026-10-04", output_dir=str(tmp_path))
    xlsx1, csv1, _ = runner.run(options1)
    assert xlsx1 is not None and xlsx1.name == "busqueda_2026-10-04.xlsx"
    assert csv1 is not None and csv1.name == "busqueda_2026-10-04.csv"

    # Con extensión manual (.xlsx)
    options2 = FilterOptions(filename="busqueda_2026-10-04.xlsx", output_dir=str(tmp_path))
    xlsx2, csv2, _ = runner.run(options2)
    assert xlsx2 is not None and xlsx2.name == "busqueda_2026-10-04.xlsx"
    assert csv2 is not None and csv2.name == "busqueda_2026-10-04.csv"


def test_pipeline_runner_with_modality_and_location_filter(tmp_path: Path):
    raw_jobs = [
        RawJob(
            title="Backend Python Remoto",
            description="Python",
            location="Argentina",
            modality="Remoto",
            url="https://getonboard.com/job/1",
            source="getonboard",
        ),
        RawJob(
            title="Frontend React Presencial",
            description="React",
            location="Córdoba",
            modality="Presencial",
            url="https://computrabajo.com/job/2",
            source="computrabajo",
        ),
        RawJob(
            title="Dev USA Only",
            description="Node",
            location="USA Only",
            modality="Remoto",
            url="https://remoteok.com/job/3",
            source="remoteok",
        ),
    ]

    runner = PipelineRunner(scrapers=[MockScraper("mixed", raw_jobs)])
    options = FilterOptions(
        modalities=["remoto"],
        location="argentina",
        output_dir=str(tmp_path),
    )

    xlsx_path, csv_path, stats = runner.run(options)
    assert stats.total_raw == 3
    assert stats.total_filtered == 1
    assert stats.total_unique == 1
    assert stats.modality_count.get("Remoto") == 1
    assert xlsx_path.exists()



"""Tests unitarios para el PipelineRunner de job0t."""

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

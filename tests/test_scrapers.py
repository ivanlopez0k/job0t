"""Tests unitarios para los scrapers de job0t utilizando fixtures offline."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from job0t.config import AppConfig, CategoryDefinition
from job0t.scrapers.computrabajo import ComputrabajoScraper
from job0t.scrapers.getonboard import GetOnBoardScraper
from job0t.scrapers.jobicy import JobicyScraper
from job0t.scrapers.remoteok import RemoteOKScraper


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_computrabajo_parser_with_fixture():
    html_file = FIXTURES_DIR / "computrabajo_snippet.html"
    with open(html_file, "r", encoding="utf-8") as f:
        html_content = f.read()

    scraper = ComputrabajoScraper()
    jobs = scraper.parse_offers_html(html_content, base_url="https://ar.computrabajo.com")

    assert len(jobs) == 2

    # Oferta 1: Python
    job1 = jobs[0]
    assert job1.title == "Desarrollador Python Backend Senior"
    assert job1.company == "Empresa Líder de Software"
    assert job1.location == "Córdoba, Córdoba"
    assert job1.modality == "Remoto"
    assert job1.salary == "$ 2.500.000 (Neto mensual)"
    assert "https://ar.computrabajo.com/ofertas-de-trabajo/" in job1.url
    assert job1.source == "computrabajo"
    assert "FastAPI y PostgreSQL" in job1.description

    # Oferta 2: Diseño UI
    job2 = jobs[1]
    assert job2.title == "Diseñador UX / UI Figma"
    assert job2.company == "Agencia Digital Creativa"
    assert job2.location == "Argentina"
    assert job2.modality == "Híbrido"
    assert job2.salary is None
    assert job2.source == "computrabajo"


def test_getonboard_parser_with_fixture():
    json_file = FIXTURES_DIR / "getonboard_snippet.json"
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    scraper = GetOnBoardScraper()
    jobs = scraper.parse_jobs_json(data)

    assert len(jobs) == 2

    # Oferta 1: Principal Backend
    job1 = jobs[0]
    assert job1.title == "Principal Backend Architect (AI-Native)"
    assert job1.company == "Cocoon Labs"
    assert job1.modality == "Remoto"
    assert job1.salary == "$7000 - $9500 USD"
    assert job1.url == "https://www.getonbrd.com/jobs/principal-engineer-cocoon-remote"
    assert job1.source == "getonboard"
    assert "GitHub Copilot and Cursor" in job1.description

    # Oferta 2: Data Analyst
    job2 = jobs[1]
    assert job2.title == "Data Analyst Power BI"
    assert job2.company == "Fintech Global"
    assert job2.salary is None
    assert job2.source == "getonboard"


def test_computrabajo_search_mocked(monkeypatch):
    scraper = ComputrabajoScraper()
    config = AppConfig()
    categories = [
        CategoryDefinition(
            label="Desarrollo de software",
            search_terms=["programador python"],
            match_keywords=["python"],
            exclude_keywords=[],
        )
    ]

    html_file = FIXTURES_DIR / "computrabajo_snippet.html"
    with open(html_file, "r", encoding="utf-8") as f:
        fake_html = f.read()

    class FakeResponse:
        status_code = 200
        text = fake_html

        def raise_for_status(self):
            pass

    mock_client = MagicMock()
    mock_client.get.return_value = FakeResponse()
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None

    monkeypatch.setattr("httpx.Client", lambda **kwargs: mock_client)

    results = scraper.search(categories, config, max_pages=1)
    assert len(results) == 2
    assert results[0].title == "Desarrollador Python Backend Senior"


def test_getonboard_search_mocked(monkeypatch):
    scraper = GetOnBoardScraper()
    config = AppConfig()
    categories = [
        CategoryDefinition(
            label="Desarrollo de software",
            search_terms=["developer"],
            match_keywords=["developer"],
            exclude_keywords=[],
        )
    ]

    json_file = FIXTURES_DIR / "getonboard_snippet.json"
    with open(json_file, "r", encoding="utf-8") as f:
        fake_json = json.load(f)

    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return fake_json

    mock_client = MagicMock()
    mock_client.get.return_value = FakeResponse()
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None

    monkeypatch.setattr("httpx.Client", lambda **kwargs: mock_client)

    results = scraper.search(categories, config, max_pages=1)
    assert len(results) == 2
    assert results[0].title == "Principal Backend Architect (AI-Native)"


def test_jobicy_parser():
    fake_payload = {
        "jobs": [
            {
                "id": 101,
                "url": "https://jobicy.com/jobs/101-python-dev",
                "jobSlug": "101-python-dev",
                "jobTitle": "Senior Python Backend Engineer",
                "companyName": "RemoteTech Inc",
                "jobGeo": "LatAm / Anywhere",
                "jobLevel": "Senior",
                "jobDescription": "Desarrollo backend con FastAPI y PostgreSQL.",
                "pubDate": "2026-10-05T12:00:00+00:00",
                "salaryMin": 90000,
                "salaryMax": 120000,
                "salaryCurrency": "USD",
                "salaryPeriod": "yearly",
            },
            {
                "id": 102,
                "url": "https://jobicy.com/jobs/102-qa-tester",
                "jobSlug": "102-qa-tester",
                "jobTitle": "Junior QA Automation",
                "companyName": "Quality Corp",
                "jobGeo": "Worldwide",
                "jobLevel": "Junior",
                "jobExcerpt": "Testing automatizado con Playwright.",
                "pubDate": "2026-10-05T10:00:00+00:00",
                "salaryMin": 0,
                "salaryMax": 0,
            },
        ]
    }

    scraper = JobicyScraper()
    jobs = scraper.parse_jobs_json(fake_payload)
    assert len(jobs) == 2

    job1 = jobs[0]
    assert job1.title == "Senior Python Backend Engineer"
    assert job1.company == "RemoteTech Inc"
    assert job1.location == "LatAm / Anywhere"
    assert job1.modality == "Remoto"
    assert job1.salary == "$90,000 - $120,000 USD/año"
    assert job1.source == "jobicy"
    assert job1.raw_payload.get("job_level") == "Senior"

    job2 = jobs[1]
    assert job2.title == "Junior QA Automation"
    assert job2.company == "Quality Corp"
    assert job2.salary is None
    assert job2.raw_payload.get("job_level") == "Junior"


def test_jobicy_search_mocked(monkeypatch):
    scraper = JobicyScraper()
    config = AppConfig()
    categories = [
        CategoryDefinition(
            label="Desarrollo de software",
            search_terms=["developer"],
            match_keywords=["developer"],
            exclude_keywords=[],
        )
    ]

    fake_json = {
        "jobs": [
            {
                "id": 201,
                "url": "https://jobicy.com/jobs/201-fullstack",
                "jobTitle": "Fullstack Python React Developer",
                "companyName": "Global Corp",
                "jobGeo": "Worldwide",
                "jobDescription": "Fullstack development.",
            }
        ]
    }

    class FakeResponse:
        status_code = 200

        def json(self):
            return fake_json

    mock_client = MagicMock()
    mock_client.get.return_value = FakeResponse()
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None

    monkeypatch.setattr("httpx.Client", lambda **kwargs: mock_client)

    results = scraper.search(categories, config, max_pages=1)
    assert len(results) == 1
    assert results[0].title == "Fullstack Python React Developer"
    assert results[0].source == "jobicy"
    assert results[0].modality == "Remoto"


def test_remoteok_parser():
    fake_payload = [
        {"legal": "Notice"},
        {
            "id": 501,
            "position": "Staff DevOps Engineer",
            "company": "CloudNative LLC",
            "location": "Anywhere",
            "salary_min": 140000,
            "salary_max": 180000,
            "tags": ["kubernetes", "aws", "terraform"],
            "url": "https://remoteok.com/remote-jobs/501",
            "description": "Infraestructura cloud y pipelines CI/CD.",
            "date": "2026-10-05T14:00:00+00:00",
            "epoch": 1728136800,
        },
        {
            "id": 502,
            "position": "UX UI Product Designer",
            "company": "",
            "location": "",
            "salary_min": 0,
            "salary_max": 0,
            "tags": ["figma", "ux"],
            "apply_url": "https://apply.workable.com/502",
            "description": "Diseño de interfaces web y mobile.",
        },
    ]

    scraper = RemoteOKScraper()
    jobs = scraper.parse_jobs_json(fake_payload)
    assert len(jobs) == 2

    job1 = jobs[0]
    assert job1.title == "Staff DevOps Engineer"
    assert job1.company == "CloudNative LLC"
    assert job1.location == "Anywhere"
    assert job1.modality == "Remoto"
    assert job1.salary == "$140,000 - $180,000 USD/año"
    assert job1.source == "remoteok"
    assert "Tags: kubernetes, aws, terraform" in job1.description

    job2 = jobs[1]
    assert job2.title == "UX UI Product Designer"
    assert job2.company == "Confidencial"
    assert job2.location == "Worldwide / Remoto"
    assert job2.salary is None
    assert job2.url == "https://apply.workable.com/502"


def test_remoteok_search_mocked(monkeypatch):
    scraper = RemoteOKScraper()
    config = AppConfig()
    categories = [
        CategoryDefinition(
            label="Desarrollo de software",
            search_terms=["developer"],
            match_keywords=["developer"],
            exclude_keywords=[],
        )
    ]

    fake_json = [
        {"legal": "meta"},
        {
            "id": 999,
            "position": "Senior Go Developer",
            "company": "GoCorp",
            "url": "https://remoteok.com/job/999",
            "description": "Golang microservices.",
        },
    ]

    class FakeResponse:
        status_code = 200

        def json(self):
            return fake_json

    mock_client = MagicMock()
    mock_client.get.return_value = FakeResponse()
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None

    monkeypatch.setattr("httpx.Client", lambda **kwargs: mock_client)

    results = scraper.search(categories, config, max_pages=1)
    assert len(results) == 1
    assert results[0].title == "Senior Go Developer"
    assert results[0].source == "remoteok"
    assert results[0].modality == "Remoto"



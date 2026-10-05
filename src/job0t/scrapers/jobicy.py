"""Scraper de ofertas de empleo para Jobicy (REST API pública v2)."""

import logging
from typing import Any, Dict, List, Optional
import httpx

from job0t.config import AppConfig, CategoryDefinition
from job0t.models import RawJob
from job0t.scrapers.base import BaseScraper

logger = logging.getLogger("job0t.scrapers.jobicy")


class JobicyScraper(BaseScraper):
    """Adaptador para consumo de la API pública REST v2 de Jobicy."""

    CATEGORY_MAP: Dict[str, List[str]] = {
        "desarrollo": ["engineering"],
        "desarrollo_frontend": ["engineering", "web-app-design"],
        "desarrollo_backend": ["engineering"],
        "desarrollo_fullstack": ["engineering"],
        "desarrollo_mobile": ["engineering"],
        "desarrollo_gamedev": ["engineering", "design-multimedia"],
        "desarrollo_desktop": ["engineering"],
        "desarrollo_ai": ["engineering", "data-science"],
        "desarrollo_ciberseguridad": ["cybersecurity"],
        "desarrollo_web3": ["engineering"],
        "diseno": ["design-multimedia", "web-app-design"],
        "diseno_ux_ui": ["web-app-design"],
        "diseno_product": ["web-app-design", "design-multimedia"],
        "diseno_ux_research": ["web-app-design"],
        "diseno_grafico": ["design-multimedia"],
        "diseno_web_nocode": ["web-app-design"],
        "diseno_motion": ["design-multimedia"],
        "diseno_3d": ["design-multimedia"],
        "data": ["data-science"],
        "data_analytics": ["data-science"],
        "data_engineering": ["data-science", "engineering"],
        "data_science": ["data-science"],
        "qa": ["qa-testing"],
        "qa_automation": ["qa-testing"],
        "qa_manual": ["qa-testing"],
        "devops": ["admin"],
        "devops_sre": ["admin"],
        "cloud_engineering": ["admin"],
        "sysadmin": ["admin"],
        "producto": ["management", "project-management"],
        "producto_management": ["management"],
        "producto_agile": ["project-management"],
        "tech_lead": ["management", "engineering"],
        "soporte": ["technical-support", "supporting"],
    }

    @property
    def name(self) -> str:
        return "jobicy"

    def parse_jobs_json(self, payload: Dict[str, Any]) -> List[RawJob]:
        """Parsea la respuesta JSON de Jobicy y extrae RawJobs."""
        items = payload.get("jobs", [])
        results: List[RawJob] = []

        for item in items:
            title = (item.get("jobTitle") or "").strip()
            if not title:
                continue

            url = (item.get("url") or "").strip()
            if not url:
                continue

            company = (item.get("companyName") or "").strip() or "Confidencial"
            location = (item.get("jobGeo") or "").strip() or "Remoto"
            modality = "Remoto"

            # Salario
            sal_min = item.get("salaryMin")
            sal_max = item.get("salaryMax")
            currency = item.get("salaryCurrency") or "USD"
            period = (item.get("salaryPeriod") or "").lower()
            period_str = "año" if period in ("yearly", "annual") else ("mes" if period in ("monthly",) else period)

            salary = None
            if sal_min and sal_max and sal_min > 0 and sal_max > 0:
                salary = f"${sal_min:,} - ${sal_max:,} {currency}/{period_str}"
            elif sal_min and sal_min > 0:
                salary = f"Desde ${sal_min:,} {currency}/{period_str}"
            elif sal_max and sal_max > 0:
                salary = f"Hasta ${sal_max:,} {currency}/{period_str}"

            # Descripción
            description = (item.get("jobDescription") or item.get("jobExcerpt") or title).strip()

            # Fecha de publicación
            pub_date = item.get("pubDate")
            published_at_raw = str(pub_date) if pub_date else None

            # Raw payload para seniority y filtrado
            job_level = item.get("jobLevel")

            results.append(
                RawJob(
                    title=title,
                    company=company,
                    location=location,
                    modality=modality,
                    salary=salary,
                    description=description,
                    url=url,
                    source=self.name,
                    published_at_raw=published_at_raw,
                    raw_payload={
                        "id": item.get("id"),
                        "job_level": job_level,
                        "job_slug": item.get("jobSlug"),
                        "industry": item.get("jobIndustry"),
                    },
                )
            )

        return results

    def _resolve_industries(self, categories: List[CategoryDefinition]) -> List[str]:
        """Obtiene la lista de slugs de industria únicos asociados a las categorías solicitadas."""
        if not categories:
            return []

        industries = set()
        for cat in categories:
            cat_label = cat.label.lower()
            matched = False
            for key, mapped_industries in self.CATEGORY_MAP.items():
                if key in cat_label or cat_label in key:
                    industries.update(mapped_industries)
                    matched = True
            # Fallback por search_terms si no matcheó directo
            if not matched:
                for term in cat.search_terms:
                    term_lower = term.lower()
                    for key, mapped_industries in self.CATEGORY_MAP.items():
                        if key in term_lower or term_lower in key:
                            industries.update(mapped_industries)

        return sorted(industries)

    def search(
        self,
        categories: List[CategoryDefinition],
        config: AppConfig,
        max_pages: Optional[int] = None,
    ) -> List[RawJob]:
        """Consulta la API de Jobicy por cada industria relevante o genérica."""
        source_cfg = config.sources.get(self.name)
        if source_cfg and not source_cfg.enabled:
            return []

        base_url = (source_cfg.base_url if source_cfg else "https://jobicy.com/api/v2/remote-jobs").rstrip("/")
        timeout = config.search.timeout_seconds
        headers = {
            "User-Agent": config.search.user_agent or "job0t/0.1.0 (https://github.com/ivanlopez0k/job0t)",
            "Accept": "application/json",
        }

        industries = self._resolve_industries(categories)
        all_jobs: List[RawJob] = []
        seen_urls = set()

        # Determinar queries a realizar
        queries = industries if industries else [None]
        limit_queries = queries[:max_pages] if max_pages else queries

        with httpx.Client(timeout=timeout, headers=headers, follow_redirects=True) as client:
            for industry in limit_queries:
                params: Dict[str, Any] = {"count": 50}
                if industry:
                    params["industry"] = industry

                try:
                    logger.info("Consultando Jobicy con params: %s", params)
                    resp = client.get(base_url, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        jobs = self.parse_jobs_json(data)
                        for job in jobs:
                            if job.url not in seen_urls:
                                seen_urls.add(job.url)
                                all_jobs.append(job)
                    else:
                        logger.warning(
                            "Jobicy retornó status %d para params %s: %s",
                            resp.status_code,
                            params,
                            resp.text[:120],
                        )
                except Exception as exc:
                    logger.error("Error consultando Jobicy con params %s: %s", params, exc)

        return all_jobs

"""Scraper de ofertas de empleo para RemoteOK (REST API pública)."""

import logging
from typing import Any, Dict, List, Optional
import httpx

from job0t.config import AppConfig, CategoryDefinition
from job0t.models import RawJob
from job0t.scrapers.base import BaseScraper

logger = logging.getLogger("job0t.scrapers.remoteok")


class RemoteOKScraper(BaseScraper):
    """Adaptador para consumo de la API pública REST de RemoteOK."""

    @property
    def name(self) -> str:
        return "remoteok"

    def parse_jobs_json(self, payload: List[Dict[str, Any]]) -> List[RawJob]:
        """Parsea la respuesta JSON de RemoteOK y extrae RawJobs."""
        if not isinstance(payload, list):
            return []

        results: List[RawJob] = []

        for item in payload:
            if not isinstance(item, dict):
                continue

            # El primer elemento de la API suele ser un objeto legal/metadata sin 'position' ni 'id'
            title = (item.get("position") or "").strip()
            if not title:
                continue

            # URL de la oferta
            job_id = item.get("id")
            url = (item.get("url") or item.get("apply_url") or "").strip()
            if not url and job_id:
                url = f"https://remoteok.com/remote-jobs/{job_id}"
            if not url:
                continue

            # Empresa
            company = (item.get("company") or "").strip() or "Confidencial"

            # Ubicación y Modalidad
            loc = (item.get("location") or "").strip()
            location = loc if loc else "Worldwide / Remoto"
            modality = "Remoto"

            # Salario
            sal_min = item.get("salary_min")
            sal_max = item.get("salary_max")
            salary = None
            try:
                min_val = int(sal_min) if sal_min is not None else 0
                max_val = int(sal_max) if sal_max is not None else 0
                if min_val > 0 and max_val > 0:
                    salary = f"${min_val:,} - ${max_val:,} USD/año"
                elif min_val > 0:
                    salary = f"Desde ${min_val:,} USD/año"
                elif max_val > 0:
                    salary = f"Hasta ${max_val:,} USD/año"
            except (ValueError, TypeError):
                pass

            # Descripción y tags
            raw_desc = item.get("description") or title
            tags = item.get("tags") or []
            tags_str = ", ".join(tags) if isinstance(tags, list) else ""
            if tags_str:
                description = f"{raw_desc}\n\nTags: {tags_str}"
            else:
                description = raw_desc

            # Fecha
            pub_date = item.get("date")
            published_at_raw = str(pub_date) if pub_date else None

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
                        "id": job_id,
                        "tags": tags,
                        "epoch": item.get("epoch"),
                    },
                )
            )

        return results

    def search(
        self,
        categories: List[CategoryDefinition],
        config: AppConfig,
        max_pages: Optional[int] = None,
    ) -> List[RawJob]:
        """Consulta la API de RemoteOK y devuelve la lista de ofertas."""
        source_cfg = config.sources.get(self.name)
        if source_cfg and not source_cfg.enabled:
            return []

        base_url = (source_cfg.base_url if source_cfg else "https://remoteok.com/api").rstrip("/")
        timeout = config.search.timeout_seconds
        headers = {
            "User-Agent": config.search.user_agent or "job0t/0.1.0 (https://github.com/ivanlopez0k/job0t)",
            "Accept": "application/json",
        }

        try:
            logger.info("Consultando RemoteOK en %s", base_url)
            with httpx.Client(timeout=timeout, headers=headers, follow_redirects=True) as client:
                resp = client.get(base_url)
                if resp.status_code == 200:
                    payload = resp.json()
                    jobs = self.parse_jobs_json(payload)
                    return jobs
                else:
                    logger.warning("RemoteOK retornó status %d: %s", resp.status_code, resp.text[:120])
                    return []
        except Exception as exc:
            logger.error("Error consultando RemoteOK: %s", exc)
            return []

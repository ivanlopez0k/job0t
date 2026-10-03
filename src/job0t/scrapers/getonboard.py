"""Scraper de ofertas de empleo para Get on Board (REST API pública)."""

import logging
import random
import re
import time
from typing import Any, Dict, List, Optional
import httpx
from job0t.config import AppConfig, CategoryDefinition
from job0t.models import RawJob
from job0t.scrapers.base import BaseScraper

logger = logging.getLogger("job0t.scrapers.getonboard")


class GetOnBoardScraper(BaseScraper):
    """Adaptador para consumo de la API pública REST de Get on Board."""

    CATEGORY_MAP: Dict[str, List[str]] = {
        "desarrollo": ["programming", "mobile-developer"],
        "diseno": ["design-ux"],
        "data": ["data-science-analytics"],
        "qa": ["sysadmin-devops-qa"],
        "devops": ["sysadmin-devops-qa"],
        "soporte": ["technical-support"],
        "producto": ["operations-management", "innovation-agile"],
        "marketing": ["digital-marketing"],
    }

    @property
    def name(self) -> str:
        return "getonboard"

    def parse_jobs_json(self, payload: Dict[str, Any]) -> List[RawJob]:
        """Parsea la respuesta JSON de Get on Board y extrae RawJobs."""
        items = payload.get("data", [])
        results: List[RawJob] = []

        for item in items:
            attrs = item.get("attributes", {})
            title = attrs.get("title", "").strip()
            if not title:
                continue

            # Enlace público
            links = item.get("links", {})
            url = links.get("public_url", "").strip()

            # Descripción combinada
            desc_parts = [attrs.get("description", "")]
            if attrs.get("functions"):
                desc_parts.append(attrs.get("functions"))
            if attrs.get("benefits"):
                desc_parts.append(attrs.get("benefits"))
            description = " ".join(filter(None, desc_parts)).strip() or title

            # Empresa
            company_data = attrs.get("company", {}).get("data", {})
            company = company_data.get("attributes", {}).get("name") if isinstance(company_data, dict) else None
            if not company and url:
                slug = url.rstrip("/").split("/")[-1]
                title_slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
                rem = slug
                for w in title_slug.split("-")[:4]:
                    if rem.startswith(w + "-"):
                        rem = rem[len(w) + 1 :]
                parts = rem.split("-")
                comp_parts = [
                    p for p in parts
                    if p not in ("remote", "santiago", "chile", "argentina", "hybrid", "colombia", "mexico", "peru", "latam")
                    and not (len(p) <= 4 and re.match(r"^[a-f0-9]+$", p))
                ]
                if comp_parts:
                    company = " ".join(comp_parts).title()

            # Modalidad y Ubicación
            is_remote = attrs.get("remote", False)
            remote_modality = (attrs.get("remote_modality") or "").lower()
            if is_remote and "hybrid" not in remote_modality:
                modality = "Remoto"
            elif "hybrid" in remote_modality:
                modality = "Híbrido"
            elif any(w in remote_modality for w in ["on_site", "presencial"]):
                modality = "Presencial"
            else:
                modality = "Remoto" if is_remote else "Presencial"

            countries = attrs.get("countries", [])
            geo_countries = [c for c in countries if c.strip().lower() not in ("remote", "remoto")]
            if geo_countries:
                location = ", ".join(geo_countries)
            else:
                location = "Cualquier lugar / LatAm" if is_remote else "N/D"

            # Salario
            min_sal = attrs.get("min_salary")
            max_sal = attrs.get("max_salary")
            salary = None
            if min_sal and max_sal:
                salary = f"${min_sal} - ${max_sal} USD"
            elif min_sal:
                salary = f"Desde ${min_sal} USD"
            elif max_sal:
                salary = f"Hasta ${max_sal} USD"

            # Fecha
            pub_at = attrs.get("published_at")
            published_at_raw = str(pub_at) if pub_at is not None else None

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
                        "seniority_id": attrs.get("seniority", {}).get("data", {}).get("id") if isinstance(attrs.get("seniority"), dict) else None,
                    },
                )
            )

        return results

    def _resolve_categories(self, categories: List[CategoryDefinition]) -> List[str]:
        """Mapea las categorías seleccionadas a identificadores de la API de Get on Board."""
        api_cats = set()
        for cat in categories:
            # Buscar coincidencia por label o clave
            matched = False
            for key, mapped in self.CATEGORY_MAP.items():
                if key in cat.label.lower() or any(term in cat.label.lower() for term in mapped):
                    api_cats.update(mapped)
                    matched = True
            if not matched:
                # Si no matcheó directo, fallback a programming
                api_cats.add("programming")
        return list(api_cats)

    def search(
        self,
        categories: List[CategoryDefinition],
        config: AppConfig,
        max_pages: Optional[int] = None,
    ) -> List[RawJob]:
        """Ejecuta búsquedas en la API de Get on Board para las categorías mapeadas."""
        source_cfg = config.sources.get(self.name)
        if source_cfg and not source_cfg.enabled:
            logger.info("Scraper %s está deshabilitado en la configuración.", self.name)
            return []

        base_url = source_cfg.base_url if source_cfg else "https://www.getonbrd.com/api/v0"
        limit_pages = max_pages or config.search.max_pages_per_source
        delay_min, delay_max = config.search.delay_range_seconds

        headers = {
            "User-Agent": config.search.user_agent,
            "Accept": "application/json",
        }

        api_categories = self._resolve_categories(categories)
        all_raw_jobs: List[RawJob] = []
        collected_urls = set()

        with httpx.Client(headers=headers, timeout=config.search.timeout_seconds, follow_redirects=True) as client:
            for cat_id in api_categories:
                for page in range(1, limit_pages + 1):
                    endpoint = f"{base_url.rstrip('/')}/categories/{cat_id}/jobs"
                    params = {"per_page": 50, "page": page}

                    try:
                        logger.debug("Consultando Get on Board: %s (página %d)", endpoint, page)
                        response = client.get(endpoint, params=params)
                        if response.status_code == 404:
                            break
                        response.raise_for_status()

                        data = response.json()
                        jobs = self.parse_jobs_json(data)
                        if not jobs:
                            break

                        for j in jobs:
                            if j.url not in collected_urls:
                                collected_urls.add(j.url)
                                all_raw_jobs.append(j)

                        # Si la página actual es la última según la metadata, frenar
                        meta = data.get("meta", {})
                        if page >= meta.get("total_pages", 1):
                            break

                    except Exception as exc:
                        logger.warning("Error al consultar Get on Board (%s, p.%d): %s", cat_id, page, exc)
                        break

                    time.sleep(random.uniform(delay_min, delay_max))

        return all_raw_jobs

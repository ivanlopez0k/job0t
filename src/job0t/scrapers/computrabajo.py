"""Scraper de ofertas de empleo para Computrabajo Argentina (HTML)."""

import logging
import random
import re
import time
from typing import List, Optional
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
import httpx
from job0t.config import AppConfig, CategoryDefinition
from job0t.models import RawJob
from job0t.scrapers.base import BaseScraper

logger = logging.getLogger("job0t.scrapers.computrabajo")


class ComputrabajoScraper(BaseScraper):
    """Adaptador para extracción de ofertas públicas desde Computrabajo Argentina."""

    @property
    def name(self) -> str:
        return "computrabajo"

    def parse_offers_html(self, html: str, base_url: str = "https://ar.computrabajo.com") -> List[RawJob]:
        """Parsea el HTML de listado de Computrabajo y extrae RawJobs."""
        if not html or not html.strip():
            return []

        soup = BeautifulSoup(html, "html.parser")
        articles = soup.select("article.box_offer")
        results: List[RawJob] = []

        for art in articles:
            # 1. Título y enlace
            title_tag = art.select_one("h2.title a, h1.title a, a.js-o-link")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            href = title_tag.get("href", "")
            if href.startswith("/"):
                url = f"{base_url.rstrip('/')}{href}"
            else:
                url = href or base_url

            # 2. Empresa
            company = None
            comp_tag = art.select_one("a[offer-grid-article-company-url], p.dFlex a.fc_base, span.it-blank, a.fc_base, span.fc_base")
            if comp_tag and comp_tag != title_tag:
                company = comp_tag.get_text(strip=True)
            elif art.select_one("p.fs16"):
                meta_p = art.select_one("p.fs16")
                c_span = meta_p.select_one("span.it-blank, a.fc_base")
                if c_span:
                    company = c_span.get_text(strip=True)

            # 3. Ubicación (p.fs16 secundario, span.item_location o URL)
            location = None
            loc_paragraphs = art.select("p.fs16")
            if len(loc_paragraphs) > 1:
                location = loc_paragraphs[1].get_text(strip=True)
            elif art.select_one("span.item_location"):
                location = art.select_one("span.item_location").get_text(strip=True)

            if not location and href:
                loc_match = re.search(r"-en-([a-z0-9\-]+)-[a-f0-9]{32}", href, re.IGNORECASE)
                if loc_match:
                    location = loc_match.group(1).replace("-", " ").title()

            # 4. Descripción o extracto
            desc_tag = art.select_one("p.bRS, p.fs13.mb10, p.fs13")
            description = desc_tag.get_text(" ", strip=True) if desc_tag else title

            # 5. Modalidad y salario (inspeccionando div.fs13 y span.tag)
            modality = None
            salary = None
            for sp in art.select("div.fs13 span, span.tag.base, span.tag"):
                txt = sp.get_text(strip=True)
                low = txt.lower()
                if any(m in low for m in ["remoto", "presencial", "híbrido", "hibrido", "home office"]):
                    modality = txt
                elif "$" in txt or "neto" in low or "mensual" in low:
                    salary = txt

            # 5. Fecha cruda
            date_tag = art.select_one("p.fc_aux.fs13, p.fc_aux, span.fc_aux")
            published_at_raw = date_tag.get_text(strip=True) if date_tag else None

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
                )
            )

        return results

    def search(
        self,
        categories: List[CategoryDefinition],
        config: AppConfig,
        max_pages: Optional[int] = None,
    ) -> List[RawJob]:
        """Ejecuta búsquedas para los términos de las categorías configuradas."""
        source_cfg = config.sources.get(self.name)
        if source_cfg and not source_cfg.enabled:
            logger.info("Scraper %s está deshabilitado en la configuración.", self.name)
            return []

        base_url = source_cfg.base_url if source_cfg else "https://ar.computrabajo.com"
        limit_pages = max_pages or config.search.max_pages_per_source
        delay_min, delay_max = config.search.delay_range_seconds

        headers = {
            "User-Agent": config.search.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9",
        }

        all_raw_jobs: List[RawJob] = []
        collected_urls = set()

        # Recolectar términos únicos de búsqueda de todas las categorías
        unique_terms = set()
        for cat in categories:
            for term in cat.search_terms:
                if term.strip():
                    unique_terms.add(term.strip().lower())

        with httpx.Client(headers=headers, timeout=config.search.timeout_seconds, follow_redirects=True) as client:
            for term in unique_terms:
                encoded_term = quote_plus(term)
                for page in range(1, limit_pages + 1):
                    url = f"{base_url.rstrip('/')}/trabajo-de-{encoded_term}"
                    params = {"p": page} if page > 1 else {}

                    try:
                        logger.debug("Consultando Computrabajo: %s (página %d)", url, page)
                        response = client.get(url, params=params)
                        if response.status_code == 404:
                            # No hay más páginas para esta búsqueda
                            break
                        response.raise_for_status()

                        jobs = self.parse_offers_html(response.text, base_url=base_url)
                        if not jobs:
                            # No se encontraron más resultados
                            break

                        for j in jobs:
                            if j.url not in collected_urls:
                                collected_urls.add(j.url)
                                all_raw_jobs.append(j)

                    except Exception as exc:
                        logger.warning("Error al consultar Computrabajo (%s, p.%d): %s", term, page, exc)
                        break

                    # Jitter respetuoso entre peticiones
                    time.sleep(random.uniform(delay_min, delay_max))

        return all_raw_jobs

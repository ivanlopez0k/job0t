# Propuesta Técnica: 001-mvp-pipeline

## 1. Contexto y Problema
El objetivo de **job0t** es automatizar la búsqueda, normalización, clasificación y reporte de ofertas laborales locales y remotas desde múltiples fuentes (portales con HTML y APIs públicas), permitiendo al usuario:
1. Seleccionar categorías de interés (`Desarrollo`, `Diseño`, `Data`, etc.).
2. Detectar y marcar banderas de valor agregado con evidencia auditable (`AI FRIENDLY`, `FREELANCE`, `REMOTO`).
3. Generar reportes ejecutables y de seguimiento directo en formatos `.xlsx` y `.csv`.

## 2. Decisiones Arquitectónicas Fundamentales

### A. Desacoplamiento DTO vs Dominio (`RawJob` -> `Job`)
- **Problema:** Los portales externos devuelven datos sucios, formatos de fechas dispares (ej. fechas relativas tipo "hace 2 horas"), textos truncados o nulos.
- **Decisión:** Los scrapers implementan un puerto común `BaseScraper` y emiten exclusivamente `RawJob` (un DTO permisivo de transporte). El paso de normalización en el pipeline se encarga de sanear y construir la entidad de dominio estricta `Job` (validada con `pydantic`).

### B. Cero Bloat: `openpyxl` puro + `csv` estándar (Sin Pandas)
- **Problema:** Incluir `pandas` implica arrastrar `numpy` y más de 80 MB de binarios solo para volcar tablas. Además, Pandas dificulta la inyección de estilos finos, dropdowns de validación de datos y fórmulas de hipervínculos nativos de Excel.
- **Decisión:** Usar `openpyxl` directo para el archivo Excel (formato condicional, colores, validación con listas desplegables, links clickeables) y el módulo estándar `csv` de Python para el archivo plano. El tiempo de arranque del CLI será instantáneo.

### C. Fuentes de Datos del MVP
- **Computrabajo Argentina:** Scraping respetuoso sobre HTML público (`httpx` + `BeautifulSoup4`), simulando User-Agent y rate limiting básico.
- **Get on Board:** Consumo directo de la API pública REST (`https://www.getonbrd.com/api/v0/categories/{category}/jobs`), sin necesidad de registrar credenciales ni API keys para el MVP.

### D. Pipeline de Procesamiento Lineal
```
CLI (Typer + Questionary)
         │
         ▼
[Scrapers] ──► List[RawJob]
         │
         ▼
[Normalizer] ──► List[Job] (Pydantic validado)
         │
         ▼
[Classifier] ──► asigna categorías según config/categories.yaml
         │
         ▼
[FlagDetector] ──► evalúa AI_FRIENDLY, FREELANCE, REMOTO + guarda evidencia
         │
         ▼
[Filter] ──► descarta o filtra según flags/categorías seleccionadas
         │
         ▼
[Deduplicator] ──► deduplica por ID/URL
         │
         ▼
[Exporters] ──► output/jobs_YYYY-MM-DD_HHMM.xlsx y .csv
```

## 3. Alcance del MVP

### Incluido
- CLI con comandos `run` (modo interactivo con `questionary` y modo directo con flags de `typer`).
- Modelos `RawJob` y `Job` en `src/job0t/models.py`.
- Configuración modular YAML (`config.yaml`, `categories.yaml`, `flags.yaml`).
- Scraper de Computrabajo (`src/job0t/scrapers/computrabajo.py`).
- Scraper de Get on Board (`src/job0t/scrapers/getonboard.py`).
- Pipeline completo: normalización, clasificación multietiqueta, detección de banderas con evidencia, filtrado y deduplicación.
- Exportador Excel con `openpyxl`: hoja "Ofertas" (con enlaces clickeables, dropdown de status "Nueva / Interesa / Postulado / Descartado", formato condicional verde para SI) y hoja "Resumen".
- Exportador CSV complementario.
- Tests unitarios con `pytest` y fixtures HTML/JSON para no depender de conexión externa.

### Excluido del MVP (Fases Posteriores)
- Base de datos SQLite para histórico entre ejecuciones (Fase 2).
- Scraping de LinkedIn / alertas por correo IMAP (Fase 3).
- Scoring con LLM (Fase 4).
- Postulación automática/asistida (Fase 5).

## 4. Riesgos y Mitigaciones
- **Bloqueo o cambios en Computrabajo:** Se aísla el scraping en un módulo independiente y se prueban los parsers con fixtures HTML locales. Delays configurables.
- **Falsos positivos en banderas:** Se incluye la columna explícita de `evidencia` (palabras encontradas) en cada fila del Excel para auditoría inmediata.

## 5. Próximo Paso Recomendado
- Fase **`sdd-spec`**: Especificación formal de contratos (esquemas de datos `RawJob`/`Job`, estructura exacta de los YAMLs, contratos de CLI y de exportación).

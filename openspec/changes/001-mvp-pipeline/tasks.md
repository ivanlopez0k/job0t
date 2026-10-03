# Plan de Tareas: 001-mvp-pipeline

## Lote 1: Cimientos, Modelos y Configuración
- [x] **Tarea 1.1**: Crear estructura de carpetas, `.gitignore`, `requirements.txt` y `pyproject.toml`.
- [x] **Tarea 1.2**: Crear archivos de configuración en `config/`: `config.yaml`, `categories.yaml` y `flags.yaml`.
- [x] **Tarea 1.3**: Implementar modelos de datos en `src/job0t/models.py` (`RawJob`, `Job`, `FilterOptions`, `RunStats`).
- [x] **Tarea 1.4**: Implementar cargador y validador de configuración en `src/job0t/config.py` con Pydantic.
- [x] **Tarea 1.5**: Tests unitarios de modelos y configuración en `tests/test_models.py` y `tests/test_config.py`.

## Lote 2: Pipeline de Negocio & Reglas Puras (TDD)
- [x] **Tarea 2.1**: Implementar `src/job0t/pipeline/normalizer.py` (sanitización de HTML, normalización de espacios, hash SHA256 para `id`).
- [x] **Tarea 2.2**: Implementar `src/job0t/pipeline/classifier.py` (clasificación multietiqueta ponderada con título x2 y exclusiones).
- [x] **Tarea 2.3**: Implementar `src/job0t/pipeline/flag_detector.py` (detección de `AI FRIENDLY`, `FREELANCE` y `REMOTO`, reglas negativas y recolección de evidencia).
- [x] **Tarea 2.4**: Implementar `src/job0t/pipeline/filter.py` (filtrado según flags y categorías seleccionadas en CLI).
- [x] **Tarea 2.5**: Implementar `src/job0t/pipeline/deduplicator.py` (deduplicación estricta por `id` y fuzzy por título/empresa).
- [x] **Tarea 2.6**: Tests unitarios exhaustivos del pipeline en `tests/test_pipeline.py`.

## Lote 3: Adaptadores de Scrapers & Fixtures
- [x] **Tarea 3.1**: Implementar interfaz `BaseScraper` en `src/job0t/scrapers/base.py`.
- [x] **Tarea 3.2**: Crear fixtures de prueba en `tests/fixtures/computrabajo_snippet.html` y `tests/fixtures/getonboard_snippet.json`.
- [x] **Tarea 3.3**: Implementar `src/job0t/scrapers/computrabajo.py` (scraping con `httpx`, parsing con BeautifulSoup, selectores robustos y manejo de errores).
- [x] **Tarea 3.4**: Implementar `src/job0t/scrapers/getonboard.py` (consumo de REST API JSON, mapeo de categorías y extracción limpia).
- [x] **Tarea 3.5**: Tests unitarios de scrapers con fixtures locales en `tests/test_scrapers.py`.

## Lote 4: Exportadores (CSV & Excel con openpyxl)
- [x] **Tarea 4.1**: Implementar interfaz `BaseExporter` en `src/job0t/exporters/base.py`.
- [x] **Tarea 4.2**: Implementar `src/job0t/exporters/csv_exporter.py` usando el módulo nativo `csv` con codificación UTF-8-sig.
- [x] **Tarea 4.3**: Implementar `src/job0t/exporters/excel_exporter.py` con `openpyxl`:
  - Hoja "Ofertas": cabecera corporativa `#1F4E79`, freeze panes, autofiltro, fórmulas `=HYPERLINK()`, dropdown de validación de datos en `Estado` y formato condicional verde en "SI".
  - Hoja "Resumen": métricas y desglose estadístico.
- [x] **Tarea 4.4**: Tests unitarios de exportadores en `tests/test_exporters.py` (verificación de integridad de workbook y celdas).

## Lote 5: Orquestador, CLI & Verificación Final
- [x] **Tarea 5.1**: Implementar orquestador `PipelineRunner` en `src/job0t/pipeline/runner.py`.
- [x] **Tarea 5.2**: Implementar interfaz CLI en `src/job0t/cli.py` con `typer` (flags directos) y selector interactivo con `questionary`.
- [x] **Tarea 5.3**: Crear `src/job0t/__main__.py` para soportar `python -m job0t run`.
- [x] **Tarea 5.4**: Ejecución de suite de tests completa (`pytest`) y prueba de humo end-to-end con salida real en `output/`.

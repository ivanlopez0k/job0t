# Progreso de Implementación: 001-mvp-pipeline

## Estado Actual
- **Fase:** `sdd-apply`
- **Lote completado:** Lote 5 (Orquestador, CLI & Verificación Final)
- **Tests ejecutados:** 26 pasados de 26 (100%)

## Bitácora de Cambios

### Lote 1: Cimientos, Modelos y Configuración
- ✅ Creados `.gitignore`, `requirements.txt` y `pyproject.toml`.
- ✅ Entorno virtual `.venv` aprovisionado con dependencias (`httpx`, `beautifulsoup4`, `pydantic`, `pyyaml`, `typer`, `questionary`, `openpyxl`, `pytest`).
- ✅ Paquete `job0t` instalado en modo editable (`pip install -e .`).
- ✅ Creados los 3 archivos de configuración YAML en `config/`: `config.yaml`, `categories.yaml`, `flags.yaml`.
- ✅ Implementados modelos `RawJob`, `Job`, `FilterOptions`, `RunStats` en `src/job0t/models.py` con generación determinística de IDs SHA-256 mediante `model_validator`.
- ✅ Implementado cargador y validador con Pydantic en `src/job0t/config.py`.
- ✅ Creado [README.md](file:///C:/Programación/job0t/README.md) con documentación de uso, CLI, configuración y arquitectura.
- ✅ Tests unitarios en `tests/test_models.py` y `tests/test_config.py` ejecutados con éxito.

### Lote 2: Pipeline de Negocio & Reglas Puras (TDD)
- ✅ Implementado `normalizer.py`: sanitización de HTML, normalización de espacios y modalidades (Remoto / Híbrido / Presencial).
- ✅ Implementado `classifier.py`: clasificación multietiqueta con ponderación doble para títulos (x2) frente a descripción (x1) y descalificación inmediata por `exclude_keywords`.
- ✅ Implementado `flag_detector.py`: detección de `AI FRIENDLY`, `FREELANCE` y `REMOTO` con reglas negativas (descalificadores inmediatos) y recolección de evidencia auditable.
- ✅ Implementado `filter.py`: filtrado según banderas booleanas y categorías seleccionadas por CLI.
- ✅ Implementado `deduplicator.py`: deduplicación en dos fases (hash determinístico estricto de URL + fingerprint fuzzy cruzado por título y empresa).
- ✅ Suite de tests en `tests/test_pipeline.py` con 11 tests adicionales cubriendo cada regla al 100%.

### Lote 3: Adaptadores de Scrapers & Fixtures
- ✅ Implementada interfaz abstracta `BaseScraper` en `src/job0t/scrapers/base.py`.
- ✅ Creadas fixtures locales `tests/fixtures/computrabajo_snippet.html` y `tests/fixtures/getonboard_snippet.json`.
- ✅ Implementado `ComputrabajoScraper` con parsing tolerante a fallos, selectores CSS robustos, jitter y soporte de paginación.
- ✅ Implementado `GetOnBoardScraper` con consumo de REST API JSON, mapeo de categorías de job0t a la taxonomía de Get on Board y límites de páginas.
- ✅ Suite de tests en `tests/test_scrapers.py` con 4 tests unitarios offline verificando extracción y clientes mockeados.

### Lote 4: Exportadores (CSV & Excel con openpyxl)
- ✅ Implementada interfaz abstracta `BaseExporter` en `src/job0t/exporters/base.py`.
- ✅ Implementado `CsvExporter` con codificación nativa UTF-8-sig (BOM para Windows).
- ✅ Implementado `ExcelExporter` con `openpyxl`:
  - Hoja "Ofertas": formato `#1F4E79`, freeze panes, autofiltro activo, enlaces nativos `=HYPERLINK()`, menú desplegable en columna `Estado` (DataValidation) y formato condicional verde (`#E2EFDA`) en las banderas "SI".
  - Hoja "Resumen": tabla de métricas y desglose estadístico por portal y categoría.
- ✅ Tests unitarios en `tests/test_exporters.py` verificando estructura de archivos, fórmulas y celdas.

### Lote 5: Orquestador, CLI & Verificación Final
- ✅ Implementado `PipelineRunner` en `src/job0t/pipeline/runner.py` coordinando la ejecución de punta a punta.
- ✅ Implementado CLI en `src/job0t/cli.py` con `typer` y selector de categorías interactivo con `questionary`.
- ✅ Configurado soporte para terminales Windows forzando UTF-8 en stdout/stderr y utilizando etiquetas de texto limpias.
- ✅ Creado entrypoint `src/job0t/__main__.py` para soportar `python -m job0t run`.
- ✅ Tests unitarios para el ciclo completo de orquestación en `tests/test_runner.py`.
- ✅ Verificación end-to-end real contra Computrabajo y Get on Board extrayendo 106 ofertas y generando reportes válidos en `output/`.

## Estado del MVP
- **Completado:** 100% de las tareas de los 5 lotes implementadas y testeadas.

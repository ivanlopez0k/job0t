# Diseño de Arquitectura: 001-mvp-pipeline

## 1. Estructura de Módulos y Paquetes

```
job0t/
├── config/
│   ├── config.yaml
│   ├── categories.yaml
│   └── flags.yaml
├── src/
│   └── job0t/
│       ├── __init__.py
│       ├── __main__.py          # Entrypoint para python -m job0t
│       ├── cli.py               # Typer app + questionary UI
│       ├── config.py            # Carga y validación con Pydantic de YAMLs
│       ├── models.py            # RawJob, Job, FilterOptions, RunSummary
│       ├── scrapers/
│       │   ├── __init__.py
│       │   ├── base.py          # Clase abstracta BaseScraper
│       │   ├── computrabajo.py  # Scraper HTML (httpx + BeautifulSoup)
│       │   └── getonboard.py    # Scraper REST API
│       ├── pipeline/
│       │   ├── __init__.py
│       │   ├── runner.py        # Orquestador del pipeline completo
│       │   ├── normalizer.py    # RawJob -> Job (limpieza de HTML y tipos)
│       │   ├── classifier.py    # Asignación de categorías por reglas ponderadas
│       │   ├── flag_detector.py # Reglas de AI Friendly, Freelance y Remoto
│       │   ├── filter.py        # Filtrado booleano por flags y categorías
│       │   └── deduplicator.py  # Deduplicación por hash y título/empresa
│       └── exporters/
│           ├── __init__.py
│           ├── base.py          # BaseExporter
│           ├── csv_exporter.py  # Exportación con módulo estándar csv (UTF-8 con BOM)
│           └── excel_exporter.py# Exportación con openpyxl (estilos, dropdowns, fórmulas)
├── tests/
│   ├── conftest.py
│   ├── fixtures/
│   │   ├── computrabajo_snippet.html
│   │   └── getonboard_snippet.json
│   ├── test_models.py
│   ├── test_normalizer.py
│   ├── test_classifier.py
│   ├── test_flag_detector.py
│   ├── test_deduplicator.py
│   ├── test_exporters.py
│   └── test_scrapers.py
├── output/                      # Ignorado en git
├── requirements.txt
├── pyproject.toml
└── .gitignore
```

---

## 2. Estrategia de Scrapers y Adaptadores

### 2.1 Computrabajo Scraper (`src/job0t/scrapers/computrabajo.py`)
- **Protocolo:** HTTP GET respetuoso con `httpx.Client(follow_redirects=True, headers=headers)`.
- **Estrategia de Búsqueda:**
  - URL Base: `https://ar.computrabajo.com/trabajo-de-{query}-en-{location}`.
  - Para cada término de búsqueda de las categorías seleccionadas, consulta hasta `max_pages_per_source` usando el parámetro `?p={page}`.
  - Jitter: `time.sleep(random.uniform(delay_min, delay_max))` entre peticiones.
- **Selectores CSS Robustos:**
  - Contenedor de oferta: `article.box_offer`
  - Título y URL: `h2.title a` o `a.js-o-link`
  - Empresa: `p.fs16 span` o `a.fc_base` (si no existe, "Confidencial")
  - Ubicación: `p.fs16 span.item_location` o segundo `span` en metadata
  - Salario: `span.tag.base` o `span.dFlex` que contenga `$`
  - Fecha cruda: `p.fc_aux.fs13` o `span.fc_aux`
  - Descripción: texto de resumen del artículo `p.bRS` (suficiente para clasificación inicial y flags en listado).
- **Tolerancia a Fallos:** Si una página responde 403/429 o error de red, se registra warning, se rescatan las ofertas recolectadas hasta ese momento y continúa con el siguiente scraper.

### 2.2 Get on Board Scraper (`src/job0t/scrapers/getonboard.py`)
- **Protocolo:** REST API JSON GET (`https://www.getonbrd.com/api/v0/categories/{category_id}/jobs`).
- **Mapeo de Categorías de job0t a Get on Board:**
  - `desarrollo` ➔ `programming`, `mobile-developer`
  - `diseno` ➔ `design-ux`
  - `data` ➔ `data-science-analytics`
  - `qa` / `devops` ➔ `sysadmin-devops-qa`
  - `soporte` ➔ `technical-support`
  - `producto` ➔ `operations-management`, `innovation-agile`
  - `marketing` ➔ `digital-marketing`
- **Extracción de Payload:**
  - Título: `attributes.title`
  - Empresa: `attributes.company.data.attributes.name` (si no, "GetOnBrd Company")
  - Ubicación: `attributes.countries` concatenado o `"Remoto"` si `attributes.remote == True`
  - Modalidad: `"Remoto"` si `attributes.remote == True`, de lo contrario `"Presencial/Híbrido"`
  - Salario: `$min_salary - $max_salary USD` (si están presentes)
  - Descripción: `attributes.description` + `attributes.functions` (limpiando HTML en normalización)
  - URL: `links.public_url`
  - Fecha: `attributes.published_at` (timestamp UNIX convertible directamente a datetime)

---

## 3. Pipeline de Procesamiento y Reglas de Negocio

El componente `PipelineRunner` (`src/job0t/pipeline/runner.py`) coordina la ejecución en memoria con una tubería funcional pura:

```
List[RawJob]
     │
     ▼
[normalizer.normalize_job] ──► List[Job]
     │
     ▼
[classifier.classify_job] ──► Asignación de categorías (pesos: Título x2, Descripción x1)
     │
     ▼
[flag_detector.detect_flags] ──► Evaluación de reglas booleanas y evidencia
     │
     ▼
[filter.filter_jobs] ──► Filtro de flags seleccionados por CLI
     │
     ▼
[deduplicator.deduplicate_jobs] ──► Filtro de unicidad
     │
     ▼
[exporters] ──► Generación de .xlsx y .csv
```

### 3.1 Ponderación en `Classifier`
- Para cada categoría candidata:
  - Se cuentan coincidencias de `match_keywords` en el título (peso 2) y en la descripción (peso 1).
  - Si aparece algún término de `exclude_keywords`, el score de esa categoría se anula (score = 0).
  - Si `score >= 1`, la categoría es agregada a `job.categories`.
  - Si ninguna categoría supera el umbral, se le asigna `["General"]`.

### 3.2 Lógica de Banderas y Evidencia en `FlagDetector`
- **`AI FRIENDLY`**:
  - Busca `yes_keywords` (ej. "copilot", "chatgpt", "llm", "ai-native").
  - Si encuentra al menos una, activa `ai_friendly = True` y agrega la palabra exacta encontrada a `ai_evidence`.
  - **Override Negativo:** Si encuentra `no_keywords` (ej. "prohibido el uso de ia"), fuerza `ai_friendly = False` y registra `"[Descalificado por regla negativa]"`.
- **`FREELANCE`**:
  - Si el source es portal freelance (ej. Workana) o matchea keywords ("contractor", "monotributista", "por proyecto"), activa `freelance = True` y guarda la evidencia.
  - Override negativo ante "relación de dependencia".
- **`REMOTO`**:
  - Si `job.modality == "Remoto"` o matchea keywords ("home office", "teletrabajo", "100% remoto"), activa `remoto = True`.
  - Override negativo ante "exclusivamente presencial".

### 3.3 Deduplicación en Dos Fases (`Deduplicator`)
1. **Fase 1 (Hash estricto):** Si el `job.id` (SHA256 de portal + URL) ya fue visto, se descarta.
2. **Fase 2 (Fuzzy normalizado entre portales):** Si dos portales publican la misma oferta con distinta URL, se genera una clave compuesta `slug(job.title)[:30] + "@" + slug(job.company)[:20]`. Si coinciden, se preserva la primera y se descarta el duplicado.

---

## 4. Diseño del Exportador Excel (`openpyxl`)

El módulo `ExcelExporter` implementa las siguientes especificaciones visuales:

1. **Paleta y Tipografía:**
   - Fuente uniforme: `Calibri` o `Segoe UI`.
   - Encabezado: Fill sólido `#1F4E79` (Azul corporativo), texto blanco en negrita, centrado vertical y horizontalmente.
   - Filas de datos: Alineación a la izquierda con padding, texto ajustado si excede longitud.
2. **Hipervínculos:**
   - La columna `Link` contendrá la fórmula `=HYPERLINK("{job.url}", "Ver oferta")`.
   - Estilo: Texto azul `#0563C1`, subrayado.
3. **Formato Condicional:**
   - Regla de celda: Si el texto es igual a `"SI"` en las columnas de `AI Friendly`, `Freelance` o `Remoto`:
     - Fill: Verde claro `#E2EFDA`.
     - Font: Verde oscuro `#375623`, negrita.
4. **Validación de Datos (Dropdown):**
   - Regla `DataValidation(type="list", formula1='"Nueva,Interesa,Postulado,Descartado"', allow_blank=True)` aplicada a todas las filas de la columna `Estado`.
5. **Autofiltro y Freeze:**
   - Congelamiento de panel en la fila 1 (`ws.freeze_panes = "A2"`).
   - Activación de autofiltro en todo el rango de datos (`ws.auto_filter.ref = ws.dimensions`).
6. **Hoja Resumen:**
   - Métricas clave en tarjetas tabulares: Total extraídas, deduplicadas, distribución por portal, por categoría y por bandera.

---

## 5. Diseño de Testing y TDD

- **Sin llamadas a red:** Todos los tests de scrapers y normalización se alimentarán de `tests/fixtures/` (`computrabajo_snippet.html` y `getonboard_snippet.json`).
- **Tests Unitarios de Reglas Puras:**
  - `test_normalizer`: Verificación de limpieza de strings, hashing y campos por defecto.
  - `test_classifier`: Verificación de pesos, asignación multietiqueta y exclusiones.
  - `test_flag_detector`: Casos positivos, negativos, override con descalificadores y recolección de evidencia.
  - `test_deduplicator`: Deduplicación por hash id y por título+empresa normalizados.
  - `test_exporters`: Creación de archivos, verificación de que el workbook se abre sin errores, presencia de fórmulas de hipervínculo y hojas requeridas.

# 🤖 job0t

> Herramienta CLI local en Python para buscar ofertas laborales en múltiples portales (Computrabajo, Get on Board, etc.), normalizarlas, clasificarlas con banderas inteligentes (`AI FRIENDLY`, `FREELANCE`, `REMOTO`) y generar un reporte en **Excel (.xlsx)** y **CSV** con enlaces clickeables, dropdown de seguimiento y formato condicional.

---

## 🚀 Características Principales

- **Multi-fuente desacoplada**: Soporte para portales web (HTML scraping respetuoso con `httpx` + `BeautifulSoup`) y APIs REST públicas (Get on Board).
- **Clasificación Automática por Reglas**: Asignación multietiqueta según categorías configurables en `categories.yaml` (Desarrollo, Diseño, Data, QA, DevOps, etc.) con ponderación en títulos y reglas de exclusión.
- **Detección Jerárquica de Seniority (`config/seniority.yaml`)**:
  - Niveles detectados: **Trainee / Entry**, **Junior**, **Semi Senior (SSR)**, **Senior (SR)** o **N/D**.
  - **Prioridad 1 (Título)**: Si el título dice *Senior Lead*, no se clasifica erróneamente como Junior aunque la descripción mencione *"supervisarás juniors"*.
  - **Prioridad 2 (Metadatos API)**: Detección nativa por ID de portal (Get on Board).
  - **Prioridad 3 (Primeras líneas)**: Fallback al encabezado de la descripción.
- **Banderas de Valor con Evidencia**:
  - `AI FRIENDLY`: Detecta si la empresa fomenta el uso de herramientas IA (ChatGPT, Copilot, Cursor, LLMs) con overrides negativos ante prohibiciones expresas.
  - `FREELANCE`: Detecta contratos por proyecto, monotributo o plataformas freelance.
  - `REMOTO`: Identifica ofertas 100% remotas o con modalidad home office.
  - **Auditoría transparente**: Cada bandera incluye una columna con los términos exactos detectados.
- **Excel Profesional (`openpyxl`)**:
  - Enlaces de postulación directos con fórmula clickeable (`=HYPERLINK()`).
  - Panel superior congelado y autofiltros activos en todas las columnas.
  - Formato condicional verde suave en banderas activas (`SI`).
  - Menú desplegable interactivo en la columna `Estado` (**Nueva**, **Interesa**, **Postulado**, **Descartado**) para seguimiento personal.
  - Hoja "Resumen" con desglose de métricas por portal, categoría y **seniority**.
- **Cero Bloat**: Sin dependencias pesadas de Data Science (sin Pandas ni NumPy); arranque instantáneo y memoria mínima.

---

## 📂 Arquitectura del Proyecto

```
job0t/
├── config/
│   ├── config.yaml          # Parámetros generales, delays, endpoints y límites
│   ├── categories.yaml      # Categorías, términos de búsqueda y keywords
│   ├── flags.yaml           # Reglas de banderas (AI Friendly, Freelance, Remoto)
│   └── seniority.yaml       # Niveles y keywords de Seniority (Trainee, Jr, SSR, Sr)
├── src/
│   └── job0t/
│       ├── cli.py           # Interfaz de línea de comandos (Typer + Questionary)
│       ├── config.py        # Carga y validación tipada con Pydantic
│       ├── models.py        # DTO RawJob y Entidad de Dominio Job
│       ├── scrapers/        # Adaptadores de portales (Computrabajo, Get on Board)
│       ├── pipeline/        # Normalización, Clasificación, Seniority, Banderas y Deduplicación
│       │   ├── normalizer.py
│       │   ├── classifier.py
│       │   ├── seniority_detector.py
│       │   ├── flag_detector.py
│       │   ├── filter.py
│       │   ├── deduplicator.py
│       │   └── runner.py
│       └── exporters/       # Generadores de Excel y CSV
├── output/                  # Archivos generados (ignorado en Git)
├── tests/                   # Suite de tests unitarios e integración offline
├── requirements.txt
└── pyproject.toml
```

---

## 🛠️ Instalación y Requisitos

Requiere **Python 3.11+**.

1. **Clonar el repositorio:**
   ```bash
   git clone <URL_DEL_REPO>
   cd job0t
   ```

2. **Crear y activar el entorno virtual:**
   ```bash
   # En Windows PowerShell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # En Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   # O instalar en modo editable:
   pip install -e .
   ```

---

## 💻 Modo de Uso

### 1. Menú Interactivo (Recomendado)
Ejecutá el comando sin parámetros para abrir el selector interactivo de categorías (con casillas de verificación) y luego el selector de seniority (`(Recomendado) Todos / No filtrar` seleccionado por defecto):

```bash
python -m job0t run
# O si instalaste el paquete:
job0t run
```

### 2. Ejecución Directa por Flags
Podés especificar las categorías, seniority y filtros directamente para automatizar ejecuciones:

```bash
# Buscar ofertas de Desarrollo Senior que sean Remotas
python -m job0t run --categories desarrollo --seniority sr --remoto

# Buscar ofertas Junior AI Friendly
python -m job0t run --categories desarrollo --seniority junior --ai-friendly

# Buscar ofertas de Diseño Freelance sin filtrar seniority
python -m job0t run --categories diseno --freelance --seniority todos

# Limitar a 1 página por portal y guardar en otra carpeta
python -m job0t run --categories desarrollo --max-pages 1 --output-dir mis_ofertas
```

---

## ⚙️ Personalización de Reglas

Todos los criterios son configurables sin tocar una sola línea de código:

- **`config/categories.yaml`**: Agregá o modificá categorías, los términos que se buscan en cada portal (`search_terms`), las palabras que definen la categoría (`match_keywords`) y palabras que la anulan (`exclude_keywords`).
- **`config/seniority.yaml`**: Modificá o sumá keywords para clasificar `trainee`, `junior`, `semi_senior` y `senior`.
- **`config/flags.yaml`**: Modificá o sumá keywords positivas (`yes_keywords`) o descalificadoras (`no_keywords`) para `ai_friendly`, `freelance` y `remoto`.
- **`config/config.yaml`**: Configurá User-Agent, timeouts, rangos de delay aleatorio y qué portales están activos.

---

## 🧪 Ejecutar Tests

La suite de pruebas corre de forma 100% offline utilizando fixtures HTML y JSON locales:

```bash
pytest -v
```

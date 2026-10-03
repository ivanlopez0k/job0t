# Especificación Técnica: 001-mvp-pipeline

## 1. Modelos de Datos (`src/job0t/models.py`)

### 1.1 `RawJob` (DTO de Transporte)
Objeto permisivo emitido por cada implementación de `BaseScraper`. No realiza transformaciones profundas ni conversiones de tipo para evitar fallos tempranos ante HTML heterogéneo.

```python
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class RawJob(BaseModel):
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    modality: Optional[str] = None        # "Remoto", "Híbrido", "Presencial", o None
    salary: Optional[str] = None
    description: str
    url: str
    source: str                          # "computrabajo" | "getonboard"
    published_at_raw: Optional[str] = None
    raw_payload: Dict[str, Any] = Field(default_factory=dict)
```

### 1.2 `Job` (Entidad de Dominio)
Representa la oferta de empleo saneada, validada, clasificada y enriquecida con banderas.

```python
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class Job(BaseModel):
    id: str                               # SHA256(source.lower() + ":" + url.strip().lower())[:16]
    title: str                            # Normalizado (espacios limpios, stripped)
    company: str = "Confidencial"         # Saneado o default si viene vacío
    location: str = "N/D"                 # Ciudad / Provincia / País saneado
    modality: str = "N/D"                 # "Remoto" | "Híbrido" | "Presencial" | "N/D"
    salary: Optional[str] = None          # Texto saneado si está publicado
    description: str                      # Texto limpio (sin tags HTML, espacios colapsados)
    url: str                              # URL canónica y válida
    source: str                           # Portal de origen
    published_at: Optional[datetime] = None
    scraped_at: datetime = Field(default_factory=datetime.now)
    categories: List[str] = Field(default_factory=list) # Labels de categorías asignadas
    ai_friendly: bool = False
    ai_evidence: str = ""                 # Keywords encontradas unidas por coma
    freelance: bool = False
    freelance_evidence: str = ""          # Keywords encontradas
    remoto: bool = False
    remoto_evidence: str = ""             # Keywords encontradas
    status: str = "Nueva"                 # "Nueva" | "Interesa" | "Postulado" | "Descartado"
```

---

## 2. Esquemas de Configuración (`config/`)

### 2.1 `config/config.yaml`
```yaml
search:
  locations:
    - "Córdoba"
    - "Argentina"
    - "Remoto"
  max_pages_per_source: 3
  delay_range_seconds: [1.5, 3.5]
  timeout_seconds: 15
  user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 job0t/0.1.0"

sources:
  computrabajo:
    enabled: true
    base_url: "https://ar.computrabajo.com"
  getonboard:
    enabled: true
    base_url: "https://www.getonbrd.com/api/v0"

output:
  directory: "output"
  formats:
    - "xlsx"
    - "csv"
```

### 2.2 `config/categories.yaml`
Diccionario de categorías disponibles para selección y clasificación:
```yaml
desarrollo:
  label: "Desarrollo de software"
  search_terms:
    - "desarrollador"
    - "developer"
    - "programador"
  match_keywords:
    - "backend"
    - "frontend"
    - "fullstack"
    - ".net"
    - "python"
    - "software engineer"
    - "react"
    - "node"
    - "java"
    - "golang"
    - "c#"
  exclude_keywords:
    - "vendedor"
    - "comercial"
    - "inmobiliario"

diseno:
  label: "Diseño"
  search_terms:
    - "diseñador"
    - "ux"
    - "ui"
  match_keywords:
    - "figma"
    - "diseño gráfico"
    - "product designer"
    - "ui designer"
    - "ux designer"
  exclude_keywords:
    - "diseño de interiores"
    - "arquitectura de interiores"

data:
  label: "Data / Análisis"
  search_terms:
    - "data analyst"
    - "analista de datos"
  match_keywords:
    - "sql"
    - "power bi"
    - "bi"
    - "data engineer"
    - "tableau"
    - "data science"
  exclude_keywords: []

qa:
  label: "QA / Testing"
  search_terms:
    - "qa"
    - "tester"
  match_keywords:
    - "automatización de pruebas"
    - "qa automation"
    - "qa manual"
    - "cypress"
    - "selenium"
  exclude_keywords: []

devops:
  label: "DevOps / Cloud"
  search_terms:
    - "devops"
    - "cloud"
    - "sre"
  match_keywords:
    - "aws"
    - "azure"
    - "docker"
    - "kubernetes"
    - "terraform"
    - "ci/cd"
  exclude_keywords: []

soporte:
  label: "Soporte IT"
  search_terms:
    - "soporte técnico"
    - "help desk"
  match_keywords:
    - "sysadmin"
    - "soporte nivel 1"
    - "soporte nivel 2"
    - "mesas de ayuda"
  exclude_keywords: []

producto:
  label: "Producto / Gestión"
  search_terms:
    - "product manager"
    - "project manager"
  match_keywords:
    - "scrum master"
    - "product owner"
    - "analista funcional"
    - "agile coach"
  exclude_keywords: []

marketing:
  label: "Marketing digital"
  search_terms:
    - "marketing digital"
    - "community manager"
  match_keywords:
    - "seo"
    - "sem"
    - "growth"
    - "copywriter"
    - "google ads"
  exclude_keywords: []
```

### 2.3 `config/flags.yaml`
```yaml
ai_friendly:
  yes_keywords:
    - "copilot"
    - "chatgpt"
    - "claude"
    - "cursor"
    - "llm"
    - "openai"
    - "prompt engineering"
    - "ai-first"
    - "ai-powered"
    - "ia generativa"
    - "generative ai"
    - "uso de ia"
    - "herramientas de ia"
    - "ai friendly"
    - "ai-native"
  no_keywords:
    - "no se permite el uso de ia"
    - "prohibido el uso de ia"
    - "prohibido chatgpt"

freelance:
  yes_keywords:
    - "freelance"
    - "freelancer"
    - "por proyecto"
    - "contractor"
    - "independiente"
    - "monotributista"
    - "honorarios"
    - "locación de servicios"
    - "contrato por obra"
  no_keywords:
    - "relación de dependencia directa"
    - "efectivo permanente"
  yes_sources:
    - "workana"
    - "upwork"
    - "freelancer"

remoto:
  yes_keywords:
    - "remoto"
    - "100% remoto"
    - "home office"
    - "trabajo remoto"
    - "teletrabajo"
    - "remote"
    - "work from home"
    - "anywhere"
  no_keywords:
    - "100% presencial"
    - "exclusivamente presencial"
    - "no remoto"
```

---

## 3. Interfaces y Componentes de Código

### 3.1 Puerto Scraper (`src/job0t/scrapers/base.py`)
```python
from abc import ABC, abstractmethod
from typing import List
from job0t.models import RawJob
from job0t.config import AppConfig, CategoryDefinition

class BaseScraper(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre identificador del portal (e.g. 'computrabajo', 'getonboard')."""
        pass

    @abstractmethod
    def search(self, categories: List[CategoryDefinition], config: AppConfig) -> List[RawJob]:
        """Ejecuta la búsqueda para las categorías solicitadas y devuelve DTOs crudos."""
        pass
```

### 3.2 Componentes del Pipeline (`src/job0t/pipeline/`)
1. **`normalizer.py`**:
   - `normalize_job(raw: RawJob) -> Job`: Extrae texto limpio con `BeautifulSoup` para eliminar tags HTML de descriptions, normaliza espacios en blanco, calcula hash sha256 para `id`, estandariza `company` y `location`.
2. **`classifier.py`**:
   - `classify_job(job: Job, categories: Dict[str, CategoryDefinition]) -> Job`: Analiza título (peso 2x) y descripción. Evalúa `match_keywords` y `exclude_keywords`. Asigna lista de labels a `job.categories`. Si no matchea ninguna, asigna `["General"]`.
3. **`flag_detector.py`**:
   - `detect_flags(job: Job, flags_config: FlagsConfig) -> Job`: Realiza búsqueda de subcadenas case-insensitive con word boundaries o matching normalizado. Si encuentra `no_keywords`, desactiva la bandera. Llena campos booleanos y los strings de evidencia (`ai_evidence`, `freelance_evidence`, `remoto_evidence`).
4. **`filter.py`**:
   - `filter_jobs(jobs: List[Job], selected_categories: List[str], only_ai: bool, only_freelance: bool, only_remoto: bool) -> List[Job]`: Aplica los filtros booleanos configurados por el usuario.
5. **`deduplicator.py`**:
   - `deduplicate_jobs(jobs: List[Job]) -> List[Job]`: Deduplica en memoria preservando el primer registro por `job.id` o por clave normalizada `(slug(job.title), slug(job.company))`.

### 3.3 Exportadores (`src/job0t/exporters/`)
- `CsvExporter`: Genera archivo `.csv` UTF-8 con BOM (para compatibilidad directa con Excel en Windows).
- `ExcelExporter` (`openpyxl`):
  - **Hoja 1: `Ofertas`**:
    - Encabezado estilizado con fondo azul oscuro `#1F4E79` y texto blanco en negrita.
    - Freeze pane en la fila 1.
    - Filtro automático en todas las columnas (`ws.auto_filter.ref`).
    - Enlace clickeable en columna `Link`: `=HYPERLINK("https://...", "Ver oferta")`.
    - Formato condicional: Regla sobre columnas `AI Friendly`, `Freelance`, `Remoto` -> si el valor es `"SI"`, fondo verde suave `#E2EFDA` y texto verde oscuro `#375623`.
    - Validación de datos: Dropdown en columna `Estado` con valores: `Nueva,Interesa,Postulado,Descartado`.
    - Ajuste dinámico de anchos de columna con padding y límites máximos para evitar celdas kilométricas.
  - **Hoja 2: `Resumen`**:
    - Tabla de métricas: Fecha de ejecución, total encontradas, total únicas, distribución por portal, distribución por categoría, cantidad de AI Friendly, Freelance y Remotas.

### 3.4 CLI (`src/job0t/cli.py`)
- Comando principal: `job0t run`
  - Argumentos opcionales:
    - `--categories` / `-c`: String separado por comas de slugs (e.g. `desarrollo,data`). Si no se provee, invoca `questionary.checkbox` con la lista de categorías disponibles en `categories.yaml`.
    - `--ai-friendly` / `-a`: Flag booleano para filtrar solo ofertas con bandera AI Friendly = SI.
    - `--freelance` / `-f`: Flag booleano para filtrar solo Freelance = SI.
    - `--remoto` / `-r`: Flag booleano para filtrar solo Remoto = SI.
    - `--max-pages` / `-p`: Entero para sobreescribir límite de páginas por portal.
    - `--output-dir` / `-o`: Directorio de salida (por defecto `output/`).

---

## 4. Estructura de Salida de Archivos
Cada ejecución generará dos archivos fechados en `output/`:
- `output/jobs_YYYY-MM-DD_HHMM.xlsx`
- `output/jobs_YYYY-MM-DD_HHMM.csv`

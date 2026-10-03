# job0t — PLANNING

> Herramienta local en **Python** que busca ofertas laborales en varios portales según las **categorías que elijas** (Desarrollo de software, Diseño, Data Analyst, etc.), las clasifica con banderas como **AI FRIENDLY** y **FREELANCE** (SI/NO) y genera un **Excel** con todas las propuestas y sus links en cada ejecución.

---

## 1. Objetivo

Que con un solo comando puedas:

1. **Elegir** una o varias categorías de trabajo.
2. (Opcional) **Filtrar** por banderas: solo AI FRIENDLY, solo FREELANCE, solo remoto, etc.
3. Buscar en los portales configurados.
4. Normalizar, **clasificar** y **deduplicar** las ofertas.
5. Obtener un **Excel (.xlsx)** y un **CSV** nuevos por ejecución, con links clickeables.

No hay interfaz gráfica: funciona por línea de comandos (con un selector interactivo de categorías). Lo único que importa es que encuentre y ordene las ofertas.

## 2. Alcance

### MVP (v0.1)
- CLI en Python, 100 % local.
- Selección de categorías (por flag o menú interactivo).
- 1–2 portales (sugerido: Computrabajo + una fuente con API/RSS).
- Clasificación por reglas: `categoria`, `ai_friendly`, `freelance`.
- Salida: `output/jobs_YYYY-MM-DD_HHMM.xlsx` y `.csv`.
- Deduplicación básica por URL.

### Más adelante
- Envío automático/asistido de CV (se analiza después, ver sección 12).
- Notificaciones, scoring con IA, dashboard, programación automática.

---

## 3. ⚠️ Consideraciones importantes

| Tema | Detalle | Recomendación |
|---|---|---|
| **LinkedIn** | Sus Términos prohíben el scraping y tiene detección anti-bot fuerte (riesgo de bloqueo de cuenta). | No scrapear con tu cuenta. Usar **alertas de empleo por email** y parsear los correos, o dejarlo para el final. |
| **Computrabajo** | HTML público, sin API oficial. | Scraping respetuoso: delays aleatorios, pocas páginas, revisar `robots.txt`. |
| **Portales cambiantes** | El HTML cambia seguido. | Un módulo por portal + tests con HTML guardado. |
| **Datos personales** | Credenciales/keys/CV. | `.env` y `.gitignore`; nunca commitear secretos. |

---

## 4. Fuentes de ofertas

**Con API o RSS (más estables):**
- Adzuna API (gratis con registro)
- Jooble API
- Get on Board (tech LatAm)
- RemoteOK API / We Work Remotely RSS (remoto)

**Scraping HTML:**
- Computrabajo
- Bumeran / ZonaJobs
- Indeed (anti-bot fuerte)
- LinkedIn (ver advertencia)

**Freelance (útil para la bandera FREELANCE):**
- Workana, Freelancer, Upwork (revisar ToS/API de cada uno)

Diseño clave: una interfaz común `Scraper` para que sumar un portal sea agregar un archivo.

---

## 5. Categorías (lo que elegís antes de buscar)

Cada categoría es un bloque en `categories.yaml` con **keywords de búsqueda** (qué se le pide al portal) y **keywords de clasificación** (cómo se reconoce una oferta de esa categoría). Son totalmente editables.

| Categoría | Ejemplos de keywords |
|---|---|
| Desarrollo de software | desarrollador, developer, programador, software engineer, backend, frontend, fullstack, .NET, Python |
| Diseño | diseñador, UX, UI, diseño gráfico, product designer, Figma |
| Data / Análisis | data analyst, analista de datos, BI, Power BI, SQL, data engineer |
| QA / Testing | QA, tester, automatización de pruebas |
| DevOps / Cloud | devops, cloud, AWS, Azure, SRE |
| Soporte IT | soporte técnico, help desk, sysadmin |
| Producto / Gestión | product manager, project manager, scrum master, analista funcional |
| Marketing digital | community manager, SEO, marketing digital, growth |

**Cómo se usa:**
```bash
# Menú interactivo (checklist con las categorías)
python -m job0t run

# Directo por flags
python -m job0t run --categories dev,data --freelance si --ai-friendly si
```

**Reglas de clasificación:**
- Una oferta puede caer en **más de una** categoría (se guarda como lista, ej. `Desarrollo; Data`).
- El título pesa más que la descripción.
- Cada categoría admite `exclude` (ej. en Diseño, excluir "diseño de interiores" si no interesa).
- Si no matchea ninguna categoría elegida, se descarta o va a "Sin categoría" (configurable).

---

## 6. Banderas (SI/NO) y cómo se detectan

Cada bandera es una **regla configurable** en `flags.yaml`. Además de SI/NO, el Excel guarda una columna de **evidencia** con las palabras que dispararon la regla, para que puedas auditar y ajustar.

### FREELANCE (SI/NO)
Se marca **SI** si el título o la descripción contienen señales como:
`freelance`, `freelancer`, `por proyecto`, `contractor`, `independiente`, `monotributista`, `honorarios`, `locación de servicios`, `contrato por obra`.
También **SI** automáticamente si la fuente es un portal freelance (Workana, Upwork…).

### AI FRIENDLY (SI/NO)
Es una bandera subjetiva, así que conviene definirla explícitamente. Propuesta: **SI** si la oferta muestra que la empresa **usa o valora la IA**:
- Menciona herramientas: `Copilot`, `ChatGPT`, `Claude`, `Cursor`, `LLM`, `OpenAI`, `prompt engineering`
- Frases tipo: `AI-first`, `AI-powered`, `IA generativa`, `uso de IA`, `herramientas de IA`, `AI friendly`
- Señales negativas explícitas (ej. `no se permite el uso de IA`) → **NO**

> ⚠️ **Limitación honesta:** la mayoría de las ofertas no dice nada sobre IA, así que un **NO** significa "*no se detectó señal*", no "*la empresa es anti-IA*". Por eso la columna de evidencia es importante. Si más adelante querés más precisión, se puede agregar un clasificador con un LLM (Fase 4).

### Otras banderas útiles (opcionales, muy baratas de detectar)
| Bandera | Valores | Para qué |
|---|---|---|
| REMOTO | SI / NO | Filtrar trabajo remoto |
| SALARIO PUBLICADO | SI / NO | Descartar ofertas sin rango |
| NIVEL | Trainee / Junior / Semi / Senior | Filtrar por experiencia |
| INGLÉS REQUERIDO | SI / NO | Ajustar a tu perfil |
| PASANTÍA | SI / NO | Ofertas para estudiantes |

---

## 7. Stack (Python)

- **Python 3.11+** con entorno virtual (`venv` o `uv`)
- `httpx` + `BeautifulSoup4` (+ `lxml`) → portales con HTML estático
- `Playwright` → portales con JavaScript dinámico (solo si hace falta)
- `pydantic` → modelo `Job` validado
- `PyYAML` → configuración
- `typer` → CLI
- `questionary` → menú interactivo para elegir categorías
- `pandas` + `openpyxl` (o `XlsxWriter`) → CSV/Excel con formato
- `sqlite3` (stdlib) → historial de ofertas vistas
- `pytest` → tests con HTML de ejemplo
- `python-dotenv` → keys en `.env`

---

## 8. Arquitectura

```
job0t/
├── config/
│   ├── config.example.yaml      # general (se versiona)
│   ├── categories.yaml          # categorías y keywords
│   └── flags.yaml               # reglas de AI FRIENDLY, FREELANCE, etc.
├── src/job0t/
│   ├── __main__.py              # entrada: python -m job0t
│   ├── cli.py                   # comandos (typer) + menú interactivo
│   ├── models.py                # Job
│   ├── config.py                # carga/valida YAMLs
│   ├── scrapers/
│   │   ├── base.py              # clase abstracta Scraper
│   │   ├── computrabajo.py
│   │   ├── adzuna.py
│   │   ├── getonboard.py
│   │   └── ...
│   ├── pipeline/
│   │   ├── normalize.py         # limpia y unifica campos
│   │   ├── classify.py          # asigna categoría(s)
│   │   ├── flags.py             # AI FRIENDLY, FREELANCE, REMOTO, NIVEL...
│   │   ├── filter.py            # aplica filtros elegidos por el usuario
│   │   └── dedupe.py
│   ├── exporters/
│   │   ├── csv_exporter.py
│   │   └── excel_exporter.py
│   └── storage/
│       └── history.py           # SQLite
├── output/                      # generados (en .gitignore)
├── data/                        # historial .db (en .gitignore)
├── tests/
│   └── fixtures/                # HTML guardado de cada portal
├── logs/
├── PLANNING.md
├── README.md
├── requirements.txt
└── .gitignore
```

### Flujo

```
Elegís categorías + filtros (CLI / menú)
        │
        ▼
[Scrapers] ─► ofertas crudas
        │
        ▼
[Normalize] ─► [Classify] ─► [Flags] ─► [Filter] ─► [Dedupe + historial]
        │
        ▼
[Exporters] ─► output/jobs_2026-10-03_1430.xlsx / .csv
```

---

## 9. Modelo de datos (`Job`)

| Campo | Notas |
|---|---|
| `id` | hash de (portal + url) |
| `title` | Puesto |
| `company` | Puede venir vacío |
| `location` | Ciudad / provincia / país |
| `modality` | Presencial / Híbrido / Remoto |
| `salary` | Texto crudo (a menudo no está) |
| `description` | Texto de la oferta |
| `url` | Link directo |
| `source` | Portal de origen |
| `published_at` | Fecha de publicación |
| `scraped_at` | Cuándo la encontró el bot |
| `categories` | Lista de categorías detectadas |
| `ai_friendly` | SI / NO |
| `ai_evidence` | Palabras que dispararon la regla |
| `freelance` | SI / NO |
| `freelance_evidence` | Palabras que dispararon la regla |
| `level` | Trainee / Junior / Semi / Senior / N/D |
| `is_new` | No estaba en el historial |
| `status` | Nueva / Interesa / Postulado / Descartado (se edita a mano en el Excel) |

---

## 10. Configuración

**`config/config.example.yaml`**
```yaml
search:
  locations: ["Córdoba", "Argentina", "Remoto"]
  max_age_days: 14

sources:
  computrabajo: { enabled: true, country: ar }
  adzuna:       { enabled: true, api_key_env: ADZUNA_KEY }
  getonboard:   { enabled: false }
  linkedin_email: { enabled: false }

scraping:
  delay_seconds: [2, 5]
  max_pages_per_source: 5
  user_agent: "job0t/0.1 (uso personal)"

output:
  folder: output
  formats: [xlsx, csv]
```

**`config/categories.yaml`**
```yaml
desarrollo:
  label: "Desarrollo de software"
  search: ["desarrollador", "developer", "programador"]
  match:  ["backend", "frontend", "fullstack", ".net", "python", "software engineer"]
  exclude: ["vendedor", "comercial"]
diseno:
  label: "Diseño"
  search: ["diseñador", "ux", "ui"]
  match:  ["figma", "diseño gráfico", "product designer"]
  exclude: ["interiores"]
data:
  label: "Data / Análisis"
  search: ["data analyst", "analista de datos"]
  match:  ["sql", "power bi", "bi", "data engineer"]
```

**`config/flags.yaml`**
```yaml
freelance:
  yes_keywords: ["freelance", "freelancer", "por proyecto", "contractor", "monotributista", "honorarios"]
  yes_sources: ["workana", "upwork"]
ai_friendly:
  yes_keywords: ["copilot", "chatgpt", "llm", "ai-first", "ia generativa", "prompt engineering", "herramientas de ia"]
  no_keywords:  ["no se permite el uso de ia"]
```

---

## 11. Salida: Excel

Un `.xlsx` por ejecución (más un CSV equivalente):

- **Hoja "Ofertas"**
  - Una fila por oferta, filtros automáticos y encabezado congelado.
  - `url` como **hipervínculo clickeable**.
  - Columnas `ai_friendly` y `freelance` con formato condicional (verde = SI).
  - Ofertas **nuevas** resaltadas.
  - `status` con **lista desplegable** para usarlo como tablero de seguimiento.
- **Hoja "Resumen"**
  - Cantidad por categoría y por portal, nuevas vs. repetidas, cuántas AI FRIENDLY y FREELANCE.
  - Parámetros de búsqueda usados en esa corrida.

---

## 12. Envío de CV (para analizar más adelante)

Queda fuera del MVP. Cuando se retome, la idea es avanzar por niveles:

1. Generar borrador de mail/carta por oferta (sin enviar).
2. Envío por **email** cuando la oferta publica un correo, con `--dry-run` por defecto y confirmación manual.
3. Postulación dentro del portal: **evitar** (riesgo de bloqueo y bajo rendimiento).

---

## 13. Roadmap

### Fase 0 — Setup
- [ ] Repo, estructura, `.gitignore`, venv, `requirements.txt`
- [ ] Modelo `Job` y clase base `Scraper`
- [ ] Carga de `config.yaml`, `categories.yaml`, `flags.yaml`
- [ ] Logging básico

### Fase 1 — MVP
- [ ] Scraper de Computrabajo (búsqueda + paginación + detalle)
- [ ] Segundo scraper vía API (Adzuna o Get on Board)
- [ ] Clasificador de categorías por reglas
- [ ] Banderas `freelance` y `ai_friendly` con evidencia
- [ ] CLI con menú interactivo y flags
- [ ] Exportador CSV + Excel con formato

### Fase 2 — Calidad
- [ ] Historial SQLite y marca de ofertas nuevas
- [ ] Dedupe entre portales (título + empresa normalizados)
- [ ] Banderas extra: remoto, nivel, salario, inglés
- [ ] Reintentos, timeouts y manejo de errores por portal
- [ ] Tests con fixtures HTML

### Fase 3 — Más fuentes
- [ ] Portales freelance (Workana, etc.)
- [ ] Alertas de LinkedIn por email (IMAP / Gmail API)
- [ ] Bumeran / ZonaJobs

### Fase 4 — Extras
- [ ] Clasificación de `ai_friendly` con un LLM para mayor precisión
- [ ] Scoring de relevancia
- [ ] Notificación por Telegram
- [ ] Ejecución programada (cron / Programador de tareas)
- [ ] Mini dashboard (Streamlit)

### Fase 5 — Postulación (a analizar)
- [ ] Ver sección 12

---

## 14. Riesgos

| Riesgo | Mitigación |
|---|---|
| Cambia el HTML de un portal | Un módulo por portal + fixtures + logs claros |
| Bloqueo por IP/captcha | Delays aleatorios, pocas páginas, caché en desarrollo |
| Violación de ToS (LinkedIn) | Alertas por email en lugar de scraping directo |
| Banderas con falsos positivos/negativos | Columna de evidencia + reglas editables en YAML |
| Categorías mal asignadas | `exclude` por categoría y título con más peso que descripción |
| Filtración de secretos | `.env` + `.gitignore` |

---

## 15. Decisiones pendientes

- [ ] ¿Qué portales entran primero? (sugerido: Computrabajo + Adzuna o Get on Board)
- [ ] ¿Qué categorías querés de entrada y con qué keywords?
- [ ] ¿AI FRIENDLY = "usa/valora IA" como está definido arriba, o querés otro criterio?
- [ ] ¿Qué países/ubicaciones cubrir?
- [ ] ¿Querés las banderas extra (remoto, nivel, salario, inglés) ya en el MVP?

---

## 16. Primeros pasos

1. Crear el repo y la estructura de la sección 8.
2. Definir `Job` y `Scraper` antes de escribir cualquier scraper.
3. Hacer **un portal de punta a punta**: scrape → clasificar → CSV.
4. Sumar banderas y el Excel con formato.
5. Recién después, historial, dedupe y más portales.

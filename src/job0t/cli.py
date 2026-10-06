import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import typer

from job0t.config import load_categories_config
from job0t.models import FilterOptions
from job0t.pipeline.runner import PipelineRunner
from job0t.ui.prompts import CATEGORY_HIERARCHY, hierarchical_checkbox

# Forzar UTF-8 en Windows para evitar UnicodeEncodeError con cp1252
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

app = typer.Typer(
    name="job0t",
    help="job0t — Herramienta local para buscar, clasificar y exportar ofertas laborales.",
    add_completion=False,
)
console = Console()


def _clear_terminal() -> None:
    """Limpia la terminal completamente (pantalla + historial de scrollback)."""
    if sys.platform == "win32":
        os.system("cls")
    else:
        os.system("clear")
    # Secuencia ANSI para limpiar scrollback buffer (\033[3J), mover a inicio (\033[H) y limpiar pantalla (\033[2J)
    sys.stdout.write("\033[3J\033[H\033[2J")
    sys.stdout.flush()


def _prompt_interactive_categories() -> List[str]:
    """Muestra un menú interactivo con casillas de verificación para elegir categorías organizadas en cajas."""
    choices = [
        questionary.Separator("┌────────────────────────────────────────────────────────┐"),
        questionary.Separator("│  DESARROLLO DE SOFTWARE                                │"),
        questionary.Separator("└────────────────────────────────────────────────────────┘"),
        questionary.Choice(title="Todo Desarrollo (Cualquier especialidad)", value="desarrollo"),
        questionary.Choice(title="Desarrollo Frontend", value="desarrollo_frontend"),
        questionary.Choice(title="Desarrollo Backend", value="desarrollo_backend"),
        questionary.Choice(title="Desarrollo Fullstack", value="desarrollo_fullstack"),
        questionary.Choice(title="Desarrollo Mobile (iOS / Android)", value="desarrollo_mobile"),
        questionary.Choice(title="Desarrollo de Videojuegos", value="desarrollo_gamedev"),
        questionary.Choice(title="Desarrollo Desktop", value="desarrollo_desktop"),
        questionary.Choice(title="Inteligencia Artificial & ML", value="desarrollo_ai"),
        questionary.Choice(title="Ciberseguridad & AppSec", value="desarrollo_ciberseguridad"),
        questionary.Choice(title="Web3 & Blockchain", value="desarrollo_web3"),

        questionary.Separator(" "),
        questionary.Separator("┌────────────────────────────────────────────────────────┐"),
        questionary.Separator("│  DISEÑO                                                │"),
        questionary.Separator("└────────────────────────────────────────────────────────┘"),
        questionary.Choice(title="Todo Diseño (Cualquier especialidad)", value="diseno"),
        questionary.Choice(title="Diseño UX / UI", value="diseno_ux_ui"),
        questionary.Choice(title="Diseño de Producto Digital", value="diseno_product"),
        questionary.Choice(title="Diseño UX Research & Content", value="diseno_ux_research"),
        questionary.Choice(title="Diseño Gráfico & Branding", value="diseno_grafico"),
        questionary.Choice(title="Diseño Web & No-Code", value="diseno_web_nocode"),
        questionary.Choice(title="Diseño Motion & Animación", value="diseno_motion"),
        questionary.Choice(title="Modelado 3D & Renders", value="diseno_3d"),

        questionary.Separator(" "),
        questionary.Separator("┌────────────────────────────────────────────────────────┐"),
        questionary.Separator("│  DATOS & ANALÍTICA                                     │"),
        questionary.Separator("└────────────────────────────────────────────────────────┘"),
        questionary.Choice(title="Todo Data (Cualquier especialidad)", value="data"),
        questionary.Choice(title="Data Analytics & BI", value="data_analytics"),
        questionary.Choice(title="Data Engineering", value="data_engineering"),
        questionary.Choice(title="Data Science & Modelos", value="data_science"),

        questionary.Separator(" "),
        questionary.Separator("┌────────────────────────────────────────────────────────┐"),
        questionary.Separator("│  QA & TESTING                                          │"),
        questionary.Separator("└────────────────────────────────────────────────────────┘"),
        questionary.Choice(title="Todo QA & Testing", value="qa"),
        questionary.Choice(title="QA Automation", value="qa_automation"),
        questionary.Choice(title="QA Manual", value="qa_manual"),

        questionary.Separator(" "),
        questionary.Separator("┌────────────────────────────────────────────────────────┐"),
        questionary.Separator("│  CLOUD, DEVOPS & INFRAESTRUCTURA                       │"),
        questionary.Separator("└────────────────────────────────────────────────────────┘"),
        questionary.Choice(title="Todo Cloud & DevOps", value="devops"),
        questionary.Choice(title="DevOps & SRE", value="devops_sre"),
        questionary.Choice(title="Cloud Engineering", value="cloud_engineering"),
        questionary.Choice(title="Administración de Sistemas", value="sysadmin"),

        questionary.Separator(" "),
        questionary.Separator("┌────────────────────────────────────────────────────────┐"),
        questionary.Separator("│  PRODUCTO, GESTIÓN & LIDERAZGO                         │"),
        questionary.Separator("└────────────────────────────────────────────────────────┘"),
        questionary.Choice(title="Todo Producto (Cualquier especialidad)", value="producto"),
        questionary.Choice(title="Product Management", value="producto_management"),
        questionary.Choice(title="Project Management & Agile", value="producto_agile"),
        questionary.Choice(title="Tech Lead & Liderazgo", value="tech_lead"),

        questionary.Separator(" "),
        questionary.Separator("┌────────────────────────────────────────────────────────┐"),
        questionary.Separator("│  SOPORTE & OPERACIONES IT                              │"),
        questionary.Separator("└────────────────────────────────────────────────────────┘"),
        questionary.Choice(title="Soporte IT & Mesa de Ayuda", value="soporte"),
    ]

    console.print("\n[bold cyan]Selector de Categorías & Especialidades[/bold cyan]")
    selected = hierarchical_checkbox(
        "Seleccioná las áreas de tu interés (Espacio para marcar, Enter para confirmar):",
        choices=choices,
        hierarchy=CATEGORY_HIERARCHY,
    ).ask()

    return selected or []


def _prompt_interactive_seniority() -> List[str]:
    """Muestra un menú interactivo con casillas de verificación para elegir uno o varios seniorities."""
    choices = [
        questionary.Choice(title="Trainee / Entry", value="trainee"),
        questionary.Choice(title="Junior", value="junior"),
        questionary.Choice(title="Semi Senior (SSR)", value="semi senior"),
        questionary.Choice(title="Senior (SR)", value="senior"),
    ]
    console.print("\n[bold cyan]Selector de Seniority[/bold cyan]")
    selected = questionary.checkbox(
        "Seleccioná los niveles deseados (Espacio para marcar, Enter para confirmar. Si no marcás ninguno, busca todos):",
        choices=choices,
    ).ask()

    return selected or []


def _prompt_interactive_modality() -> List[str]:
    """Muestra un menú interactivo con casillas de verificación para elegir modalidades de trabajo."""
    choices = [
        questionary.Choice(title="Remoto (Home office / 100% online)", value="remoto"),
        questionary.Choice(title="Híbrido (Días presenciales + home office)", value="hibrido"),
        questionary.Choice(title="Presencial (En oficina / sede)", value="presencial"),
    ]
    console.print("\n[bold cyan]Selector de Modalidad[/bold cyan]")
    selected = questionary.checkbox(
        "Seleccioná las modalidades de tu interés (Espacio para marcar, Enter para confirmar. Si no marcás ninguna, busca todas):",
        choices=choices,
    ).ask()

    return selected or []


def _prompt_interactive_location(selected_modalities: List[str]) -> Optional[str]:
    """Muestra un flujo inteligente para acotar la ubicación geográfica según la modalidad elegida."""
    has_presencial_or_hybrid = any(m in ("presencial", "hibrido") for m in selected_modalities)
    only_remoto = len(selected_modalities) == 1 and selected_modalities[0] == "remoto"

    # Caso 1: Se eligió presencial o híbrido (con o sin remoto)
    if has_presencial_or_hybrid:
        console.print("\n[bold cyan]Selector de Ubicación Geográfica (Presencial / Híbrido)[/bold cyan]")
        country_choices = [
            questionary.Choice(title="[1] (Recomendado) Argentina", value="argentina"),
            questionary.Choice(title="[2] Otro país", value="otro"),
            questionary.Choice(title="[3] Cualquier país / Sin filtro de ubicación", value="todos"),
        ]
        country_resp = questionary.select(
            "Seleccioná el país para las ofertas presenciales / híbridas:",
            choices=country_choices,
            default="argentina",
        ).ask()

        if country_resp == "argentina":
            prov = questionary.text(
                "Provincia o ciudad en Argentina (ej: Córdoba, Buenos Aires, Rosario. ENTER para todo el país):",
                default="",
            ).ask()
            if prov and prov.strip():
                return prov.strip()
            return "argentina"
        elif country_resp == "otro":
            other_country = questionary.text(
                "Ingresá el país deseado (ej: Chile, Uruguay, España, México):",
                default="",
            ).ask()
            return other_country.strip() if other_country and other_country.strip() else None
        else:
            return None

    # Caso 2: Se eligió exclusivamente Remoto
    if only_remoto:
        console.print("\n[bold cyan]Selector de Ubicación para Ofertas Remotas[/bold cyan]")
        remote_scope_choices = [
            questionary.Choice(
                title="[1] (Recomendado) Remoto Global / Cualquier lugar (incluye vacantes en USD y Worldwide)",
                value="global",
            ),
            questionary.Choice(
                title="[2] Acotar a país o región específica (ej: Argentina, LatAm, etc.)",
                value="custom",
            ),
        ]
        scope_resp = questionary.select(
            "¿Cómo querés filtrar la ubicación de las ofertas remotas?:",
            choices=remote_scope_choices,
            default="global",
        ).ask()

        if scope_resp == "custom":
            target = questionary.text(
                "Ingresá el país o región (ej: Argentina, LatAm, Chile):",
                default="Argentina",
            ).ask()
            return target.strip() if target and target.strip() else None
        return None

    # Caso 3: Sin filtro de modalidad (o las tres marcadas)
    console.print("\n[bold cyan]Selector de Ubicación Geográfica[/bold cyan]")
    general_choices = [
        questionary.Choice(
            title="[1] (Recomendado) Cualquier ubicación / Sin filtro",
            value="global",
        ),
        questionary.Choice(
            title="[2] Acotar por país o ciudad (ej: Argentina, Córdoba, Chile)",
            value="custom",
        ),
    ]
    gen_resp = questionary.select(
        "¿Deseás filtrar por alguna ubicación geográfica?:",
        choices=general_choices,
        default="global",
    ).ask()

    if gen_resp == "custom":
        target = questionary.text(
            "Ingresá la ubicación, país o ciudad (ej: Córdoba, Argentina, México):",
            default="Argentina",
        ).ask()
        return target.strip() if target and target.strip() else None
    return None


def _prompt_interactive_format() -> str:
    """Muestra un menú interactivo con casillas de verificación para elegir el formato de descarga."""
    choices = [
        questionary.Choice(title="Excel (.xlsx)", value="xlsx"),
        questionary.Choice(title="CSV (.csv)", value="csv"),
    ]
    console.print("\n[bold cyan]Formato de Descarga[/bold cyan]")
    selected = questionary.checkbox(
        "Seleccioná el/los formatos que querés descargar (Espacio para marcar, Enter para confirmar):",
        choices=choices,
    ).ask()

    if not selected:
        console.print("[dim]No marcaste ninguno: se exportarán ambos formatos (.xlsx y .csv)[/dim]")
        return "both"
    if "xlsx" in selected and "csv" in selected:
        return "both"
    if "xlsx" in selected:
        return "xlsx"
    if "csv" in selected:
        return "csv"
    return "both"


def _prompt_interactive_filename() -> str:
    """Solicita el nombre del archivo de reporte (con fecha YYYY-MM-DD por defecto)."""
    default_name = f"jobs_{datetime.now().strftime('%Y-%m-%d')}"
    console.print("\n[bold cyan]Nombre del Archivo[/bold cyan]")
    name = questionary.text(
        f"Ingresá el nombre base del archivo (sin extensión, ENTER para '{default_name}'):",
        default=default_name,
    ).ask()

    return name.strip() if name and name.strip() else default_name


JOB0T_LOGO = r"""
    o8o            .o8         .oooo.       .   
    `"'           "888        d8P'`Y8b    .o8   
   oooo  .ooooo.   888oooo.  888    888 .o888oo 
   `888 d88' `88b  d88' `88b 888    888   888   
    888 888   888  888   888 888    888   888   
    888 888   888  888   888 `88b  d88'   888 . 
    888 `Y8bod8P'  `Y8bod8P'  `Y8bd8P'    "888" 
    888                                         
.o. 88P                                         
`Y888P                                          
"""


@app.callback()
def main_callback():
    """job0t — Herramienta local para buscar, clasificar y exportar ofertas laborales."""
    pass


@app.command(name="run")
def run(
    categories: Optional[str] = typer.Option(
        None,
        "--categories",
        "-c",
        help="Categorías separadas por comas (ej: 'desarrollo,data'). Si se omite, abre el menú interactivo.",
    ),
    seniority: Optional[str] = typer.Option(
        None,
        "--seniority",
        "-s",
        help="Filtrar por seniority: trainee, junior, ssr, sr (o 'todos'). Si se omite en modo interactivo, se preguntará.",
    ),
    modality: Optional[str] = typer.Option(
        None,
        "--modality",
        "-m",
        help="Modalidades separadas por comas (remoto, hibrido, presencial). Si se omite en modo interactivo, se preguntará.",
    ),
    location: Optional[str] = typer.Option(
        None,
        "--location",
        "-l",
        help="Ubicación geográfica o país (ej: 'cordoba', 'argentina'). Si se omite en modo interactivo, se preguntará.",
    ),
    export_format: Optional[str] = typer.Option(
        None,
        "--format",
        "-F",
        help="Formato de exportación: 'xlsx', 'csv' o 'both'. Si se omite en modo interactivo, se preguntará.",
    ),
    filename: Optional[str] = typer.Option(
        None,
        "--filename",
        "-n",
        help="Nombre base del archivo de salida sin extensión (ej: 'jobs_2026-10-04'). Por defecto usa la fecha actual.",
    ),
    ai_friendly: bool = typer.Option(
        False,
        "--ai-friendly",
        "-a",
        help="Filtrar exclusivamente ofertas AI Friendly (SI).",
    ),
    freelance: bool = typer.Option(
        False,
        "--freelance",
        "-f",
        help="Filtrar exclusivamente ofertas Freelance / Contractor (SI).",
    ),
    remoto: bool = typer.Option(
        False,
        "--remoto",
        "-r",
        help="Filtrar exclusivamente ofertas con modalidad Remota (SI).",
    ),
    max_pages: Optional[int] = typer.Option(
        None,
        "--max-pages",
        "-p",
        help="Límite de páginas a consultar por portal.",
    ),
    output_dir: Optional[str] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Directorio de destino para los reportes generados.",
    ),
):
    """Ejecuta la búsqueda, clasificación y exportación de ofertas laborales."""
    _clear_terminal()
    console.print(f"[bold cyan]{JOB0T_LOGO}[/bold cyan]")
    console.print(
        Panel(
            "[bold white]job0t[/bold white] — [green]Buscador & Clasificador de Empleo[/green]\n"
            "[dim]Scraping respetuoso, flags de valor y Excel profesional[/dim]",
            border_style="cyan",
        )
    )

    is_interactive = categories is None

    # 1. Determinar categorías seleccionadas
    selected_categories: List[str] = []
    if categories:
        selected_categories = [c.strip().lower() for c in categories.split(",") if c.strip()]
    else:
        selected_categories = _prompt_interactive_categories()
        if not selected_categories:
            console.print("[yellow]No seleccionaste ninguna categoría. Búsqueda cancelada.[/yellow]")
            raise typer.Exit(code=0)

    # 2. Determinar seniority seleccionado
    selected_seniority = seniority
    if is_interactive and selected_seniority is None:
        selected_seniority = _prompt_interactive_seniority()

    # 3. Determinar modalidad seleccionada
    selected_modalities: List[str] = []
    if modality:
        selected_modalities = [m.strip().lower() for m in modality.split(",") if m.strip()]
    elif is_interactive:
        selected_modalities = _prompt_interactive_modality()

    # 4. Determinar ubicación seleccionada
    selected_location = location
    if is_interactive and selected_location is None:
        selected_location = _prompt_interactive_location(selected_modalities)

    # 5. Determinar formato de exportación
    selected_format = export_format
    if is_interactive and selected_format is None:
        selected_format = _prompt_interactive_format()
    elif not selected_format:
        selected_format = "both"

    # 6. Determinar nombre de archivo
    selected_filename = filename
    if is_interactive and selected_filename is None:
        selected_filename = _prompt_interactive_filename()

    console.print(f"\n[bold]Categorías activas:[/bold] {', '.join(selected_categories)}")
    if selected_seniority:
        if isinstance(selected_seniority, list):
            if selected_seniority:
                sen_str = ", ".join(s.title() for s in selected_seniority)
                console.print(f"[bold]Seniority activo:[/bold] [blue]{sen_str}[/blue]")
            else:
                console.print("[bold]Seniority activo:[/bold] [dim]Todos / Sin filtro[/dim]")
        elif selected_seniority.lower() not in ("todos", "all", "none", "no"):
            console.print(f"[bold]Seniority activo:[/bold] [blue]{selected_seniority.title()}[/blue]")
        else:
            console.print("[bold]Seniority activo:[/bold] [dim]Todos / Sin filtro[/dim]")
    else:
        console.print("[bold]Seniority activo:[/bold] [dim]Todos / Sin filtro[/dim]")

    if selected_modalities:
        mod_str = ", ".join(m.title() for m in selected_modalities)
        console.print(f"[bold]Modalidad activa:[/bold] [magenta]{mod_str}[/magenta]")
    else:
        console.print("[bold]Modalidad activa:[/bold] [dim]Todas / Sin filtro[/dim]")

    if selected_location and selected_location.lower() not in ("todos", "all", "global", "sin filtro"):
        console.print(f"[bold]Ubicación activa:[/bold] [yellow]{selected_location.title()}[/yellow]")
    else:
        console.print("[bold]Ubicación activa:[/bold] [dim]Todas / Global[/dim]")

    console.print(f"[bold]Formato de descarga:[/bold] [green]{selected_format.upper()}[/green]")
    if selected_filename:
        console.print(f"[bold]Nombre de archivo:[/bold] [cyan]{selected_filename}[/cyan]")

    filter_flags_msg = []
    if ai_friendly:
        filter_flags_msg.append("[green]AI Friendly[/green]")
    if freelance:
        filter_flags_msg.append("[cyan]Freelance[/cyan]")
    if remoto:
        filter_flags_msg.append("[magenta]Remoto[/magenta]")

    if filter_flags_msg:
        console.print(f"[bold]Banderas activas:[/bold] {' + '.join(filter_flags_msg)}")

    options = FilterOptions(
        categories=selected_categories,
        only_ai=ai_friendly,
        only_freelance=freelance,
        only_remoto=remoto,
        modalities=selected_modalities,
        location=selected_location,
        seniority=selected_seniority,
        export_format=selected_format,
        filename=selected_filename,
        max_pages=max_pages,
        output_dir=output_dir,
    )

    # 5. Ejecutar Runner con indicador de progreso
    runner = PipelineRunner()
    with console.status("[bold green]Buscando y procesando ofertas laborales...", spinner="dots"):
        xlsx_path, csv_path, stats = runner.run(options)

    # 6. Mostrar Resumen de Resultados
    console.print("\n[bold green][OK] Búsqueda finalizada exitosamente[/bold green]\n")

    table = Table(title="Resumen de Ejecución", border_style="dim")
    table.add_column("Métrica", style="bold")
    table.add_column("Valor", justify="right")

    table.add_row("Ofertas crudas extraídas", str(stats.total_raw))
    table.add_row("Ofertas filtradas", str(stats.total_filtered))
    table.add_row("Ofertas únicas consolidadas", f"[bold cyan]{stats.total_unique}[/bold cyan]")
    table.add_row("AI Friendly", f"[green]{stats.ai_friendly_count}[/green]")
    table.add_row("Freelance / Contractor", f"[yellow]{stats.freelance_count}[/yellow]")
    table.add_row("Remotas", f"[magenta]{stats.remoto_count}[/magenta]")

    console.print(table)

    # Desglose por portal
    if stats.sources_count:
        source_table = Table(title="Distribución por Portal", border_style="dim")
        source_table.add_column("Portal", style="bold")
        source_table.add_column("Ofertas", justify="right")
        for src, cnt in stats.sources_count.items():
            source_table.add_row(src.capitalize(), str(cnt))
        console.print(source_table)

    # Desglose por modalidad
    if stats.modality_count:
        mod_table = Table(title="Distribución por Modalidad", border_style="dim")
        mod_table.add_column("Modalidad", style="bold")
        mod_table.add_column("Ofertas", justify="right")
        for mod, cnt in sorted(stats.modality_count.items(), key=lambda x: x[1], reverse=True):
            mod_table.add_row(mod, str(cnt))
        console.print(mod_table)

    # Desglose por seniority
    if stats.seniority_count:
        sen_table = Table(title="Distribución por Seniority", border_style="dim")
        sen_table.add_column("Seniority", style="bold")
        sen_table.add_column("Ofertas", justify="right")
        for sen, cnt in sorted(stats.seniority_count.items(), key=lambda x: x[1], reverse=True):
            sen_table.add_row(sen, str(cnt))
        console.print(sen_table)

    console.print("\n[bold]Reportes generados:[/bold]")
    if xlsx_path:
        console.print(f"  [Excel] {xlsx_path.resolve()}")
    if csv_path:
        console.print(f"  [CSV]   {csv_path.resolve()}")
    console.print()


@app.command(name="update")
def update(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Fuerza la reinstalación y actualización incluso si el commit local coincide con el remoto.",
    ),
):
    """Actualiza job0t a la versión más reciente publicada en GitHub."""
    from job0t.updater import (
        check_uncommitted_changes,
        get_app_root,
        get_current_git_branch,
        get_local_commit_sha,
        get_remote_commit_info,
        update_via_git,
        update_via_zip,
    )

    _clear_terminal()
    console.print(f"[bold cyan]{JOB0T_LOGO}[/bold cyan]")
    console.print(
        Panel(
            "[bold white]job0t updater[/bold white] — [green]Actualizador Automático[/green]\n"
            "[dim]Sincronización directa con el repositorio oficial en GitHub[/dim]",
            border_style="cyan",
        )
    )

    app_root = get_app_root()
    is_git_repo = (app_root / ".git").exists()
    branch = get_current_git_branch(app_root) or "main"

    console.print(f"[dim]Ruta de instalación:[/dim] {app_root}")
    if is_git_repo:
        console.print(f"[dim]Rama activa:[/dim] {branch}")

    # 1. Chequear cambios locales sin commitear (si es repo git)
    if is_git_repo and check_uncommitted_changes(app_root):
        console.print(
            "\n[bold yellow]Atención:[/bold yellow] Tenés cambios locales sin guardar en tu copia de trabajo.\n"
            "Por favor hacé un commit o 'git stash' antes de ejecutar el actualizador para evitar conflictos."
        )
        raise typer.Exit(code=1)

    # 2. Consultar último commit remoto
    with console.status("[bold cyan]Consultando actualizaciones en GitHub...", spinner="dots"):
        local_sha = get_local_commit_sha(app_root)
        remote_sha, remote_msg, err = get_remote_commit_info(branch)

    if err:
        console.print(f"\n[bold red]No se pudo verificar la actualización:[/bold red] {err}")
        if not force:
            raise typer.Exit(code=1)

    if local_sha and remote_sha and local_sha == remote_sha and not force:
        console.print("\n[bold green][OK] job0t ya se encuentra en la versión más reciente.[/bold green]")
        console.print(f"Commit actual: [cyan]{local_sha[:7]}[/cyan] ({remote_msg})\n")
        return

    # 3. Mostrar información del nuevo commit a instalar
    if remote_sha:
        console.print(f"\n[bold green]Nueva versión encontrada:[/bold green] [cyan]{remote_sha[:7]}[/cyan]")
        if remote_msg:
            console.print(f"[dim]Mensaje:[/dim] {remote_msg}")

    # 4. Ejecutar actualización
    with console.status("[bold green]Descargando actualización y actualizando dependencias...", spinner="dots"):
        if is_git_repo:
            success, msg = update_via_git(app_root, branch)
        else:
            success, msg = update_via_zip(app_root, target_sha=remote_sha)

    if success:
        console.print("\n[bold green][OK] ¡job0t se actualizó exitosamente![/bold green]")
        if remote_sha:
            console.print(f"Versión activa: [cyan]{remote_sha[:7]}[/cyan]")
        console.print("\nYa podés continuar usando [bold cyan]job0t run[/bold cyan].\n")
    else:
        console.print(f"\n[bold red]Ocurrió un error al actualizar:[/bold red] {msg}\n")
        raise typer.Exit(code=1)


def main():
    app()


if __name__ == "__main__":
    main()

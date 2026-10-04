import sys
from pathlib import Path
from typing import List, Optional
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import typer

from job0t.config import load_categories_config
from job0t.models import FilterOptions
from job0t.pipeline.runner import PipelineRunner

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
    selected = questionary.checkbox(
        "Seleccioná las áreas de tu interés (Espacio para marcar, Enter para confirmar):",
        choices=choices,
    ).ask()

    return selected or []


def _prompt_interactive_seniority() -> Optional[str]:
    """Muestra un menú interactivo para elegir el nivel de seniority deseado."""
    choices = [
        questionary.Choice(title="[1] (Recomendado) Todos / No filtrar", value="todos"),
        questionary.Choice(title="[2] Junior", value="junior"),
        questionary.Choice(title="[3] Semi Senior (SSR)", value="semi senior"),
        questionary.Choice(title="[4] Senior (SR)", value="senior"),
        questionary.Choice(title="[5] Trainee / Entry", value="trainee"),
    ]
    console.print("\n[bold cyan]Selector de Seniority[/bold cyan]")
    choice = questionary.select(
        "Seleccioná el seniority deseado (Navegá con flechas ↑/↓ y presioná ENTER para confirmar):",
        choices=choices,
        default=choices[0],
    ).ask()

    if not choice or choice in ("todos", "(recomendado) todos / no filtrar"):
        return None
    return choice


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
    console.clear()
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

    console.print(f"\n[bold]Categorías activas:[/bold] {', '.join(selected_categories)}")
    if selected_seniority and selected_seniority.lower() not in ("todos", "all", "none", "no"):
        console.print(f"[bold]Seniority activo:[/bold] [blue]{selected_seniority.title()}[/blue]")
    else:
        console.print("[bold]Seniority activo:[/bold] [dim]Todos / Sin filtro[/dim]")

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
        seniority=selected_seniority,
        max_pages=max_pages,
        output_dir=output_dir,
    )

    # 3. Ejecutar Runner con indicador de progreso
    runner = PipelineRunner()
    with console.status("[bold green]Buscando y procesando ofertas laborales...", spinner="dots"):
        xlsx_path, csv_path, stats = runner.run(options)

    # 4. Mostrar Resumen de Resultados
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

    # Desglose por seniority
    if stats.seniority_count:
        sen_table = Table(title="Distribución por Seniority", border_style="dim")
        sen_table.add_column("Seniority", style="bold")
        sen_table.add_column("Ofertas", justify="right")
        for sen, cnt in sorted(stats.seniority_count.items(), key=lambda x: x[1], reverse=True):
            sen_table.add_row(sen, str(cnt))
        console.print(sen_table)

    console.print("\n[bold]Reportes generados:[/bold]")
    console.print(f"  [Excel] {xlsx_path.resolve()}")
    console.print(f"  [CSV]   {csv_path.resolve()}\n")


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

    console.clear()
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

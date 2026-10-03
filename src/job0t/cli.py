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
    """Muestra un menú interactivo con casillas de verificación para elegir categorías."""
    categories_cfg = load_categories_config()
    choices = [
        questionary.Choice(title=f"{v.label} ({k})", value=k)
        for k, v in categories_cfg.items()
    ]

    console.print("[bold cyan]Selector Interactivo de Categorías[/bold cyan]")
    selected = questionary.checkbox(
        "Seleccioná una o varias categorías (Espacio para marcar, Enter para confirmar):",
        choices=choices,
    ).ask()

    return selected or []


def _prompt_interactive_seniority() -> Optional[str]:
    """Muestra un menú interactivo para elegir el nivel de seniority deseado."""
    choices = [
        "(Recomendado) Todos / No filtrar",
        "Junior",
        "Semi Senior (SSR)",
        "Senior (SR)",
        "Trainee / Entry",
    ]
    console.print("\n[bold cyan]Selector de Seniority[/bold cyan]")
    choice = questionary.select(
        "Seleccioná el seniority deseado:",
        choices=choices,
        default="(Recomendado) Todos / No filtrar",
    ).ask()

    if not choice or choice.startswith("(Recomendado)"):
        return None
    return choice


@app.callback()
def main_callback():
    """🤖 job0t — Herramienta local para buscar, clasificar y exportar ofertas laborales."""
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

    console.print(f"[bold]Categorías activas:[/bold] {', '.join(selected_categories)}")

    filter_flags_msg = []
    if ai_friendly:
        filter_flags_msg.append("[green]AI Friendly[/green]")
    if freelance:
        filter_flags_msg.append("[cyan]Freelance[/cyan]")
    if remoto:
        filter_flags_msg.append("[magenta]Remoto[/magenta]")
    if selected_seniority and selected_seniority.lower() not in ("todos", "all", "none", "no"):
        filter_flags_msg.append(f"[blue]Seniority: {selected_seniority}[/blue]")

    if filter_flags_msg:
        console.print(f"[bold]Filtros aplicados:[/bold] {' + '.join(filter_flags_msg)}")

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


def main():
    app()


if __name__ == "__main__":
    main()

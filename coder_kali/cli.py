"""
coder_kali/cli.py - Enrutador Principal de Comandos CLI con Typer.
Punto de entrada de la aplicación para chat interactivo, configuración, ejecución directa y diagnóstico.
"""

import os
import sys
import shutil
import typer
from rich.console import Console
from rich.prompt import Prompt

from coder_kali import __version__
from coder_kali.config import ConfigManager
from coder_kali.agent import KaliAgent
from coder_kali.system_executor import SystemExecutor
from coder_kali.ui.chat_render import (
    print_banner,
    render_user_message,
    render_error,
    render_info,
    render_system_status,
)
from coder_kali.ui.config_menus import interactive_config_wizard, test_provider_connection

app = typer.Typer(
    name="coder-kali",
    help="⚡ Agente de IA de Élite para Ciberseguridad, Hacking Ético y Administración de Sistemas Linux.",
    add_completion=False,
)
console = Console()


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="Muestra la versión de Coder-Kali."),
):
    """Comando por defecto cuando se invoca coder-kali sin argumentos."""
    if version:
        console.print(f"[bold cyan]coder-kali[/bold cyan] versión [bold green]{__version__}[/bold green]")
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        # Iniciar chat interactivo por defecto
        chat()


@app.command(name="chat", help="Inicia una sesión de chat interactiva en vivo con Coder-Kali.")
def chat():
    """Modo conversacional interactivo con terminal enriquecida."""
    config_mgr = ConfigManager()

    # Si no está configurado, ofrecer wizard inicial
    if not config_mgr.is_configured():
        console.print("[yellow][!] Coder-Kali no tiene un proveedor de IA o API Key configurada.[/yellow]")
        console.print("[cyan][*] Iniciando asistente de configuración inicial...[/cyan]")
        configured = interactive_config_wizard(config_mgr)
        if not configured:
            console.print("[red][!] No se completó la configuración. Saliendo...[/red]")
            raise typer.Exit(1)

    provider = config_mgr.get_active_provider()
    model = config_mgr.get_active_model()
    print_banner(version=__version__, provider=provider, model=model)

    agent = KaliAgent(config_mgr=config_mgr)

    while True:
        try:
            user_input = Prompt.ask("[bold bright_green]coder-kali >[/bold bright_green]")
            if not user_input or not user_input.strip():
                continue

            cleaned_cmd = user_input.strip().lower()

            if cleaned_cmd in ["exit", "quit", "salir"]:
                console.print("[bold cyan]Hasta pronto, operador. Sesión finalizada.[/bold cyan]")
                break
            elif cleaned_cmd in ["clear", "cls", "limpiar"]:
                os.system("clear" if os.name != "nt" else "cls")
                print_banner(version=__version__, provider=provider, model=model)
                continue
            elif cleaned_cmd in ["reset", "reiniciar"]:
                agent.reset_conversation()
                console.print("[bold green][✓] Historial de conversación reiniciado.[/bold green]")
                continue
            elif cleaned_cmd in ["config", "configurar"]:
                interactive_config_wizard(config_mgr)
                # Actualizar instancia del agente con nueva configuración
                provider = config_mgr.get_active_provider()
                model = config_mgr.get_active_model()
                agent = KaliAgent(config_mgr=config_mgr)
                continue
            elif cleaned_cmd in ["ayuda", "help"]:
                console.print("""
[bold cyan]Comandos de la sesión:[/bold cyan]
  [green]exit / quit[/green]     - Salir de Coder-Kali
  [green]clear[/green]           - Limpiar la pantalla de la terminal
  [green]reset[/green]           - Reiniciar el contexto de la conversación
  [green]config[/green]          - Abrir el menú de configuración de IA
  [green]ayuda[/green]           - Mostrar este mensaje de ayuda
                """)
                continue

            # Renderizar mensaje del usuario
            render_user_message(user_input)

            # Ejecutar turno de razonamiento y acción
            agent.send_message(user_input)

        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold cyan]Sesión interrumpida. Cerrando Coder-Kali...[/bold cyan]")
            break
        except Exception as e:
            render_error("Excepción en la sesión", str(e))


@app.command(name="config", help="Abre el menú interactivo para configurar proveedores y API Keys.")
def config():
    """Configura modelos, API keys y opciones del sistema."""
    config_mgr = ConfigManager()
    interactive_config_wizard(config_mgr)


@app.command(name="run", help="Ejecuta una instrucción directa en una sola línea sin entrar al chat.")
def run_command_line(
    prompt: str = typer.Argument(..., help="Instrucción o tarea a ejecutar (ej. 'audita puertos locales')")
):
    """Ejecución de un solo disparo desde la terminal."""
    config_mgr = ConfigManager()
    if not config_mgr.is_configured():
        console.print("[yellow][!] Configura primero Coder-Kali ejecutando 'coder-kali config'.[/yellow]")
        raise typer.Exit(1)

    agent = KaliAgent(config_mgr=config_mgr)
    render_user_message(prompt)
    agent.send_message(prompt)


@app.command(name="doctor", help="Comprueba el estado del sistema, dependencias y herramientas de seguridad.")
def doctor():
    """Diagnóstico del entorno y herramientas."""
    import platform

    config_mgr = ConfigManager()
    os_name = platform.system()
    py_ver = sys.version.split()[0]

    # Verificar herramientas comunes de Kali / Pentesting
    tools = [
        "nmap",
        "nikto",
        "gobuster",
        "hydra",
        "sqlmap",
        "wireshark",
        "tshark",
        "msfconsole",
        "john",
        "aircrack-ng",
        "curl",
        "docker",
        "git",
    ]

    tools_status = {}
    for tool in tools:
        path = shutil.which(tool)
        tools_status[tool] = "[green]Instalado[/green]" if path else "[dim red]No encontrado[/dim red]"

    status_data = {
        "Sistema Operativo": f"{os_name} ({platform.release()})",
        "Versión de Python": py_ver,
        "Proveedor Activo": config_mgr.get_active_provider(),
        "Modelo Activo": config_mgr.get_active_model(),
        "API Key Configurada": "[green]Sí[/green]" if config_mgr.is_configured() else "[red]No[/red]",
        "Herramientas Detectadas": ", ".join([t for t, s in tools_status.items() if "Instalado" in s]) or "Ninguna específica",
    }

    render_system_status(status_data)


# ==============================================================================
# SUBCOMANDOS DE HERRAMIENTAS Y SCRAPING (https://www.kali.org/tools/)
# ==============================================================================
tools_app = typer.Typer(
    name="tools",
    help="🧰 Base de conocimiento y scraper oficial de herramientas de Kali Linux (https://www.kali.org/tools/).",
)
app.add_typer(tools_app, name="tools")


@tools_app.command(name="list", help="Lista las herramientas y categorías disponibles en la base de datos local.")
def list_tools():
    """Muestra todas las herramientas indexadas por categoría."""
    from rich.table import Table
    from coder_kali.tools_database import KaliToolsDatabase

    db = KaliToolsDatabase()
    categories = db.get_categories()

    table = Table(title="🧰 Herramientas de Kali Linux Indexadas", box=typer.colors.RESET)
    table.add_column("Categoría", style="bold cyan")
    table.add_column("Herramientas", style="white")

    total = 0
    for cat, tools in categories.items():
        table.add_row(cat, ", ".join(tools))
        total += len(tools)

    console.print(table)
    console.print(f"\n[bold green]Total de herramientas indexadas:[/bold green] {total}")


@tools_app.command(name="search", help="Busca una herramienta por nombre, comando o palabra clave.")
def search_tools(
    query: str = typer.Argument(..., help="Término de búsqueda (ej. 'fuzzing', 'wifi', 'sql', 'nmap')")
):
    """Busca herramientas en la base de conocimiento."""
    from rich.table import Table
    from coder_kali.tools_database import KaliToolsDatabase

    db = KaliToolsDatabase()
    results = db.search_tools(query)

    if not results:
        console.print(f"[yellow][!] No se encontraron herramientas para: '{query}'[/yellow]")
        return

    table = Table(title=f"Resultados para '{query}' ({len(results)})", border_style="cyan")
    table.add_column("Herramienta", style="bold green")
    table.add_column("Categoría", style="bold cyan")
    table.add_column("Descripción", style="white")

    for t in results:
        table.add_row(t.name, t.category, t.summary[:90] + ("..." if len(t.summary) > 90 else ""))

    console.print(table)


@tools_app.command(name="info", help="Muestra la sintaxis oficial, flags y ejemplos de una herramienta de Kali.")
def info_tool(
    name: str = typer.Argument(..., help="Nombre de la herramienta (ej. 'nmap', 'hydra', 'sqlmap')")
):
    """Muestra la ficha técnica completa de una herramienta."""
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.table import Table
    from coder_kali.tools_database import KaliToolsDatabase

    db = KaliToolsDatabase()
    tool = db.get_tool(name)

    if not tool:
        console.print(f"[red][!] La herramienta '{name}' no está en la base de datos local.[/red]")
        console.print(f"[dim]Puedes sincronizar la base completa con: coder-kali tools sync[/dim]")
        return

    console.print()
    header_text = f"[bold green]{tool.name.upper()}[/bold green] - [cyan]{tool.category}[/cyan]\n[dim]{tool.url}[/dim]\n\n{tool.description}"
    console.print(Panel(header_text, title="📖 FICHA DE HERRAMIENTA KALI", border_style="bright_cyan"))

    if tool.usage_examples:
        console.print("\n[bold cyan]💡 Sintaxis y Ejemplos Oficiales:[/bold cyan]")
        for ex in tool.usage_examples:
            console.print(Panel(Syntax(ex, "bash", theme="monokai"), border_style="green", padding=(0, 1)))

    if tool.flags:
        table = Table(title="🚩 Parámetros & Flags Clave", border_style="yellow")
        table.add_column("Flag / Opción", style="bold yellow")
        table.add_column("Descripción", style="white")
        for flg, desc in tool.flags.items():
            table.add_row(flg, desc)
        console.print(table)


@tools_app.command(name="sync", help="Descarga y actualiza todas las herramientas directamente desde https://www.kali.org/tools/.")
def sync_tools(
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limitar cantidad de herramientas a scrapear (útil para pruebas rápidas)")
):
    """Ejecuta el scraper en vivo contra kali.org/tools/."""
    from coder_kali.tools_database import KaliToolsDatabase

    db = KaliToolsDatabase()
    console.print("[bold cyan]Iniciando sincronización con el repositorio oficial de Kali Linux...[/bold cyan]")
    db.scrape_from_kali_org(limit=limit, verbose=True)


@app.command(name="reset", help="Restaura la configuración a los valores de fábrica.")
def reset():
    """Restablece la configuración."""
    config_mgr = ConfigManager()
    confirm = typer.confirm("¿Estás seguro de restablecer toda la configuración?")
    if confirm:
        config_mgr.reset()
        console.print("[bold green][✓] Configuración restablecida exitosamente.[/bold green]")


def main():
    app()


if __name__ == "__main__":
    main()

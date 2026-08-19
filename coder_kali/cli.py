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

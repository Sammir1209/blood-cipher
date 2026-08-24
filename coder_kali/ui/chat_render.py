"""
coder_kali/ui/chat_render.py - Renderizador TUI de Élite con Rich.
Muestra banners, paneles cyberpunk, respuestas Markdown, bloques de código
y resultados de comandos estilizados.
"""

import sys
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.text import Text
from rich.syntax import Syntax
from rich.box import ROUNDED, DOUBLE, HEAVY

console = Console()

BANNER_ART = r"""
  ██████╗ ██╗      ██████╗  ██████╗ ██████╗       ██████╗██╗██████╗ ██╗  ██╗███████╗██████╗ 
  ██╔══██╗██║     ██╔═══██╗██╔═══██╗██╔══██╗     ██╔════╝██║██╔══██╗██║  ██║██╔════╝██╔══██╗
  ██████╔╝██║     ██║   ██║██║   ██║██║  ██║     ██║     ██║██████╔╝███████║█████╗  ██████╔╝
  ██╔══██╗██║     ██║   ██║██║   ██║██║  ██║     ██║     ██║██╔═══╝ ██╔══██║██╔══╝  ██╔══██╗
  ██████╔╝███████╗╚██████╔╝╚██████╔╝██████╔╝     ╚██████╗██║██║     ██║  ██║███████╗██║  ██║
  ╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝       ╚═════╝╚═╝╚═╝     ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
"""


def print_banner(version: str = "1.5.0", provider: str = "gemini", model: str = "gemini-2.0-flash", scope: Optional[str] = None, key_pool_size: int = 1):
    """Imprime el banner principal estilo hacker/cyberpunk con metadata de sesión."""
    console.print(f"[bold red]{BANNER_ART}[/bold red]")

    info_table = Table.grid(padding=(0, 2))
    info_table.add_column(style="bold bright_green")
    info_table.add_column(style="bold white")

    info_table.add_row("⚡ Versión:", f"v{version} [Linux Native]")
    provider_str = f"[cyan]{provider.upper()}[/cyan]"
    if key_pool_size > 1:
        provider_str += f"  [bold green]🔄 {key_pool_size} API Keys en rotación[/bold green]"
    info_table.add_row("🤖 Proveedor IA:", provider_str)
    info_table.add_row("🧠 Modelo Activo:", f"[yellow]{model}[/yellow]")
    info_table.add_row("🎯 Alcance / SOW:", f"[bold green]{scope}[/bold green]" if scope else "[dim]No definido ('scope' para cargar)[/dim]")
    info_table.add_row("🛡️  Modo de Seguridad:", "[green]Supervisión PTY Activa[/green]")
    info_table.add_row("💡 Comandos Rápidos:", "[dim]escribe 'exit', 'scope', 'config', 'clear' o 'ayuda'[/dim]")

    panel = Panel(
        info_table,
        title="[bold green]● SISTEMA DE OPERACIONES TÁCTICAS IA[/bold green]",
        border_style="bright_blue",
        box=ROUNDED,
        padding=(0, 2),
    )
    console.print(panel)
    console.print()


def render_user_message(message: str):
    """Renderiza el mensaje del operador."""
    console.print()
    header = Text(" 👤 OPERADOR ", style="bold black on bright_green")
    console.print(header)
    panel = Panel(
        Text(message, style="white"),
        border_style="green",
        box=ROUNDED,
        padding=(0, 1),
    )
    console.print(panel)


def render_ai_message(message: str):
    """Renderiza la respuesta directa de Blood-Cipher en formato Markdown limpio, suprimiendo pensamientos internos."""
    import re

    # 1. Eliminar etiquetas de razonamiento/pensamiento comunes en modelos (DeepSeek, Qwen, Claude, Groq, etc.)
    cleaned_text = re.sub(r'<think>[\s\S]*?</think>', '', message, flags=re.IGNORECASE)
    cleaned_text = re.sub(r'```(?:thought|thinking|reasoning)[\s\S]*?```', '', cleaned_text, flags=re.IGNORECASE)
    cleaned_text = re.sub(r'^\s*<think>[\s\S]*$', '', cleaned_text, flags=re.IGNORECASE)
    
    # 2. Filtrar las etiquetas XML de comandos (se muestran en su propio panel interactivo)
    raw_for_preview = cleaned_text
    cleaned_text = re.sub(r'<ejecutar_comando>[\s\S]*?</ejecutar_comando>', '', cleaned_text)
    cleaned_text = re.sub(r'<escribir_archivo[^>]*>[\s\S]*?</escribir_archivo>', '', cleaned_text)
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text).strip()

    # 3. Si no hay texto conversacional pero sí hay comandos, extraer un resumen descriptivo
    if not cleaned_text.strip():
        # Buscar comandos XML en el texto pre-limpieza y también en el mensaje original (por si estaban dentro de <think>)
        xml_cmds = re.findall(r'<ejecutar_comando>([\s\S]*?)</ejecutar_comando>', raw_for_preview, flags=re.IGNORECASE)
        if not xml_cmds:
            xml_cmds = re.findall(r'<ejecutar_comando>([\s\S]*?)</ejecutar_comando>', message, flags=re.IGNORECASE)
        if xml_cmds:
            cmd_lines = [c.strip().split('\n')[0] for c in xml_cmds if c.strip()]
            cleaned_text = "⚡ **Iniciando secuencia de ejecución:**\n" + "\n".join([f"- `{cmd}`" for cmd in cmd_lines[:6]])
        else:
            # No hay ni texto ni comandos - no renderizar nada
            return

    # 4. Solo imprimir header y panel cuando hay contenido real
    console.print()
    header = Text(" 🤖 BLOOD-CIPHER ", style="bold black on bright_cyan")
    console.print(header)

    md = Markdown(cleaned_text, code_theme="monokai", hyperlinks=True)
    panel = Panel(
        md,
        border_style="bright_cyan",
        box=ROUNDED,
        padding=(1, 2),
    )
    console.print(panel)


def render_execution_result(result, command: Optional[str] = None):
    """Muestra el resultado de la ejecución del comando o escritura de archivo."""
    console.print()
    if result.was_rejected:
        panel = Panel(
            Text(result.output, style="bold red"),
            title="[bold red]⛔ ACCIÓN CANCELADA[/bold red]",
            border_style="red",
            box=ROUNDED,
        )
        console.print(panel)
        return

    if result.is_file_op:
        title = f"[bold green]✓ ARCHIVO GENERADO: {result.target_path}[/bold green]" if result.success else f"[bold red]✗ ERROR EN ARCHIVO: {result.target_path}[/bold red]"
        border_color = "bright_green" if result.success else "bright_red"
        panel = Panel(
            Text(result.output, style="white"),
            title=title,
            border_style=border_color,
            box=ROUNDED,
        )
        console.print(panel)
        return

    # Para comandos de terminal
    title = f"[bold green]✓ SALIDA DEL SISTEMA (Código {result.returncode})[/bold green]" if result.success else f"[bold red]✗ ERROR DE EJECUCIÓN (Código {result.returncode})[/bold red]"
    border_color = "bright_green" if result.success else "bright_red"

    # Si la salida es muy larga o tiene líneas minificadas gigantes, darle formato limpio y seguro
    output_text = result.output
    lines = output_text.splitlines()

    # Si hay líneas larguísimas (ej. JS minificado), truncar las líneas individuales
    safe_lines = []
    for l in lines[:60]:
        if len(l) > 300:
            safe_lines.append(l[:297] + "...")
        else:
            safe_lines.append(l)

    if len(lines) > 50:
        preview = "\n".join(safe_lines[:30]) + f"\n\n... [{len(lines) - 40} líneas omitidas para agilizar visualización] ...\n\n" + "\n".join([l[:300] for l in lines[-10:]])
        display_content = preview
    elif len(output_text) > 5000:
        display_content = "\n".join(safe_lines[:30]) + f"\n\n... [Salida extensa: {len(output_text)} caracteres] ...\n"
    else:
        display_content = "\n".join(safe_lines)

    panel = Panel(
        Text(display_content, style="white on black" if not result.success else "white"),
        title=title,
        border_style=border_color,
        box=ROUNDED,
        subtitle=f"[dim cyan]{command or ''}[/dim cyan]",
    )
    console.print(panel)


def render_error(title: str, details: str):
    """Muestra una caja de error visual."""
    console.print()
    content = f"[bold red]{title}[/bold red]\n\n[white]{details}[/white]"
    panel = Panel(
        content,
        title="[bold red]🚨 ERROR DEL SISTEMA[/bold red]",
        border_style="bright_red",
        box=HEAVY,
        padding=(1, 2),
    )
    console.print(panel)


def render_info(message: str):
    """Muestra un mensaje informativo estilizado."""
    console.print(f"[bold cyan][*][/bold cyan] [white]{message}[/white]")


def render_system_status(status_dict: dict):
    """Renderiza una tabla con el estado del sistema y herramientas de diagnóstico."""
    table = Table(title="📊 Estado de Blood-Cipher", box=ROUNDED, border_style="cyan")
    table.add_column("Propiedad", style="bold cyan")
    table.add_column("Valor", style="white")

    for k, v in status_dict.items():
        table.add_row(k, str(v))

    console.print()
    console.print(table)
    console.print()

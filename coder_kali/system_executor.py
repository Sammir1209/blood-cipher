"""
coder_kali/system_executor.py - Ejecutor Seguro de Comandos del Sistema y Gestor PTY.
Interpreta etiquetas XML <ejecutar_comando> y <escribir_archivo ruta="...">,
solicita confirmación al operador y ejecuta en terminal segura / PTY interactivo.
"""

import os
import re
import sys
import subprocess
import platform
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.syntax import Syntax
from rich.text import Text

console = Console()

COMMAND_REGEX = re.compile(r"<ejecutar_comando>(.*?)</ejecutar_comando>", re.DOTALL | re.IGNORECASE)
FILE_REGEX = re.compile(
    r'<escribir_archivo\s+ruta=(?:"([^"]+)"|\'([^\']+)\'|([^\s>]+))>(.*?)</escribir_archivo>',
    re.DOTALL | re.IGNORECASE,
)

# Comandos de alto riesgo que requieren advertencia especial
CRITICAL_PATTERNS = [
    r"\brm\s+-[rf]*\s+/",
    r"\bmkfs\b",
    r"\bdd\s+if=",
    r">\s*/dev/sd",
    r":\(\)\{\s*:\|:&\s*\};:", # fork bomb
    r"\bchmod\s+-R\s+777\s+/",
    r"\bchown\s+-R\s+.*?\s+/",
]


@dataclass
class ParsedAction:
    action_type: str  # 'command' | 'file'
    content: str
    target_path: Optional[str] = None
    is_sudo: bool = False
    is_dangerous: bool = False


@dataclass
class ExecutionResult:
    success: bool
    output: str
    returncode: int
    command: Optional[str] = None
    target_path: Optional[str] = None
    was_rejected: bool = False
    is_file_op: bool = False


class SystemExecutor:
    """Ejecutor seguro de acciones del sistema con confirmación y PTY interactivo."""

    def __init__(self, auto_approve_safe: bool = False):
        self.auto_approve_safe = auto_approve_safe
        self.is_linux = platform.system() == "Linux"

    def parse_actions(self, text: str) -> List[ParsedAction]:
        """Extrae todas las acciones (XML o JSON) en el texto de la IA en orden de aparición."""
        actions: List[ParsedAction] = []
        seen_commands = set()

        # 1. Buscar comandos en etiquetas XML estándar <ejecutar_comando>
        for match in COMMAND_REGEX.finditer(text):
            cmd = match.group(1).strip()
            if not cmd or cmd in seen_commands:
                continue
            seen_commands.add(cmd)
            is_sudo = bool(re.search(r"\bsudo\b", cmd))
            is_dangerous = any(re.search(pat, cmd) for pat in CRITICAL_PATTERNS)
            actions.append(
                ParsedAction(
                    action_type="command",
                    content=cmd,
                    is_sudo=is_sudo,
                    is_dangerous=is_dangerous,
                )
            )

        # 2. Buscar comandos en formato JSON emitidos por modelos OSS / Groq (ej: {"cmd": ["bash", "-lc", "..."]})
        json_cmd_regex = re.compile(r'\{[^{}]*"(?:cmd|command|bash|exec)"\s*:\s*(?:\[[^\]]*\]|"[^"]*")[^{}]*\}', re.DOTALL)
        for match in json_cmd_regex.finditer(text):
            try:
                raw_json = match.group(0)
                data = json.loads(raw_json)
                cmd_val = data.get("cmd") or data.get("command") or data.get("exec") or data.get("bash")
                cmd_str = ""
                if isinstance(cmd_val, list):
                    if len(cmd_val) >= 3 and cmd_val[0] in ["bash", "sh", "/bin/bash", "/bin/sh"] and cmd_val[1] in ["-c", "-lc"]:
                        cmd_str = cmd_val[2]
                    else:
                        cmd_str = " ".join(cmd_val)
                elif isinstance(cmd_val, str):
                    cmd_str = cmd_val

                cmd_str = cmd_str.strip()
                if cmd_str and cmd_str not in seen_commands:
                    seen_commands.add(cmd_str)
                    is_sudo = bool(re.search(r"\bsudo\b", cmd_str))
                    is_dangerous = any(re.search(pat, cmd_str) for pat in CRITICAL_PATTERNS)
                    actions.append(
                        ParsedAction(
                            action_type="command",
                            content=cmd_str,
                            is_sudo=is_sudo,
                            is_dangerous=is_dangerous,
                        )
                    )
            except Exception:
                continue

        # 3. Buscar creación de archivos <escribir_archivo>
        for match in FILE_REGEX.finditer(text):
            path = match.group(1) or match.group(2) or match.group(3)
            file_content = match.group(4)
            if file_content.startswith("\n"):
                file_content = file_content[1:]
            actions.append(
                ParsedAction(
                    action_type="file",
                    content=file_content,
                    target_path=path.strip(),
                )
            )

        return actions

    def has_actions(self, text: str) -> bool:
        return bool(COMMAND_REGEX.search(text) or FILE_REGEX.search(text))

    def confirm_command(self, cmd: str, is_sudo: bool, is_dangerous: bool) -> bool:
        """Muestra panel visual y solicita confirmación al operador."""
        if is_dangerous:
            panel_title = "[bold red]⚠️  ¡ALERTA DE SEGURIDAD CRÍTICA! ⚠️[/bold red]"
            border_style = "bright_red"
        elif is_sudo:
            panel_title = "[bold yellow]⚡ COMANDO CON PRIVILEGIOS DE ROOT (SUDO) ⚡[/bold yellow]"
            border_style = "yellow"
        else:
            panel_title = "[bold cyan]🛠️  EJECUCIÓN DE COMANDO EN TERMINAL[/bold cyan]"
            border_style = "cyan"

        syntax = Syntax(cmd, "bash", theme="monokai", word_wrap=True, line_numbers=False)
        console.print()
        console.print(Panel(syntax, title=panel_title, border_style=border_style, padding=(1, 2)))

        if is_dangerous:
            console.print("[bold red][!] Advertencia: Este comando puede causar daños destructivos al sistema.[/bold red]")

        try:
            return Confirm.ask(
                "[bold green]¿Autorizar ejecución?[/bold green]",
                default=False,
                console=console
            )
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow][*] Operación cancelada por el usuario.[/yellow]")
            return False

    def confirm_file_write(self, path: str, content: str) -> bool:
        """Solicita confirmación antes de escribir o sobrescribir un archivo."""
        path_obj = Path(path).expanduser()
        exists = path_obj.exists()
        action_str = "SOBRESCRIBIR" if exists else "CREAR"
        border_style = "bright_magenta" if exists else "magenta"

        panel_title = f"[bold magenta]📝 {action_str} ARCHIVO: {path}[/bold magenta]"

        # Detectar lenguaje para resaltado de sintaxis
        ext = path_obj.suffix.lstrip(".") or "txt"
        preview_content = content if len(content) <= 2000 else content[:2000] + "\n\n... [Contenido truncado en la vista previa] ..."
        syntax = Syntax(preview_content, ext, theme="monokai", word_wrap=True, line_numbers=True)

        console.print()
        console.print(Panel(syntax, title=panel_title, border_style=border_style, padding=(1, 2)))

        if exists:
            console.print(f"[bold yellow][!] El archivo ya existe ({path_obj.stat().st_size} bytes). Será sobrescrito.[/bold yellow]")

        try:
            return Confirm.ask(
                f"[bold green]¿Autorizar {action_str.lower()} archivo en '{path}'?[/bold green]",
                default=False,
                console=console
            )
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow][*] Operación cancelada por el usuario.[/yellow]")
            return False

    def execute_command(self, cmd: str, is_sudo: bool = False) -> ExecutionResult:
        """Ejecuta un comando en el sistema operativo capturando stdout y stderr."""
        console.print(f"[dim cyan][*] Ejecutando: {cmd}[/dim cyan]")

        # Si estamos en Linux y requiere sudo o interactividad
        if self.is_linux and is_sudo:
            return self._execute_linux_pty(cmd)
        else:
            return self._execute_standard(cmd)

    def _execute_linux_pty(self, cmd: str) -> ExecutionResult:
        """Ejecuta en Linux usando PTY o pexpect para permitir interacción segura con sudo."""
        try:
            import pexpect

            # Ejecutar a través de bash con pty
            child = pexpect.spawn("/bin/bash", ["-c", cmd], encoding="utf-8", timeout=600)
            output_chunks = []

            # Dejar que el usuario interactúe directamente si pide contraseña
            try:
                while True:
                    index = child.expect([r"\[sudo\] password for .*: ", pexpect.EOF, pexpect.TIMEOUT], timeout=3)
                    if index == 0:
                        # Reenviar prompt a la terminal real
                        sys.stdout.write(child.after)
                        sys.stdout.flush()
                        import getpass
                        pwd = getpass.getpass("")
                        child.sendline(pwd)
                    elif index == 1:
                        output_chunks.append(child.before)
                        break
                    elif index == 2:
                        # Timeout parcial, guardar chunk y continuar
                        output_chunks.append(child.before)
            except pexpect.EOF:
                output_chunks.append(child.before)
            except Exception as e:
                output_chunks.append(f"\n[!] Excepción en PTY: {e}\n")

            child.close()
            full_output = "".join(output_chunks).strip()
            if not full_output:
                full_output = "[Comando ejecutado sin salida estándar]"
            elif len(full_output) > 20000:
                total_len = len(full_output)
                full_output = (
                    full_output[:10000]
                    + f"\n\n... [Salida muy extensa: {total_len} caracteres detectados. Truncado para preservar contexto de IA] ...\n\n"
                    + full_output[-5000:]
                )

            return ExecutionResult(
                success=child.exitstatus == 0,
                output=full_output,
                returncode=child.exitstatus or 0,
                command=cmd,
            )
        except ImportError:
            # Si pexpect no está disponible, usar subprocess normal
            return self._execute_standard(cmd)
        except Exception as e:
            return ExecutionResult(
                success=False,
                output=f"Error durante la ejecución en PTY: {str(e)}",
                returncode=1,
                command=cmd,
            )

    def _execute_standard(self, cmd: str) -> ExecutionResult:
        """Ejecución estándar mediante subprocess."""
        try:
            shell_cmd = ["/bin/bash", "-c", cmd] if self.is_linux else cmd
            use_shell = not self.is_linux

            process = subprocess.Popen(
                shell_cmd,
                shell=use_shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            stdout, stderr = process.communicate(timeout=600)
            combined_output = []
            if stdout:
                combined_output.append(stdout.strip())
            if stderr:
                combined_output.append(f"[STDERR]\n{stderr.strip()}")

            final_output = "\n".join(combined_output).strip()
            if not final_output:
                final_output = "[Comando ejecutado con éxito (código de salida 0), sin salida estándar]"

            # Truncar salidas gigantes (ej. bundles JS minificados)
            max_chars = 20000
            if len(final_output) > max_chars:
                total_len = len(final_output)
                final_output = (
                    final_output[:10000]
                    + f"\n\n... [Salida muy extensa: {total_len} caracteres detectados. Truncado para preservar contexto de IA] ...\n\n"
                    + final_output[-5000:]
                )

            return ExecutionResult(
                success=process.returncode == 0,
                output=final_output,
                returncode=process.returncode,
                command=cmd,
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                output="[!] Tiempo de espera agotado (Timeout de 600 segundos excedido).",
                returncode=124,
                command=cmd,
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                output=f"Error al ejecutar comando: {str(e)}",
                returncode=1,
                command=cmd,
            )

    def write_file(self, target_path: str, content: str) -> ExecutionResult:
        """Crea o sobrescribe un archivo en el sistema de archivos."""
        try:
            path_obj = Path(target_path).expanduser().resolve()
            # Crear directorios padres si no existen
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            path_obj.write_text(content, encoding="utf-8")

            msg = f"[✓] Archivo '{path_obj}' escrito exitosamente ({len(content.encode('utf-8'))} bytes)."
            return ExecutionResult(
                success=True,
                output=msg,
                returncode=0,
                target_path=str(path_obj),
                is_file_op=True,
            )
        except Exception as e:
            err_msg = f"[!] Error al escribir en '{target_path}': {str(e)}"
            return ExecutionResult(
                success=False,
                output=err_msg,
                returncode=1,
                target_path=target_path,
                is_file_op=True,
            )

    def process_action(self, action: ParsedAction) -> ExecutionResult:
        """Procesa una acción individual (comando o archivo) gestionando la confirmación."""
        if action.action_type == "command":
            if self.auto_approve_safe and not action.is_dangerous:
                authorized = True
            else:
                authorized = self.confirm_command(
                    action.content,
                    is_sudo=action.is_sudo,
                    is_dangerous=action.is_dangerous,
                )
            if not authorized:
                return ExecutionResult(
                    success=False,
                    output="[RECHAZADO] El operador canceló la ejecución del comando.",
                    returncode=130,
                    command=action.content,
                    was_rejected=True,
                )
            return self.execute_command(action.content, is_sudo=action.is_sudo)

        elif action.action_type == "file":
            if not action.target_path:
                return ExecutionResult(
                    success=False,
                    output="[ERROR] No se especificó la ruta de archivo en la etiqueta XML.",
                    returncode=1,
                    is_file_op=True,
                )
            if self.auto_approve_safe and not action.is_dangerous:
                authorized = True
            else:
                authorized = self.confirm_file_write(action.target_path, action.content)
            if not authorized:
                return ExecutionResult(
                    success=False,
                    output=f"[RECHAZADO] El operador canceló la creación del archivo '{action.target_path}'.",
                    returncode=130,
                    target_path=action.target_path,
                    was_rejected=True,
                    is_file_op=True,
                )
            return self.write_file(action.target_path, action.content)

        return ExecutionResult(
            success=False,
            output="[ERROR] Tipo de acción desconocido.",
            returncode=1,
        )

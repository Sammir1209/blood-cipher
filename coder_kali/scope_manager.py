"""
coder_kali/scope_manager.py - Gestor de Documentos de Alcance y Autorización (Scope of Work / Rules of Engagement).
Permite cargar, gestionar e inyectar documentos de alcance ético y objetivos autorizados en el contexto de la IA.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
from rich.console import Console

console = Console()

CONFIG_DIR = Path.home() / ".config" / "blood-cipher"
if not CONFIG_DIR.exists() and (Path.home() / ".config" / "coder-kali").exists():
    CONFIG_DIR = Path.home() / ".config" / "coder-kali"

SCOPES_DIR = CONFIG_DIR / "scopes"
ACTIVE_SCOPE_FILE = CONFIG_DIR / "active_scope.txt"


class ScopeManager:
    """Administrador de alcances (Scopes of Work / SOW) y autorizaciones de seguridad."""

    def __init__(self):
        self._ensure_dirs()

    def _ensure_dirs(self):
        SCOPES_DIR.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(SCOPES_DIR, 0o700)
        except Exception:
            pass

    def list_scopes(self) -> List[Dict[str, str]]:
        """Lista todos los scopes guardados."""
        scopes = []
        for file_path in SCOPES_DIR.glob("*.md"):
            name = file_path.stem
            try:
                content = file_path.read_text(encoding="utf-8")
                preview = content.splitlines()[0] if content.splitlines() else "Sin contenido"
                scopes.append({
                    "name": name,
                    "path": str(file_path),
                    "preview": preview[:60],
                    "size": len(content),
                })
            except Exception:
                continue
        return sorted(scopes, key=lambda s: s["name"])

    def get_active_scope_name(self) -> Optional[str]:
        """Obtiene el nombre del scope actualmente activo."""
        if not ACTIVE_SCOPE_FILE.exists():
            return None
        try:
            name = ACTIVE_SCOPE_FILE.read_text(encoding="utf-8").strip()
            if name and (SCOPES_DIR / f"{name}.md").exists():
                return name
        except Exception:
            pass
        return None

    def get_active_scope_content(self) -> Optional[str]:
        """Devuelve el contenido completo del scope activo."""
        name = self.get_active_scope_name()
        if not name:
            return None
        file_path = SCOPES_DIR / f"{name}.md"
        if file_path.exists():
            try:
                return file_path.read_text(encoding="utf-8")
            except Exception as e:
                console.print(f"[dim red][!] Error al leer el scope activo: {e}[/dim red]")
        return None

    def set_active_scope(self, name: str) -> bool:
        """Establece un scope como el activo."""
        file_path = SCOPES_DIR / f"{name}.md"
        if not file_path.exists():
            return False
        try:
            ACTIVE_SCOPE_FILE.write_text(name, encoding="utf-8")
            return True
        except Exception as e:
            console.print(f"[bold red][!] Error al activar scope: {e}[/bold red]")
            return False

    def clear_active_scope(self):
        """Desactiva cualquier scope activo."""
        if ACTIVE_SCOPE_FILE.exists():
            try:
                ACTIVE_SCOPE_FILE.unlink()
            except Exception:
                pass

    def save_scope(self, name: str, content: str) -> str:
        """Guarda un nuevo documento de scope o actualiza uno existente."""
        clean_name = "".join(c for c in name if c.isalnum() or c in ("-", "_")).strip()
        if not clean_name:
            clean_name = "default_scope"

        file_path = SCOPES_DIR / f"{clean_name}.md"
        file_path.write_text(content.strip(), encoding="utf-8")
        return clean_name

    def delete_scope(self, name: str) -> bool:
        """Elimina un documento de scope."""
        file_path = SCOPES_DIR / f"{name}.md"
        if file_path.exists():
            try:
                file_path.unlink()
                if self.get_active_scope_name() == name:
                    self.clear_active_scope()
                return True
            except Exception:
                return False
        return False

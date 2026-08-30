"""
coder_kali/session_manager.py - Gestor de Sesiones e Historial de Conversaciones Persistente.
Guarda los chats en ~/.config/blood-cipher/sessions/<session_id>.json con títulos basados en la primera petición.
"""

import os
import json
import time
import uuid
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional
from rich.console import Console

console = Console()

CONFIG_DIR = Path.home() / ".config" / "blood-cipher"
if not CONFIG_DIR.exists() and (Path.home() / ".config" / "coder-kali").exists():
    CONFIG_DIR = Path.home() / ".config" / "coder-kali"

SESSIONS_DIR = CONFIG_DIR / "sessions"
WORKSPACES_DIR = CONFIG_DIR / "workspaces"


@dataclass
class ChatSession:
    id: str
    title: str
    created_at: float
    updated_at: float
    provider: str
    model: str
    messages: List[Dict[str, str]] = field(default_factory=list)
    workspace_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatSession":
        sess_id = data.get("id", str(uuid.uuid4())[:8])
        default_workspace = str(WORKSPACES_DIR / f"session_{sess_id}")
        return cls(
            id=sess_id,
            title=data.get("title", "Nueva Sesión"),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            provider=data.get("provider", "desconocido"),
            model=data.get("model", "desconocido"),
            messages=data.get("messages", []),
            workspace_path=data.get("workspace_path", default_workspace),
        )


class SessionManager:
    """Administrador de sesiones guardadas e historial de chat con espacio de trabajo dedicado."""

    def __init__(self):
        self._ensure_sessions_dir()

    def _ensure_sessions_dir(self):
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        WORKSPACES_DIR.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(SESSIONS_DIR, 0o700)
            os.chmod(WORKSPACES_DIR, 0o700)
        except Exception:
            pass

    def create_session(self, provider: str, model: str, initial_prompt: Optional[str] = None) -> ChatSession:
        """Crea una nueva sesión con su propia carpeta de trabajo aislada y organizada."""
        sess_id = str(uuid.uuid4())[:8]
        now = time.time()
        title = self._generate_title(initial_prompt) if initial_prompt else f"Sesión {time.strftime('%Y-%m-%d %H:%M')}"
        workspace_dir = WORKSPACES_DIR / f"session_{sess_id}"
        workspace_dir.mkdir(parents=True, exist_ok=True)
        
        sess = ChatSession(
            id=sess_id,
            title=title,
            created_at=now,
            updated_at=now,
            provider=provider,
            model=model,
            messages=[],
            workspace_path=str(workspace_dir),
        )
        self.save_session(sess)
        return sess

    def get_session_workspace(self, session_id: str) -> Path:
        """Obtiene y asegura la carpeta de trabajo de una sesión."""
        workspace_dir = WORKSPACES_DIR / f"session_{session_id}"
        workspace_dir.mkdir(parents=True, exist_ok=True)
        return workspace_dir

    def _generate_title(self, prompt: str) -> str:
        """Genera un título descriptivo y limpio a partir del primer mensaje del usuario."""
        clean = prompt.strip().replace("\n", " ")
        if len(clean) > 50:
            return clean[:47] + "..."
        return clean or "Sesión Táctica"

    def save_session(self, session: ChatSession):
        """Guarda o actualiza la sesión en disco."""
        session.updated_at = time.time()
        # Si aún tiene título genérico y ya hay mensajes de usuario, actualizar el título
        if session.title.startswith("Sesión 20") or session.title == "Nueva Sesión":
            for msg in session.messages:
                if msg.get("role") == "user":
                    session.title = self._generate_title(msg.get("content", ""))
                    break

        file_path = SESSIONS_DIR / f"{session.id}.json"
        try:
            from coder_kali.fast_engine import fast_json_dumps
            file_path.write_text(fast_json_dumps(session.to_dict(), indent=True), encoding="utf-8")
        except Exception as e:
            console.print(f"[dim red][!] Error al guardar historial de sesión: {e}[/dim red]")

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Carga una sesión específica por su ID."""
        file_path = SESSIONS_DIR / f"{session_id}.json"
        if not file_path.exists():
            return None
        try:
            from coder_kali.fast_engine import fast_json_loads
            data = fast_json_loads(file_path.read_bytes())
            return ChatSession.from_dict(data)
        except Exception as e:
            console.print(f"[dim red][!] Error al leer sesión {session_id}: {e}[/dim red]")
            return None

    def list_sessions(self) -> List[ChatSession]:
        """Lista todas las sesiones ordenadas por la más reciente."""
        sessions = []
        from coder_kali.fast_engine import fast_json_loads
        for file in SESSIONS_DIR.glob("*.json"):
            try:
                data = fast_json_loads(file.read_bytes())
                sessions.append(ChatSession.from_dict(data))
            except Exception:
                continue
        # Ordenar por updated_at descendente
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        return sessions

    def delete_session(self, session_id: str) -> bool:
        """Elimina una sesión del historial."""
        file_path = SESSIONS_DIR / f"{session_id}.json"
        if file_path.exists():
            try:
                file_path.unlink()
                return True
            except Exception:
                return False
        return False

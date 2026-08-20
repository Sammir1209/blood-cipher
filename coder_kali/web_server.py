"""
coder_kali/web_server.py - Servidor Web y Panel Gráfico Táctico (Web UI) para Coder-Kali.
Permite interactuar con el agente, auditar objetivos y gestionar scopes e historial desde el navegador web.
"""

import os
import json
import time
import socket
import threading
import webbrowser
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Optional

from rich.console import Console

from coder_kali.config import ConfigManager
from coder_kali.agent import KaliAgent
from coder_kali.session_manager import SessionManager
from coder_kali.scope_manager import ScopeManager
from coder_kali.tools_database import KaliToolsDatabase

console = Console()

HTML_DASHBOARD = r"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CODER-KALI // Centro de Operaciones Tácticas IA</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600;700&family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-base: #0a0d14;
            --bg-surface: #101622;
            --bg-card: #151d2d;
            --border: #1e293b;
            --border-glow: #00ff8840;
            --accent-green: #00ff88;
            --accent-cyan: #00e5ff;
            --accent-purple: #9d4edd;
            --accent-red: #ff3366;
            --text-main: #f1f5f9;
            --text-muted: #94a3b8;
            --font-ui: 'Outfit', sans-serif;
            --font-code: 'Fira Code', monospace;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-base);
            color: var(--text-main);
            font-family: var(--font-ui);
            display: flex;
            height: 100vh;
            overflow: hidden;
        }

        /* Sidebar */
        .sidebar {
            width: 320px;
            background: var(--bg-surface);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            padding: 20px;
            gap: 20px;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--border);
        }

        .brand-logo {
            width: 38px;
            height: 38px;
            background: linear-gradient(135deg, var(--accent-green), var(--accent-cyan));
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: var(--font-code);
            font-weight: 800;
            color: #000;
            box-shadow: 0 0 15px var(--border-glow);
        }

        .brand-text h1 {
            font-size: 1.2rem;
            font-weight: 800;
            letter-spacing: 1px;
            background: linear-gradient(90deg, #fff, var(--accent-cyan));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .brand-text p {
            font-size: 0.72rem;
            color: var(--text-muted);
            font-family: var(--font-code);
        }

        .status-badge {
            background: rgba(0, 255, 136, 0.1);
            border: 1px solid var(--accent-green);
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 0.8rem;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .status-badge span {
            font-family: var(--font-code);
            font-size: 0.75rem;
            color: var(--accent-green);
        }

        .section-title {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: var(--text-muted);
            font-weight: 600;
        }

        .session-list {
            flex: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .session-item {
            padding: 10px 14px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .session-item:hover, .session-item.active {
            border-color: var(--accent-cyan);
            background: rgba(0, 229, 255, 0.05);
            box-shadow: 0 0 10px rgba(0, 229, 255, 0.1);
        }

        .session-item .title {
            font-size: 0.85rem;
            font-weight: 600;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .session-item .meta {
            font-size: 0.7rem;
            color: var(--text-muted);
            font-family: var(--font-code);
        }

        .btn-new-chat {
            background: linear-gradient(135deg, var(--accent-green), #00cc6a);
            color: #000;
            font-weight: 700;
            border: none;
            padding: 12px;
            border-radius: 6px;
            cursor: pointer;
            font-family: var(--font-ui);
            font-size: 0.9rem;
            transition: all 0.2s;
            box-shadow: 0 0 15px rgba(0, 255, 136, 0.2);
        }

        .btn-new-chat:hover {
            transform: translateY(-1px);
            box-shadow: 0 0 20px rgba(0, 255, 136, 0.4);
        }

        /* Main Workspace */
        .main-workspace {
            flex: 1;
            display: flex;
            flex-direction: column;
            height: 100vh;
            background: var(--bg-base);
        }

        .topbar {
            height: 60px;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 24px;
            background: var(--bg-surface);
        }

        .scope-pill {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(157, 78, 221, 0.15);
            border: 1px solid var(--accent-purple);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-family: var(--font-code);
            color: #d8b4fe;
        }

        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .message {
            display: flex;
            flex-direction: column;
            max-width: 85%;
            gap: 6px;
        }

        .message.user {
            align-self: flex-end;
        }

        .message.assistant {
            align-self: flex-start;
        }

        .msg-sender {
            font-size: 0.75rem;
            font-family: var(--font-code);
            font-weight: 600;
        }

        .message.user .msg-sender {
            color: var(--accent-green);
            text-align: right;
        }

        .message.assistant .msg-sender {
            color: var(--accent-cyan);
        }

        .msg-bubble {
            padding: 14px 18px;
            border-radius: 8px;
            font-size: 0.92rem;
            line-height: 1.6;
        }

        .message.user .msg-bubble {
            background: #132a1e;
            border: 1px solid var(--accent-green);
            color: #e2fced;
        }

        .message.assistant .msg-bubble {
            background: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text-main);
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }

        .msg-bubble pre {
            background: #090d16;
            border: 1px solid #1e293b;
            padding: 12px;
            border-radius: 6px;
            margin: 10px 0;
            overflow-x: auto;
            font-family: var(--font-code);
            font-size: 0.85rem;
            color: var(--accent-cyan);
        }

        .msg-bubble code {
            font-family: var(--font-code);
            background: rgba(0, 229, 255, 0.1);
            padding: 2px 5px;
            border-radius: 4px;
            color: var(--accent-cyan);
        }

        /* Input area */
        .input-bar {
            padding: 16px 24px;
            background: var(--bg-surface);
            border-top: 1px solid var(--border);
            display: flex;
            gap: 12px;
        }

        .input-bar input {
            flex: 1;
            background: var(--bg-card);
            border: 1px solid var(--border);
            color: #fff;
            padding: 14px 18px;
            border-radius: 8px;
            font-size: 0.95rem;
            font-family: var(--font-ui);
            outline: none;
            transition: all 0.2s;
        }

        .input-bar input:focus {
            border-color: var(--accent-cyan);
            box-shadow: 0 0 10px rgba(0, 229, 255, 0.2);
        }

        .btn-send {
            background: var(--accent-cyan);
            color: #000;
            font-weight: 700;
            border: none;
            padding: 0 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.95rem;
            transition: all 0.2s;
        }

        .btn-send:hover {
            box-shadow: 0 0 15px var(--accent-cyan);
        }

        .loading-spinner {
            display: inline-block;
            width: 14px;
            height: 14px;
            border: 2px solid rgba(0,255,136,0.3);
            border-radius: 50%;
            border-top-color: var(--accent-green);
            animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <!-- Sidebar -->
    <div class="sidebar">
        <div class="brand">
            <div class="brand-logo">CK</div>
            <div class="brand-text">
                <h1>CODER-KALI</h1>
                <p>IA TÁCTICA LINUX // WEB UI</p>
            </div>
        </div>

        <button class="btn-new-chat" onclick="startNewSession()">➕ NUEVA AUDITORÍA</button>

        <div class="status-badge">
            <div><strong>MODELO ACTIVO:</strong></div>
            <span id="activeModelBadge">Cargando...</span>
        </div>

        <div class="section-title">HISTORIAL DE SESIONES</div>
        <div class="session-list" id="sessionList">
            <!-- Sesiones cargadas dinámicamente -->
        </div>
    </div>

    <!-- Main Workspace -->
    <div class="main-workspace">
        <div class="topbar">
            <div class="scope-pill">
                <span>🎯 ALCANCE / SOW:</span>
                <strong id="activeScopeLabel">Modo Libre</strong>
            </div>
            <div style="display: flex; gap: 10px;">
                <button onclick="refreshData()" style="background: transparent; border: 1px solid var(--border); color: var(--text-muted); padding: 6px 12px; border-radius: 6px; cursor: pointer;">🔄 Actualizar</button>
            </div>
        </div>

        <div class="chat-container" id="chatBox">
            <div class="message assistant">
                <div class="msg-sender">🤖 CODER-KALI</div>
                <div class="msg-bubble">
                    ¡Bienvenido al <strong>Centro de Operaciones Visual de Coder-Kali</strong>!<br><br>
                    Escribe tu objetivo de auditoría, reconocimiento web, escaneo de vulnerabilidades o administración de sistemas en el panel inferior.
                </div>
            </div>
        </div>

        <div class="input-bar">
            <input type="text" id="userInput" placeholder="Ej: Realiza un reconocimiento y auditoría de cabeceras en binsperu.pe..." onkeypress="handleKey(event)">
            <button class="btn-send" id="sendBtn" onclick="sendMessage()">EJECUTAR</button>
        </div>
    </div>

    <script>
        let currentSessionId = null;

        async function fetchStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                document.getElementById('activeModelBadge').innerText = data.model + " (" + data.provider.toUpperCase() + ")";
                document.getElementById('activeScopeLabel').innerText = data.scope || "Modo Libre";
            } catch (e) {
                console.error(e);
            }
        }

        async function loadSessions() {
            try {
                const res = await fetch('/api/sessions');
                const sessions = await res.json();
                const container = document.getElementById('sessionList');
                container.innerHTML = '';
                sessions.forEach(s => {
                    const item = document.createElement('div');
                    item.className = `session-item ${s.id === currentSessionId ? 'active' : ''}`;
                    item.onclick = () => loadSession(s.id);
                    item.innerHTML = `
                        <div class="title">${s.title}</div>
                        <div class="meta">${s.model.split('/').pop()} • ${s.message_count} msgs</div>
                    `;
                    container.appendChild(item);
                });
            } catch (e) {
                console.error(e);
            }
        }

        async function loadSession(id) {
            currentSessionId = id;
            loadSessions();
            try {
                const res = await fetch(`/api/session?id=${id}`);
                const data = await res.json();
                renderMessages(data.messages || []);
            } catch (e) {
                console.error(e);
            }
        }

        function renderMessages(messages) {
            const box = document.getElementById('chatBox');
            box.innerHTML = '';
            messages.forEach(m => {
                if (m.role === 'system' || m.content.startsWith('[RESULTADOS_SISTEMA')) return;
                appendMessage(m.role, m.content);
            });
            box.scrollTop = box.scrollHeight;
        }

        function appendMessage(role, text) {
            const box = document.getElementById('chatBox');
            const msgDiv = document.createElement('div');
            msgDiv.className = `message ${role}`;
            
            const formatted = text
                .replace(/<ejecutar_comando>([\s\S]*?)<\/ejecutar_comando>/g, '<pre><code>$1</code></pre>')
                .replace(/\n/g, '<br>');

            msgDiv.innerHTML = `
                <div class="msg-sender">${role === 'user' ? '👤 OPERADOR' : '🤖 CODER-KALI'}</div>
                <div class="msg-bubble">${formatted}</div>
            `;
            box.appendChild(msgDiv);
            box.scrollTop = box.scrollHeight;
        }

        async function sendMessage() {
            const input = document.getElementById('userInput');
            const text = input.value.trim();
            if (!text) return;

            input.value = '';
            appendMessage('user', text);

            const btn = document.getElementById('sendBtn');
            btn.innerHTML = '<div class="loading-spinner"></div>';
            btn.disabled = true;

            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: text, session_id: currentSessionId })
                });
                const data = await res.json();
                if (data.session_id) currentSessionId = data.session_id;
                appendMessage('assistant', data.response);
                loadSessions();
            } catch (e) {
                appendMessage('assistant', 'Error de conexión con el backend: ' + e);
            } finally {
                btn.innerHTML = 'EJECUTAR';
                btn.disabled = false;
            }
        }

        function handleKey(e) {
            if (e.key === 'Enter') sendMessage();
        }

        function startNewSession() {
            currentSessionId = null;
            const box = document.getElementById('chatBox');
            box.innerHTML = `
                <div class="message assistant">
                    <div class="msg-sender">🤖 CODER-KALI</div>
                    <div class="msg-bubble">Nueva sesión iniciada. ¿Cuál es el siguiente objetivo?</div>
                </div>
            `;
            loadSessions();
        }

        function refreshData() {
            fetchStatus();
            loadSessions();
        }

        fetchStatus();
        loadSessions();
    </script>
</body>
</html>
"""


class CoderKaliHTTPHandler(BaseHTTPRequestHandler):
    """Manejador de endpoints HTTP y API para el Dashboard Visual."""

    def log_message(self, format, *args):
        # Silenciar logs ruidosos de peticiones HTTP en consola
        return

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_DASHBOARD.encode("utf-8"))
            return

        elif path == "/api/status":
            config_mgr = ConfigManager()
            scope_mgr = ScopeManager()
            data = {
                "provider": config_mgr.get_active_provider(),
                "model": config_mgr.get_active_model(),
                "scope": scope_mgr.get_active_scope_name(),
            }
            self._send_json(data)
            return

        elif path == "/api/sessions":
            session_mgr = SessionManager()
            sessions = session_mgr.list_sessions()
            result = [
                {
                    "id": s.id,
                    "title": s.title,
                    "model": s.model,
                    "provider": s.provider,
                    "updated_at": s.updated_at,
                    "message_count": len([m for m in s.messages if m.get("role") == "user"]),
                }
                for s in sessions
            ]
            self._send_json(result)
            return

        elif path == "/api/session":
            sess_id = query.get("id", [None])[0]
            if not sess_id:
                self.send_error(400, "Falta el parámetro id")
                return
            session_mgr = SessionManager()
            sess = session_mgr.get_session(sess_id)
            if sess:
                self._send_json(sess.to_dict())
            else:
                self.send_error(404, "Sesión no encontrada")
            return

        self.send_error(404, "Ruta no encontrada")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body.decode("utf-8"))
            except Exception:
                self.send_error(400, "JSON inválido")
                return

            prompt = data.get("prompt", "")
            session_id = data.get("session_id")

            config_mgr = ConfigManager()
            session_mgr = SessionManager()
            scope_mgr = ScopeManager()

            agent = KaliAgent(
                config_mgr=config_mgr,
                session_mgr=session_mgr,
                scope_mgr=scope_mgr,
                session_id=session_id,
            )

            # Ejecutar consulta a través del agente
            response_text = agent.send_message(prompt)

            self._send_json({
                "response": response_text,
                "session_id": agent.current_session.id,
            })
            return

        self.send_error(404, "Ruta no encontrada")

    def _send_json(self, data: Any):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))


def start_web_server(port: int = 7777, open_browser: bool = True):
    """Inicia el servidor Web Dashboard de Coder-Kali."""
    server_address = ("127.0.0.1", port)
    try:
        httpd = HTTPServer(server_address, CoderKaliHTTPHandler)
    except OSError:
        port = port + 1
        server_address = ("127.0.0.1", port)
        httpd = HTTPServer(server_address, CoderKaliHTTPHandler)

    url = f"http://localhost:{port}"
    console.print(f"\n[bold green]⚡ Panel Visual Web de Coder-Kali Activo en:[/bold green] [bold cyan]{url}[/bold cyan]")
    console.print("[dim]Presiona Ctrl+C en esta terminal para detener el servidor web.[/dim]\n")

    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        console.print("\n[bold yellow][*] Servidor web detenido.[/bold yellow]")
        httpd.server_close()

"""
coder_kali/web_server.py - Centro de Operaciones Visual y Web UI Táctica para Blood-Cipher.
Diseño Negro y Blanco con Ave Fénix de Código, Modo Planificación con botón PROCEED, confirmaciones modales y streaming en tiempo real.
"""

import os
import json
import time
import socket
import threading
import subprocess
import webbrowser
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Optional, Dict, Any, List

from rich.console import Console

from coder_kali.config import ConfigManager, DEFAULT_PROVIDERS
from coder_kali.agent import KaliAgent
from coder_kali.session_manager import SessionManager
from coder_kali.scope_manager import ScopeManager
from coder_kali.system_executor import SystemExecutor, ParsedAction
from coder_kali.model_discovery import fetch_live_models, fetch_online_models

console = Console()

HTML_DASHBOARD = r"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BLOOD-CIPHER // Autonomous Cyber Operations v1.5</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Outfit:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <style>
        :root {
            --bg-base: #020408;
            --bg-surface: #070a10;
            --bg-card: #0d121c;
            --bg-card-hover: #131a28;
            --border: #1a2333;
            --border-light: #26334a;
            --border-focus: #ffffff;
            --accent-white: #ffffff;
            --accent-silver: #cbd5e1;
            --accent-green: #00ff9d;
            --accent-cyan: #00f0ff;
            --accent-red: #ff3366;
            --text-main: #ffffff;
            --text-muted: #94a3b8;
            --text-dim: #64748b;
            --font-ui: 'Outfit', -apple-system, sans-serif;
            --font-code: 'Fira Code', monospace;
            --glow-white: 0 0 25px rgba(255, 255, 255, 0.25);
            --glow-green: 0 0 20px rgba(0, 255, 157, 0.3);
            --glow-cyan: 0 0 20px rgba(0, 240, 255, 0.3);
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            background-color: var(--bg-base);
            color: var(--text-main);
            font-family: var(--font-ui);
            display: flex;
            height: 100vh;
            overflow: hidden;
            background-image: 
                radial-gradient(circle at 10% 10%, rgba(255, 255, 255, 0.03) 0%, transparent 40%),
                radial-gradient(circle at 90% 90%, rgba(255, 255, 255, 0.02) 0%, transparent 40%);
        }

        /* Scrollbars */
        ::-webkit-scrollbar { width: 5px; height: 5px; }
        ::-webkit-scrollbar-track { background: rgba(0,0,0,0.5); }
        ::-webkit-scrollbar-thumb { background: var(--border-light); border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #fff; }

        /* Left Sidebar */
        .sidebar {
            width: 320px;
            background: var(--bg-surface);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            padding: 20px;
            gap: 16px;
            z-index: 10;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 14px;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--border);
        }

        .brand-logo-phoenix {
            width: 46px;
            height: 46px;
            background: #000000;
            border: 1px solid rgba(255,255,255,0.25);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: var(--glow-white);
            flex-shrink: 0;
        }

        .brand-logo-phoenix svg {
            width: 28px;
            height: 28px;
            fill: #ffffff;
            filter: drop-shadow(0 0 4px rgba(255,255,255,0.8));
        }

        .brand-text h1 {
            font-size: 1.22rem;
            font-weight: 900;
            letter-spacing: 2px;
            color: #ffffff;
            text-shadow: 0 0 10px rgba(255,255,255,0.3);
        }

        .brand-text p {
            font-size: 0.7rem;
            color: var(--accent-silver);
            font-family: var(--font-code);
            font-weight: 600;
            letter-spacing: 0.5px;
        }

        .btn-action {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            padding: 12px 16px;
            border-radius: 8px;
            font-family: var(--font-ui);
            font-weight: 700;
            font-size: 0.9rem;
            cursor: pointer;
            border: none;
            transition: all 0.2s ease;
        }

        .btn-new-chat {
            background: #ffffff;
            color: #000000;
            box-shadow: 0 4px 15px rgba(255, 255, 255, 0.2);
        }

        .btn-new-chat:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 22px rgba(255, 255, 255, 0.4);
            background: #f1f5f9;
        }

        /* Planning Mode Toggle Pill */
        .mode-toggle-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 10px 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .mode-toggle-label {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.8rem;
            font-weight: 700;
            color: #ffffff;
        }

        .toggle-switch {
            position: relative;
            display: inline-block;
            width: 42px;
            height: 22px;
        }

        .toggle-switch input { opacity: 0; width: 0; height: 0; }

        .slider {
            position: absolute;
            cursor: pointer;
            top: 0; left: 0; right: 0; bottom: 0;
            background-color: var(--border-light);
            transition: .3s;
            border-radius: 22px;
        }

        .slider:before {
            position: absolute;
            content: "";
            height: 16px; width: 16px;
            left: 3px; bottom: 3px;
            background-color: white;
            transition: .3s;
            border-radius: 50%;
        }

        input:checked + .slider {
            background-color: var(--accent-green);
        }

        input:checked + .slider:before {
            transform: translateX(20px);
            background-color: #000;
        }

        .status-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px 14px;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .status-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 0.75rem;
        }

        .status-row .label { color: var(--text-muted); display: flex; align-items: center; gap: 6px; }
        .status-row .val { font-family: var(--font-code); font-weight: 600; color: #ffffff; }

        .nav-tabs-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 6px;
        }

        .btn-tab {
            background: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text-main);
            padding: 9px;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn-tab:hover, .btn-tab.active {
            border-color: #ffffff;
            background: var(--bg-card-hover);
            color: #ffffff;
        }

        .section-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-dim);
        }

        .btn-del-all {
            background: transparent;
            border: none;
            color: var(--text-dim);
            cursor: pointer;
            font-size: 0.72rem;
            transition: all 0.2s;
        }

        .btn-del-all:hover { color: var(--accent-red); }

        .session-list {
            flex: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 8px;
            padding-right: 4px;
        }

        .session-item {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 10px 12px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .session-item:hover {
            border-color: var(--border-light);
            background: var(--bg-card-hover);
            transform: translateX(3px);
        }

        .session-item.active {
            border-color: #ffffff;
            background: rgba(255, 255, 255, 0.05);
            box-shadow: 0 0 15px rgba(255, 255, 255, 0.1);
        }

        .session-item .session-item-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 6px;
        }

        .session-item .s-title {
            font-size: 0.85rem;
            font-weight: 600;
            color: #fff;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            flex: 1;
        }

        .btn-del-session {
            background: transparent;
            border: none;
            color: var(--text-dim);
            cursor: pointer;
            padding: 3px 6px;
            border-radius: 4px;
            font-size: 0.75rem;
            opacity: 0.5;
            transition: all 0.2s;
        }

        .session-item:hover .btn-del-session { opacity: 1; }
        .btn-del-session:hover { color: var(--accent-red); background: rgba(255, 51, 102, 0.15); transform: scale(1.15); }

        .session-item .s-meta {
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 0.7rem;
            color: var(--text-muted);
            font-family: var(--font-code);
        }

        /* Workspace */
        .workspace {
            flex: 1;
            display: flex;
            flex-direction: column;
            height: 100vh;
            position: relative;
            background: var(--bg-base);
        }

        .topbar {
            height: 65px;
            background: var(--bg-surface);
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 28px;
            z-index: 5;
        }

        .topbar-left { display: flex; align-items: center; gap: 14px; }

        .badge-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-family: var(--font-code);
            font-weight: 600;
        }

        .badge-scope {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-light);
            color: #ffffff;
        }

        .badge-engine {
            background: rgba(0, 255, 157, 0.08);
            border: 1px solid var(--accent-green);
            color: var(--accent-green);
        }

        .topbar-actions { display: flex; align-items: center; gap: 10px; }

        .btn-icon {
            background: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text-muted);
            width: 38px;
            height: 38px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn-icon:hover { color: #fff; border-color: #ffffff; background: var(--bg-card-hover); }

        /* Quick Tools Toolbar */
        .quick-tools-bar {
            background: var(--bg-surface);
            border-bottom: 1px solid var(--border);
            padding: 8px 28px;
            display: flex;
            align-items: center;
            gap: 10px;
            overflow-x: auto;
        }

        .tool-chip {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 5px 12px;
            font-size: 0.78rem;
            font-weight: 600;
            color: var(--text-muted);
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            white-space: nowrap;
            transition: all 0.2s;
        }

        .tool-chip:hover {
            border-color: #ffffff;
            color: #fff;
            background: rgba(255, 255, 255, 0.06);
        }

        .view-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        /* Chat Stream */
        .chat-stream {
            flex: 1;
            overflow-y: auto;
            padding: 28px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .chat-msg {
            display: flex;
            flex-direction: column;
            max-width: 88%;
            gap: 8px;
            animation: fadeIn 0.25s ease-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .chat-msg.user { align-self: flex-end; }
        .chat-msg.assistant { align-self: flex-start; }

        .msg-header {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.78rem;
            font-family: var(--font-code);
            font-weight: 700;
        }

        .chat-msg.user .msg-header { color: #ffffff; flex-direction: row-reverse; }
        .chat-msg.assistant .msg-header { color: var(--accent-silver); }

        .msg-body {
            padding: 16px 20px;
            border-radius: 10px;
            font-size: 0.95rem;
            line-height: 1.65;
            word-break: break-word;
        }

        .chat-msg.user .msg-body {
            background: #111622;
            border: 1px solid var(--border-light);
            color: #ffffff;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
        }

        .chat-msg.assistant .msg-body {
            background: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text-main);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.6);
        }

        /* Rich Markdown Typography & Styles */
        .msg-body h1, .msg-body h2, .msg-body h3, .msg-body h4 {
            color: #ffffff;
            font-weight: 800;
            margin: 16px 0 10px 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .msg-body h1 { font-size: 1.25rem; border-bottom: 1px solid var(--border-light); padding-bottom: 6px; }
        .msg-body h2 { font-size: 1.12rem; border-bottom: 1px dashed rgba(255,255,255,0.15); padding-bottom: 5px; }
        .msg-body h3 { font-size: 1.02rem; color: var(--accent-silver); }
        .msg-body h4 { font-size: 0.92rem; color: var(--accent-green); }

        .msg-body p {
            margin-bottom: 12px;
            line-height: 1.7;
        }

        .msg-body p:last-child {
            margin-bottom: 0;
        }

        .msg-body ul, .msg-body ol {
            margin: 8px 0 14px 22px;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .msg-body li {
            line-height: 1.6;
        }

        .msg-body strong {
            color: #ffffff;
            font-weight: 700;
        }

        .msg-body table {
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
            background: #050811;
            border: 1px solid var(--border-light);
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        }

        .msg-body th, .msg-body td {
            padding: 10px 14px;
            text-align: left;
            border-bottom: 1px solid var(--border);
            font-size: 0.88rem;
        }

        .msg-body th {
            background: #0e1526;
            color: #ffffff;
            font-weight: 800;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.8px;
        }

        .msg-body tr:nth-child(even) {
            background: rgba(255, 255, 255, 0.02);
        }

        .msg-body tr:hover {
            background: rgba(255, 255, 255, 0.04);
        }

        .msg-body blockquote {
            border-left: 3px solid var(--accent-green);
            background: rgba(0, 255, 157, 0.05);
            padding: 10px 16px;
            margin: 12px 0;
            border-radius: 0 8px 8px 0;
            color: #cbd5e1;
            font-size: 0.92rem;
        }

        .msg-body code {
            font-family: var(--font-code);
            background: rgba(255, 255, 255, 0.08);
            color: var(--accent-green);
            padding: 2px 7px;
            border-radius: 4px;
            font-size: 0.85rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .msg-body pre {
            background: #000000;
            border: 1px solid var(--border-light);
            border-radius: 8px;
            padding: 14px;
            margin: 12px 0;
            overflow-x: auto;
            position: relative;
        }

        .msg-body pre code {
            background: transparent;
            color: #ffffff;
            padding: 0;
            border: none;
            font-size: 0.85rem;
            line-height: 1.5;
        }

        .msg-body hr {
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            margin: 18px 0;
        }

        .msg-body a {
            color: var(--accent-cyan);
            text-decoration: none;
            border-bottom: 1px dashed var(--accent-cyan);
        }

        .msg-body a:hover {
            color: #ffffff;
            border-bottom-style: solid;
        }

        /* Implementation Plan Card (Antigravity Style) */
        .plan-card {
            background: #090e18;
            border: 1px solid rgba(255, 255, 255, 0.25);
            border-radius: 10px;
            padding: 18px 22px;
            margin: 12px 0;
            display: flex;
            flex-direction: column;
            gap: 14px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.6);
        }

        .plan-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--border);
            padding-bottom: 10px;
        }

        .plan-card-header h3 {
            font-size: 1rem;
            font-weight: 800;
            color: #ffffff;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .plan-card-content {
            font-size: 0.9rem;
            line-height: 1.6;
            color: #e2e8f0;
            white-space: pre-wrap;
        }

        .btn-proceed {
            background: linear-gradient(135deg, var(--accent-green) 0%, #00cc7a 100%);
            color: #000000;
            font-weight: 900;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 0.95rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            box-shadow: var(--glow-green);
            transition: all 0.2s;
        }

        .btn-proceed:hover {
            transform: scale(1.02);
            box-shadow: 0 0 25px rgba(0, 255, 157, 0.6);
        }

        /* Live Terminal Boxes */
        .terminal-box {
            background: #000000;
            border: 1px solid var(--border-light);
            border-radius: 8px;
            margin: 12px 0;
            overflow: hidden;
            box-shadow: 0 6px 20px rgba(0,0,0,0.6);
        }

        .terminal-box-header {
            background: #080c14;
            padding: 8px 14px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--border);
            font-family: var(--font-code);
            font-size: 0.78rem;
            color: var(--text-muted);
        }

        .terminal-box-header .tag { color: #ffffff; font-weight: 700; display: flex; align-items: center; gap: 6px; }
        .terminal-box-header .badge-run { background: rgba(255, 255, 255, 0.1); color: #ffffff; padding: 2px 6px; border-radius: 4px; }

        .terminal-box-code {
            padding: 14px;
            font-family: var(--font-code);
            font-size: 0.85rem;
            color: #ffffff;
            overflow-x: auto;
            white-space: pre-wrap;
            line-height: 1.5;
            background: #000000;
        }

        /* Input Controls */
        .input-container {
            background: var(--bg-surface);
            border-top: 1px solid var(--border);
            padding: 18px 28px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .input-box {
            display: flex;
            align-items: center;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 6px 14px;
            transition: all 0.2s;
            box-shadow: 0 4px 15px rgba(0,0,0,0.4);
        }

        .input-box:focus-within {
            border-color: #ffffff;
            box-shadow: 0 0 15px rgba(255, 255, 255, 0.2);
        }

        .input-box input {
            flex: 1;
            background: transparent;
            border: none;
            color: #fff;
            font-size: 1rem;
            font-family: var(--font-ui);
            padding: 10px 8px;
            outline: none;
        }

        .input-box input::placeholder { color: var(--text-dim); }

        .btn-submit {
            background: #ffffff;
            color: #000000;
            font-weight: 800;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-family: var(--font-ui);
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s;
        }

        .btn-submit:hover { box-shadow: var(--glow-white); transform: scale(1.02); }
        .btn-submit:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

        /* Recon Scanner Visual View */
        .recon-view {
            flex: 1;
            overflow-y: auto;
            padding: 28px;
            display: none;
            flex-direction: column;
            gap: 20px;
        }

        .recon-header {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 20px;
            display: flex;
            gap: 12px;
            align-items: center;
        }

        .recon-header input {
            flex: 1;
            background: var(--bg-surface);
            border: 1px solid var(--border-light);
            color: #fff;
            padding: 12px 16px;
            border-radius: 8px;
            font-family: var(--font-code);
            font-size: 0.95rem;
            outline: none;
        }

        .recon-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
        }

        .recon-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 18px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .recon-card h4 {
            font-size: 0.95rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 8px;
            color: #ffffff;
        }

        .recon-card .card-body {
            font-family: var(--font-code);
            font-size: 0.8rem;
            color: var(--text-muted);
            background: var(--bg-surface);
            padding: 12px;
            border-radius: 6px;
            min-height: 80px;
            max-height: 160px;
            overflow-y: auto;
            white-space: pre-wrap;
        }

        /* Minimal 3-Dot Neural Thinking Indicator */
        .minimal-thinking {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            padding: 10px 16px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        }

        .neural-dots-wave {
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .neural-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #ffffff;
            box-shadow: 0 0 8px rgba(255,255,255,0.8);
            animation: neuralBounce 1.2s infinite ease-in-out both;
        }

        .neural-dot:nth-child(1) { animation-delay: -0.32s; }
        .neural-dot:nth-child(2) { animation-delay: -0.16s; }
        .neural-dot:nth-child(3) { animation-delay: 0s; }

        @keyframes neuralBounce {
            0%, 80%, 100% { transform: scale(0.4) translateY(0); opacity: 0.3; }
            40% { transform: scale(1.2) translateY(-4px); opacity: 1; }
        }

        .thinking-context-text {
            font-family: var(--font-code);
            font-size: 0.8rem;
            font-weight: 600;
            color: #ffffff;
            letter-spacing: 0.5px;
        }

        /* Modals */
        .modal-overlay {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.85);
            backdrop-filter: blur(8px);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 100;
        }

        .modal-card {
            background: var(--bg-surface);
            border: 1px solid var(--border-light);
            border-radius: 12px;
            width: 90%;
            max-width: 550px;
            max-height: 85vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: 0 20px 50px rgba(0,0,0,0.9);
            animation: modalPop 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }

        @keyframes modalPop {
            from { transform: scale(0.94); opacity: 0; }
            to { transform: scale(1); opacity: 1; }
        }

        .modal-header {
            padding: 18px 24px;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .modal-header h3 { font-size: 1.1rem; font-weight: 800; display: flex; align-items: center; gap: 10px; color: #fff; }
        .modal-body { padding: 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 18px; }

        .form-group { display: flex; flex-direction: column; gap: 8px; }
        .form-group label { font-size: 0.85rem; font-weight: 600; color: var(--text-muted); }
        .form-group select, .form-group input, .form-group textarea {
            background: var(--bg-card);
            border: 1px solid var(--border);
            color: #fff;
            padding: 12px 14px;
            border-radius: 8px;
            font-family: var(--font-ui);
            font-size: 0.92rem;
            outline: none;
            transition: all 0.2s;
        }

        .form-group select:focus, .form-group input:focus, .form-group textarea:focus {
            border-color: #ffffff;
            box-shadow: 0 0 10px rgba(255,255,255,0.2);
        }

        .form-group textarea { font-family: var(--font-code); font-size: 0.85rem; min-height: 120px; resize: vertical; }
        .modal-footer { padding: 16px 24px; border-top: 1px solid var(--border); display: flex; justify-content: flex-end; gap: 10px; }

        .spinner {
            width: 16px;
            height: 16px;
            border: 2px solid rgba(0,0,0,0.3);
            border-top-color: #000;
            border-radius: 50%;
            animation: spin 0.7s linear infinite;
        }

        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body>

    <!-- Sidebar -->
    <div class="sidebar">
        <div class="brand">
            <div class="brand-logo-phoenix">
                <!-- SVG Code Phoenix Vector Logo -->
                <svg viewBox="0 0 24 24">
                    <path d="M12 2L9 7L12 9L15 7L12 2Z" />
                    <path d="M3 10L8 12L7 16L2 11L3 10Z" />
                    <path d="M21 10L16 12L17 16L22 11L21 10Z" />
                    <path d="M12 11L9 15L12 22L15 15L12 11Z" />
                    <path d="M6 5L8 9L5 8L6 5Z" />
                    <path d="M18 5L16 9L19 8L18 5Z" />
                </svg>
            </div>
            <div class="brand-text">
                <h1>BLOOD-CIPHER</h1>
                <p>AUTONOMOUS OPERATIONS v1.5</p>
            </div>
        </div>

        <button class="btn-action btn-new-chat" onclick="startNewSession()">
            <i class="fa-solid fa-plus"></i> NUEVA AUDITORÍA
        </button>

        <!-- Planning Mode Toggle -->
        <div class="mode-toggle-card">
            <div class="mode-toggle-label">
                <i class="fa-solid fa-list-check" style="color: #ffffff;"></i>
                <span>Modo Plan (Antigravity)</span>
            </div>
            <label class="toggle-switch">
                <input type="checkbox" id="planningModeSwitch" onchange="togglePlanningMode()">
                <span class="slider"></span>
            </label>
        </div>

        <div class="status-card">
            <div class="status-row">
                <span class="label"><i class="fa-solid fa-microchip"></i> IA ACTIVA</span>
                <span class="val" id="sbProvider">...</span>
            </div>
            <div class="status-row">
                <span class="label"><i class="fa-solid fa-brain"></i> MODELO</span>
                <span class="val" id="sbModel" style="max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">...</span>
            </div>
        </div>

        <div class="nav-tabs-grid">
            <button class="btn-tab active" id="tabBtnChat" onclick="switchView('chat')"><i class="fa-solid fa-comments"></i> Chat</button>
            <button class="btn-tab" id="tabBtnRecon" onclick="switchView('recon')"><i class="fa-solid fa-satellite-dish"></i> Scanner</button>
            <button class="btn-tab" id="tabBtnCreds" onclick="switchView('creds')"><i class="fa-solid fa-key"></i> Creds</button>
            <button class="btn-tab" id="tabBtnVulns" onclick="switchView('vulns')"><i class="fa-solid fa-shield-virus"></i> Vulns</button>
            <button class="btn-tab" id="tabBtnNet" onclick="switchView('net')"><i class="fa-solid fa-network-wired"></i> Net</button>
            <button class="btn-tab" onclick="openConfigModal()"><i class="fa-solid fa-gear"></i> Config</button>
        </div>

        <div class="section-header">
            <span><i class="fa-solid fa-clock-rotate-left"></i> Sesiones (<span id="sessionCount" style="color: #ffffff;">0</span>)</span>
            <button class="btn-del-all" title="Limpiar todas las sesiones" onclick="promptClearAllSessions()"><i class="fa-solid fa-trash"></i> Vaciar</button>
        </div>

        <div class="session-list" id="sessionList">
            <!-- Sesiones cargadas vía JS -->
        </div>
    </div>

    <!-- Main Workspace -->
    <div class="workspace">
        <div class="topbar">
            <div class="topbar-left">
                <div class="badge-pill badge-scope" onclick="openScopeModal()" style="cursor: pointer;">
                    <i class="fa-solid fa-bullseye"></i> ALCANCE: <strong id="topScopeLabel">MODO LIBRE</strong>
                </div>
                <div class="badge-pill badge-engine" id="modeBadge">
                    <i class="fa-solid fa-bolt"></i> MODO RÁPIDO
                </div>
            </div>
            <div class="topbar-actions">
                <button class="btn-icon" title="Ajustes de IA" onclick="openConfigModal()"><i class="fa-solid fa-sliders"></i></button>
                <button class="btn-icon" title="Refrescar Estado" onclick="refreshAll()"><i class="fa-solid fa-arrows-rotate"></i></button>
            </div>
        </div>

        <!-- Quick Access Pentest Tools -->
        <div class="quick-tools-bar">
            <div class="tool-chip" onclick="quickPrompt('Realiza un reconocimiento pasivo y escaneo de puertos nmap rápido a ')">
                <i class="fa-solid fa-network-wired"></i> Nmap Scan
            </div>
            <div class="tool-chip" onclick="quickPrompt('Inspecciona cabeceras HTTP, WAF y tecnologías con curl y whatweb en ')">
                <i class="fa-solid fa-globe"></i> WhatWeb
            </div>
            <div class="tool-chip" onclick="quickPrompt('Descubre subdominios activos usando assetfinder y subfinder para ')">
                <i class="fa-solid fa-sitemap"></i> Subdomains
            </div>
            <div class="tool-chip" onclick="quickPrompt('Ejecuta un escaneo de vulnerabilidades con nuclei contra ')">
                <i class="fa-solid fa-radiation"></i> Nuclei
            </div>
            <div class="tool-chip" onclick="switchView('creds')">
                <i class="fa-solid fa-key" style="color: var(--accent-green);"></i> Hash Cracker
            </div>
            <div class="tool-chip" onclick="switchView('vulns')">
                <i class="fa-solid fa-shield-virus" style="color: var(--accent-cyan);"></i> Vuln Scanner
            </div>
            <div class="tool-chip" onclick="switchView('net')">
                <i class="fa-solid fa-ethernet" style="color: var(--accent-green);"></i> Net Audit
            </div>
        </div>

        <!-- Chat View -->
        <div class="view-content" id="chatView">
            <div class="chat-stream" id="chatStream">
                <div class="chat-msg assistant">
                    <div class="msg-header"><i class="fa-solid fa-shield-halved"></i> BLOOD-CIPHER // NÚCLEO AUTÓNOMO</div>
                    <div class="msg-body">
                        ¡Bienvenido a <strong>Blood-Cipher v1.5</strong>!<br><br>
                        Plataforma autónoma de auditoría de seguridad y reconocimiento de infraestructura.<br>
                        Escribe tu objetivo abajo o activa el <strong>Modo Plan</strong> en el panel lateral.
                    </div>
                </div>
            </div>

            <!-- Input Bar -->
            <div class="input-container">
                <div class="input-box">
                    <i class="fa-solid fa-chevron-right" style="color: #ffffff; margin-right: 8px;"></i>
                    <input type="text" id="promptInput" placeholder="Ej: Realiza un reconocimiento completo de arquitectura y cabeceras en binsperu.pe..." onkeypress="handleKey(event)">
                    <button class="btn-submit" id="submitBtn" onclick="submitPrompt()">
                        <span>EJECUTAR</span> <i class="fa-solid fa-arrow-right"></i>
                    </button>
                </div>
            </div>
        </div>

        <!-- Recon Scanner Visual View -->
        <div class="recon-view" id="reconView">
            <div class="recon-header">
                <i class="fa-solid fa-crosshairs" style="color: #ffffff; font-size: 1.2rem;"></i>
                <input type="text" id="reconTargetInput" placeholder="Ingresa un dominio o IP objetivo (ej. binsperu.pe)...">
                <button class="btn-submit" id="btnRunScan" onclick="runVisualScan()"><i class="fa-solid fa-radar"></i> LANZAR ESCANEO 360°</button>
            </div>
            <div class="recon-grid">
                <div class="recon-card">
                    <h4><i class="fa-solid fa-network-wired"></i> Puertos y Servicios (Nmap)</h4>
                    <div class="card-body" id="rcNmap">Esperando escaneo...</div>
                </div>
                <div class="recon-card">
                    <h4><i class="fa-solid fa-globe"></i> Tecnologías Web (WhatWeb)</h4>
                    <div class="card-body" id="rcWhatWeb">Esperando escaneo...</div>
                </div>
                <div class="recon-card">
                    <h4><i class="fa-solid fa-shield-virus"></i> Cabeceras de Seguridad</h4>
                    <div class="card-body" id="rcHeaders">Esperando escaneo...</div>
                </div>
                <div class="recon-card">
                    <h4><i class="fa-solid fa-sitemap"></i> Subdominios Activos</h4>
                    <div class="card-body" id="rcSubs">Esperando escaneo...</div>
                </div>
            </div>
        </div>

        <!-- Credentials Audit View -->
        <div class="recon-view" id="credsView">
            <div class="recon-header" style="flex-wrap: wrap; gap: 10px;">
                <i class="fa-solid fa-key" style="color: var(--accent-green); font-size: 1.2rem;"></i>
                <textarea id="credsHashInput" placeholder="Pega uno o más hashes (uno por línea)...
Ej: 5f4dcc3b5aa765d61d8327deb882cf99
admin:$1$salt$hashvalue
user:e10adc3949ba59abbe56e057f20f883e" style="flex: 1; min-width: 300px; min-height: 80px; resize: vertical; background: var(--bg-surface); border: 1px solid var(--border-light); color: #fff; padding: 12px; border-radius: 8px; font-family: var(--font-code); font-size: 0.85rem;"></textarea>
                <div style="display: flex; flex-direction: column; gap: 8px; min-width: 200px;">
                    <select id="credsHashType" style="background: var(--bg-card); border: 1px solid var(--border); color: #fff; padding: 8px 12px; border-radius: 6px; font-size: 0.82rem;">
                        <option value="auto">Auto-Detectar Tipo</option>
                        <option value="MD5">MD5</option>
                        <option value="SHA1">SHA1</option>
                        <option value="SHA256">SHA256</option>
                        <option value="SHA512">SHA512</option>
                        <option value="NTLM">NTLM</option>
                    </select>
                    <select id="credsMethod" style="background: var(--bg-card); border: 1px solid var(--border); color: #fff; padding: 8px 12px; border-radius: 6px; font-size: 0.82rem;">
                        <option value="native">Python Nativo (Built-in)</option>
                        <option value="john">John the Ripper</option>
                        <option value="hashcat">Hashcat (GPU)</option>
                    </select>
                </div>
                <button class="btn-submit" id="btnCrackHash" onclick="runCredAudit()"><i class="fa-solid fa-unlock-keyhole"></i> CRACKEAR</button>
            </div>
            <div style="padding: 8px 0;">
                <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
                    <span style="font-size: 0.8rem; color: var(--text-muted);">Análisis rápido:</span>
                    <input type="text" id="credsPwAnalyze" placeholder="Escribe una contraseña para analizar su fortaleza..." style="flex: 1; background: var(--bg-card); border: 1px solid var(--border); color: #fff; padding: 8px 12px; border-radius: 6px; font-family: var(--font-code); font-size: 0.85rem; min-width: 200px;" onkeypress="if(event.key==='Enter') analyzePassword()">
                    <button class="btn-tab" onclick="analyzePassword()" style="white-space: nowrap;"><i class="fa-solid fa-chart-bar"></i> Analizar</button>
                </div>
            </div>
            <div id="credsStrengthResult" style="display: none; background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 14px; margin-bottom: 10px;"></div>
            <div class="recon-grid" id="credsResultsGrid">
                <div class="recon-card" style="grid-column: 1 / -1;">
                    <h4><i class="fa-solid fa-table-list"></i> Resultados de Cracking</h4>
                    <div class="card-body" id="credsResults" style="min-height: 120px; max-height: 400px;">Esperando hashes para crackear...</div>
                </div>
            </div>
        </div>

        <!-- Vulnerability Scanner View -->
        <div class="recon-view" id="vulnsView">
            <div class="recon-header">
                <i class="fa-solid fa-shield-virus" style="color: var(--accent-cyan); font-size: 1.2rem;"></i>
                <input type="text" id="vulnsTargetInput" placeholder="Dominio o IP objetivo (ej. example.com)...">
                <select id="vulnsScanType" style="background: var(--bg-card); border: 1px solid var(--border); color: #fff; padding: 12px; border-radius: 8px; font-size: 0.85rem; min-width: 180px;">
                    <option value="all">Auditítoria Completa</option>
                    <option value="headers">Cabeceras HTTP</option>
                    <option value="ssl">SSL/TLS Audit</option>
                    <option value="cms">CMS Detection</option>
                    <option value="nuclei">Nuclei Scan</option>
                    <option value="nikto">Nikto Scan</option>
                </select>
                <button class="btn-submit" id="btnRunVulns" onclick="runVulnScan()"><i class="fa-solid fa-shield-halved"></i> LANZAR AUDITORÍA</button>
            </div>
            <div class="recon-grid" id="vulnsResultsGrid">
                <div class="recon-card">
                    <h4><i class="fa-solid fa-shield-virus" style="color: var(--accent-cyan);"></i> Cabeceras de Seguridad</h4>
                    <div class="card-body" id="vulnsHeaders">Esperando escaneo...</div>
                </div>
                <div class="recon-card">
                    <h4><i class="fa-solid fa-lock" style="color: var(--accent-green);"></i> SSL/TLS Audit</h4>
                    <div class="card-body" id="vulnsSsl">Esperando escaneo...</div>
                </div>
                <div class="recon-card">
                    <h4><i class="fa-solid fa-code" style="color: #ffffff;"></i> CMS & Tecnologías</h4>
                    <div class="card-body" id="vulnsCms">Esperando escaneo...</div>
                </div>
                <div class="recon-card">
                    <h4><i class="fa-solid fa-radiation" style="color: var(--accent-red);"></i> Nuclei / Nikto Findings</h4>
                    <div class="card-body" id="vulnsFindings" style="max-height: 250px;">Esperando escaneo...</div>
                </div>
            </div>
        </div>

        <!-- Network Audit View -->
        <div class="recon-view" id="netView">
            <div class="recon-header" style="flex-wrap: wrap; gap: 10px;">
                <i class="fa-solid fa-ethernet" style="color: var(--accent-green); font-size: 1.2rem;"></i>
                <input type="text" id="netTargetInput" placeholder="IP, rango CIDR o dominio (ej. 192.168.1.0/24 o example.com)..." style="flex: 1; min-width: 250px;">
                <select id="netScanType" style="background: var(--bg-card); border: 1px solid var(--border); color: #fff; padding: 12px; border-radius: 8px; font-size: 0.85rem; min-width: 180px;">
                    <option value="ports">Port Scan Avanzado</option>
                    <option value="discovery">Host Discovery</option>
                    <option value="services">Service Enumeration</option>
                    <option value="os">OS Detection</option>
                    <option value="dns">DNS Enumeration</option>
                    <option value="traceroute">Traceroute</option>
                </select>
                <select id="netPorts" style="background: var(--bg-card); border: 1px solid var(--border); color: #fff; padding: 12px; border-radius: 8px; font-size: 0.85rem; min-width: 140px;">
                    <option value="top1000">Top 1000 Ports</option>
                    <option value="top100">Top 100 Ports</option>
                    <option value="full">All 65535 Ports</option>
                    <option value="1-1000">1-1000</option>
                    <option value="80,443,8080,8443">Web Ports</option>
                </select>
                <button class="btn-submit" id="btnRunNet" onclick="runNetAudit()"><i class="fa-solid fa-tower-broadcast"></i> EJECUTAR ANÁLISIS</button>
            </div>
            <div class="recon-grid" id="netResultsGrid">
                <div class="recon-card" style="grid-column: 1 / -1;">
                    <h4><i class="fa-solid fa-terminal"></i> Resultado del Análisis de Red</h4>
                    <div class="card-body" id="netResults" style="min-height: 120px; max-height: 500px;">Esperando análisis...</div>
                </div>
                <div class="recon-card">
                    <h4><i class="fa-solid fa-server"></i> Puertos / Hosts Detectados</h4>
                    <div class="card-body" id="netParsed" style="min-height: 80px;">-</div>
                </div>
                <div class="recon-card">
                    <h4><i class="fa-solid fa-circle-info"></i> Datos Parseados</h4>
                    <div class="card-body" id="netExtra" style="min-height: 80px;">-</div>
                </div>
            </div>
        </div>
    </div>

    <!-- Modal: Confirmación Personalizada de Eliminación -->
    <div class="modal-overlay" id="confirmDeleteModal">
        <div class="modal-card" style="max-width: 420px;">
            <div class="modal-header">
                <h3><i class="fa-solid fa-trash-can" style="color: var(--accent-red);"></i> Confirmar Eliminación</h3>
                <button class="btn-icon" onclick="closeModal('confirmDeleteModal')"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="modal-body" style="gap: 14px;">
                <p id="confirmDeleteText" style="font-size: 0.95rem; color: #e2e8f0;">¿Deseas eliminar esta sesión permanentemente?</p>
                <label style="display: flex; align-items: center; gap: 8px; font-size: 0.82rem; color: var(--text-muted); cursor: pointer;">
                    <input type="checkbox" id="chkSkipDeleteConfirm">
                    <span>No volver a preguntar</span>
                </label>
            </div>
            <div class="modal-footer">
                <button class="btn-tab" onclick="closeModal('confirmDeleteModal')">Cancelar</button>
                <button class="btn-action" style="background: var(--accent-red); color: #fff;" onclick="executeConfirmedDelete()">Eliminar</button>
            </div>
        </div>
    </div>

    <!-- Modal: Configuración de IA -->
    <div class="modal-overlay" id="configModal">
        <div class="modal-card">
            <div class="modal-header">
                <h3><i class="fa-solid fa-sliders" style="color: #ffffff;"></i> Configuración de IA y Proveedores</h3>
                <button class="btn-icon" onclick="closeModal('configModal')"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label>Proveedor de Inteligencia Artificial:</label>
                    <select id="cfgProvider" onchange="onProviderChange()">
                        <option value="groq">Groq (Inferencia Ultra Rápida)</option>
                        <option value="gemini">Google Gemini</option>
                        <option value="openai">OpenAI (GPT-4o, o1, o3)</option>
                        <option value="anthropic">Anthropic Claude</option>
                        <option value="deepseek">DeepSeek (R1, Chat)</option>
                        <option value="openrouter">OpenRouter</option>
                        <option value="ollama">Ollama (100% Local / Offline)</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>API Key del Proveedor:</label>
                    <input type="password" id="cfgApiKey" placeholder="Ingresa tu clave de acceso...">
                </div>
                <div class="form-group">
                    <label>Modelo Activo:</label>
                    <input type="text" id="cfgModel" placeholder="Ej: groq/llama-3.3-70b-versatile">
                </div>
                <div style="display: flex; gap: 10px;">
                    <button class="btn-tab" style="flex: 1;" onclick="discoverOnlineModels()"><i class="fa-solid fa-cloud-arrow-down"></i> Descubrir Modelos Disponibles</button>
                </div>
                <div class="form-group" id="discoveredModelsGroup" style="display: none;">
                    <label>Modelos Disponibles con tu API Key:</label>
                    <select id="cfgDiscoveredSelect" onchange="document.getElementById('cfgModel').value = this.value;"></select>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn-tab" onclick="closeModal('configModal')">Cancelar</button>
                <button class="btn-action btn-new-chat" onclick="saveConfiguration()">Guardar Configuración</button>
            </div>
        </div>
    </div>

    <!-- Modal: Gestor de Alcance / SOW -->
    <div class="modal-overlay" id="scopeModal">
        <div class="modal-card">
            <div class="modal-header">
                <h3><i class="fa-solid fa-crosshairs" style="color: #ffffff;"></i> Documento de Alcance (SOW / ROE)</h3>
                <button class="btn-icon" onclick="closeModal('scopeModal')"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label>Nombre del Objetivo / Proyecto:</label>
                    <input type="text" id="scopeName" placeholder="Ej: binsperu_audit">
                </div>
                <div class="form-group">
                    <label>Texto del Documento de Autorización / Scope:</label>
                    <textarea id="scopeContent" placeholder="Pega aquí el documento de autorización formal con los objetivos In-Scope y exclusiones Out-of-Scope..."></textarea>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn-tab" onclick="deactivateScope()" style="color: var(--accent-red);"><i class="fa-solid fa-ban"></i> Modo Libre (Sin Scope)</button>
                <button class="btn-action btn-new-chat" onclick="saveScopeDocument()"><i class="fa-solid fa-check"></i> Activar Alcance</button>
            </div>
        </div>
    </div>

    <script>
        let currentSessionId = null;
        let isPlanningMode = false;
        let pendingDeleteId = null;
        let isDeleteAllAction = false;

        function togglePlanningMode() {
            isPlanningMode = document.getElementById('planningModeSwitch').checked;
            const badge = document.getElementById('modeBadge');
            if (isPlanningMode) {
                badge.innerHTML = '<i class="fa-solid fa-list-check"></i> MODO PLANIFICACIÓN ACTIVO';
                badge.style.borderColor = '#ffffff';
                badge.style.color = '#ffffff';
            } else {
                badge.innerHTML = '<i class="fa-solid fa-bolt"></i> MODO RÁPIDO';
                badge.style.borderColor = 'var(--accent-green)';
                badge.style.color = 'var(--accent-green)';
            }
        }

        function switchView(view) {
            ['chat','recon','creds','vulns','net'].forEach(v => {
                const btn = document.getElementById('tabBtn' + v.charAt(0).toUpperCase() + v.slice(1));
                if (btn) btn.classList.toggle('active', view === v);
            });
            document.getElementById('chatView').style.display = view === 'chat' ? 'flex' : 'none';
            document.getElementById('reconView').style.display = view === 'recon' ? 'flex' : 'none';
            document.getElementById('credsView').style.display = view === 'creds' ? 'flex' : 'none';
            document.getElementById('vulnsView').style.display = view === 'vulns' ? 'flex' : 'none';
            document.getElementById('netView').style.display = view === 'net' ? 'flex' : 'none';
        }

        async function fetchStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                document.getElementById('sbProvider').innerText = (data.provider || 'desconocido').toUpperCase();
                document.getElementById('sbModel').innerText = (data.model || 'no configurado').split('/').pop();
                document.getElementById('topScopeLabel').innerText = (data.scope || 'MODO LIBRE').toUpperCase();
            } catch (e) { console.error(e); }
        }

        async function loadSessions() {
            try {
                const res = await fetch('/api/sessions');
                const sessions = await res.json();
                const list = document.getElementById('sessionList');
                document.getElementById('sessionCount').innerText = sessions.length;
                list.innerHTML = '';
                sessions.forEach(s => {
                    const item = document.createElement('div');
                    item.className = `session-item ${s.id === currentSessionId ? 'active' : ''}`;
                    item.onclick = () => loadSession(s.id);
                    item.innerHTML = `
                        <div class="session-item-row">
                            <div class="s-title"><i class="fa-regular fa-message" style="color: #ffffff; margin-right: 6px;"></i>${escapeHtml(s.title)}</div>
                            <button class="btn-del-session" title="Eliminar sesión" onclick="promptDeleteSession(event, '${s.id}')"><i class="fa-solid fa-trash-can"></i></button>
                        </div>
                        <div class="s-meta">
                            <span>${s.model.split('/').pop()}</span>
                            <span>${s.message_count} msgs</span>
                        </div>
                    `;
                    list.appendChild(item);
                });
            } catch (e) { console.error(e); }
        }

        function promptDeleteSession(e, id) {
            e.stopPropagation();
            if (localStorage.getItem('coderkali_skip_delete_confirm') === 'true') {
                performDeleteSession(id);
                return;
            }
            pendingDeleteId = id;
            isDeleteAllAction = false;
            document.getElementById('confirmDeleteText').innerText = '¿Deseas eliminar permanentemente esta sesión del historial?';
            openModal('confirmDeleteModal');
        }

        function promptClearAllSessions() {
            if (localStorage.getItem('coderkali_skip_delete_confirm') === 'true') {
                performClearAllSessions();
                return;
            }
            isDeleteAllAction = true;
            document.getElementById('confirmDeleteText').innerText = '¿Deseas vaciar TODO el historial de sesiones guardadas?';
            openModal('confirmDeleteModal');
        }

        async function executeConfirmedDelete() {
            if (document.getElementById('chkSkipDeleteConfirm').checked) {
                localStorage.setItem('coderkali_skip_delete_confirm', 'true');
            }
            closeModal('confirmDeleteModal');

            if (isDeleteAllAction) {
                await performClearAllSessions();
            } else if (pendingDeleteId) {
                await performDeleteSession(pendingDeleteId);
            }
        }

        async function performDeleteSession(id) {
            try {
                await fetch(`/api/sessions?action=delete&id=${id}`, { method: 'POST' });
                if (currentSessionId === id) {
                    startNewSession();
                } else {
                    loadSessions();
                }
            } catch (err) {
                console.error(err);
            }
        }

        async function performClearAllSessions() {
            try {
                await fetch('/api/sessions?action=clear_all', { method: 'POST' });
                startNewSession();
            } catch (err) {
                console.error(err);
            }
        }

        async function loadSession(id) {
            currentSessionId = id;
            loadSessions();
            try {
                const res = await fetch(`/api/session?id=${id}`);
                const data = await res.json();
                const stream = document.getElementById('chatStream');
                stream.innerHTML = '';
                (data.messages || []).forEach(m => {
                    if (m.role === 'system' || (m.content && m.content.startsWith('[RESULTADOS_SISTEMA'))) return;
                    renderBubble(m.role, m.content);
                });
                stream.scrollTop = stream.scrollHeight;
            } catch (e) { console.error(e); }
        }

        function renderBubble(role, rawContent) {
            const stream = document.getElementById('chatStream');
            const msgDiv = document.createElement('div');
            msgDiv.className = `chat-msg ${role}`;

            if (role === 'user') {
                msgDiv.innerHTML = `
                    <div class="msg-header"><i class="fa-solid fa-user-shield"></i> OPERADOR</div>
                    <div class="msg-body">${escapeHtml(rawContent).replace(/\n/g, '<br>')}</div>
                `;
                stream.appendChild(msgDiv);
                stream.scrollTop = stream.scrollHeight;
                return;
            }

            let text = rawContent || '';
            
            // 0. Limpieza exhaustiva de bloques de razonamiento/pensamiento interno
            text = text.replace(/<think>[\s\S]*?<\/think>/gi, '');
            text = text.replace(/```(?:thought|thinking|reasoning)[\s\S]*?```/gi, '');
            text = text.replace(/^\s*<think>[\s\S]*$/gi, '');
            text = text.trim();

            const placeholders = {};
            let pIndex = 0;

            // 1. Extraer planes de acción
            text = text.replace(/<plan_de_accion>([\s\S]*?)<\/plan_de_accion>/g, function(match, planText) {
                const key = `%%PLAN_BLOCK_${pIndex++}%%`;
                const renderedPlan = typeof marked !== 'undefined' ? marked.parse(planText.trim()) : escapeHtml(planText.trim());
                placeholders[key] = `<div class="plan-card">
                    <div class="plan-card-header">
                        <h3><i class="fa-solid fa-list-check"></i> PLAN DE IMPLEMENTACIÓN TÁCTICO</h3>
                        <span class="badge-pill badge-engine">ESPERANDO AUTORIZACIÓN</span>
                    </div>
                    <div class="plan-card-content">${renderedPlan}</div>
                    <button class="btn-proceed" onclick="proceedWithPlan()"><i class="fa-solid fa-bolt"></i> PROCEED / AUTORIZAR Y EJECUTAR</button>
                </div>`;
                return `\n\n${key}\n\n`;
            });

            // 2. Extraer creación de archivos <escribir_archivo ruta="...">
            text = text.replace(/<escribir_archivo\s+ruta=(?:"([^"]+)"|'([^']+)'|([^\s>]+))>([\s\S]*?)<\/escribir_archivo>/gi, function(match, p1, p2, p3, content) {
                const ruta = p1 || p2 || p3 || "script";
                const key = `%%FILE_BLOCK_${pIndex++}%%`;
                const cleanContent = content.trim();
                placeholders[key] = `<div class="plan-card" style="border-color: #00d2ff; background: rgba(0, 210, 255, 0.04);">
                    <div class="plan-card-header">
                        <h3 style="color: #00d2ff;"><i class="fa-solid fa-file-code"></i> ARCHIVO GENERADO: ${escapeHtml(ruta)}</h3>
                        <span class="badge-pill badge-engine" style="border-color: #00d2ff; color: #00d2ff;">SCRIPT LISTO</span>
                    </div>
                    <pre style="background: #050811; padding: 12px; border-radius: 8px; border: 1px solid var(--border-light); max-height: 250px; overflow: auto; font-family: var(--font-code); font-size: 0.82rem; color: #f3f4f6;"><code>${escapeHtml(cleanContent)}</code></pre>
                </div>`;
                return `\n\n${key}\n\n`;
            });

            // 3. Extraer comandos XML <ejecutar_comando>
            text = text.replace(/<ejecutar_comando>([\s\S]*?)<\/ejecutar_comando>/g, function(match, cmd) {
                const key = `%%CMD_BLOCK_${pIndex++}%%`;
                const cleanCmd = cmd.trim();
                placeholders[key] = `<div class="terminal-box">
                    <div class="terminal-box-header">
                        <span class="tag"><i class="fa-solid fa-terminal"></i> COMANDO EN TERMINAL</span>
                        <span class="badge-run">EJECUTADO</span>
                    </div>
                    <div class="terminal-box-code">${escapeHtml(cleanCmd)}</div>
                </div>`;
                return `\n\n${key}\n\n`;
            });

            // 4. Extraer llamadas JSON crudas (ej: {"cmd": [...]})
            text = text.replace(/\{[^{}]*"(?:cmd|command|bash|exec)"\s*:\s*(\[[^\]]*\]|"[^"]*")[^{}]*\}/g, function(match) {
                try {
                    let parsed = JSON.parse(match);
                    let cmdVal = parsed.cmd || parsed.command || parsed.bash || parsed.exec;
                    let cmdStr = "";
                    if (Array.isArray(cmdVal)) {
                        if (cmdVal.length >= 3 && (cmdVal[0].includes('bash') || cmdVal[0].includes('sh')) && (cmdVal[1] === '-c' || cmdVal[1] === '-lc')) {
                            cmdStr = cmdVal[2];
                        } else {
                            cmdStr = cmdVal.join(' ');
                        }
                    } else if (typeof cmdVal === 'string') {
                        cmdStr = cmdVal;
                    }
                    if (cmdStr) {
                        const key = `%%JSON_BLOCK_${pIndex++}%%`;
                        placeholders[key] = `<div class="terminal-box">
                            <div class="terminal-box-header">
                                <span class="tag"><i class="fa-solid fa-terminal"></i> COMANDO EN TERMINAL</span>
                                <span class="badge-run">EJECUTADO</span>
                            </div>
                            <div class="terminal-box-code">${escapeHtml(cmdStr.trim())}</div>
                        </div>`;
                        return `\n\n${key}\n\n`;
                    }
                } catch(e) {}
                return match;
            });

            // 5. Renderizar Markdown con marked.js
            let parsedHtml = '';
            if (typeof marked !== 'undefined') {
                marked.setOptions({
                    breaks: true,
                    gfm: true
                });
                parsedHtml = marked.parse(text);
            } else {
                parsedHtml = escapeHtml(text).replace(/\n/g, '<br>');
            }

            // 6. Reemplazar los placeholders por sus componentes HTML
            for (const [key, val] of Object.entries(placeholders)) {
                parsedHtml = parsedHtml.replace(new RegExp(key, 'g'), val);
            }

            msgDiv.innerHTML = `
                <div class="msg-header"><i class="fa-solid fa-shield-halved"></i> BLOOD-CIPHER</div>
                <div class="msg-body">${parsedHtml}</div>
            `;
            stream.appendChild(msgDiv);
            stream.scrollTop = stream.scrollHeight;

            if (typeof hljs !== 'undefined') {
                msgDiv.querySelectorAll('pre code').forEach((block) => {
                    hljs.highlightElement(block);
                });
            }
        }

        function escapeHtml(text) {
            return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
        }

        function updateThinkingStatus(statusText) {
            const el = document.getElementById('thinkingStatusText');
            if (el) {
                el.innerText = statusText;
            }
        }

        function appendLiveActionPreview(action) {
            const el = document.getElementById('thinkingActionsLog');
            if (!el) return;
            const item = document.createElement('div');
            item.style.cssText = "font-size: 0.76rem; font-family: var(--font-code); color: var(--accent-green); display: flex; align-items: center; gap: 6px; padding: 3px 0; border-bottom: 1px dashed rgba(255,255,255,0.06);";
            const icon = action.type === "command" ? '<i class="fa-solid fa-terminal" style="color:#ffffff;"></i>' : '<i class="fa-solid fa-file-code" style="color:#00d2ff;"></i>';
            const text = action.command || action.target_path || "Acción ejecutada";
            item.innerHTML = `${icon} <span>${escapeHtml(text)}</span> <span style="color:#00ff9d; margin-left:auto;">[✓]</span>`;
            el.appendChild(item);
            el.scrollTop = el.scrollHeight;
        }

        function showThinkingBubble(promptText) {
            const stream = document.getElementById('chatStream');
            removeThinkingBubble();

            // Extraer dinámicamente el objetivo o acción del prompt
            let targetLabel = "OBJETIVO";
            const urlMatch = promptText.match(/(?:https?:\/\/)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/);
            if (urlMatch) {
                targetLabel = urlMatch[1];
            } else if (promptText.length < 30) {
                targetLabel = promptText;
            }

            const msgDiv = document.createElement('div');
            msgDiv.id = 'thinkingBubble';
            msgDiv.className = 'chat-msg assistant';
            msgDiv.innerHTML = `
                <div class="minimal-thinking" style="flex-direction: column; align-items: flex-start; gap: 8px; max-width: 100%;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div class="neural-dots-wave">
                            <div class="neural-dot"></div>
                            <div class="neural-dot"></div>
                            <div class="neural-dot"></div>
                        </div>
                        <span class="thinking-context-text" id="thinkingStatusText">Analizando ${escapeHtml(targetLabel)}...</span>
                    </div>
                    <div id="thinkingActionsLog" style="width: 100%; max-height: 140px; overflow-y: auto; padding-left: 28px; display: flex; flex-direction: column; gap: 2px;"></div>
                </div>
            `;
            stream.appendChild(msgDiv);
            stream.scrollTop = stream.scrollHeight;
        }

        function removeThinkingBubble() {
            const existing = document.getElementById('thinkingBubble');
            if (existing) existing.remove();
        }

        async function submitPrompt() {
            const input = document.getElementById('promptInput');
            const text = input.value.trim();
            if (!text) return;

            input.value = '';
            renderBubble('user', text);
            showThinkingBubble(text);

            const btn = document.getElementById('submitBtn');
            btn.innerHTML = '<div class="spinner"></div>';
            btn.disabled = true;

            try {
                const res = await fetch('/api/chat_stream', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        prompt: text,
                        session_id: currentSessionId,
                        planning_mode: isPlanningMode
                    })
                });

                if (!res.ok) {
                    throw new Error(`HTTP error ${res.status}`);
                }

                const reader = res.body.getReader();
                const decoder = new TextDecoder('utf-8');
                let buffer = '';

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n\n');
                    buffer = lines.pop(); // Mantener el último segmento incompleto

                    for (const block of lines) {
                        if (!block.trim()) continue;
                        let eventType = 'message';
                        let dataStr = '';

                        const blockLines = block.split('\n');
                        for (const line of blockLines) {
                            if (line.startsWith('event: ')) {
                                eventType = line.substring(7).trim();
                            } else if (line.startsWith('data: ')) {
                                dataStr = line.substring(6).trim();
                            }
                        }

                        if (dataStr) {
                            try {
                                const parsedData = JSON.parse(dataStr);
                                if (eventType === 'status') {
                                    updateThinkingStatus(parsedData.message);
                                } else if (eventType === 'action') {
                                    appendLiveActionPreview(parsedData);
                                } else if (eventType === 'done') {
                                    removeThinkingBubble();
                                    if (parsedData.session_id) currentSessionId = parsedData.session_id;
                                    renderBubble('assistant', parsedData.response);
                                    loadSessions();
                                }
                            } catch (e) {
                                console.error("Error al parsear SSE:", e, dataStr);
                            }
                        }
                    }
                }
            } catch (e) {
                removeThinkingBubble();
                renderBubble('assistant', 'Error de comunicación: ' + e);
            } finally {
                removeThinkingBubble();
                btn.innerHTML = '<span>EJECUTAR</span> <i class="fa-solid fa-arrow-right"></i>';
                btn.disabled = false;
            }
        }

        function proceedWithPlan() {
            const input = document.getElementById('promptInput');
            input.value = "Proceder y ejecutar el plan táctico autorizado paso a paso.";
            submitPrompt();
        }

        async function runVisualScan() {
            const target = document.getElementById('reconTargetInput').value.trim();
            if (!target) {
                alert('Por favor ingresa un dominio o IP.');
                return;
            }

            document.getElementById('rcNmap').innerText = "Ejecutando Nmap port scan en tiempo real...";
            document.getElementById('rcWhatWeb').innerText = "Inspeccionando tecnologías web...";
            document.getElementById('rcHeaders').innerText = "Analizando cabeceras HTTP y WAF...";
            document.getElementById('rcSubs').innerText = "Enumerando subdominios...";

            try {
                const res = await fetch('/api/visual_scan', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ target: target })
                });
                const data = await res.json();

                document.getElementById('rcNmap').innerText = data.nmap || 'Completado sin salida.';
                document.getElementById('rcWhatWeb').innerText = data.whatweb || 'Completado sin salida.';
                document.getElementById('rcHeaders').innerText = data.headers || 'Completado sin salida.';
                document.getElementById('rcSubs').innerText = data.subdomains || 'Completado sin salida.';
            } catch (e) {
                alert('Error al ejecutar escaneo visual: ' + e);
            }
        }

        function quickPrompt(prefix) {
            switchView('chat');
            const input = document.getElementById('promptInput');
            input.value = prefix;
            input.focus();
        }

        // === CREDENTIAL AUDIT FUNCTIONS ===
        async function runCredAudit() {
            const rawInput = document.getElementById('credsHashInput').value.trim();
            if (!rawInput) { alert('Ingresa al menos un hash para crackear.'); return; }
            const hashType = document.getElementById('credsHashType').value;
            const method = document.getElementById('credsMethod').value;
            const btn = document.getElementById('btnCrackHash');
            btn.innerHTML = '<div class="spinner"></div> Crackeando...';
            btn.disabled = true;
            document.getElementById('credsResults').innerText = 'Procesando hashes con ' + method + '...';
            try {
                const res = await fetch('/api/audit/creds', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ hashes: rawInput, hash_type: hashType, method: method })
                });
                const data = await res.json();
                let html = '';
                if (data.results && data.results.length > 0) {
                    html = '<table style="width:100%;border-collapse:collapse;font-size:0.82rem;">';
                    html += '<tr style="border-bottom:1px solid #26334a;"><th style="text-align:left;padding:6px;color:#fff;">Hash</th><th style="text-align:left;padding:6px;color:#fff;">Tipo</th><th style="text-align:left;padding:6px;color:#fff;">Contraseña</th><th style="padding:6px;color:#fff;">Tiempo</th><th style="padding:6px;color:#fff;">Estado</th></tr>';
                    data.results.forEach(r => {
                        const statusIcon = r.status === 'cracked' ? '✅' : (r.status === 'error' ? '⚠️' : '❌');
                        const pwColor = r.status === 'cracked' ? 'color:#00ff9d;font-weight:700;' : 'color:#64748b;';
                        html += `<tr style="border-bottom:1px solid #1a2333;"><td style="padding:6px;color:#94a3b8;font-family:'Fira Code',monospace;font-size:0.75rem;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${escapeHtml(r.original_hash)}">${escapeHtml(r.original_hash.substring(0,30))}${r.original_hash.length>30?'...':''}</td><td style="padding:6px;color:#00f0ff;">${r.hash_type}</td><td style="padding:6px;${pwColor}">${r.cracked_password || '-'}</td><td style="padding:6px;color:#cbd5e1;text-align:center;">${r.time_seconds}s</td><td style="padding:6px;text-align:center;">${statusIcon}</td></tr>`;
                    });
                    html += '</table>';
                    const cracked = data.results.filter(r => r.status === 'cracked').length;
                    html += `<div style="margin-top:10px;font-size:0.85rem;color:#00ff9d;font-weight:700;">✅ ${cracked}/${data.results.length} hashes crackeados</div>`;
                } else {
                    html = data.error || 'Sin resultados.';
                }
                document.getElementById('credsResults').innerHTML = html;
            } catch (e) {
                document.getElementById('credsResults').innerText = 'Error: ' + e;
            } finally {
                btn.innerHTML = '<i class="fa-solid fa-unlock-keyhole"></i> CRACKEAR';
                btn.disabled = false;
            }
        }

        async function analyzePassword() {
            const pw = document.getElementById('credsPwAnalyze').value.trim();
            if (!pw) return;
            try {
                const res = await fetch('/api/audit/creds', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ analyze_password: pw })
                });
                const data = await res.json();
                if (data.analysis) {
                    const a = data.analysis;
                    const gradeColors = {'A+':'#00ff9d','A':'#00ff9d','B':'#00f0ff','C':'#fbbf24','D':'#f87171','F':'#ff3366'};
                    const barColor = gradeColors[a.grade] || '#fff';
                    const barWidth = Math.max(5, a.score);
                    let html = `<div style="display:flex;align-items:center;gap:14px;margin-bottom:8px;"><span style="font-size:1.8rem;font-weight:900;color:${barColor};">${a.grade}</span><div style="flex:1;"><div style="height:8px;background:#1a2333;border-radius:4px;overflow:hidden;"><div style="height:100%;width:${barWidth}%;background:${barColor};border-radius:4px;transition:width 0.5s;"></div></div></div><span style="font-size:0.9rem;font-weight:700;color:${barColor};">${a.score}/100</span></div>`;
                    html += `<div style="font-size:0.8rem;color:#94a3b8;margin-bottom:6px;">Entropía: ${a.entropy} bits | Longitud: ${a.length} | Mayúsculas: ${a.has_upper?'✅':'❌'} Minúsculas: ${a.has_lower?'✅':'❌'} Números: ${a.has_digits?'✅':'❌'} Especiales: ${a.has_special?'✅':'❌'}</div>`;
                    if (a.is_common) html += '<div style="color:#ff3366;font-weight:700;font-size:0.82rem;">⚠️ Contraseña extremadamente común</div>';
                    if (a.feedback && a.feedback.length) {
                        html += '<div style="margin-top:6px;">' + a.feedback.map(f => `<div style="font-size:0.8rem;color:#cbd5e1;">${escapeHtml(f)}</div>`).join('') + '</div>';
                    }
                    const el = document.getElementById('credsStrengthResult');
                    el.innerHTML = html;
                    el.style.display = 'block';
                }
            } catch (e) { console.error(e); }
        }

        // === VULNERABILITY SCAN FUNCTIONS ===
        async function runVulnScan() {
            const target = document.getElementById('vulnsTargetInput').value.trim();
            if (!target) { alert('Ingresa un dominio o IP objetivo.'); return; }
            const scanType = document.getElementById('vulnsScanType').value;
            const btn = document.getElementById('btnRunVulns');
            btn.innerHTML = '<div class="spinner"></div> Escaneando...';
            btn.disabled = true;
            document.getElementById('vulnsHeaders').innerText = 'Analizando...';
            document.getElementById('vulnsSsl').innerText = 'Auditando...';
            document.getElementById('vulnsCms').innerText = 'Detectando...';
            document.getElementById('vulnsFindings').innerText = 'Escaneando...';
            try {
                const res = await fetch('/api/audit/vulns', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ target: target, scan_type: scanType })
                });
                const data = await res.json();
                if (data.results) {
                    data.results.forEach(r => {
                        if (r.scanner === 'headers') document.getElementById('vulnsHeaders').innerText = r.raw_output || r.title;
                        else if (r.scanner === 'testssl' || r.scanner === 'openssl') document.getElementById('vulnsSsl').innerText = r.raw_output || r.title;
                        else if (r.scanner === 'cms') document.getElementById('vulnsCms').innerText = r.raw_output || r.title;
                        else document.getElementById('vulnsFindings').innerText += '\n' + (r.raw_output || r.title);
                    });
                    // Clear default for findings if nothing was added
                    if (document.getElementById('vulnsFindings').innerText === 'Escaneando...') {
                        document.getElementById('vulnsFindings').innerText = 'Sin hallazgos adicionales.';
                    }
                } else {
                    document.getElementById('vulnsHeaders').innerText = data.error || 'Error';
                }
            } catch (e) {
                document.getElementById('vulnsHeaders').innerText = 'Error: ' + e;
            } finally {
                btn.innerHTML = '<i class="fa-solid fa-shield-halved"></i> LANZAR AUDITORÍA';
                btn.disabled = false;
            }
        }

        // === NETWORK AUDIT FUNCTIONS ===
        async function runNetAudit() {
            const target = document.getElementById('netTargetInput').value.trim();
            if (!target) { alert('Ingresa un objetivo (IP, CIDR o dominio).'); return; }
            const scanType = document.getElementById('netScanType').value;
            const ports = document.getElementById('netPorts').value;
            const btn = document.getElementById('btnRunNet');
            btn.innerHTML = '<div class="spinner"></div> Analizando...';
            btn.disabled = true;
            document.getElementById('netResults').innerText = 'Ejecutando análisis de red...';
            document.getElementById('netParsed').innerText = 'Procesando...';
            document.getElementById('netExtra').innerText = 'Procesando...';
            try {
                const res = await fetch('/api/audit/network', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ target: target, scan_type: scanType, ports: ports })
                });
                const data = await res.json();
                document.getElementById('netResults').innerText = data.raw_output || data.error || 'Completado.';
                if (data.parsed_data) {
                    if (data.parsed_data.open_ports) {
                        document.getElementById('netParsed').innerText = 'Puertos abiertos: ' + data.parsed_data.open_ports.join(', ');
                    } else if (data.parsed_data.hosts) {
                        document.getElementById('netParsed').innerText = 'Hosts activos: ' + data.parsed_data.total + '\n' + data.parsed_data.hosts.map(h => (h.ip || '') + ' ' + (h.hostname || '') + ' ' + (h.mac || '')).join('\n');
                    } else {
                        document.getElementById('netParsed').innerText = JSON.stringify(data.parsed_data, null, 2);
                    }
                    document.getElementById('netExtra').innerText = JSON.stringify(data.parsed_data, null, 2);
                } else {
                    document.getElementById('netParsed').innerText = '-';
                    document.getElementById('netExtra').innerText = '-';
                }
            } catch (e) {
                document.getElementById('netResults').innerText = 'Error: ' + e;
            } finally {
                btn.innerHTML = '<i class="fa-solid fa-tower-broadcast"></i> EJECUTAR ANÁLISIS';
                btn.disabled = false;
            }
        }

        function handleKey(e) {
            if (e.key === 'Enter') submitPrompt();
        }

        function startNewSession() {
            currentSessionId = null;
            switchView('chat');
            const stream = document.getElementById('chatStream');
            stream.innerHTML = `
                <div class="chat-msg assistant">
                    <div class="msg-header"><i class="fa-solid fa-shield-halved"></i> BLOOD-CIPHER</div>
                    <div class="msg-body">Nueva sesión táctica iniciada. ¿Cuál es el objetivo?</div>
                </div>
            `;
            loadSessions();
        }

        function openModal(id) { document.getElementById(id).style.display = 'flex'; }
        function closeModal(id) { document.getElementById(id).style.display = 'none'; }

        async function openConfigModal() {
            try {
                const res = await fetch('/api/config');
                const cfg = await res.json();
                document.getElementById('cfgProvider').value = cfg.provider || 'groq';
                document.getElementById('cfgModel').value = cfg.model || '';
                document.getElementById('cfgApiKey').value = cfg.api_key || '';
                openModal('configModal');
            } catch (e) { console.error(e); }
        }

        async function onProviderChange() {
            const prov = document.getElementById('cfgProvider').value;
            const res = await fetch(`/api/config?provider=${prov}`);
            const data = await res.json();
            document.getElementById('cfgModel').value = data.default_model || '';
            document.getElementById('cfgApiKey').value = data.api_key || '';
        }

        async function discoverOnlineModels() {
            const prov = document.getElementById('cfgProvider').value;
            const key = document.getElementById('cfgApiKey').value;
            const select = document.getElementById('cfgDiscoveredSelect');
            select.innerHTML = '<option>Consultando catálogo...</option>';
            document.getElementById('discoveredModelsGroup').style.display = 'flex';

            try {
                const res = await fetch('/api/discover_models', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ provider: prov, api_key: key })
                });
                const data = await res.json();
                select.innerHTML = '';
                if (data.models && data.models.length > 0) {
                    data.models.forEach(m => {
                        const opt = document.createElement('option');
                        opt.value = m;
                        opt.innerText = m;
                        select.appendChild(opt);
                    });
                    document.getElementById('cfgModel').value = data.models[0];
                } else {
                    select.innerHTML = '<option>No se pudieron listar automáticamente</option>';
                }
            } catch (e) {
                select.innerHTML = '<option>Error al consultar modelos</option>';
            }
        }

        async function saveConfiguration() {
            const prov = document.getElementById('cfgProvider').value;
            const key = document.getElementById('cfgApiKey').value;
            const model = document.getElementById('cfgModel').value;

            try {
                await fetch('/api/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ provider: prov, api_key: key, model: model })
                });
                closeModal('configModal');
                refreshAll();
            } catch (e) { alert('Error: ' + e); }
        }

        async function openScopeModal() {
            try {
                const res = await fetch('/api/scopes');
                const data = await res.json();
                document.getElementById('scopeName').value = data.active_name || '';
                document.getElementById('scopeContent').value = data.active_content || '';
                openModal('scopeModal');
            } catch (e) { console.error(e); }
        }

        async function saveScopeDocument() {
            const name = document.getElementById('scopeName').value.trim();
            const content = document.getElementById('scopeContent').value.trim();
            if (!name || !content) {
                alert('Por favor especifica un nombre y el contenido del alcance.');
                return;
            }

            try {
                await fetch('/api/scopes', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: name, content: content, active: true })
                });
                closeModal('scopeModal');
                refreshAll();
            } catch (e) { alert('Error: ' + e); }
        }

        async function deactivateScope() {
            try {
                await fetch('/api/scopes?action=clear', { method: 'POST' });
                closeModal('scopeModal');
                refreshAll();
            } catch (e) { alert('Error: ' + e); }
        }

        function refreshAll() {
            fetchStatus();
            loadSessions();
        }

        refreshAll();
    </script>
</body>
</html>
"""


class CoderKaliHTTPHandler(BaseHTTPRequestHandler):
    """Manejador HTTP REST para el Dashboard Web."""

    def log_message(self, format, *args):
        return

    def do_GET(self):
        try:
            self._handle_get()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _handle_get(self):
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
            self._send_json({
                "provider": config_mgr.get_active_provider(),
                "model": config_mgr.get_active_model(),
                "scope": scope_mgr.get_active_scope_name(),
            })
            return

        elif path == "/api/config":
            config_mgr = ConfigManager()
            target_prov = query.get("provider", [config_mgr.get_active_provider()])[0]
            prov_data = DEFAULT_PROVIDERS.get(target_prov, {})
            self._send_json({
                "provider": target_prov,
                "model": config_mgr.get_active_model() if target_prov == config_mgr.get_active_provider() else prov_data.get("default_model", ""),
                "api_key": config_mgr.get_api_key(target_prov),
                "default_model": prov_data.get("default_model", ""),
                "available_models": prov_data.get("available_models", []),
            })
            return

        elif path == "/api/scopes":
            scope_mgr = ScopeManager()
            self._send_json({
                "active_name": scope_mgr.get_active_scope_name(),
                "active_content": scope_mgr.get_active_scope_content(),
                "scopes": scope_mgr.list_scopes(),
            })
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
                self.send_error(400, "Falta el id")
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
        try:
            self._handle_post()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _handle_post(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            data = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            data = {}

        if path == "/api/chat_stream":
            prompt = data.get("prompt", "")
            session_id = data.get("session_id")
            planning_mode = data.get("planning_mode", False)

            config_mgr = ConfigManager()
            session_mgr = SessionManager()
            scope_mgr = ScopeManager()
            web_executor = SystemExecutor(auto_approve_safe=True)

            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            def send_event(event_type: str, event_data: Any):
                try:
                    payload = f"event: {event_type}\ndata: {json.dumps(event_data, ensure_ascii=False)}\n\n"
                    self.wfile.write(payload.encode("utf-8"))
                    self.wfile.flush()
                except Exception:
                    pass

            def on_status(status_msg: str):
                send_event("status", {"message": status_msg})

            def on_action(action_data: Dict[str, Any]):
                send_event("action", action_data)

            agent = KaliAgent(
                config_mgr=config_mgr,
                system_executor=web_executor,
                session_mgr=session_mgr,
                scope_mgr=scope_mgr,
                session_id=session_id,
                planning_mode=planning_mode,
                on_status_update=on_status,
                on_action_update=on_action,
            )

            agent.max_tool_iterations = 4
            send_event("status", {"message": "Analizando objetivo e inicializando arsenal táctico..."})
            response_text = agent.send_message(prompt)

            send_event("done", {
                "response": response_text,
                "session_id": agent.current_session.id,
            })
            return

        elif path == "/api/chat":
            prompt = data.get("prompt", "")
            session_id = data.get("session_id")
            planning_mode = data.get("planning_mode", False)

            config_mgr = ConfigManager()
            session_mgr = SessionManager()
            scope_mgr = ScopeManager()

            # Usar ejecutor seguro con auto_approve y timeout ágil para respuestas ultrarrápidas
            web_executor = SystemExecutor(auto_approve_safe=True)

            agent = KaliAgent(
                config_mgr=config_mgr,
                system_executor=web_executor,
                session_mgr=session_mgr,
                scope_mgr=scope_mgr,
                session_id=session_id,
                planning_mode=planning_mode,
            )

            # Limitar iteraciones automáticas por turno en la web para máxima velocidad
            agent.max_tool_iterations = 3
            response_text = agent.send_message(prompt)

            self._send_json({
                "response": response_text,
                "session_id": agent.current_session.id,
            })
            return

        elif path == "/api/visual_scan":
            target = data.get("target", "").strip()
            # Limpiar target
            clean_target = target.replace("https://", "").replace("http://", "").split("/")[0]

            def run_cmd(cmd_list, timeout=12):
                try:
                    res = subprocess.run(cmd_list, capture_output=True, text=True, timeout=timeout)
                    return res.stdout.strip() or res.stderr.strip()
                except Exception as e:
                    return f"Error / Timeout: {e}"

            # Ejecutar escaneos rápidos concurrentes
            nmap_res = run_cmd(["nmap", "-F", "-T4", clean_target])
            whatweb_res = run_cmd(["whatweb", f"http://{clean_target}"])
            headers_res = run_cmd(["curl", "-I", "-s", "-L", f"https://{clean_target}"])
            sub_res = run_cmd(["assetfinder", "--subs-only", clean_target], timeout=8)

            self._send_json({
                "nmap": nmap_res,
                "whatweb": whatweb_res,
                "headers": headers_res,
                "subdomains": sub_res,
            })
            return

        elif path == "/api/config":
            config_mgr = ConfigManager()
            provider = data.get("provider")
            api_key = data.get("api_key")
            model = data.get("model")

            if provider:
                config_mgr.set("provider", provider)
                if api_key is not None:
                    config_mgr.set_api_key(provider, api_key.strip())
                if model:
                    config_mgr.set("model", model.strip())

            self._send_json({"success": True})
            return

        elif path == "/api/sessions":
            action = query.get("action", [None])[0]
            session_mgr = SessionManager()

            if action == "delete":
                sess_id = query.get("id", [None])[0] or data.get("id")
                if sess_id:
                    session_mgr.delete_session(sess_id)
                    self._send_json({"success": True, "deleted": sess_id})
                    return
                else:
                    self.send_error(400, "Falta el id de sesión")
                    return
            elif action == "clear_all":
                for s in session_mgr.list_sessions():
                    session_mgr.delete_session(s.id)
                self._send_json({"success": True})
                return

            self.send_error(400, "Acción desconocida")
            return

        elif path == "/api/discover_models":
            provider = data.get("provider", "groq")
            api_key = data.get("api_key", "")
            models = fetch_online_models(provider, api_key)
            self._send_json({"models": models})
            return

        elif path == "/api/scopes":
            action = query.get("action", [None])[0]
            scope_mgr = ScopeManager()

            if action == "clear":
                scope_mgr.clear_active_scope()
                self._send_json({"success": True})
                return

            name = data.get("name")
            content = data.get("content")
            if name and content:
                saved = scope_mgr.save_scope(name, content)
                scope_mgr.set_active_scope(saved)
                self._send_json({"success": True, "name": saved})
            else:
                self.send_error(400, "Nombre y contenido requeridos")
            return

        elif path == "/api/audit/creds":
            try:
                from coder_kali.audit_modules import CredentialAuditor
                auditor = CredentialAuditor()

                # Mode: Password strength analysis
                if data.get("analyze_password"):
                    analysis = auditor.analyze_password(data["analyze_password"])
                    self._send_json({"analysis": analysis.to_dict()})
                    return

                # Mode: Hash cracking
                raw_hashes = data.get("hashes", "")
                hash_type = data.get("hash_type", "auto")
                method = data.get("method", "native")

                lines = [l.strip() for l in raw_hashes.strip().splitlines() if l.strip()]
                results = []

                for line in lines:
                    # Parse user:hash format
                    h = line
                    if ":" in line and not line.startswith("$"):
                        parts = line.split(":", 1)
                        h = parts[1].strip() if parts[1].strip() else parts[0].strip()

                    ht = hash_type if hash_type != "auto" else None

                    if method == "john":
                        result = auditor.crack_with_john(h, hash_format=ht)
                    elif method == "hashcat":
                        result = auditor.crack_with_hashcat(h)
                    else:
                        result = auditor.crack_hash_native(h, hash_type=ht)

                    results.append(result.to_dict())

                self._send_json({"results": results})
            except Exception as e:
                self._send_json({"error": str(e)})
            return

        elif path == "/api/audit/vulns":
            try:
                from coder_kali.audit_modules import VulnerabilityScanner
                scanner = VulnerabilityScanner()
                target = data.get("target", "").strip()
                scan_type = data.get("scan_type", "all")

                if not target:
                    self._send_json({"error": "Target requerido"})
                    return

                results = []
                if scan_type == "all":
                    vuln_results = scanner.quick_vuln_scan(target)
                    results = [r.to_dict() for r in vuln_results]
                elif scan_type == "headers":
                    results = [scanner.header_analysis(target).to_dict()]
                elif scan_type == "ssl":
                    results = [scanner.ssl_audit(target).to_dict()]
                elif scan_type == "cms":
                    results = [scanner.cms_detection(target).to_dict()]
                elif scan_type == "nuclei":
                    results = [scanner.nuclei_scan(target).to_dict()]
                elif scan_type == "nikto":
                    results = [scanner.nikto_scan(target).to_dict()]

                self._send_json({"results": results})
            except Exception as e:
                self._send_json({"error": str(e)})
            return

        elif path == "/api/audit/network":
            try:
                from coder_kali.audit_modules import NetworkAuditor
                net_auditor = NetworkAuditor()
                target = data.get("target", "").strip()
                scan_type = data.get("scan_type", "ports")
                ports = data.get("ports", "top1000")

                if not target:
                    self._send_json({"error": "Target requerido"})
                    return

                result = None
                if scan_type == "ports":
                    result = net_auditor.advanced_port_scan(target, ports=ports)
                elif scan_type == "discovery":
                    result = net_auditor.host_discovery(target)
                elif scan_type == "services":
                    result = net_auditor.service_enumeration(target)
                elif scan_type == "os":
                    result = net_auditor.os_detection(target)
                elif scan_type == "dns":
                    result = net_auditor.dns_enumeration(target)
                elif scan_type == "traceroute":
                    result = net_auditor.traceroute_analysis(target)
                else:
                    result = net_auditor.advanced_port_scan(target, ports=ports)

                if result:
                    self._send_json(result.to_dict())
                else:
                    self._send_json({"error": "No se pudo ejecutar el análisis"})
            except Exception as e:
                self._send_json({"error": str(e)})
            return

        self.send_error(404, "Ruta no encontrada")

    def _send_json(self, data: Any):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))


from http.server import HTTPServer, SimpleHTTPRequestHandler, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def start_web_server(port: int = 7777, open_browser: bool = True):
    """Inicia el servidor Web Dashboard multi-hilo de Blood-Cipher."""
    httpd = None
    for attempt_port in range(port, port + 10):
        try:
            server_address = ("127.0.0.1", attempt_port)
            httpd = ThreadingHTTPServer(server_address, CoderKaliHTTPHandler)
            port = attempt_port
            break
        except OSError:
            continue

    if not httpd:
        console.print(f"[bold red][!] No se pudo enlazar el servidor web en el rango de puertos {port}-{port+10}.[/bold red]")
        return

    url = f"http://localhost:{port}"
    console.print(f"\n[bold white]⚡ Centro de Operaciones Blood-Cipher Activo (Multi-Hilo):[/bold white] [bold cyan]{url}[/bold cyan]")
    console.print("[dim]Presiona Ctrl+C en esta terminal para detener el servidor.[/dim]\n")

    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        console.print("\n[bold yellow][*] Servidor web detenido.[/bold yellow]")
    finally:
        try:
            httpd.server_close()
        except Exception:
            pass

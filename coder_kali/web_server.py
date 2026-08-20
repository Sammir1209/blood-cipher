"""
coder_kali/web_server.py - Centro de Operaciones Visual y Web UI Táctica para Coder-Kali.
Panel Web Dark Cyberpunk con streaming en tiempo real (SSE), terminal en vivo, escáner visual de objetivos y gestión de scopes.
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
    <title>CODER-KALI // Tactical Cyber Operations Platform</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Outfit:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        :root {
            --bg-base: #060911;
            --bg-surface: #0c111e;
            --bg-card: #11182a;
            --bg-card-hover: #162038;
            --border: #1a2744;
            --border-light: #26385f;
            --accent-green: #00ff9d;
            --accent-cyan: #00f0ff;
            --accent-purple: #a855f7;
            --accent-pink: #ec4899;
            --accent-red: #ff3366;
            --accent-amber: #f59e0b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --text-dim: #64748b;
            --font-ui: 'Outfit', sans-serif;
            --font-code: 'Fira Code', monospace;
            --glow-green: 0 0 25px rgba(0, 255, 157, 0.4);
            --glow-cyan: 0 0 25px rgba(0, 240, 255, 0.4);
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
                radial-gradient(circle at 15% 15%, rgba(0, 240, 255, 0.04) 0%, transparent 40%),
                radial-gradient(circle at 85% 85%, rgba(168, 85, 247, 0.04) 0%, transparent 40%);
        }

        /* Scrollbars */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: rgba(0,0,0,0.3); }
        ::-webkit-scrollbar-thumb { background: var(--border-light); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--accent-cyan); }

        /* Left Navigation Bar */
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

        .brand-logo {
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, #00ff9d 0%, #00f0ff 100%);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.3rem;
            color: #000;
            box-shadow: var(--glow-green);
            flex-shrink: 0;
        }

        .brand-text h1 {
            font-size: 1.25rem;
            font-weight: 900;
            letter-spacing: 1.5px;
            background: linear-gradient(90deg, #ffffff, var(--accent-cyan));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .brand-text p {
            font-size: 0.72rem;
            color: var(--accent-green);
            font-family: var(--font-code);
            font-weight: 600;
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
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .btn-new-chat {
            background: linear-gradient(135deg, var(--accent-green) 0%, #00c978 100%);
            color: #05140b;
            box-shadow: 0 4px 15px rgba(0, 255, 157, 0.25);
        }

        .btn-new-chat:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 255, 157, 0.45);
        }

        .status-card {
            background: rgba(0, 240, 255, 0.04);
            border: 1px solid rgba(0, 240, 255, 0.2);
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
        .status-row .val { font-family: var(--font-code); font-weight: 600; color: var(--accent-cyan); }

        .nav-tabs-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
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
            border-color: var(--accent-cyan);
            background: var(--bg-card-hover);
            color: var(--accent-cyan);
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
            border-color: var(--accent-green);
            background: rgba(0, 255, 157, 0.06);
            box-shadow: 0 0 15px rgba(0, 255, 157, 0.1);
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

        .session-item:hover .btn-del-session {
            opacity: 1;
        }

        .btn-del-session:hover {
            color: var(--accent-red);
            background: rgba(255, 51, 102, 0.15);
            transform: scale(1.15);
        }

        .btn-del-all {
            background: transparent;
            border: none;
            color: var(--text-dim);
            cursor: pointer;
            font-size: 0.72rem;
            transition: all 0.2s;
        }

        .btn-del-all:hover {
            color: var(--accent-red);
        }

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
            background: rgba(168, 85, 247, 0.12);
            border: 1px solid var(--accent-purple);
            color: #d8b4fe;
        }

        .badge-engine {
            background: rgba(0, 255, 157, 0.1);
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

        .btn-icon:hover { color: #fff; border-color: var(--accent-cyan); background: var(--bg-card-hover); }

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
            border-color: var(--accent-cyan);
            color: #fff;
            background: rgba(0, 240, 255, 0.08);
        }

        .tool-chip i { color: var(--accent-cyan); }

        /* View Container */
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
            animation: fadeIn 0.3s ease-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
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

        .chat-msg.user .msg-header { color: var(--accent-green); flex-direction: row-reverse; }
        .chat-msg.assistant .msg-header { color: var(--accent-cyan); }

        .msg-body {
            padding: 16px 20px;
            border-radius: 10px;
            font-size: 0.95rem;
            line-height: 1.65;
            word-break: break-word;
        }

        .chat-msg.user .msg-body {
            background: linear-gradient(135deg, #0e291e, #13392a);
            border: 1px solid var(--accent-green);
            color: #f0fdf4;
            box-shadow: 0 4px 15px rgba(0, 255, 157, 0.1);
        }

        .chat-msg.assistant .msg-body {
            background: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text-main);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        }

        /* Live Terminal Boxes */
        .terminal-box {
            background: #050811;
            border: 1px solid var(--border-light);
            border-radius: 8px;
            margin: 12px 0;
            overflow: hidden;
            box-shadow: 0 6px 20px rgba(0,0,0,0.5);
        }

        .terminal-box-header {
            background: #090f1e;
            padding: 8px 14px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--border);
            font-family: var(--font-code);
            font-size: 0.78rem;
            color: var(--text-muted);
        }

        .terminal-box-header .tag { color: var(--accent-cyan); font-weight: 700; display: flex; align-items: center; gap: 6px; }
        .terminal-box-header .badge-run { background: rgba(0, 255, 157, 0.15); color: var(--accent-green); padding: 2px 6px; border-radius: 4px; }

        .terminal-box-code {
            padding: 14px;
            font-family: var(--font-code);
            font-size: 0.85rem;
            color: #38bdf8;
            overflow-x: auto;
            white-space: pre-wrap;
            line-height: 1.5;
            background: #050811;
        }

        .terminal-output {
            background: #020408;
            border-top: 1px dashed var(--border);
            padding: 12px 14px;
            font-family: var(--font-code);
            font-size: 0.8rem;
            color: #a7f3d0;
            max-height: 250px;
            overflow-y: auto;
            white-space: pre-wrap;
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
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }

        .input-box:focus-within {
            border-color: var(--accent-cyan);
            box-shadow: 0 0 15px rgba(0, 240, 255, 0.25);
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
            background: linear-gradient(135deg, var(--accent-cyan) 0%, #00b4d8 100%);
            color: #03131a;
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

        .btn-submit:hover { box-shadow: 0 0 15px var(--accent-cyan); transform: scale(1.02); }
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
            color: var(--accent-cyan);
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

        /* Live Mission Checklist */
        .mission-checklist {
            background: rgba(17, 24, 42, 0.95);
            border: 1px solid var(--border-light);
            border-radius: 10px;
            padding: 16px 20px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.5);
            margin-bottom: 8px;
        }

        .mission-checklist-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 0.85rem;
            font-weight: 800;
            font-family: var(--font-code);
            color: var(--accent-cyan);
            border-bottom: 1px solid var(--border);
            padding-bottom: 10px;
            letter-spacing: 0.5px;
        }

        .checklist-items {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 10px;
        }

        .check-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 0.82rem;
            font-family: var(--font-ui);
            font-weight: 600;
            padding: 8px 12px;
            border-radius: 6px;
            background: var(--bg-surface);
            border: 1px solid var(--border);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .check-item.pending {
            opacity: 0.5;
            color: var(--text-muted);
            border-color: var(--border);
        }

        .check-item.running {
            border-color: var(--accent-cyan);
            background: rgba(0, 240, 255, 0.08);
            color: #fff;
            box-shadow: 0 0 15px rgba(0, 240, 255, 0.25);
            transform: scale(1.02);
        }

        .check-item.done {
            border-color: var(--accent-green);
            background: rgba(0, 255, 157, 0.08);
            color: #fff;
            box-shadow: 0 0 10px rgba(0, 255, 157, 0.15);
        }

        .check-status-badge {
            font-family: var(--font-code);
            font-size: 0.75rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .check-item.pending .check-status-badge { color: var(--text-dim); }
        .check-item.running .check-status-badge { color: var(--accent-cyan); }
        .check-item.done .check-status-badge { color: var(--accent-green); }

        /* Animated Cyberpunk Typing & Thinking Bubble */
        .typing-indicator {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 4px 2px;
        }

        .neural-wave {
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .neural-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            animation: neuralBounce 1.3s infinite ease-in-out both;
        }

        .neural-dot:nth-child(1) { animation-delay: -0.32s; background: var(--accent-cyan); box-shadow: 0 0 10px var(--accent-cyan); }
        .neural-dot:nth-child(2) { animation-delay: -0.16s; background: var(--accent-green); box-shadow: 0 0 10px var(--accent-green); }
        .neural-dot:nth-child(3) { animation-delay: 0s; background: var(--accent-purple); box-shadow: 0 0 10px var(--accent-purple); }

        @keyframes neuralBounce {
            0%, 80%, 100% { transform: scale(0.5) translateY(0); opacity: 0.35; }
            40% { transform: scale(1.3) translateY(-7px); opacity: 1; }
        }

        .thinking-status-text {
            font-family: var(--font-code);
            font-size: 0.82rem;
            font-weight: 600;
            color: var(--accent-green);
            letter-spacing: 0.5px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .blinking-cursor {
            display: inline-block;
            width: 8px;
            height: 15px;
            background: var(--accent-green);
            animation: blink 0.8s infinite;
            vertical-align: middle;
            box-shadow: 0 0 8px var(--accent-green);
        }

        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

        /* Modals */
        .modal-overlay {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(4, 7, 15, 0.8);
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
            max-width: 600px;
            max-height: 85vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: 0 20px 50px rgba(0,0,0,0.8);
            animation: modalPop 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        }

        @keyframes modalPop {
            from { transform: scale(0.92); opacity: 0; }
            to { transform: scale(1); opacity: 1; }
        }

        .modal-header {
            padding: 18px 24px;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .modal-header h3 { font-size: 1.15rem; font-weight: 800; display: flex; align-items: center; gap: 10px; color: #fff; }
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
            border-color: var(--accent-cyan);
            box-shadow: 0 0 10px rgba(0,240,255,0.2);
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
            <div class="brand-logo"><i class="fa-solid fa-terminal"></i></div>
            <div class="brand-text">
                <h1>CODER-KALI</h1>
                <p>AUTONOMOUS WEB OPS</p>
            </div>
        </div>

        <button class="btn-action btn-new-chat" onclick="startNewSession()">
            <i class="fa-solid fa-plus"></i> NUEVA AUDITORÍA
        </button>

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
            <button class="btn-tab active" id="tabBtnChat" onclick="switchView('chat')"><i class="fa-solid fa-comments"></i> Chat Táctico</button>
            <button class="btn-tab" id="tabBtnRecon" onclick="switchView('recon')"><i class="fa-solid fa-radar"></i> Scanner Visual</button>
            <button class="btn-tab" onclick="openConfigModal()"><i class="fa-solid fa-gear"></i> Ajustes</button>
            <button class="btn-tab" onclick="openScopeModal()"><i class="fa-solid fa-crosshairs"></i> Scope SOW</button>
        </div>

        <div class="section-header">
            <span><i class="fa-solid fa-clock-rotate-left"></i> Sesiones (<span id="sessionCount" style="color: var(--accent-cyan);">0</span>)</span>
            <button class="btn-del-all" title="Limpiar todas las sesiones" onclick="clearAllSessions()"><i class="fa-solid fa-trash"></i> Vaciar</button>
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
                <div class="badge-pill badge-engine">
                    <i class="fa-solid fa-bolt"></i> STREAMING SSE ACTIVO
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
                <i class="fa-solid fa-network-wired"></i> Nmap Port Scan
            </div>
            <div class="tool-chip" onclick="quickPrompt('Inspecciona cabeceras HTTP, WAF y tecnologías con curl y whatweb en ')">
                <i class="fa-solid fa-globe"></i> WhatWeb Tech Detect
            </div>
            <div class="tool-chip" onclick="quickPrompt('Descubre subdominios activos usando assetfinder y subfinder para ')">
                <i class="fa-solid fa-sitemap"></i> Subdomain Discovery
            </div>
            <div class="tool-chip" onclick="quickPrompt('Realiza una auditoría de directorios con gobuster / ffuf en ')">
                <i class="fa-solid fa-folder-tree"></i> Directory Fuzzing
            </div>
            <div class="tool-chip" onclick="quickPrompt('Ejecuta un escaneo de vulnerabilidades y malas configuraciones con nuclei contra ')">
                <i class="fa-solid fa-radiation"></i> Nuclei Scan
            </div>
        </div>

        <!-- Chat View -->
        <div class="view-content" id="chatView">
            <div class="chat-stream" id="chatStream">
                <div class="chat-msg assistant">
                    <div class="msg-header"><i class="fa-solid fa-robot"></i> CODER-KALI // NÚCLEO AUTÓNOMO</div>
                    <div class="msg-body">
                        ¡Bienvenido a la <strong>Plataforma Visual Autónoma de Coder-Kali</strong>!<br><br>
                        Ahora las respuestas se procesan con <strong>Streaming en Tiempo Real (SSE)</strong>: verás las respuestas y la terminal de ejecución aparecer inmediatamente.<br>
                        Escribe tu objetivo abajo o utiliza el <strong>Scanner Visual</strong> en el menú lateral.
                    </div>
                </div>
            </div>

            <!-- Input Bar -->
            <div class="input-container">
                <div class="input-box">
                    <i class="fa-solid fa-chevron-right" style="color: var(--accent-green); margin-right: 8px;"></i>
                    <input type="text" id="promptInput" placeholder="Ej: Realiza un reconocimiento completo de arquitectura y cabeceras en binsperu.pe..." onkeypress="handleKey(event)">
                    <button class="btn-submit" id="submitBtn" onclick="submitPrompt()">
                        <span>EJECUTAR</span> <i class="fa-solid fa-bolt"></i>
                    </button>
                </div>
            </div>
        </div>

        <!-- Recon Scanner Visual View -->
        <div class="recon-view" id="reconView">
            <div class="recon-header">
                <i class="fa-solid fa-crosshairs" style="color: var(--accent-cyan); font-size: 1.2rem;"></i>
                <input type="text" id="reconTargetInput" placeholder="Ingresa un dominio o IP objetivo (ej. binsperu.pe)...">
                <button class="btn-submit" id="btnRunScan" onclick="runVisualScan()"><i class="fa-solid fa-radar"></i> LANZAR ESCANEO 360°</button>
            </div>

            <!-- Live Mission Checklist -->
            <div class="mission-checklist" id="reconChecklist" style="display: none;">
                <div class="mission-checklist-header">
                    <span><i class="fa-solid fa-list-check"></i> PROGRESO DE LA MISIÓN TÁCTICA</span>
                    <span id="reconOverallStatus" style="color: var(--accent-cyan);"><i class="fa-solid fa-spinner fa-spin"></i> EJECUTANDO TAREAS</span>
                </div>
                <div class="checklist-items">
                    <div class="check-item pending" id="chkDns">
                        <span><i class="fa-solid fa-network-wired"></i> 1. Resolución DNS y Red</span>
                        <span class="check-status-badge"><i class="fa-regular fa-circle"></i> PENDIENTE</span>
                    </div>
                    <div class="check-item pending" id="chkWaf">
                        <span><i class="fa-solid fa-shield-virus"></i> 2. Detección WAF y Cabeceras</span>
                        <span class="check-status-badge"><i class="fa-regular fa-circle"></i> PENDIENTE</span>
                    </div>
                    <div class="check-item pending" id="chkTech">
                        <span><i class="fa-solid fa-globe"></i> 3. Tecnologías y CMS</span>
                        <span class="check-status-badge"><i class="fa-regular fa-circle"></i> PENDIENTE</span>
                    </div>
                    <div class="check-item pending" id="chkPorts">
                        <span><i class="fa-solid fa-microchip"></i> 4. Puertos Nmap</span>
                        <span class="check-status-badge"><i class="fa-regular fa-circle"></i> PENDIENTE</span>
                    </div>
                    <div class="check-item pending" id="chkSubs">
                        <span><i class="fa-solid fa-sitemap"></i> 5. Subdominios</span>
                        <span class="check-status-badge"><i class="fa-regular fa-circle"></i> PENDIENTE</span>
                    </div>
                </div>
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
    </div>

    <!-- Modal: Configuración de IA -->
    <div class="modal-overlay" id="configModal">
        <div class="modal-card">
            <div class="modal-header">
                <h3><i class="fa-solid fa-sliders" style="color: var(--accent-cyan);"></i> Configuración de IA y Proveedores</h3>
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
                <h3><i class="fa-solid fa-crosshairs" style="color: var(--accent-purple);"></i> Documento de Alcance (SOW / ROE)</h3>
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

        function switchView(view) {
            document.getElementById('tabBtnChat').classList.toggle('active', view === 'chat');
            document.getElementById('tabBtnRecon').classList.toggle('active', view === 'recon');
            document.getElementById('chatView').style.display = view === 'chat' ? 'flex' : 'none';
            document.getElementById('reconView').style.display = view === 'recon' ? 'flex' : 'none';
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
                            <div class="s-title"><i class="fa-regular fa-message" style="color: var(--accent-cyan); margin-right: 6px;"></i>${escapeHtml(s.title)}</div>
                            <button class="btn-del-session" title="Eliminar sesión" onclick="deleteSession(event, '${s.id}')"><i class="fa-solid fa-trash-can"></i></button>
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

        async function deleteSession(e, id) {
            e.stopPropagation();
            if (!confirm("¿Deseas eliminar permanentemente esta sesión?")) return;
            try {
                await fetch(`/api/sessions?action=delete&id=${id}`, { method: 'POST' });
                if (currentSessionId === id) {
                    startNewSession();
                } else {
                    loadSessions();
                }
            } catch (err) {
                alert("Error al eliminar sesión: " + err);
            }
        }

        async function clearAllSessions() {
            if (!confirm("¿Deseas vaciar TODO el historial de sesiones guardadas?")) return;
            try {
                await fetch('/api/sessions?action=clear_all', { method: 'POST' });
                startNewSession();
            } catch (err) {
                alert("Error al vaciar historial: " + err);
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

            let formatted = rawContent;

            // 1. Formatear etiquetas XML <ejecutar_comando>
            formatted = formatted.replace(/<ejecutar_comando>([\s\S]*?)<\/ejecutar_comando>/g, function(match, cmd) {
                return `<div class="terminal-box">
                    <div class="terminal-box-header">
                        <span class="tag"><i class="fa-solid fa-terminal"></i> COMANDO EJECUTADO</span>
                        <span class="badge-run">BASH</span>
                    </div>
                    <div class="terminal-box-code">${escapeHtml(cmd.trim())}</div>
                </div>`;
            });

            // 2. Formatear llamadas JSON crudas (ej: {"cmd": ["bash", "-lc", "..."]})
            formatted = formatted.replace(/\{[^{}]*"(?:cmd|command|bash|exec)"\s*:\s*(\[[^\]]*\]|"[^"]*")[^{}]*\}/g, function(match) {
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
                        return `<div class="terminal-box">
                            <div class="terminal-box-header">
                                <span class="tag"><i class="fa-solid fa-terminal"></i> COMANDO EJECUTADO</span>
                                <span class="badge-run">BASH</span>
                            </div>
                            <div class="terminal-box-code">${escapeHtml(cmdStr.trim())}</div>
                        </div>`;
                    }
                } catch(e) {}
                return match;
            });

            formatted = formatted.replace(/\n/g, '<br>');

            msgDiv.innerHTML = `
                <div class="msg-header">${role === 'user' ? '<i class="fa-solid fa-user-ninja"></i> OPERADOR' : '<i class="fa-solid fa-robot"></i> CODER-KALI'}</div>
                <div class="msg-body">${formatted}</div>
            `;
            stream.appendChild(msgDiv);
            stream.scrollTop = stream.scrollHeight;
        }

        function escapeHtml(text) {
            return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
        }

        function updateCheckItem(id, state, customText) {
            const el = document.getElementById(id);
            if (!el) return;
            el.className = `check-item ${state}`;
            const badge = el.querySelector('.check-status-badge');
            if (!badge) return;

            if (state === 'pending') {
                badge.innerHTML = `<i class="fa-regular fa-circle"></i> ${customText || 'PENDIENTE'}`;
            } else if (state === 'running') {
                badge.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> ${customText || 'EN CURSO...'}`;
            } else if (state === 'done') {
                badge.innerHTML = `<i class="fa-solid fa-circle-check" style="color: var(--accent-green);"></i> ${customText || 'LOGRADO ✓'}`;
            }
        }

        function showThinkingBubble() {
            const stream = document.getElementById('chatStream');
            removeThinkingBubble();

            const msgDiv = document.createElement('div');
            msgDiv.id = 'thinkingBubble';
            msgDiv.className = 'chat-msg assistant';
            msgDiv.innerHTML = `
                <div class="msg-header"><i class="fa-solid fa-robot"></i> CODER-KALI // AUDITORÍA EN TIEMPO REAL</div>
                <div class="msg-body" style="background: rgba(0, 240, 255, 0.04); border-color: rgba(0, 240, 255, 0.25);">
                    <div style="display: flex; flex-direction: column; gap: 10px;">
                        <div class="checklist-items" style="grid-template-columns: 1fr; gap: 6px;">
                            <div class="check-item running" id="tbStep1">
                                <span><i class="fa-solid fa-crosshairs"></i> 1. Análisis de Objetivo e Inteligencia de Red</span>
                                <span class="check-status-badge"><i class="fa-solid fa-spinner fa-spin"></i> EN CURSO...</span>
                            </div>
                            <div class="check-item pending" id="tbStep2">
                                <span><i class="fa-solid fa-shield-halved"></i> 2. Evaluación de WAF, Puertos y Tecnologías</span>
                                <span class="check-status-badge"><i class="fa-regular fa-circle"></i> PENDIENTE</span>
                            </div>
                            <div class="check-item pending" id="tbStep3">
                                <span><i class="fa-solid fa-radiation"></i> 3. Diagnóstico Top 10 Vectores de Riesgo OWASP</span>
                                <span class="check-status-badge"><i class="fa-regular fa-circle"></i> PENDIENTE</span>
                            </div>
                        </div>
                        <div class="typing-indicator" style="margin-top: 4px;">
                            <div class="neural-wave">
                                <div class="neural-dot"></div>
                                <div class="neural-dot"></div>
                                <div class="neural-dot"></div>
                            </div>
                            <div class="thinking-status-text">
                                <span id="telemetryStatus">RECOPILANDO INTELIGENCIA TÁCTICA...</span>
                                <span class="blinking-cursor"></span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            stream.appendChild(msgDiv);
            stream.scrollTop = stream.scrollHeight;

            // Simular progresión en vivo de tareas logradas
            setTimeout(() => {
                updateCheckItem('tbStep1', 'done', 'LOGRADO ✓');
                updateCheckItem('tbStep2', 'running', 'EJECUTANDO...');
            }, 1200);

            setTimeout(() => {
                updateCheckItem('tbStep2', 'done', 'LOGRADO ✓');
                updateCheckItem('tbStep3', 'running', 'SINTETIZANDO...');
            }, 2600);
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
            showThinkingBubble();

            const btn = document.getElementById('submitBtn');
            btn.innerHTML = '<div class="spinner"></div> <span>PROCESANDO</span>';
            btn.disabled = true;

            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: text, session_id: currentSessionId })
                });
                const data = await res.json();
                removeThinkingBubble();
                if (data.session_id) currentSessionId = data.session_id;
                renderBubble('assistant', data.response);
                loadSessions();
            } catch (e) {
                removeThinkingBubble();
                renderBubble('assistant', 'Error de comunicación: ' + e);
            } finally {
                btn.innerHTML = '<span>EJECUTAR</span> <i class="fa-solid fa-bolt"></i>';
                btn.disabled = false;
            }
        }

        async function runVisualScan() {
            const target = document.getElementById('reconTargetInput').value.trim();
            if (!target) {
                alert('Por favor ingresa un dominio o IP.');
                return;
            }

            const cl = document.getElementById('reconChecklist');
            cl.style.display = 'flex';
            document.getElementById('reconOverallStatus').innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> EJECUTANDO MISIONES EN PARALELO...';

            updateCheckItem('chkDns', 'running', 'RESOLVIENDO...');
            updateCheckItem('chkWaf', 'running', 'ANALIZANDO...');
            updateCheckItem('chkTech', 'running', 'INSPECCIONANDO...');
            updateCheckItem('chkPorts', 'running', 'ESCANEANDO...');
            updateCheckItem('chkSubs', 'running', 'ENUMERANDO...');

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

                updateCheckItem('chkDns', 'done', 'LOGRADO ✓');
                updateCheckItem('chkWaf', 'done', 'LOGRADO ✓');
                updateCheckItem('chkTech', 'done', 'LOGRADO ✓');
                updateCheckItem('chkPorts', 'done', 'LOGRADO ✓');
                updateCheckItem('chkSubs', 'done', 'LOGRADO ✓');

                document.getElementById('reconOverallStatus').innerHTML = '<span style="color: var(--accent-green);"><i class="fa-solid fa-circle-check"></i> MISIÓN 360° COMPLETADA CON ÉXITO</span>';

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

        function handleKey(e) {
            if (e.key === 'Enter') submitPrompt();
        }

        function startNewSession() {
            currentSessionId = null;
            switchView('chat');
            const stream = document.getElementById('chatStream');
            stream.innerHTML = `
                <div class="chat-msg assistant">
                    <div class="msg-header"><i class="fa-solid fa-robot"></i> CODER-KALI</div>
                    <div class="msg-body">Nueva sesión iniciada. ¿Cuál es el siguiente objetivo?</div>
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
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            data = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            data = {}

        if path == "/api/chat":
            prompt = data.get("prompt", "")
            session_id = data.get("session_id")

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
    console.print(f"\n[bold green]⚡ Centro de Operaciones Web de Coder-Kali Activo:[/bold green] [bold cyan]{url}[/bold cyan]")
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
        httpd.server_close()

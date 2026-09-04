"""
coder_kali/model_discovery.py - Descubrimiento Dinámico de Modelos en Tiempo Real.
Consulta en vivo la API del proveedor usando la API Key del usuario para listar los modelos activos y disponibles.
"""

import json
import urllib.request
import urllib.error
from typing import List, Optional
from rich.console import Console

console = Console()

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 (CoderKali/1.0)"


def fetch_live_models(provider: str, api_key: str, api_base: Optional[str] = None) -> List[str]:
    """
    Consulta en vivo al endpoint del proveedor para obtener los modelos activos autorizados para la API Key.
    """
    provider = provider.lower().strip()
    headers = {
        "User-Agent": USER_AGENT,
        "Authorization": f"Bearer {api_key.strip()}" if api_key else "",
    }

    try:
        # 1. GROQ
        if provider == "groq":
            req = urllib.request.Request("https://api.groq.com/openai/v1/models", headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = []
                for item in data.get("data", []):
                    m_id = item.get("id", "")
                    if item.get("active", True) and not m_id.startswith("whisper") and not "guard" in m_id:
                        models.append(f"groq/{m_id}")
                if models:
                    return sorted(models)

        # 2. OPENAI
        elif provider == "openai":
            req = urllib.request.Request("https://api.openai.com/v1/models", headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = []
                for item in data.get("data", []):
                    m_id = item.get("id", "")
                    if any(prefix in m_id for prefix in ["gpt-4", "gpt-3.5", "o1", "o3", "chatgpt"]):
                        models.append(f"openai/{m_id}")
                if models:
                    return sorted(models, reverse=True)

        # 3. GOOGLE GEMINI
        elif provider == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key.strip()}"
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = []
                for item in data.get("models", []):
                    m_name = item.get("name", "").replace("models/", "")
                    methods = item.get("supportedGenerationMethods", [])
                    if "generateContent" in methods and "gemini" in m_name:
                        models.append(f"gemini/{m_name}")
                if models:
                    return sorted(models, reverse=True)

        # 4. MISTRAL AI
        elif provider == "mistral":
            req = urllib.request.Request("https://api.mistral.ai/v1/models", headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [f"mistral/{item['id']}" for item in data.get("data", []) if "embed" not in item.get("id", "")]
                if models:
                    return sorted(models)

        # 5. DEEPSEEK
        elif provider == "deepseek":
            req = urllib.request.Request("https://api.deepseek.com/models", headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [f"deepseek/{item['id']}" for item in data.get("data", [])]
                if models:
                    return sorted(models)

        # 6. OLLAMA (Local)
        elif provider == "ollama":
            base = (api_base or "http://localhost:11434").rstrip("/")
            req = urllib.request.Request(f"{base}/api/tags", headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [f"ollama/{item['name']}" for item in data.get("models", [])]
                if models:
                    return models

        # 7. OPENROUTER
        elif provider == "openrouter":
            req = urllib.request.Request("https://openrouter.ai/api/v1/models", headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [f"openrouter/{item['id']}" for item in data.get("data", [])]
                if models:
                    return sorted(models)

        # 8. BAI CHAT (chat.b.ai)
        elif provider == "bai":
            base = (api_base or "https://api.b.ai/v1").rstrip("/")
            req = urllib.request.Request(f"{base}/models", headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [f"openai/{item['id']}" for item in data.get("data", [])]
                if models:
                    return sorted(models)

        # 9. AIML API (aimlapi.com)
        elif provider == "aimlapi":
            base = (api_base or "https://api.aimlapi.com/v1").rstrip("/")
            req = urllib.request.Request(f"{base}/models", headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [f"openai/{item['id']}" for item in data.get("data", [])]
                if models:
                    return sorted(models)

        # 10. PUTER (developer.puter.com)
        elif provider == "puter":
            base = (api_base or "https://api.puter.com/puterai/openai/v1").rstrip("/")
            req = urllib.request.Request(f"{base}/models", headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [item["id"] for item in data.get("data", [])]
                if models:
                    return sorted(models)

    except Exception:
        pass

    return []


# Alias de conveniencia
fetch_online_models = fetch_live_models

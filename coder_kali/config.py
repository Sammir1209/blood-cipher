"""
coder_kali/config.py - Gestor de Configuración, Credenciales y Modelos.
Almacena la configuración en ~/.config/coder-kali/config.json con permisos seguros.
"""

import os
import json
import base64
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional

CONFIG_DIR = Path.home() / ".config" / "coder-kali"
CONFIG_FILE = CONFIG_DIR / "config.json"
SECRET_KEY_FILE = CONFIG_DIR / ".secret.key"

DEFAULT_PROVIDERS = {
    "gemini": {
        "name": "Google Gemini",
        "default_model": "gemini/gemini-2.0-flash",
        "available_models": [
            "gemini/gemini-2.0-flash",
            "gemini/gemini-2.0-pro-exp-02-05",
            "gemini/gemini-1.5-pro",
            "gemini/gemini-1.5-flash",
        ],
        "env_var": "GEMINI_API_KEY",
        "requires_api_key": True,
    },
    "anthropic": {
        "name": "Anthropic Claude",
        "default_model": "anthropic/claude-3-5-sonnet-20241022",
        "available_models": [
            "anthropic/claude-3-5-sonnet-20241022",
            "anthropic/claude-3-5-haiku-20241022",
            "anthropic/claude-3-opus-20240229",
        ],
        "env_var": "ANTHROPIC_API_KEY",
        "requires_api_key": True,
    },
    "openai": {
        "name": "OpenAI",
        "default_model": "openai/gpt-4o",
        "available_models": [
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "openai/o3-mini",
            "openai/gpt-4-turbo",
        ],
        "env_var": "OPENAI_API_KEY",
        "requires_api_key": True,
    },
    "deepseek": {
        "name": "DeepSeek",
        "default_model": "deepseek/deepseek-chat",
        "available_models": [
            "deepseek/deepseek-chat",
            "deepseek/deepseek-reasoner",
        ],
        "env_var": "DEEPSEEK_API_KEY",
        "requires_api_key": True,
    },
    "groq": {
        "name": "Groq (Ultra Rápido)",
        "default_model": "groq/llama-3.3-70b-versatile",
        "available_models": [
            "groq/llama-3.3-70b-versatile",
            "groq/deepseek-r1-distill-llama-70b",
            "groq/mixtral-8x7b-32768",
        ],
        "env_var": "GROQ_API_KEY",
        "requires_api_key": True,
    },
    "ollama": {
        "name": "Ollama (100% Local / Offline)",
        "default_model": "ollama/llama3.2",
        "available_models": [
            "ollama/llama3.2",
            "ollama/deepseek-r1",
            "ollama/qwen2.5-coder:7b",
            "ollama/mistral",
        ],
        "env_var": "OLLAMA_API_BASE",
        "requires_api_key": False,
        "default_api_base": "http://localhost:11434",
    },
    "openrouter": {
        "name": "OpenRouter",
        "default_model": "openrouter/anthropic/claude-3.5-sonnet",
        "available_models": [
            "openrouter/anthropic/claude-3.5-sonnet",
            "openrouter/google/gemini-2.0-flash-exp:free",
            "openrouter/meta-llama/llama-3.3-70b-instruct",
            "openrouter/deepseek/deepseek-r1",
        ],
        "env_var": "OPENROUTER_API_KEY",
        "requires_api_key": True,
    },
}

DEFAULT_CONFIG: Dict[str, Any] = {
    "provider": "gemini",
    "model": "gemini/gemini-2.0-flash",
    "temperature": 0.2,
    "max_tokens": 4096,
    "api_keys": {},
    "api_bases": {
        "ollama": "http://localhost:11434"
    },
    "auto_approve_safe_commands": False,
    "theme": "cyberpunk",
    "system_prompt_mode": "default",
}


class ConfigManager:
    """Administrador de configuración persistente con cifrado local."""

    def __init__(self):
        self._ensure_config_dir()
        self._cipher = self._get_or_create_cipher()
        self.config = self._load()

    def _ensure_config_dir(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        try:
            # Permisos estrictos 0700 en Linux/Unix
            os.chmod(CONFIG_DIR, 0o700)
        except Exception:
            pass

    def _get_or_create_cipher(self):
        try:
            from cryptography.fernet import Fernet
            if not SECRET_KEY_FILE.exists():
                key = Fernet.generate_key()
                SECRET_KEY_FILE.write_bytes(key)
                try:
                    os.chmod(SECRET_KEY_FILE, 0o600)
                except Exception:
                    pass
            else:
                key = SECRET_KEY_FILE.read_bytes()
            return Fernet(key)
        except Exception:
            return None

    def _encrypt(self, plain_text: str) -> str:
        if not plain_text:
            return ""
        if self._cipher:
            try:
                return self._cipher.encrypt(plain_text.encode("utf-8")).decode("utf-8")
            except Exception:
                pass
        # Fallback de codificación simple
        return "b64:" + base64.b64encode(plain_text.encode("utf-8")).decode("utf-8")

    def _decrypt(self, cipher_text: str) -> str:
        if not cipher_text:
            return ""
        if cipher_text.startswith("b64:"):
            try:
                return base64.b64decode(cipher_text[4:].encode("utf-8")).decode("utf-8")
            except Exception:
                return cipher_text
        if self._cipher:
            try:
                return self._cipher.decrypt(cipher_text.encode("utf-8")).decode("utf-8")
            except Exception:
                pass
        return cipher_text

    def _load(self) -> Dict[str, Any]:
        if not CONFIG_FILE.exists():
            cfg = DEFAULT_CONFIG.copy()
            self._save_raw(cfg)
            return cfg
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                merged = DEFAULT_CONFIG.copy()
                merged.update(data)
                return merged
        except Exception:
            return DEFAULT_CONFIG.copy()

    def _save_raw(self, data: Dict[str, Any]):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            try:
                os.chmod(CONFIG_FILE, 0o600)
            except Exception:
                pass
        except Exception as e:
            print(f"[!] Error al guardar configuración: {e}")

    def save(self):
        self._save_raw(self.config)

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        self.config[key] = value
        self.save()

    def set_api_key(self, provider: str, raw_key: str):
        if "api_keys" not in self.config:
            self.config["api_keys"] = {}
        self.config["api_keys"][provider] = self._encrypt(raw_key.strip())
        self.save()

    def get_api_key(self, provider: Optional[str] = None) -> str:
        prov = provider or self.config.get("provider", "gemini")
        # Primero revisar variable de entorno
        env_var = DEFAULT_PROVIDERS.get(prov, {}).get("env_var")
        if env_var and os.environ.get(env_var):
            return os.environ[env_var]

        # Luego revisar config guardada
        encrypted_key = self.config.get("api_keys", {}).get(prov, "")
        if encrypted_key:
            return self._decrypt(encrypted_key)
        return ""

    def set_provider(self, provider: str, model: Optional[str] = None):
        self.config["provider"] = provider
        if model:
            self.config["model"] = model
        else:
            default_mod = DEFAULT_PROVIDERS.get(provider, {}).get("default_model")
            if default_mod:
                self.config["model"] = default_mod
        self.save()

    def set_model(self, model: str):
        self.config["model"] = model
        self.save()

    def get_active_provider(self) -> str:
        return self.config.get("provider", "gemini")

    def get_active_model(self) -> str:
        return self.config.get("model", "gemini/gemini-2.0-flash")

    def get_api_base(self, provider: Optional[str] = None) -> Optional[str]:
        prov = provider or self.get_active_provider()
        return self.config.get("api_bases", {}).get(prov)

    def is_configured(self) -> bool:
        provider = self.get_active_provider()
        prov_info = DEFAULT_PROVIDERS.get(provider, {})
        if not prov_info.get("requires_api_key", True):
            return True
        key = self.get_api_key(provider)
        return bool(key and len(key.strip()) > 5)

    def reset(self):
        self.config = DEFAULT_CONFIG.copy()
        self.save()

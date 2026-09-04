"""
coder_kali/providers/puter.py - Driver dedicado para Puter API / Puter.js (Acceso a DeepSeek y 500+ modelos).
Comunica vía la API REST OpenAI-compatible de Puter (https://api.puter.com/puterai/openai/v1/).
"""

import json
from typing import Any, Dict, List, Optional, Tuple
import requests

from .base import BaseLLMProvider, LLMResponse


class PuterProvider(BaseLLMProvider):
    """Driver dedicado para Puter (Acceso libre a DeepSeek, Claude, GPT y más modelos)."""

    DEFAULT_BASE = "https://api.puter.com/puterai/openai/v1"

    def _clean_model_name(self, model: str) -> str:
        """Limpia el nombre del modelo conservando el formato correcto."""
        if not model:
            return "deepseek/deepseek-chat"
        m = model.strip()
        if m.lower().startswith("puter/"):
            m = m[len("puter/"):]
        return m

    def _get_api_base(self) -> str:
        base = self.config_mgr.get_api_base("puter") or self.DEFAULT_BASE
        base = base.strip().rstrip("/")
        if base.endswith("/chat/completions"):
            base = base[:-len("/chat/completions")].rstrip("/")
        return base

    def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        clean_model = self._clean_model_name(model)
        api_base = self._get_api_base()
        endpoint = f"{api_base}/chat/completions"

        api_key = self.config_mgr.get_api_key("puter")
        if not api_key:
            return LLMResponse(
                error=(
                    "No hay Puter Auth Token configurado. Puedes obtener tu Auth Token gratis "
                    "en https://puter.com/dashboard. "
                    "Ejecuta 'blood-cipher config' para configurarlo."
                ),
                success=False,
            )

        headers = {
            "Authorization": f"Bearer {api_key.strip()}",
            "Content-Type": "application/json",
            "User-Agent": "Blood-Cipher/1.0 (Puter.js Integration)",
        }

        payload = {
            "model": clean_model,
            "messages": messages,
            "temperature": float(temperature),
            "max_tokens": int(max_tokens),
        }

        try:
            resp = requests.post(endpoint, json=payload, headers=headers, timeout=120)

            # Manejo de rotación en caso de rate limit
            if resp.status_code == 429:
                next_key = self.config_mgr.rotate_api_key("puter")
                if next_key and next_key != api_key:
                    headers["Authorization"] = f"Bearer {next_key.strip()}"
                    resp = requests.post(endpoint, json=payload, headers=headers, timeout=120)

            if resp.status_code != 200:
                err_text = resp.text
                if resp.status_code == 401:
                    return LLMResponse(
                        error=(
                            "Auth Token de Puter rechazado (401 No autorizado). "
                            "Verifica tu Puter Auth Token en https://puter.com/dashboard."
                        ),
                        success=False,
                    )
                if resp.status_code == 429:
                    return LLMResponse(
                        error="Límite de peticiones alcanzado en Puter (429 Rate Limit). Intenta más tarde o rota tu token.",
                        success=False,
                    )
                return LLMResponse(
                    error=f"Error al consultar Puter API ({resp.status_code}): {err_text}",
                    success=False,
                )

            data = resp.json()
            choice = data.get("choices", [{}])[0]
            message_obj = choice.get("message", {})
            content = message_obj.get("content", "") or ""
            reasoning = message_obj.get("reasoning", "") or message_obj.get("reasoning_content", "") or ""
            usage = data.get("usage", {}).get("total_tokens", 0)

            return LLMResponse(
                content=content,
                reasoning_content=reasoning,
                raw_response=data,
                tokens_used=usage,
                success=True,
            )

        except requests.exceptions.Timeout:
            return LLMResponse(
                error="Tiempo de espera agotado al conectar con Puter API (Timeout 120s).",
                success=False,
            )
        except requests.exceptions.ConnectionError:
            return LLMResponse(
                error=f"No se pudo conectar con el servidor de Puter en {endpoint}. Revisa tu conexión a internet.",
                success=False,
            )
        except Exception as e:
            return LLMResponse(error=f"Excepción inesperada en Puter Provider: {str(e)}", success=False)

    def test_connection(self, model: str) -> Tuple[bool, str]:
        clean_model = self._clean_model_name(model)
        test_messages = [{"role": "user", "content": "Responde únicamente 'OK'"}]
        res = self.chat_completion(clean_model, test_messages, max_tokens=20)
        if res.success:
            reply = res.content.strip() or res.reasoning_content.strip() or "OK"
            return True, f"Conexión exitosa con Puter ({clean_model}): {reply}"
        return False, res.error or "Error desconocido al conectar con Puter"

    def list_models(self) -> List[str]:
        api_key = self.config_mgr.get_api_key("puter")
        if not api_key:
            return []
        endpoint = f"{self._get_api_base()}/models"
        headers = {"Authorization": f"Bearer {api_key.strip()}"}
        try:
            r = requests.get(endpoint, headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                return sorted([item["id"] for item in data.get("data", [])])
        except Exception:
            pass
        return []

"""
coder_kali/providers/bai.py - Driver independiente para Bai Chat (chat.b.ai).
Comunica directamente vía HTTP REST sin intermediarios ni cruce de variables.
"""

import json
from typing import Any, Dict, List, Optional, Tuple
import requests

from .base import BaseLLMProvider, LLMResponse


class BaiChatProvider(BaseLLMProvider):
    """Driver dedicado para Bai Chat (chat.b.ai API)."""

    DEFAULT_BASE = "https://api.b.ai/v1"

    def _clean_model_name(self, model: str) -> str:
        """Elimina prefijos artificiales como 'openai/' o 'bai/'."""
        if not model:
            return "deepseek-chat"
        m = model.strip()
        for prefix in ("openai/", "bai/", "gpt/"):
            if m.lower().startswith(prefix):
                m = m[len(prefix):]
        return m

    def _get_api_base(self) -> str:
        base = self.config_mgr.get_api_base("bai") or self.DEFAULT_BASE
        base = base.strip().rstrip("/")
        if base.endswith("/chat/completions"):
            base = base[:-len("/chat/completions")].rstrip("/")
        return base

    def _parse_bai_error(self, status_code: int, error_text: str, model: str) -> str:
        """Traduce los errores típicos de Bai Chat a mensajes comprensibles."""
        err_lower = error_text.lower()
        if "invalid api_key format" in err_lower or "鉴权服务请求失败" in error_text:
            return (
                "Error de Autenticación en Bai Chat: La API Key ingresada no es válida "
                "o tiene un formato incorrecto. Verifica tu clave en https://chat.b.ai/."
            )
        if "deposit required" in err_lower or "unlock premium models" in err_lower:
            return (
                f"Acceso Restringido en Bai Chat: El modelo '{model}' requiere depósito de saldo "
                "en tu cuenta de chat.b.ai. Usa un modelo disponible para cuentas estándar (ej. 'deepseek-chat')."
            )
        if status_code == 401:
            return "API Key de Bai Chat rechazada (401 No autorizado). Revisa tus credenciales."
        if status_code == 429:
            return "Límite de peticiones alcanzado en Bai Chat (429 Rate Limit). Intenta más tarde o rota tu API Key."
        if status_code == 404:
            return f"Endpoint no encontrado (404). Verifica que la URL base sea '{self.DEFAULT_BASE}'."
        return f"Error de Bai Chat (HTTP {status_code}): {error_text}"

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

        # Manejo de keys y rotación
        api_key = self.config_mgr.get_api_key("bai")
        if not api_key:
            return LLMResponse(
                error="No hay API Key configurada para Bai Chat. Ejecuta 'blood-cipher config'.",
                success=False,
            )

        headers = {
            "Authorization": f"Bearer {api_key.strip()}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": clean_model,
            "messages": messages,
            "temperature": float(temperature),
            "max_tokens": int(max_tokens),
        }

        try:
            resp = requests.post(endpoint, json=payload, headers=headers, timeout=120)
            
            # En caso de 429 intentar rotar key si hay pool
            if resp.status_code == 429:
                next_key = self.config_mgr.rotate_api_key("bai")
                if next_key and next_key != api_key:
                    headers["Authorization"] = f"Bearer {next_key.strip()}"
                    resp = requests.post(endpoint, json=payload, headers=headers, timeout=120)

            if resp.status_code != 200:
                err_msg = self._parse_bai_error(resp.status_code, resp.text, clean_model)
                return LLMResponse(error=err_msg, success=False)

            data = resp.json()
            choice = data.get("choices", [{}])[0]
            message_obj = choice.get("message", {})
            content = message_obj.get("content", "") or ""
            reasoning = message_obj.get("reasoning_content", "") or ""
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
                error="Tiempo de espera agotado al conectar con Bai Chat (Timeout de 120s).",
                success=False,
            )
        except requests.exceptions.ConnectionError:
            return LLMResponse(
                error=f"No se pudo conectar con el servidor de Bai Chat en {endpoint}. Revisa tu conexión a internet.",
                success=False,
            )
        except Exception as e:
            return LLMResponse(error=f"Excepción inesperada en Bai Chat: {str(e)}", success=False)

    def test_connection(self, model: str) -> Tuple[bool, str]:
        """Prueba de conexión limpia sin contaminar logs."""
        clean_model = self._clean_model_name(model)
        test_messages = [{"role": "user", "content": "Responde únicamente 'OK'"}]
        res = self.chat_completion(clean_model, test_messages, max_tokens=20)
        if res.success:
            reply = res.content.strip() or res.reasoning_content.strip() or "OK"
            return True, f"Conexión exitosa con Bai Chat ({clean_model}): {reply}"
        return False, res.error or "Error desconocido al conectar con Bai Chat"

    def list_models(self) -> List[str]:
        api_key = self.config_mgr.get_api_key("bai")
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

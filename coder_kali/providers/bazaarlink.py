"""
coder_kali/providers/bazaarlink.py - Driver dedicado para BazaarLink AI (bazaarlink.ai).
Comunica directamente vía HTTP REST OpenAI-compatible contra https://bazaarlink.ai/api/v1.
"""

import json
from typing import Any, Dict, List, Optional, Tuple
import requests

from .base import BaseLLMProvider, LLMResponse


class BazaarLinkProvider(BaseLLMProvider):
    """Driver dedicado para BazaarLink AI (bazaarlink.ai)."""

    DEFAULT_BASE = "https://bazaarlink.ai/api/v1"

    def _clean_model_name(self, model: str) -> str:
        """Limpia prefijos innecesarios conservando el id exacto del modelo."""
        if not model:
            return "deepseek-v3.2"
        m = model.strip()
        for prefix in ("bazaarlink/", "bazaar/"):
            if m.lower().startswith(prefix):
                m = m[len(prefix):]
        return m

    def _get_api_base(self) -> str:
        base = self.config_mgr.get_api_base("bazaarlink") or self.DEFAULT_BASE
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

        api_key = self.config_mgr.get_api_key("bazaarlink")
        if not api_key:
            return LLMResponse(
                error=(
                    "No hay API Key configurada para BazaarLink AI. "
                    "Ejecuta 'blood-cipher config' y pega tu clave (sk-bl-...)."
                ),
                success=False,
            )

        headers = {
            "Authorization": f"Bearer {api_key.strip()}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (Blood-Cipher/2.0)",
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
                next_key = self.config_mgr.rotate_api_key("bazaarlink")
                if next_key and next_key != api_key:
                    headers["Authorization"] = f"Bearer {next_key.strip()}"
                    resp = requests.post(endpoint, json=payload, headers=headers, timeout=120)

            if resp.status_code != 200:
                err_text = resp.text
                if resp.status_code == 401 or resp.status_code == 403:
                    return LLMResponse(
                        error=(
                            f"Acceso denegado en BazaarLink AI (HTTP {resp.status_code}). "
                            "Verifica tu API Key (sk-bl-...) en https://bazaarlink.ai/."
                        ),
                        success=False,
                    )
                if resp.status_code == 402 or "insufficient credits" in err_text.lower():
                    return LLMResponse(
                        error=(
                            "Créditos insuficientes en BazaarLink AI (HTTP 402): Tu cuenta no tiene saldo suficiente. "
                            "Recarga créditos en https://bazaarlink.ai/ o usa el modelo 'auto:free' / modelos gratuitos."
                        ),
                        success=False,
                    )
                if resp.status_code == 429:
                    return LLMResponse(
                        error="Límite de peticiones alcanzado en BazaarLink AI (429 Rate Limit). Intenta más tarde o rota tu API Key.",
                        success=False,
                    )
                return LLMResponse(
                    error=f"Error en BazaarLink AI ({resp.status_code}): {err_text}",
                    success=False,
                )

            data = resp.json()
            choice = data.get("choices", [{}])[0]
            message_obj = choice.get("message", {})
            content = message_obj.get("content", "") or ""
            reasoning = message_obj.get("reasoning_content", "") or message_obj.get("reasoning", "") or ""
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
                error="Tiempo de espera agotado al conectar con BazaarLink AI (Timeout de 120s).",
                success=False,
            )
        except requests.exceptions.ConnectionError:
            return LLMResponse(
                error=f"No se pudo conectar con el servidor de BazaarLink AI en {endpoint}. Revisa tu conexión a internet.",
                success=False,
            )
        except Exception as e:
            return LLMResponse(error=f"Excepción inesperada en BazaarLink AI: {str(e)}", success=False)

    def test_connection(self, model: str) -> Tuple[bool, str]:
        clean_model = self._clean_model_name(model)
        test_messages = [{"role": "user", "content": "Responde únicamente 'OK'"}]
        res = self.chat_completion(clean_model, test_messages, max_tokens=20)
        if res.success:
            reply = res.content.strip() or res.reasoning_content.strip() or "OK"
            return True, f"Conexión exitosa con BazaarLink AI ({clean_model}): {reply}"
        return False, res.error or "Error desconocido al conectar con BazaarLink AI"

    def list_models(self) -> List[str]:
        api_key = self.config_mgr.get_api_key("bazaarlink")
        if not api_key:
            return []
        endpoint = f"{self._get_api_base()}/models"
        headers = {
            "Authorization": f"Bearer {api_key.strip()}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (Blood-Cipher/2.0)",
        }
        try:
            r = requests.get(endpoint, headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                return sorted([item["id"] for item in data.get("data", [])])
        except Exception:
            pass
        return []

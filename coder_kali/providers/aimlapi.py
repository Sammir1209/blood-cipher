"""
coder_kali/providers/aimlapi.py - Driver independiente para AIML API (aimlapi.com).
"""

from typing import Any, Dict, List, Tuple
import requests

from .base import BaseLLMProvider, LLMResponse


class AimlApiProvider(BaseLLMProvider):
    """Driver dedicado para AIML API."""

    DEFAULT_BASE = "https://api.aimlapi.com/v1"

    def _clean_model_name(self, model: str) -> str:
        if not model:
            return "deepseek-ai/DeepSeek-R1"
        m = model.strip()
        for prefix in ("openai/", "aimlapi/"):
            if m.lower().startswith(prefix):
                m = m[len(prefix):]
        return m

    def _get_api_base(self) -> str:
        base = self.config_mgr.get_api_base("aimlapi") or self.DEFAULT_BASE
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
        api_key = self.config_mgr.get_api_key("aimlapi")
        if not api_key:
            return LLMResponse(
                error="No hay API Key configurada para AIML API. Ejecuta 'blood-cipher config'.",
                success=False,
            )

        endpoint = f"{self._get_api_base()}/chat/completions"
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
            if resp.status_code != 200:
                err_text = resp.text
                if "run out of funds" in err_text.lower() or "billing" in err_text.lower():
                    return LLMResponse(
                        error="Saldo agotado en AIML API. Recarga fondos en https://aimlapi.com/app/billing/ o cambia de proveedor con 'blood-cipher config'.",
                        success=False,
                    )
                if resp.status_code == 401:
                    return LLMResponse(
                        error="API Key de AIML API inválida o expirada. Verifica tu clave en https://aimlapi.com/.",
                        success=False,
                    )
                return LLMResponse(error=f"Error en AIML API ({resp.status_code}): {err_text}", success=False)

            data = resp.json()
            choice = data.get("choices", [{}])[0]
            msg_obj = choice.get("message", {})
            content = msg_obj.get("content", "") or ""
            reasoning = msg_obj.get("reasoning_content", "") or ""
            usage = data.get("usage", {}).get("total_tokens", 0)

            return LLMResponse(
                content=content,
                reasoning_content=reasoning,
                raw_response=data,
                tokens_used=usage,
                success=True,
            )
        except requests.exceptions.Timeout:
            return LLMResponse(error="Timeout de conexión con AIML API.", success=False)
        except Exception as e:
            return LLMResponse(error=f"Excepción en AIML API: {str(e)}", success=False)

    def test_connection(self, model: str) -> Tuple[bool, str]:
        clean_model = self._clean_model_name(model)
        test_messages = [{"role": "user", "content": "Responde únicamente 'OK'"}]
        res = self.chat_completion(clean_model, test_messages, max_tokens=15)
        if res.success:
            return True, f"Conexión exitosa con AIML API ({clean_model}): {res.content.strip() or 'OK'}"
        return False, res.error or "Error al conectar con AIML API"

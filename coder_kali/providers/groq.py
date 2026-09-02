"""
coder_kali/providers/groq.py - Driver independiente para Groq Cloud.
Inferencia de altísima velocidad vía API directa de Groq.
"""

from typing import Any, Dict, List, Tuple
import requests

from .base import BaseLLMProvider, LLMResponse


class GroqProvider(BaseLLMProvider):
    """Driver dedicado para Groq Cloud."""

    API_URL = "https://api.groq.com/openai/v1/chat/completions"

    def _clean_model_name(self, model: str) -> str:
        if not model:
            return "llama-3.3-70b-versatile"
        m = model.strip()
        if m.lower().startswith("groq/"):
            m = m[len("groq/"):]
        return m

    def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 1024,
        **kwargs,
    ) -> LLMResponse:
        clean_model = self._clean_model_name(model)
        api_key = self.config_mgr.get_api_key("groq")
        if not api_key:
            return LLMResponse(
                error="No hay API Key configurada para Groq. Ejecuta 'blood-cipher config'.",
                success=False,
            )

        headers = {
            "Authorization": f"Bearer {api_key.strip()}",
            "Content-Type": "application/json",
        }

        # Groq maneja un límite estricto de max_tokens según el tier gratuito
        capped_tokens = min(int(max_tokens), 4096)

        payload = {
            "model": clean_model,
            "messages": messages,
            "temperature": float(temperature),
            "max_tokens": capped_tokens,
        }

        try:
            resp = requests.post(self.API_URL, json=payload, headers=headers, timeout=60)
            
            if resp.status_code == 429:
                next_key = self.config_mgr.rotate_api_key("groq")
                if next_key and next_key != api_key:
                    headers["Authorization"] = f"Bearer {next_key.strip()}"
                    resp = requests.post(self.API_URL, json=payload, headers=headers, timeout=60)

            if resp.status_code != 200:
                err_text = resp.text
                if resp.status_code == 401:
                    return LLMResponse(
                        error="API Key de Groq inválida. Verifica tu clave en https://console.groq.com/.",
                        success=False,
                    )
                if resp.status_code == 429:
                    return LLMResponse(
                        error="Límite de tasa excedido en Groq (TPM/RPM). Espera unos segundos.",
                        success=False,
                    )
                return LLMResponse(error=f"Error en Groq (HTTP {resp.status_code}): {err_text}", success=False)

            data = resp.json()
            choice = data.get("choices", [{}])[0]
            content = choice.get("message", {}).get("content", "") or ""
            usage = data.get("usage", {}).get("total_tokens", 0)

            return LLMResponse(
                content=content,
                raw_response=data,
                tokens_used=usage,
                success=True,
            )

        except requests.exceptions.Timeout:
            return LLMResponse(error="Timeout de conexión con Groq.", success=False)
        except Exception as e:
            return LLMResponse(error=f"Excepción en Groq: {str(e)}", success=False)

    def test_connection(self, model: str) -> Tuple[bool, str]:
        clean_model = self._clean_model_name(model)
        test_messages = [{"role": "user", "content": "Responde únicamente 'OK'"}]
        res = self.chat_completion(clean_model, test_messages, max_tokens=15)
        if res.success:
            return True, f"Conexión exitosa con Groq ({clean_model}): {res.content.strip() or 'OK'}"
        return False, res.error or "Error al conectar con Groq"

"""
coder_kali/providers/fallback.py - Driver de respaldo para OpenAI, Anthropic y modelos genéricos.
"""

from typing import Any, Dict, List, Tuple
from .base import BaseLLMProvider, LLMResponse


class GenericLLMProvider(BaseLLMProvider):
    """Driver para OpenAI directo, Anthropic o endpoints personalizados mediante LiteLLM."""

    def __init__(self, config_mgr: Any, provider_name: str = "openai"):
        super().__init__(config_mgr)
        self.provider_name = provider_name

    def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        try:
            import litellm
            import os
            import logging
            
            # Silenciar logs ruidosos de LiteLLM
            litellm.suppress_debug_info = True
            litellm.drop_params = True
            logging.getLogger("LiteLLM").setLevel(logging.CRITICAL)

            api_key = self.config_mgr.get_api_key(self.provider_name)
            api_base = self.config_mgr.get_api_base(self.provider_name)

            call_kwargs: Dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": float(temperature),
                "max_tokens": int(max_tokens),
            }
            if api_key:
                call_kwargs["api_key"] = api_key.strip()
            if api_base:
                call_kwargs["api_base"] = api_base

            response = litellm.completion(**call_kwargs)
            choice = response.choices[0]
            raw_msg = getattr(choice, "message", None)
            content = getattr(raw_msg, "content", "") if raw_msg else ""
            reasoning = getattr(raw_msg, "reasoning_content", "") if raw_msg else ""

            return LLMResponse(
                content=content or "",
                reasoning_content=reasoning or "",
                raw_response=response.dict() if hasattr(response, "dict") else {},
                success=True,
            )
        except Exception as e:
            return LLMResponse(error=str(e), success=False)

    def test_connection(self, model: str) -> Tuple[bool, str]:
        test_messages = [{"role": "user", "content": "Responde únicamente 'OK'"}]
        res = self.chat_completion(model, test_messages, max_tokens=15)
        if res.success:
            return True, f"Conexión exitosa ({model}): {res.content.strip() or 'OK'}"
        return False, res.error or f"Error al conectar con {self.provider_name}"

"""
coder_kali/providers/base.py - Definición de la interfaz base para proveedores de IA.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class LLMResponse:
    """Respuesta unificada devuelta por cualquier proveedor de IA."""
    content: str = ""
    reasoning_content: str = ""
    raw_response: Dict[str, Any] = field(default_factory=dict)
    tokens_used: int = 0
    error: Optional[str] = None
    success: bool = True


class BaseLLMProvider(ABC):
    """Interfaz abstracta que todo driver de IA debe implementar."""

    def __init__(self, config_mgr: Any):
        self.config_mgr = config_mgr

    @abstractmethod
    def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        """Ejecuta una petición de completado de chat al proveedor."""
        pass

    @abstractmethod
    def test_connection(self, model: str) -> Tuple[bool, str]:
        """Prueba rápida de conectividad y validez de credenciales con el modelo."""
        pass

    def list_models(self) -> List[str]:
        """Lista los modelos disponibles en el proveedor si es soportado."""
        return []

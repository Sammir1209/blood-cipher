"""
coder_kali/agent.py - Conector Multi-IA (LiteLLM) y Bucle de Ejecución del Agente.
Gestiona el contexto de la conversación, envía el Mega-Prompt y ejecuta el bucle de herramientas XML.
"""

import os
import sys
from typing import List, Dict, Any, Optional, Generator
from rich.console import Console

from coder_kali.config import ConfigManager
from coder_kali.prompts import MEGA_PROMPT_SISTEMA
from coder_kali.system_executor import SystemExecutor, ExecutionResult
from coder_kali.tools_database import KaliToolsDatabase
from coder_kali.ui.chat_render import (
    render_ai_message,
    render_execution_result,
    render_error,
)

console = Console()


class KaliAgent:
    """Núcleo del agente de IA que gestiona el contexto y el ciclo de razonamiento/acción."""

    def __init__(
        self,
        config_mgr: Optional[ConfigManager] = None,
        system_executor: Optional[SystemExecutor] = None,
        tools_db: Optional[KaliToolsDatabase] = None,
        custom_system_prompt: Optional[str] = None,
    ):
        self.config_mgr = config_mgr or ConfigManager()
        self.executor = system_executor or SystemExecutor()
        self.tools_db = tools_db or KaliToolsDatabase()
        self.system_prompt = custom_system_prompt or MEGA_PROMPT_SISTEMA
        self.messages: List[Dict[str, str]] = []
        self.max_tool_iterations = 10
        self.reset_conversation()

    def reset_conversation(self):
        """Reinicia el historial de mensajes con el Mega-Prompt del sistema."""
        self.messages = [{"role": "system", "content": self.system_prompt}]

    def _prepare_call_kwargs(self) -> Dict[str, Any]:
        """Prepara los argumentos necesarios para la llamada a LiteLLM."""
        provider = self.config_mgr.get_active_provider()
        model = self.config_mgr.get_active_model()
        api_key = self.config_mgr.get_api_key(provider)
        api_base = self.config_mgr.get_api_base(provider)

        # Sincronizar variable de entorno para librerías subyacentes
        from coder_kali.config import DEFAULT_PROVIDERS
        env_var = DEFAULT_PROVIDERS.get(provider, {}).get("env_var")
        if env_var and api_key:
            os.environ[env_var] = api_key.strip()

        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": self.messages,
            "temperature": self.config_mgr.get("temperature", 0.2),
            "max_tokens": self.config_mgr.get("max_tokens", 4096),
        }

        if api_key:
            kwargs["api_key"] = api_key.strip()
        if api_base:
            kwargs["api_base"] = api_base

        return kwargs

    def send_message(self, user_text: str) -> str:
        """
        Envía un mensaje de usuario e inicia el bucle de ejecución de acciones XML.
        Retorna la respuesta final generada por el modelo.
        """
        # Detectar si se mencionan herramientas de Kali y adjuntar su sintaxis oficial
        tool_context = self.tools_db.detect_relevant_context(user_text)
        augmented_user_message = user_text
        if tool_context:
            augmented_user_message = f"{user_text}\n\n{tool_context}"

        self.messages.append({"role": "user", "content": augmented_user_message})

        iterations = 0
        final_response = ""

        while iterations < self.max_tool_iterations:
            iterations += 1

            # 1. Llamar al modelo con LiteLLM
            with console.status("[bold cyan]Coder-Kali está pensando...[/bold cyan]", spinner="dots"):
                try:
                    import litellm
                    litellm.suppress_debug_info = True
                    kwargs = self._prepare_call_kwargs()
                    response = litellm.completion(**kwargs)
                    choice = response.choices[0]
                    ai_content = getattr(choice.message, "content", "") or getattr(choice.message, "reasoning_content", "") or ""
                except ImportError:
                    err_msg = "El paquete 'litellm' no está instalado. Ejecuta: pip install -r requirements.txt"
                    render_error("Dependencia faltante", err_msg)
                    return f"Error: {err_msg}"
                except Exception as e:
                    render_error("Error al comunicarse con el proveedor de IA", str(e))
                    return f"Error: {str(e)}"

            # 2. Renderizar la respuesta del modelo
            render_ai_message(ai_content)
            self.messages.append({"role": "assistant", "content": ai_content})
            final_response = ai_content

            # 3. Detectar si hay acciones XML
            actions = self.executor.parse_actions(ai_content)
            if not actions:
                # No hay comandos ni archivos pendientes por ejecutar, fin del ciclo de razonamiento
                break

            # 4. Procesar cada acción interceptada
            results_feedback = []
            should_stop = False

            for action in actions:
                result = self.executor.process_action(action)
                render_execution_result(result, command=action.content if action.action_type == "command" else None)

                if action.action_type == "command":
                    feedback_str = (
                        f"[SALIDA_COMANDO: {action.content}]\n"
                        f"Código de retorno: {result.returncode}\n"
                        f"Éxito: {result.success}\n"
                        f"Salida:\n{result.output}"
                    )
                else:
                    feedback_str = (
                        f"[RESULTADO_ESCRITURA_ARCHIVO: {action.target_path}]\n"
                        f"Éxito: {result.success}\n"
                        f"Mensaje: {result.output}"
                    )

                results_feedback.append(feedback_str)

                # Si el usuario rechazó el comando, no ejecutar los subsecuentes del mismo paso
                if result.was_rejected:
                    should_stop = True
                    break

            # 5. Enviar el feedback de la terminal de regreso a la IA
            system_feedback_message = (
                "[RESULTADOS_SISTEMA_INTERCEPTADOS]\n"
                + "\n\n".join(results_feedback)
                + "\n\nPor favor interpreta estos resultados y procede con el siguiente paso."
            )
            self.messages.append({"role": "user", "content": system_feedback_message})

            if should_stop:
                console.print("[yellow][*] Secuencia detenida debido a que el operador rechazó una acción.[/yellow]")
                break

        return final_response

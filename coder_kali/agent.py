"""
coder_kali/agent.py - Conector Multi-IA (LiteLLM) y Bucle de Ejecución del Agente.
Gestiona el contexto de la conversación, envía el Mega-Prompt y ejecuta el bucle de herramientas XML.
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional, Generator
from rich.console import Console

# Silenciar warnings innecesarios de LiteLLM sobre mapas de costos
os.environ["LITELLM_LOG"] = "ERROR"
logging.getLogger("LiteLLM").setLevel(logging.ERROR)

from coder_kali.config import ConfigManager
from coder_kali.prompts import MEGA_PROMPT_SISTEMA
from coder_kali.system_executor import SystemExecutor, ExecutionResult
from coder_kali.tools_database import KaliToolsDatabase
from coder_kali.session_manager import SessionManager, ChatSession
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
        session_mgr: Optional[SessionManager] = None,
        session_id: Optional[str] = None,
        custom_system_prompt: Optional[str] = None,
    ):
        self.config_mgr = config_mgr or ConfigManager()
        self.executor = system_executor or SystemExecutor()
        self.tools_db = tools_db or KaliToolsDatabase()
        self.session_mgr = session_mgr or SessionManager()
        self.system_prompt = custom_system_prompt or MEGA_PROMPT_SISTEMA
        self.messages: List[Dict[str, str]] = []
        self.max_tool_iterations = 10

        # Cargar sesión existente o crear nueva
        provider = self.config_mgr.get_active_provider()
        model = self.config_mgr.get_active_model()
        if session_id:
            loaded_sess = self.session_mgr.get_session(session_id)
            if loaded_sess:
                self.current_session = loaded_sess
                self.messages = list(loaded_sess.messages) if loaded_sess.messages else [{"role": "system", "content": self.system_prompt}]
            else:
                self.current_session = self.session_mgr.create_session(provider, model)
                self.reset_conversation()
        else:
            self.current_session = self.session_mgr.create_session(provider, model)
            self.reset_conversation()

    def reset_conversation(self):
        """Reinicia el historial de mensajes con el Mega-Prompt del sistema."""
        self.messages = [{"role": "system", "content": self.system_prompt}]
        self.current_session.messages = list(self.messages)
        self.session_mgr.save_session(self.current_session)

    def _prune_context(self):
        """Mantiene el contexto compacto para no exceder los límites de tokens por minuto (TPM)."""
        if len(self.messages) <= 4:
            return

        # Mantener mensaje de sistema [0]
        system_msg = self.messages[0]
        # Recortar salidas de comandos antiguas de mensajes intermedios
        for i in range(1, len(self.messages) - 2):
            msg = self.messages[i]
            content = msg.get("content", "")
            if len(content) > 500:
                msg["content"] = content[:300] + "\n... [salida anterior resumida para ahorrar tokens] ..."

        # Si el historial tiene más de 8 mensajes, conservar solo los últimos 4
        if len(self.messages) > 8:
            self.messages = [system_msg] + self.messages[-4:]

    def _prepare_call_kwargs(self) -> Dict[str, Any]:
        """Prepara los argumentos necesarios para la llamada a LiteLLM."""
        self._prune_context()

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
            "max_tokens": min(self.config_mgr.get("max_tokens", 1500), 2048),
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

            # 1. Llamar al modelo con LiteLLM con reintentos automáticos en caso de Rate Limit
            ai_content = ""
            max_retries = 3
            retry_count = 0

            while retry_count < max_retries:
                with console.status("[bold cyan]Coder-Kali está pensando...[/bold cyan]", spinner="dots"):
                    try:
                        import litellm
                        import time
                        litellm.suppress_debug_info = True
                        kwargs = self._prepare_call_kwargs()
                        response = litellm.completion(**kwargs)
                        choice = response.choices[0]
                        ai_content = getattr(choice.message, "content", "") or getattr(choice.message, "reasoning_content", "") or ""
                        break
                    except ImportError:
                        err_msg = "El paquete 'litellm' no está instalado. Ejecuta: pip install -r requirements.txt"
                        render_error("Dependencia faltante", err_msg)
                        return f"Error: {err_msg}"
                    except Exception as e:
                        err_str = str(e)

                        # Si el mensaje es muy largo (Request too large), podar agresivamente y reintentar
                        if "request too large" in err_str.lower() or "reduce your message size" in err_str.lower():
                            console.print("[yellow][!] Historial muy extenso. Compactando contexto automáticamente...[/yellow]")
                            if len(self.messages) > 2:
                                self.messages = [self.messages[0], self.messages[-1]]
                            retry_count += 1
                            continue

                        # Si es un Rate Limit temporal (común en tiers gratuitos de Groq/Gemini)
                        if "RateLimitError" in type(e).__name__ or "rate_limit" in err_str.lower() or "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                            retry_count += 1
                            if retry_count < max_retries:
                                wait_seconds = 15
                                # Intentar extraer el tiempo exacto si viene en el mensaje de error (ej. retryDelay o try again in X.Xs)
                                import re
                                match = re.search(r"(?:retry in|retryDelay[\"':\s]+)(\d+(?:\.\d+)?)s?", err_str, re.IGNORECASE)
                                if match:
                                    wait_seconds = int(float(match.group(1))) + 2

                                console.print(f"[yellow][!] Límite de la API alcanzado. Reintentando automáticamente en {wait_seconds}s ({retry_count}/{max_retries})...[/yellow]")
                                time.sleep(wait_seconds)
                                continue
                        
                        render_error("Error al comunicarse con el proveedor de IA", err_str)
                        return f"Error: {err_str}"

            if not ai_content:
                return "No se pudo obtener respuesta del modelo debido a límites de la API."

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

        # Guardar historial actualizado en la sesión persistente
        self.current_session.messages = list(self.messages)
        self.session_mgr.save_session(self.current_session)

        return final_response

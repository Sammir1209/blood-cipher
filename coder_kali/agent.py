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
from coder_kali.prompts import MEGA_PROMPT_SISTEMA, PROMPT_PLANNING_MODE
from coder_kali.system_executor import SystemExecutor, ExecutionResult
from coder_kali.tools_database import KaliToolsDatabase
from coder_kali.session_manager import SessionManager, ChatSession
from coder_kali.scope_manager import ScopeManager
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
        scope_mgr: Optional[ScopeManager] = None,
        session_id: Optional[str] = None,
        custom_system_prompt: Optional[str] = None,
        planning_mode: bool = False,
    ):
        self.config_mgr = config_mgr or ConfigManager()
        self.executor = system_executor or SystemExecutor()
        self.tools_db = tools_db or KaliToolsDatabase()
        self.session_mgr = session_mgr or SessionManager()
        self.scope_mgr = scope_mgr or ScopeManager()
        self.planning_mode = planning_mode
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
                self.messages = list(loaded_sess.messages) if loaded_sess.messages else [{"role": "system", "content": self._get_effective_system_prompt()}]
            else:
                self.current_session = self.session_mgr.create_session(provider, model)
                self.reset_conversation()
        else:
            self.current_session = self.session_mgr.create_session(provider, model)
            self.reset_conversation()

    def _get_effective_system_prompt(self) -> str:
        """Construye el prompt de sistema directo."""
        prompt = self.system_prompt
        active_scope = self.scope_mgr.get_active_scope_content()
        if active_scope:
            prompt += f"\n\n[CONTEXTO OPERATIVO / OBJETIVO]\n{active_scope}"
        if self.planning_mode:
            prompt += f"\n\n{PROMPT_PLANNING_MODE}"
        return prompt

    def reset_conversation(self):
        """Reinicia el historial de mensajes con el Mega-Prompt del sistema."""
        self.messages = [{"role": "system", "content": self._get_effective_system_prompt()}]
        self.current_session.messages = list(self.messages)
        self.session_mgr.save_session(self.current_session)

    def _get_api_messages(self) -> List[Dict[str, str]]:
        """
        Genera una versión optimizada del historial para la API sin destruir
        la memoria persistente de la sesión del usuario.
        Aplica compactación agresiva cuando el proveedor es Groq para evitar rebasar los límites de TPM.
        """
        effective_sys = self._get_effective_system_prompt()
        if not self.messages:
            return [{"role": "system", "content": effective_sys}]

        provider = self.config_mgr.get_active_provider()
        is_groq = provider == "groq"

        # Mensaje de sistema al inicio
        system_msg = {"role": "system", "content": effective_sys}
        
        # Filtrar mensajes de conversación (omitir sistema previo si estaba duplicado)
        chat_msgs = [m for m in self.messages if m.get("role") != "system"]

        # En Groq, conservar máximo 6 turnos para no agotar el límite de tokens por minuto (TPM)
        max_history = 6 if is_groq else 16
        recent_msgs = chat_msgs[-max_history:] if len(chat_msgs) > max_history else chat_msgs

        api_messages: List[Dict[str, str]] = [system_msg]
        
        for i, m in enumerate(recent_msgs):
            role = m.get("role", "user")
            content = m.get("content", "")

            # Limpiar bloques <think> o reasoning internos que puedan saturar el contexto
            import re
            content = re.sub(r'<think>[\s\S]*?</think>', '', content).strip()

            # Compactar salidas de terminal para no consumir TPM innecesario
            is_latest = i == (len(recent_msgs) - 1)
            max_char_limit = 1500 if is_latest else (500 if is_groq else 1000)

            if "[RESULTADOS_SISTEMA" in content or "[SALIDA_COMANDO" in content:
                if len(content) > max_char_limit:
                    compacted_content = content[:int(max_char_limit * 0.7)] + "\n... [salida de terminal resumida] ...\n" + content[-int(max_char_limit * 0.3):]
                    api_messages.append({"role": role, "content": compacted_content})
                    continue

            api_messages.append({"role": role, "content": content})

        return api_messages

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

        # En Groq limitar max_tokens a un valor prudente (ej. 1024) para no agotar TPM solicitado
        configured_max = self.config_mgr.get("max_tokens", 1500)
        max_tokens = min(configured_max, 1024 if provider == "groq" else 2048)

        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": self._get_api_messages(),
            "temperature": self.config_mgr.get("temperature", 0.2),
            "max_tokens": max_tokens,
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
        results_feedback: List[str] = []
        should_stop = False

        while iterations < self.max_tool_iterations:
            iterations += 1

            # 1. Llamar al modelo con LiteLLM con reintentos automáticos en caso de Rate Limit
            ai_content = ""
            max_retries = 5
            retry_count = 0

            while retry_count < max_retries:
                with console.status("[bold cyan]Blood-Cipher está pensando...[/bold cyan]", spinner="dots"):
                    try:
                        provider = self.config_mgr.get_active_provider()
                        model = self.config_mgr.get_active_model()

                        # Fast-Path: Inferencia directa ultrarrápida si el modelo es Ollama
                        if provider == "ollama":
                            from coder_kali.fast_engine import OllamaFastClient
                            api_base = self.config_mgr.get_api_base(provider) or "http://localhost:11434"
                            ollama_client = OllamaFastClient(host=api_base)
                            res = ollama_client.chat_completion(
                                model=model,
                                messages=self._get_api_messages(),
                                temperature=self.config_mgr.get("temperature", 0.2),
                                timeout=300,
                            )
                            if "content" in res and res["content"]:
                                ai_content = res["content"]
                                break
                            elif "error" in res:
                                render_error("Error de Inferencia Ollama", res["error"])
                                return f"Error al comunicar con Ollama: {res['error']}"

                        import litellm
                        import time
                        litellm.suppress_debug_info = True
                        litellm.drop_params = True
                        kwargs = self._prepare_call_kwargs()
                        response = litellm.completion(**kwargs)
                        choice = response.choices[0]
                        ai_content = getattr(choice.message, "content", "") or getattr(choice.message, "reasoning_content", "") or ""
                        if ai_content:
                            import re
                            ai_content = re.sub(r'<think>[\s\S]*?</think>', '', ai_content, flags=re.IGNORECASE).strip()
                            ai_content = re.sub(r'```(?:thought|thinking|reasoning)[\s\S]*?```', '', ai_content, flags=re.IGNORECASE).strip()
                        break
                    except ImportError:
                        err_msg = "El paquete 'litellm' no está instalado. Ejecuta: pip install -r requirements.txt"
                        render_error("Dependencia faltante", err_msg)
                        return f"Error: {err_msg}"
                    except Exception as e:
                        err_str = str(e)

                        # Caso especial Groq: 'Tool choice is none, but model called a tool'
                        # Groq incluye el contenido generado completo en 'failed_generation'
                        if "tool_use_failed" in err_str or "failed_generation" in err_str or "Tool choice is none" in err_str:
                            import re
                            try:
                                idx = err_str.find('"failed_generation":')
                                if idx != -1:
                                    raw = err_str[idx + len('"failed_generation":'):].strip()
                                    if raw.startswith('"'):
                                        raw = raw[1:]
                                    raw = re.sub(r'\"\}\}\s*$', '', raw)
                                    raw = re.sub(r'\}\}\s*$', '', raw)
                                    raw = re.sub(r'\"$', '', raw)
                                    try:
                                        decoded = raw.encode('utf-8').decode('unicode_escape')
                                    except Exception:
                                        decoded = raw.replace('\\u003c', '<').replace('\\u003e', '>').replace('\\n', '\n').replace('\\"', '"')

                                    extracted = None
                                    if '"arguments":' in decoded:
                                        arg_idx = decoded.find('"arguments":')
                                        extracted = decoded[arg_idx + len('"arguments":'):].strip()
                                    elif 'arguments:' in decoded:
                                        arg_idx = decoded.find('arguments:')
                                        extracted = decoded[arg_idx + len('arguments:'):].strip()
                                    else:
                                        extracted = decoded.strip()

                                    if extracted:
                                        if extracted.startswith('"') and extracted.endswith('"'):
                                            extracted = extracted[1:-1]
                                        if extracted.endswith('}'):
                                            extracted = extracted[:-1].strip()
                                        
                                        # Limpiar bloques <think> o ```thought
                                        extracted = re.sub(r'<think>[\s\S]*?</think>', '', extracted, flags=re.IGNORECASE).strip()
                                        extracted = re.sub(r'```(?:thought|thinking|reasoning)[\s\S]*?```', '', extracted, flags=re.IGNORECASE).strip()

                                        # Si el JSON extrajo un comando directo o texto
                                        ai_content = extracted
                                        break
                            except Exception:
                                pass

                        # Si el mensaje es muy largo (Request too large), podar agresivamente y reintentar
                        if "request too large" in err_str.lower() or "reduce your message size" in err_str.lower():
                            console.print("[yellow][!] Historial muy extenso. Compactando contexto automáticamente...[/yellow]")
                            if len(self.messages) > 2:
                                self.messages = [self.messages[0], self.messages[-1]]
                            retry_count += 1
                            continue

                        # Si es un Rate Limit temporal (común en tiers gratuitos de Groq/Gemini)
                        if "RateLimitError" in type(e).__name__ or "rate_limit" in err_str.lower() or "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "tpm" in err_str.lower():
                            retry_count += 1
                            # Compactar el historial de inmediato ante saturación de TPM
                            if len(self.messages) > 3:
                                self.messages = [self.messages[0], self.messages[-2], self.messages[-1]]

                            if retry_count < max_retries:
                                wait_seconds = 12 + (retry_count * 4)
                                import re
                                match = re.search(r"(?:retry in|retryDelay[\"':\s]+|try again in\s+)(\d+(?:\.\d+)?)s?", err_str, re.IGNORECASE)
                                if match:
                                    wait_seconds = max(int(float(match.group(1))) + 2, 5)

                                console.print(f"[yellow][!] Límite de tasa de tokens (TPM) alcanzado en Groq/API. Esperando {wait_seconds}s (Reintento {retry_count}/{max_retries})...[/yellow]")
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

        # Turno de análisis e interpretación interactiva de resultados para el operador
        if results_feedback and not should_stop:
            try:
                synth_prompt = (
                    "Interpreta ahora los resultados obtenidos de la terminal de forma detallada e interactiva. "
                    "Explica al operador qué tecnologías, puertos, cabeceras o hallazgos interesantes descubriste y cuál es el siguiente paso lógico."
                )
                self.messages.append({"role": "user", "content": synth_prompt})
                synth_text = ""
                provider = self.config_mgr.get_active_provider()
                model = self.config_mgr.get_active_model()
                if provider == "ollama":
                    from coder_kali.fast_engine import OllamaFastClient
                    api_base = self.config_mgr.get_api_base(provider) or "http://localhost:11434"
                    ollama_client = OllamaFastClient(host=api_base)
                    res = ollama_client.chat_completion(
                        model=model,
                        messages=self._get_api_messages(),
                        temperature=self.config_mgr.get("temperature", 0.2),
                        timeout=180,
                    )
                    synth_text = res.get("content", "")
                else:
                    import litellm
                    litellm.drop_params = True
                    kwargs = self._prepare_call_kwargs()
                    res = litellm.completion(**kwargs)
                    choice = res.choices[0]
                    synth_text = getattr(choice.message, "content", "") or getattr(choice.message, "reasoning_content", "") or ""

                if synth_text:
                    import re
                    synth_text = re.sub(r'<think>[\s\S]*?</think>', '', synth_text, flags=re.IGNORECASE).strip()
                    synth_text = re.sub(r'```(?:thought|thinking|reasoning)[\s\S]*?```', '', synth_text, flags=re.IGNORECASE).strip()
                    if synth_text:
                        final_response = synth_text
                        render_ai_message(synth_text)
                        self.messages.append({"role": "assistant", "content": synth_text})
            except Exception:
                pass

        # Guardar historial actualizado en la sesión persistente
        self.current_session.messages = list(self.messages)
        self.session_mgr.save_session(self.current_session)

        return final_response

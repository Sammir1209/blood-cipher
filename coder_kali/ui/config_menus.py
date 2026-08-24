import os
import sys
from typing import Optional, List, Dict, Any
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from coder_kali.config import ConfigManager, DEFAULT_PROVIDERS
from coder_kali.model_discovery import fetch_live_models

console = Console()


def interactive_config_wizard(config_mgr: ConfigManager) -> bool:
    """Guía al usuario paso a paso en la configuración de Blood-Cipher."""
    console.print()
    console.print(
        Panel(
            "[bold cyan]Asistente de Configuración de Modelos y Credenciales de IA[/bold cyan]\n"
            "[dim]Elige tu proveedor preferido e introduce tu clave de API si es requerida.[/dim]",
            title="⚙️ CONFIGURACIÓN BLOOD-CIPHER",
            border_style="cyan",
        )
    )

    # 1. Selección de Proveedor
    provider_choices = [
        questionary.Choice(
            title=f"{info['name']} ({prov})",
            value=prov
        )
        for prov, info in DEFAULT_PROVIDERS.items()
    ]

    current_provider = config_mgr.get_active_provider()
    default_choice = next((c for c in provider_choices if c.value == current_provider), provider_choices[0])

    chosen_provider = questionary.select(
        "Elige tu proveedor de Inteligencia Artificial:",
        choices=provider_choices,
        default=default_choice,
    ).ask()

    if not chosen_provider:
        console.print("[yellow][*] Configuración cancelada.[/yellow]")
        return False

    prov_meta = DEFAULT_PROVIDERS[chosen_provider]

    # 2. Solicitar API Key o Endpoint URL PRIMERO
    api_key = ""
    api_base = None

    if prov_meta.get("requires_api_key", True):
        current_key = config_mgr.get_api_key(chosen_provider)
        key_count = config_mgr.get_api_key_count(chosen_provider)
        key_hint = f" (Actual: {'*'*6}...{current_key[-4:]})" if current_key and len(current_key) > 8 else ""
        if key_count > 1:
            key_hint += f" [{key_count} keys en pool]"

        entered_key = questionary.password(
            f"Ingresa tu API Key para {prov_meta['name']}{key_hint}:"
        ).ask()

        if entered_key and entered_key.strip():
            api_key = entered_key.strip()
            config_mgr.set_api_key(chosen_provider, api_key)
        else:
            api_key = current_key or ""

        if not api_key:
            console.print("[yellow][!] Advertencia: No se proporcionó API Key para este proveedor.[/yellow]")

        # Ofrecer configurar múltiples keys para rotación automática
        if api_key:
            add_more = questionary.confirm(
                f"¿Deseas agregar más API Keys de {prov_meta['name']} para rotación automática? (evita rate limits)",
                default=False
            ).ask()
            if add_more:
                all_keys = [api_key]
                console.print("[dim]Pega cada API Key adicional (una por línea). Escribe 'FIN' para terminar:[/dim]")
                while True:
                    extra_key = questionary.password("API Key adicional (o 'FIN'):").ask()
                    if not extra_key or extra_key.strip().upper() == "FIN":
                        break
                    if extra_key.strip():
                        all_keys.append(extra_key.strip())
                        console.print(f"[green]  ✓ Key #{len(all_keys)} agregada[/green]")
                if len(all_keys) > 1:
                    config_mgr.set_api_keys(chosen_provider, all_keys)
                    console.print(f"[bold green][✓] {len(all_keys)} API Keys configuradas para rotación automática en {prov_meta['name']}[/bold green]")
    else:
        # Proveedor sin API Key (como Ollama)
        current_base = config_mgr.get_api_base(chosen_provider) or prov_meta.get("default_api_base", "http://localhost:11434")
        api_base = questionary.text(
            f"Endpoint URL de {prov_meta['name']}:",
            default=current_base,
        ).ask()
        if api_base:
            if "api_bases" not in config_mgr.config:
                config_mgr.config["api_bases"] = {}
            config_mgr.config["api_bases"][chosen_provider] = api_base.strip()

    # 3. Consultar modelos activos en vivo desde la API del proveedor
    live_models = []
    with console.status(f"[bold cyan]Consultando modelos activos en tiempo real para {prov_meta['name']}...[/bold cyan]", spinner="dots"):
        live_models = fetch_live_models(chosen_provider, api_key=api_key, api_base=api_base)

    if live_models:
        console.print(f"[bold green][✓] Se detectaron {len(live_models)} modelos activos disponibles en tu cuenta.[/bold green]")
        model_choices = list(live_models)
    else:
        # Fallback a la lista curada si no fue posible consultar en vivo
        model_choices = list(prov_meta.get("available_models", []))

    model_choices.append("Personalizado (Escribir manualmente)")

    current_model = config_mgr.get_active_model()
    default_model = current_model if current_model in model_choices else model_choices[0]

    # 4. Selección del modelo activo
    chosen_model = questionary.select(
        f"Elige el modelo para {prov_meta['name']}:",
        choices=model_choices,
        default=default_model,
    ).ask()

    if not chosen_model:
        return False

    if chosen_model.startswith("Personalizado"):
        custom_model = questionary.text(
            "Ingresa el identificador exacto del modelo (ej. groq/qwen/qwen3.6-27b, gemini/gemini-2.5-flash):",
            default=prov_meta["default_model"],
        ).ask()
        if custom_model:
            chosen_model = custom_model.strip()
        else:
            chosen_model = prov_meta["default_model"]

    # Guardar proveedor y modelo
    config_mgr.set_provider(chosen_provider, chosen_model)

    console.print()
    console.print("[bold green][✓] ¡Configuración guardada correctamente en ~/.config/blood-cipher/config.json![/bold green]")
    console.print(f"[cyan]Proveedor activo:[/cyan] {chosen_provider.upper()} | [yellow]Modelo:[/yellow] {chosen_model}")

    # Probar conexión opcionalmente
    test_now = questionary.confirm("¿Deseas realizar un test de conexión ahora?", default=True).ask()
    if test_now:
        test_provider_connection(config_mgr)

    return True


def test_provider_connection(config_mgr: ConfigManager) -> bool:
    """Prueba la conexión con el modelo configurado mediante LiteLLM."""
    import litellm
    from rich.status import Status

    provider = config_mgr.get_active_provider()
    model = config_mgr.get_active_model()
    api_key = config_mgr.get_api_key(provider)
    api_base = config_mgr.get_api_base(provider)

    # Sincronizar variable de entorno para librerías subyacentes
    env_var = DEFAULT_PROVIDERS.get(provider, {}).get("env_var")
    if env_var and api_key:
        os.environ[env_var] = api_key.strip()

    console.print()
    with console.status(f"[bold cyan]Probando comunicación con {model}...[/bold cyan]", spinner="dots"):
        try:
            if provider == "ollama":
                from coder_kali.fast_engine import OllamaFastClient
                fast_client = OllamaFastClient(host=api_base or "http://localhost:11434")
                if not fast_client.is_online():
                    console.print("[bold red][✗] El servicio de Ollama no está activo en http://localhost:11434.[/bold red]")
                    console.print("[dim]Inicia el servicio ejecutando: 'ollama serve' o 'sudo systemctl start ollama'.[/dim]")
                    return False

                res = fast_client.chat_completion(
                    model=model,
                    messages=[{"role": "user", "content": "Responde únicamente 'OK'"}],
                    timeout=180,
                )
                if "error" in res:
                    console.print(f"[bold red][✗] Error de Ollama:[/bold red] {res['error']}")
                    return False
                reply = res.get("content", "OK (Conexión establecida)").strip()
                console.print(f"[bold green][✓] Test exitoso. Respuesta del modelo:[/bold green] [white]{reply}[/white]")
                return True

            kwargs = {
                "model": model,
                "messages": [{"role": "user", "content": "Responde únicamente 'OK'"}],
                "max_tokens": 50,
            }
            if api_key:
                kwargs["api_key"] = api_key.strip()
            if api_base:
                kwargs["api_base"] = api_base

            response = litellm.completion(**kwargs)
            choice = response.choices[0]
            raw_content = getattr(choice.message, "content", None) or getattr(choice.message, "reasoning_content", None) or "OK (Conexión establecida)"
            reply = str(raw_content).strip()
            console.print(f"[bold green][✓] Test exitoso. Respuesta del modelo:[/bold green] [white]{reply}[/white]")
            return True
        except Exception as e:
            console.print(f"[bold red][✗] Falló la prueba de conexión:[/bold red] {str(e)}")
            console.print("[dim]Verifica tu API Key, conexión a internet o endpoint de Ollama.[/dim]")
            return False

"""
coder_kali/ui/config_menus.py - Menús interactivos con Questionary.
Permite configurar el proveedor de IA, modelo, API Key y probar conectividad.
"""

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from coder_kali.config import ConfigManager, DEFAULT_PROVIDERS

console = Console()


def interactive_config_wizard(config_mgr: ConfigManager) -> bool:
    """Guía al usuario paso a paso en la configuración de Coder-Kali."""
    console.print()
    console.print(
        Panel(
            "[bold cyan]Asistente Interactivo de Configuración de IA[/bold cyan]\n"
            "[dim]Selecciona tu proveedor, modelo y credenciales de acceso.[/dim]",
            title="⚙️ CONFIGURACIÓN CODER-KALI",
            border_style="cyan",
        )
    )

    # 1. Selección de Proveedor
    provider_choices = [
        {"name": f"{info['name']} ({prov})", "value": prov}
        for prov, info in DEFAULT_PROVIDERS.items()
    ]

    current_provider = config_mgr.get_active_provider()
    chosen_provider = questionary.select(
        "Elige tu proveedor de Inteligencia Artificial:",
        choices=provider_choices,
        default=current_provider,
    ).ask()

    if not chosen_provider:
        console.print("[yellow][*] Configuración cancelada.[/yellow]")
        return False

    prov_meta = DEFAULT_PROVIDERS[chosen_provider]

    # 2. Selección de Modelo
    model_choices = prov_meta.get("available_models", [])
    model_choices.append("Personalizado (Escribir manualmente)")

    current_model = config_mgr.get_active_model()
    chosen_model = questionary.select(
        f"Elige el modelo para {prov_meta['name']}:",
        choices=model_choices,
        default=current_model if current_model in model_choices else prov_meta["default_model"],
    ).ask()

    if not chosen_model:
        return False

    if chosen_model.startswith("Personalizado"):
        custom_model = questionary.text(
            "Ingresa el identificador exacto del modelo (ej. gemini/gemini-2.5-pro, deepseek/deepseek-chat):",
            default=prov_meta["default_model"],
        ).ask()
        if custom_model:
            chosen_model = custom_model.strip()
        else:
            chosen_model = prov_meta["default_model"]

    # 3. Clave de API o Base URL
    if prov_meta.get("requires_api_key", True):
        current_key = config_mgr.get_api_key(chosen_provider)
        key_hint = f" (Actual: {'*'*6}...{current_key[-4:]})" if current_key and len(current_key) > 8 else ""

        api_key = questionary.password(
            f"Ingresa tu API Key para {prov_meta['name']}{key_hint}:"
        ).ask()

        if api_key and api_key.strip():
            config_mgr.set_api_key(chosen_provider, api_key.strip())
        elif not current_key:
            console.print("[yellow][!] Advertencia: No se proporcionó API Key para este proveedor.[/yellow]")
    else:
        # Proveedor sin API Key requerida (como Ollama)
        current_base = config_mgr.get_api_base(chosen_provider) or prov_meta.get("default_api_base", "http://localhost:11434")
        api_base = questionary.text(
            f"Endpoint URL de {prov_meta['name']}:",
            default=current_base,
        ).ask()
        if api_base:
            if "api_bases" not in config_mgr.config:
                config_mgr.config["api_bases"] = {}
            config_mgr.config["api_bases"][chosen_provider] = api_base.strip()

    # Guardar proveedor y modelo
    config_mgr.set_provider(chosen_provider, chosen_model)

    console.print()
    console.print("[bold green][✓] ¡Configuración guardada correctamente en ~/.config/coder-kali/config.json![/bold green]")
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

    console.print()
    with console.status(f"[bold cyan]Probando comunicación con {model}...[/bold cyan]", spinner="dots"):
        try:
            kwargs = {
                "model": model,
                "messages": [{"role": "user", "content": "Responde únicamente 'OK'"}],
                "max_tokens": 10,
            }
            if api_key:
                kwargs["api_key"] = api_key
            if api_base:
                kwargs["api_base"] = api_base

            response = litellm.completion(**kwargs)
            reply = response.choices[0].message.content.strip()
            console.print(f"[bold green][✓] Test exitoso. Respuesta del modelo:[/bold green] [white]{reply}[/white]")
            return True
        except Exception as e:
            console.print(f"[bold red][✗] Falló la prueba de conexión:[/bold red] {str(e)}")
            console.print("[dim]Verifica tu API Key, conexión a internet o endpoint de Ollama.[/dim]")
            return False

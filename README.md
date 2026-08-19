# ⚡ Coder-Kali

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Kali-red.svg)](https://www.kali.org/)
[![LiteLLM](https://img.shields.io/badge/Multi--LLM-LiteLLM-purple.svg)](https://litellm.ai/)

**Coder-Kali** es un agente de Inteligencia Artificial autónomo y supervisado diseñado específicamente para entornos Linux (Kali Linux, Debian, Ubuntu, Arch), enfocado en **ciberseguridad, hacking ético, auditoría de código, pentesting y administración de sistemas**.

Integra modelos de lenguaje de vanguardia (**Google Gemini, OpenAI, Claude 3.5 Sonnet, DeepSeek R1, Groq, Ollama**) con una terminal interactiva nativa protegida por **PTY** y confirmación explícita del operador humano.

---

## 🎯 Características Principales

- 🛡️ **Supervisión y Seguridad por Diseño**: La IA nunca ejecuta comandos sin tu autorización explícita.
- ⚡ **Soporte Nativo de PTY & `sudo`**: Manejo seguro e interactivo de contraseñas de superusuario en la consola sin fugas de credenciales.
- 🧠 **Multi-Proveedor (LiteLLM)**: Conéctate con Gemini, Claude, GPT-4o, DeepSeek, Groq o modelos 100% locales con Ollama.
- 🎨 **TUI Cyberpunk (Rich)**: Interfaz de terminal con colores vivos, formateo Markdown, bloques de código resaltados y paneles de advertencia.
- 📜 **Protocolo de Acción XML**: Intercepta comandos del sistema (`<ejecutar_comando>`) y escritura de archivos (`<escribir_archivo>`).
- 🔌 **Extensión para VS Code**: Integración en el editor para auditar archivos y abrir sesiones en un solo clic.

---

## 📁 Estructura del Repositorio

```plaintext
coder-kali/
├── install.sh                 # Instalador interactivo nativo para distribuciones Linux
├── setup.py                   # Configuración de empaquetado para Python
├── requirements.txt           # Dependencias (litellm, rich, typer, questionary, etc.)
├── README.md                  # Documentación oficial
│
├── coder_kali/                # [NÚCLEO DEL SISTEMA PYTHON]
│   ├── __init__.py
│   ├── cli.py                 # Enrutador principal de comandos (Typer)
│   ├── config.py              # Gestor de credenciales y rutas (~/.config/coder-kali)
│   ├── agent.py               # Conector multi-IA (LiteLLM) y gestión del contexto
│   ├── prompts.py             # Archivo dedicado a almacenar el Mega-Prompt
│   ├── system_executor.py     # Ejecutor seguro de comandos Linux y gestor PTY (Sudo)
│   └── ui/                    # Interfaz de Usuario de Terminal (TUI)
│       ├── __init__.py
│       ├── chat_render.py     # Dibuja el chat con colores y tablas (Rich)
│       └── config_menus.py    # Menús interactivos de selección de IA (Questionary)
│
└── vscode_extension/          # [INTERFAZ VISUAL VS CODE - FASE 2]
    ├── package.json           # Configuración de la extensión Node.js
    ├── tsconfig.json          # Configuración TypeScript
    └── src/
        └── extension.ts       # Puente TypeScript con coder-kali
```

---

## 🚀 Instalación Rápida (Linux / Kali)

Clona el repositorio y ejecuta el instalador nativo:

```bash
git clone https://github.com/Sammir1209/coder-kali.git
cd coder-kali
bash install.sh
```

El script se encargará de:
1. Validar el entorno Linux y Python 3.
2. Crear un entorno virtual aislado en `~/.local/share/coder-kali/env`.
3. Instalar todas las dependencias sin interferir con los paquetes del sistema.
4. Generar el binario/enlace simbólico global en `/usr/local/bin/coder-kali`.

---

## ⚙️ Configuración Inicial

Para configurar tu modelo y API Key preferida, ejecuta:

```bash
coder-kali config
```

Aparecerá un menú interactivo:

```plaintext
? Elige tu proveedor de Inteligencia Artificial:
  ▸ Google Gemini (gemini)
    Anthropic Claude (anthropic)
    OpenAI (openai)
    DeepSeek (deepseek)
    Groq (Ultra Rápido) (groq)
    Ollama (100% Local / Offline) (ollama)
    OpenRouter (openrouter)
```

Las credenciales se almacenan localmente y cifradas en `~/.config/coder-kali/config.json`.

---

## 💻 Uso

### 1. Modo Conversacional Táctico
Inicia el chat interactivo ejecutando simplemente:

```bash
coder-kali
# o también:
coder-kali chat
```

### 2. Ejecución Directa en Una Línea
Para resolver una tarea puntual sin ingresar al chat:

```bash
coder-kali run "Escanea los puertos abiertos en localhost y sugiere remediaciones de seguridad"
```

### 3. Diagnóstico del Entorno
Comprueba si tus herramientas de pentesting están listas:

```bash
coder-kali doctor
```

---

## 🛡️ Protocolo de Acción XML & Seguridad

Coder-Kali opera bajo un estricto protocolo de delimitadores XML interceptados por el backend:

```xml
<ejecutar_comando>
sudo nmap -sS -p- -T4 127.0.0.1
</ejecutar_comando>
```

```xml
<escribir_archivo ruta="/home/user/script_auditoria.sh">
#!/bin/bash
echo "Auditoría en curso..."
</escribir_archivo>
```

Cada bloque es interceptado por `system_executor.py`, mostrando un panel con resaltado de sintaxis y solicitando:

```plaintext
¿Autorizar ejecución? [s/N]:
```

---

## ⚖️ Descargo de Responsabilidad (Disclaimer)

Esta herramienta está destinada exclusivamente para **auditorías de seguridad autorizadas, investigación defensiva, hacking ético y administración legítima de sistemas**. El uso de esta herramienta contra objetivos sin autorización previa y por escrito es estrictamente ilegal. Los desarrolladores no se hacen responsables del mal uso de este software.

---

## 📄 Licencia

Distribuido bajo la Licencia **MIT**. Consulta el archivo `LICENSE` para más detalles.

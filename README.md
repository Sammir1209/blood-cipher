# Blood-Cipher

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/Version-v1.5.0-red.svg?style=for-the-badge)](https://github.com/Sammir1209/coder-kali)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Kali%20%7C%20BlackArch%20%7C%20Arch%20%7C%20Debian%20%7C%20Ubuntu-557C94.svg?style=for-the-badge&logo=linux&logoColor=white)](https://www.kali.org/)
[![LiteLLM](https://img.shields.io/badge/Multi--LLM-Gemini%20%7C%20Claude%20%7C%20GPT--4o%20%7C%20DeepSeek%20%7C%20Ollama-8A2BE2.svg?style=for-the-badge)](https://litellm.ai/)
[![Web UI](https://img.shields.io/badge/Interface-CLI%20%2B%20Web%20Dashboard%20(Port%207777)-00FF9D.svg?style=for-the-badge)](http://localhost:7777)

<p align="center">
  <strong>Agente Autónomo de Inteligencia Artificial para Hacktivismo Técnico, Reconocimiento 360°, Auditoría de Redes, OSINT y Soberanía Digital en Linux.</strong>
</p>

```
  ██████╗ ██╗      ██████╗  ██████╗ ██████╗       ██████╗██╗██████╗ ██╗  ██╗███████╗██████╗ 
  ██╔══██╗██║     ██╔═══██╗██╔═══██╗██╔══██╗     ██╔════╝██║██╔══██╗██║  ██║██╔════╝██╔══██╗
  ██████╔╝██║     ██║   ██║██║   ██║██║  ██║     ██║     ██║██████╔╝███████║█████╗  ██████╔╝
  ██╔══██╗██║     ██║   ██║██║   ██║██║  ██║     ██║     ██║██╔═══╝ ██╔══██║██╔══╝  ██╔══██╗
  ██████╔╝███████╗╚██████╔╝╚██████╔╝██████╔╝     ╚██████╗██║██║     ██║  ██║███████╗██║  ██║
  ╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝       ╚═════╝╚═╝╚═╝     ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
          [ NÚCLEO TÁCTICO PARA HACKTIVISMO, OSINT & AUDITORÍA LIBRE // v1.5 ]
```

</div>

---

## [01] Visión General

**Blood-Cipher v1.5** es una plataforma táctica impulsada por IA diseñada para la **comunidad hacktivista, investigadores de ciberinteligencia independiente (OSINT), auditores de infraestructura y defensores de la soberanía digital**. Combina la potencia de modelos de lenguaje de última generación (**Google Gemini, Claude 3.5 Sonnet, OpenAI o1/GPT-4o, DeepSeek R1, Groq y Ollama 100% Offline**) con el arsenal técnico de **Kali Linux, BlackArch, Arch Linux, Debian y Ubuntu**.

Ofrece un centro de mando unificado para operaciones tácticas:
- **Terminal Táctico (CLI):** Control interactivo PTY, análisis de credenciales y subcomandos de red (`blood-cipher`).
- **Centro de Mando Web (Dashboard):** Escaneo visual 360°, auditoría de credenciales y radar de vulnerabilidades en tiempo real.

---

## [02] Capacidades Principales

### [›] Inteligencia Artificial Multi-Proveedor
- Compatible con **OpenAI, Anthropic, Google Gemini, DeepSeek, Groq, OpenRouter** y modelos 100% locales y offline mediante **Ollama**.
- Detección automática y conmutación ágil de modelos en caliente.

### [›] Modo Planificación Táctico (Planning Mode)
- Generación de planes de implementación paso a paso antes de ejecutar cualquier comando en el sistema.
- Control granular con botón de autorización explícita (*Proceed / Step-by-Step*).

### [›] Gestor de Alcance y Autorización (SOW / ROE)
- Carga y validación de documentos formales de alcance (*Statement of Work* y *Rules of Engagement*).
- Prevención de acciones fuera del perímetro acordado durante la auditoría.

### [›] Módulos Profesionales de Auditoría (`blood-cipher audit`)

| Módulo | Comando CLI | Capacidades Técnicas |
|---|---|---|
| **Credenciales & Hashes** | `blood-cipher audit creds` | Detección automática de algoritmos (MD5, SHA1/256/512, NTLM, bcrypt), cracking nativo en memoria con Python, wrappers para `John the Ripper` y `Hashcat` (GPU), evaluador de entropía/fortaleza y parser de `/etc/shadow` / volcados SAM. |
| **Vulnerabilidades** | `blood-cipher audit vulns` | Escaneo automatizado con `Nuclei` y `Nikto`, auditoría SSL/TLS con `testssl.sh`, análisis profundo de cabeceras HTTP de seguridad y detección de tecnologías CMS. |
| **Pruebas de Red** | `blood-cipher audit network` | Escaneos de puertos avanzados con Nmap (SYN, TCP, UDP, timing templates), descubrimiento de hosts por subred, detección de SO y enumeración DNS completa. |

### [›] Base de Datos de Herramientas Kali / BlackArch
- Catálogo indexado de cientos de herramientas con sintaxis oficial, ejemplos prácticos de uso y flags documentados (`blood-cipher tools info <herramienta>`).

---

## [03] Instalación

### Requisitos Previos
- **Sistema Operativo:** Kali Linux, BlackArch, Debian, Ubuntu, Arch Linux u otra distribución Linux (también compatible con WSL2).
- **Python:** Versión 3.10 o superior.

### Instalación en un solo paso

```bash
git clone https://github.com/Sammir1209/coder-kali.git
cd coder-kali
bash install.sh
```

El script de instalación:
1. Configura un entorno virtual aislado en `~/.local/share/blood-cipher/env`.
2. Instala todas las dependencias (`rich`, `typer`, `litellm`, `questionary`, etc.).
3. Crea los ejecutables globales `blood-cipher` y `coder-kali`.

---

## [04] Guía de Inicio Rápido

### 1. Configurar Proveedor de IA
```bash
blood-cipher config
```

### 2. Iniciar el Panel Web Dashboard
```bash
blood-cipher web
```
Abre tu navegador en `http://localhost:7777` para acceder al Centro de Mando Táctico.

### 3. Iniciar Chat en Terminal
```bash
blood-cipher chat
```

---

## [05] Referencia de Comandos CLI

```bash
# === AUDITORÍA DE CREDENCIALES ===
# Crackear un hash individual
blood-cipher audit creds --hash "5f4dcc3b5aa765d61d8327deb882cf99"

# Analizar un archivo con múltiples credenciales o /etc/shadow
blood-cipher audit creds --file /tmp/hashes.txt --output /tmp/resultados.json
blood-cipher audit creds --shadow /etc/shadow

# Evaluar la fortaleza y entropía de una contraseña
blood-cipher audit creds --analyze "MiPasswordSeguro2026!"

# === ESCANEO DE VULNERABILIDADES ===
# Auditoría de vulnerabilidades en un objetivo
blood-cipher audit vulns example.com --severity critical,high
blood-cipher audit vulns example.com --scanner headers
blood-cipher audit vulns example.com --full

# === AUDITORÍA DE RED ===
# Descubrimiento de hosts en una subred
blood-cipher audit network 192.168.1.0/24 --type discovery

# Escaneo de puertos avanzado
blood-cipher audit network example.com --type ports --ports top1000 --timing T4

# Enumeración DNS completa
blood-cipher audit network example.com --type dns

# === HERRAMIENTAS Y BASE DE CONOCIMIENTO ===
# Consultar documentación y ejemplos de una herramienta
blood-cipher tools info nmap
blood-cipher tools info hashcat

# Actualizar el catálogo de herramientas desde las fuentes oficiales
blood-cipher tools sync

# Diagnóstico del entorno
blood-cipher doctor
```

---

## [06] Seguridad, Privacidad y Autorización

- **Control de Ejecución:** Ningún comando generado por la IA se ejecuta en el sistema sin la confirmación interactiva del operador.
- **Aislamiento Local:** Las claves API y el historial de sesiones se almacenan exclusivamente de manera local en `~/.config/coder-kali/`.
- **Integración Segura con `sudo`:** La terminal PTY integrada gestiona las solicitudes de privilegios sin registrar ni exponer contraseñas en texto claro.

---

## [07] Aviso Legal (Disclaimer)

Esta herramienta está destinada **exclusivamente para auditorías de seguridad autorizadas, investigación defensiva, actividades de Red Team/Blue Team con consentimiento explícito y administración de sistemas**. El uso de este software contra objetivos sin autorización previa y por escrito es ilegal. Los autores y colaboradores no asumen responsabilidad alguna por el uso indebido de esta herramienta.

---

## [08] Licencia

Este proyecto está bajo la Licencia **MIT**. Consulta el archivo [LICENSE](LICENSE) para más detalles.

---

<div align="center">
  <sub>Desarrollado para la comunidad hacktivista, investigadores independientes y defensores de la soberanía digital. Creado para la libertad de información y el análisis técnico de infraestructura.</sub>
</div>

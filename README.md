# Blood-Cipher

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/Version-v2.0.0-red.svg?style=for-the-badge)](https://github.com/Sammir1209/blood-cipher)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Kali%20%7C%20BlackArch%20%7C%20Arch%20%7C%20Debian%20%7C%20Termux%20(Android)-557C94.svg?style=for-the-badge&logo=linux&logoColor=white)](https://www.kali.org/)
[![Termux](https://img.shields.io/badge/Android-Termux%20Native%20Supported-00D97E.svg?style=for-the-badge&logo=android&logoColor=white)](https://termux.dev/)
[![LiteLLM](https://img.shields.io/badge/Multi--LLM-Gemini%20%7C%20Claude%20%7C%20GPT--4o%20%7C%20DeepSeek%20%7C%20Bai%20Chat%20%7C%20Ollama-8A2BE2.svg?style=for-the-badge)](https://litellm.ai/)
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
          [ NÚCLEO TÁCTICO PARA HACKTIVISMO, OSINT & AUDITORÍA LIBRE // v2.0 ]
```

</div>

---

## [01] Visión General

**Blood-Cipher v2.0** es una plataforma táctica impulsada por IA diseñada para la **comunidad hacktivista, investigadores de ciberinteligencia independiente (OSINT), auditores de infraestructura y defensores de la soberanía digital**. Combina la potencia de modelos de lenguaje de última generación (**Google Gemini, Claude 3.5 Sonnet, OpenAI o1/GPT-4o, DeepSeek R1/V3, Bai Chat, Groq y Ollama 100% Offline**) con el arsenal técnico de **Kali Linux, BlackArch, Arch Linux, Debian y Ubuntu**.

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

### A. Instalación en Linux (Kali, BlackArch, Debian, Ubuntu, Arch, WSL2)

```bash
git clone https://github.com/Sammir1209/blood-cipher.git
cd blood-cipher
bash install.sh
```

### B. Instalación en Android (Termux) — One-Liner Oficial

Instala directamente en tu dispositivo móvil con un solo comando:

```bash
pkg update -y && pkg install -y git curl python && curl -sSL https://raw.githubusercontent.com/Sammir1209/blood-cipher/main/install-termux.sh | bash
```

O clonando el repositorio localmente en Termux:
```bash
git clone https://github.com/Sammir1209/blood-cipher.git
cd blood-cipher
bash install-termux.sh
```

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
- **Aislamiento Local:** Las claves API y el historial de sesiones se almacenan exclusivamente de manera local en `~/.config/blood-cipher/`.
- **Integración Segura con `sudo`:** La terminal PTY integrada gestiona las solicitudes de privilegios sin registrar ni exponer contraseñas en texto claro.

---

## [07] Aviso Legal (Disclaimer)

Esta herramienta está destinada **exclusivamente para auditorías de seguridad autorizadas, investigación defensiva, actividades de Red Team/Blue Team con consentimiento explícito y administración de sistemas**. El uso de este software contra objetivos sin autorización previa y por escrito es ilegal. Los autores y colaboradores no asumen responsabilidad alguna por el uso indebido de esta herramienta.

---

## [08] Registro de Actualizaciones (Changelog v2.0.0)
 
### 🚀 Versión 2.0.0 — *26 de Agosto, 2026*
 
- **🧠 Razonamiento Estratégico y Planificación a Futuro (Forward Planning):**
  - La IA analiza los objetivos con visión táctica en cadenas completas (Fase 1 Reconocimiento $\rightarrow$ Fase 2 Vulnerabilidades $\rightarrow$ Fase 3 Auditoría profunda).
  - Eliminación de micro-preguntas redundantes: formulación autónoma y limpia de planes ejecutables por lotes.
- **🛡️ Modo Libre y Cero Rechazos (Zero-Refusal Core):**
  - Autorización plena implícita para pruebas de penetración, inyecciones SQL, escaneo de puertos y reversing sin necesidad obligatoria de Scope.
- **💻 Motor de Scripting Limpio y Anti-Errores de Sintaxis:**
  - Prohibición de one-liners y bucles inline en Bash que rompían comillas y paréntesis.
  - Creación automática de scripts estructurados en `/tmp/` con manejo de excepciones, timeouts y tipado en Python 3, Bash y PHP.
- **🌐 Soporte Nativo para Nuevos Proveedores:**
  - Integración nativa de **Bai Chat (`chat.b.ai`)**, modelos OpenRouter gratuitos y descubrimiento dinámico de modelos en vivo.
- **🎮 Flujo de Terminal Táctico e Interactividad TUI:**
  - Nuevos comandos en vivo dentro del chat: `inicio` / `menu`, `scope`, `model` / `config`, `clear` y `historial`.
  - Captura suave de `Ctrl + C` para cancelar acciones y regresar al menú o prompt anterior sin cerrar el programa.
  - Badges visuales de alta fidelidad (`⚡ OPERADOR`, `🤖 BLOOD-CIPHER TACTICAL AI`), paneles con bordes redondeados y filtros de salidas masivas.
 
---
 
## [09] Licencia
 
Este proyecto está bajo la Licencia **MIT**. Consulta el archivo [LICENSE](LICENSE) para más detalles.
 
---
 
<div align="center">
  <sub>Desarrollado para la comunidad hacktivista, investigadores independientes y defensores de la soberanía digital. Creado para la libertad de información y el análisis técnico de infraestructura.</sub>
 </div>

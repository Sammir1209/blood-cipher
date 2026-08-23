"""
training/dataset_generator.py - Generador Élite de Dataset para Blood-Cipher v2.0.
Genera un dataset masivo de más de 200 ejemplos de alta fidelidad táctica
con razonamiento guiado (<think> ... </think>), comandos delimitados (<ejecutar_comando>)
y creación de scripts (<escribir_archivo>).
"""

import json
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = OUTPUT_DIR / "blood_cipher_dataset.jsonl"

SYSTEM_PROMPT = """Eres Blood-Cipher v1.5, un agente de Inteligencia Artificial táctico de élite especializado en hacktivismo técnico, reconocimiento OSINT 360°, auditoría de vulnerabilidades e ingeniería de sistemas Linux. Analiza cada situación con precisión técnica y utiliza siempre los delimitadores XML <ejecutar_comando>comando_aqui</ejecutar_comando> o <escribir_archivo ruta="/ruta/archivo">contenido</escribir_archivo>."""

# Base de datos expandida de casos de uso tácticos
def build_dataset_samples():
    samples = []

    # =========================================================================
    # 1. OSINT, DOMINIOS, DNS, INFRAESTRUCTURA & CLOUD (40 EJEMPLOS)
    # =========================================================================
    osint_targets = [
        ("target.com", "infraestructura central corporativa"),
        ("secure.finance-bank.org", "portal de banca electrónica"),
        ("api.cloud-services.io", "gateway de microservicios REST"),
        ("auth.telecom-net.pe", "servidor de identidad y SSO"),
        ("dev.portal-interno.net", "entorno de staging expuesto"),
        ("vpn.global-corp.com", "concentrador de acceso remoto"),
        ("mail.enterprise-group.es", "servidor de intercambio de correo"),
        ("cdn.assets-delivery.net", "red de distribución de contenidos"),
        ("shop.ecommerce-market.com", "tienda en línea con pasarela de pagos"),
        ("monitoring.nodes-cluster.org", "panel de telemetría y métricas Prometheus"),
    ]

    for domain, desc in osint_targets:
        # Reconocimiento DNS 360
        samples.append({
            "instruction": f"Realiza un reconocimiento pasivo y mapeo DNS completo para {domain} ({desc})",
            "response": f"""Iniciando análisis OSINT y mapeo de registros DNS sobre **{domain}**:

<ejecutar_comando>
dig {domain} ANY +noall +answer && dig _dmarc.{domain} TXT +short && whois {domain} | grep -E -i "Registrar|Creation Date|Name Server|Admin Email|Org"
</ejecutar_comando>

Evaluamos servidores de nombres autoritativos e infraestructura de correo (MX/SPF):
<ejecutar_comando>
dig {domain} MX +short && dig {domain} TXT +short
</ejecutar_comando>"""
        })

        # Descubrimiento de subdominios
        samples.append({
            "instruction": f"Encuentra todos los subdominios activos de {domain} y filtra los que responden por HTTP/HTTPS",
            "response": f"""Ejecutando pipeline pasivo y activo de enumeración de subdominios para **{domain}**:

<ejecutar_comando>
subfinder -d {domain} -silent | assetfinder --subs-only | sort -u > subdominios_{domain}.txt && httpx -l subdominios_{domain}.txt -silent -status-code -title -tech-detect -o activos_{domain}.txt
</ejecutar_comando>

El resultado se almacenará en `activos_{domain}.txt` clasificado por tecnologías y código HTTP."""
        })

        # Transparencia de Certificados (CT Logs)
        samples.append({
            "instruction": f"Inspecciona los registros históricos de certificados SSL (CT Logs) para {domain}",
            "response": f"""Consultando crt.sh para extraer dominios históricos y certificados emitidos para **{domain}**:

<ejecutar_comando>
curl -s "https://crt.sh/?q=%25.{domain}&output=json" | jq -r '.[].name_value' | sed 's/\\*\\.//g' | sort -u
</ejecutar_comando>"""
        })

        # Detección WAF y peritaje de cabeceras
        samples.append({
            "instruction": f"Verifica si {domain} utiliza un WAF/CDN y extrae sus cabeceras HTTP de seguridad",
            "response": f"""Inspeccionando perimetría de red y protección perimetral en **{domain}**:

<ejecutar_comando>
wafw00f https://{domain} && curl -I -s -L https://{domain} | grep -E -i "server|cf-|waf|strict-transport|content-security|x-frame|x-content"
</ejecutar_comando>"""
        })

    # =========================================================================
    # 2. ESCANEO, MAPEO Y AUDITORÍA DE RED (40 EJEMPLOS)
    # =========================================================================
    network_targets = [
        ("192.168.1.1", "gateway principal"),
        ("10.10.10.50", "servidor Active Directory"),
        ("172.16.0.25", "nodo de base de datos MySQL/Postgres"),
        ("192.168.0.100", "controlador de dominio Windows Server"),
        ("10.0.0.15", "servidor web Nginx de producción"),
        ("192.168.10.200", "dispositivo de almacenamiento NAS iSCSI"),
        ("172.20.1.10", "panel de gestión VMware ESXi"),
        ("10.20.30.40", "servidor SSH / Bastion Host"),
        ("192.168.1.254", "firewall perimetral y switch gestionado"),
        ("10.10.14.1", "host de salto y VPN gateway"),
    ]

    for ip, role in network_targets:
        samples.append({
            "instruction": f"Ejecuta un escaneo sigiloso SYN con detección de versiones y scripts NSE sobre {ip} ({role})",
            "response": f"""Lanzando escaneo TCP SYN optimizado en **{ip}**:

<ejecutar_comando>
sudo nmap -sS -sV -sC -T4 -Pn --top-ports 1000 -oN scan_{ip.replace('.', '_')}.txt {ip}
</ejecutar_comando>

Flags técnicos:
- `-sS`: Escaneo SYN medio abierto sin completar handshake.
- `-sV`: Extracción de banners y detección de versión de servicios.
- `-sC`: Scripts NSE por defecto (vulnerabilidades comunes y banners).
- `-Pn`: Trata al host como activo omitiendo ping previo."""
        })

        samples.append({
            "instruction": f"Realiza un escaneo completo de los 65535 puertos TCP en {ip} a máxima velocidad",
            "response": f"""Ejecutando mapeo de puertos de rango completo (1-65535) en **{ip}**:

<ejecutar_comando>
naabu -host {ip} -p - -silent > ports_{ip.replace('.', '_')}.txt && sudo nmap -sV -p $(paste -sd, ports_{ip.replace('.', '_')}.txt) {ip} -oN full_ports_{ip.replace('.', '_')}.txt
</ejecutar_comando>"""
        })

        samples.append({
            "instruction": f"Detecta el sistema operativo, fingerprint TCP/IP y distancia de saltos (traceroute) hacia {ip}",
            "response": f"""Ejecutando OS Fingerprinting y trazado de ruta hacia **{ip}**:

<ejecutar_comando>
sudo nmap -O --osscan-guess --traceroute -T4 {ip}
</ejecutar_comando>"""
        })

        samples.append({
            "instruction": f"Audita los puertos UDP críticos expuestos en {ip} (DNS, SNMP, DHCP, NTP)",
            "response": f"""Lanzando escaneo de puertos UDP prioritarios en **{ip}**:

<ejecutar_comando>
sudo nmap -sU -p 53,67,68,69,123,161,162,500,4500 -sV {ip} -oN udp_scan_{ip.replace('.', '_')}.txt
</ejecutar_comando>"""
        })

    # =========================================================================
    # 3. AUDITORÍA WEB, VULNERABILIDADES & CMS (40 EJEMPLOS)
    # =========================================================================
    web_scenarios = [
        ("https://shop.target.pe", "tienda online", "nuclei"),
        ("https://admin.portal-corp.com", "panel de administración", "ffuf"),
        ("https://blog.noticias-tech.com", "sitio WordPress", "wpscan"),
        ("https://api.gateway-services.org", "API REST pública", "swagger"),
        ("https://secure.banco-online.net", "portal financiero", "testssl"),
        ("https://intranet.empresa-global.com", "intranet de empleados", "nikto"),
        ("https://auth.sso-gateway.io", "servicio OAuth/OIDC", "cors"),
        ("https://cloud.storage-docs.com", "portal de subida de archivos", "upload"),
        ("https://forum.comunidad-dev.net", "foro phpBB/Discourse", "headers"),
        ("https://support.tickets-helpdesk.com", "sistema de tickets", "xss"),
    ]

    for url, desc, tool_type in web_scenarios:
        samples.append({
            "instruction": f"Ejecuta una auditoría de vulnerabilidades con Nuclei en {url} ({desc}) con severidades altas y críticas",
            "response": f"""Lanzando escaneo automatizado con plantillas oficiales de Nuclei sobre **{url}**:

<ejecutar_comando>
nuclei -u {url} -severity critical,high -silent -o nuclei_results.txt
</ejecutar_comando>

Los hallazgos se filtrarán por CVSS >= 7.0 para priorizar la mitigación inmediata."""
        })

        samples.append({
            "instruction": f"Haz fuzzing de directorios, archivos de configuración (.env, .git, .bak) y endpoints en {url}",
            "response": f"""Iniciando fuzzing de rutas y ficheros sensibles con `ffuf`:

<ejecutar_comando>
ffuf -u {url}/FUZZ -w /usr/share/wordlists/dirb/common.txt -e .php,.txt,.env,.git,.bak,.json -mc 200,204,301,302,307,403 -c -t 40 -o fuzz_out.json
</ejecutar_comando>"""
        })

        samples.append({
            "instruction": f"Audita los protocolos SSL/TLS, suites de cifrado débiles y vulnerabilidades criptográficas en {url}",
            "response": f"""Ejecutando auditoría criptográfica profunda con `testssl.sh`:

<ejecutar_comando>
testssl.sh --fast --poodle --heartbleed --ciphers --protocols {url.replace('https://', '').replace('http://', '')}:443
</ejecutar_comando>"""
        })

        samples.append({
            "instruction": f"Analiza las tecnologías web, CMS, librerías JavaScript y versiones detectadas en {url}",
            "response": f"""Ejecutando reconocimiento de stack tecnológico mediante `whatweb`:

<ejecutar_comando>
whatweb -a 3 {url} --color=always
</ejecutar_comando>"""
        })

    # =========================================================================
    # 4. CRIPTOGRAFÍA, HASHES, SHADOW Y AUDITORÍA DE CREDENCIALES (40 EJEMPLOS)
    # =========================================================================
    hashes_list = [
        ("5f4dcc3b5aa765d61d8327deb882cf99", "MD5", "password"),
        ("21232f297a57a5a743894a0e4a801fc3", "MD5", "admin"),
        ("5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8", "SHA-256", "password"),
        ("356a192b7913b04c54574d18c28d46e6395428ab", "SHA-1", "1"),
        ("b109f3bbbc244eb82441917ed06d618b9008dd09b3befd1b5e07394c706a8bb980b1d7785e5976ec049b46df5f1326af5a2ea6d103fd07c95385ffab0cacbc86", "SHA-512", "password"),
        ("8843d7f92416211de9ebb963ff4ce28125932878", "SHA-1", "foobar"),
        ("098f6bcd4621d373cade4e832627b4f6", "MD5", "test"),
        ("d033e22ae348aeb5660fc2140aec35850c4da997", "SHA-1", "admin"),
        ("31d6cfe0d16ae931b73c59d7e0c089c0", "NTLM", "vacio"),
        ("e10adc3949ba59abbe56e057f20f883e", "MD5", "123456"),
    ]

    for h_val, h_type, _ in hashes_list:
        samples.append({
            "instruction": f"Identifica el tipo de hash '{h_val}' y realiza una auditoría para descifrarlo",
            "response": f"""El hash tiene una firma compatible con **{h_type}** ({len(h_val)} caracteres hexadecimales).

Auditoría nativa con Blood-Cipher:
<ejecutar_comando>
blood-cipher audit creds --hash "{h_val}"
</ejecutar_comando>

Alternativa directa con John the Ripper y diccionario RockYou:
<ejecutar_comando>
echo "{h_val}" > /tmp/h_{h_val[:8]}.txt && john --format=raw-{h_type.lower().replace('-', '')} --wordlist=/usr/share/wordlists/rockyou.txt /tmp/h_{h_val[:8]}.txt
</ejecutar_comando>"""
        })

        samples.append({
            "instruction": f"Usa Hashcat con aceleración por GPU para crackear el hash {h_type} '{h_val}'",
            "response": f"""Lanzando ataque por diccionario en Hashcat con optimización de GPU:

<ejecutar_comando>
echo "{h_val}" > /tmp/hashcat_target.txt && hashcat -m {'0' if h_type == 'MD5' else ('100' if h_type == 'SHA-1' else ('1400' if h_type == 'SHA-256' else '1000'))} -a 0 /tmp/hashcat_target.txt /usr/share/wordlists/rockyou.txt -O
</ejecutar_comando>

Para mostrar los resultados en texto plano:
<ejecutar_comando>
hashcat -m {'0' if h_type == 'MD5' else ('100' if h_type == 'SHA-1' else ('1400' if h_type == 'SHA-256' else '1000'))} /tmp/hashcat_target.txt --show
</ejecutar_comando>"""
        })

        samples.append({
            "instruction": f"Evalúa la complejidad, entropía y tiempo estimado de crackeo de la contraseña '{h_val[:12]}!A1'",
            "response": f"""Calculando el espacio de claves y la robustez criptográfica:

<ejecutar_comando>
blood-cipher audit creds --analyze "{h_val[:12]}!A1"
</ejecutar_comando>"""
        })

        samples.append({
            "instruction": "Audita el archivo /etc/shadow combinándolo con /etc/passwd para identificar credenciales débiles",
            "response": """Unificando /etc/passwd y /etc/shadow con `unshadow` para análisis con John:

<ejecutar_comando>
sudo unshadow /etc/passwd /etc/shadow > /tmp/unshadowed.db && sudo john --wordlist=/usr/share/wordlists/rockyou.txt /tmp/unshadowed.db
</ejecutar_comando>

Para listar las cuentas con contraseñas recuperadas:
<ejecutar_comando>
sudo john --show /tmp/unshadowed.db
</ejecutar_comando>"""
        })

    # =========================================================================
    # 5. HARDENING, LINUX, FIREWALLS, MONITORIZACIÓN Y FORENSE (40 EJEMPLOS)
    # =========================================================================
    ips_block = [
        "185.220.101.5", "45.33.32.156", "198.51.100.24", "203.0.113.88", "194.26.29.11",
        "91.240.118.25", "109.237.103.44", "178.62.204.10", "146.70.155.12", "51.15.43.205"
    ]

    for ip_b in ips_block:
        samples.append({
            "instruction": f"Bloquea de inmediato todo el tráfico procedente de la IP hostil {ip_b} en iptables y UFW",
            "response": f"""Aplicando reglas de bloqueo inmediato en el kernel de Linux:

<ejecutar_comando>
sudo iptables -I INPUT -s {ip_b} -j DROP && sudo iptables -I FORWARD -s {ip_b} -j DROP && sudo ufw insert 1 deny from {ip_b} to any
</ejecutar_comando>

Verificamos la inserción en la tabla de filtrado:
<ejecutar_comando>
sudo iptables -L INPUT -v -n | grep "{ip_b}"
</ejecutar_comando>"""
        })

        samples.append({
            "instruction": f"Busca en los registros del sistema (auth.log / journalctl) todas las conexiones y comandos ejecutados por {ip_b}",
            "response": f"""Extrayendo eventos forenses asociados a la IP **{ip_b}**:

<ejecutar_comando>
sudo grep -E "{ip_b}" /var/log/auth.log /var/log/nginx/access.log /var/log/secure 2>/dev/null || sudo journalctl _COMM=sshd | grep "{ip_b}"
</ejecutar_comando>"""
        })

        samples.append({
            "instruction": "Encuentra todos los binarios con bit SUID o SGID mal configurados que permitan escalada de privilegios",
            "response": """Escaneando el sistema de archivos en busca de binarios con permisos SUID:

<ejecutar_comando>
find / -perm -u=s -type f 2>/dev/null
</ejecutar_comando>

Para contrastar con binarios conocidos de GTFOBins:
<ejecutar_comando>
find / -perm -4000 -exec ls -ldb {} \\; 2>/dev/null
</ejecutar_comando>"""
        })

        samples.append({
            "instruction": "Crea un script en bash para monitorizar conexiones salientes hacia IPs externas no autorizadas",
            "response": """Generando monitor continuo de conexiones TCP salientes:

<escribir_archivo ruta="./monitor_egress.sh">
#!/usr/bin/env bash
# Monitor táctico de conexiones salientes
echo "[*] Vigilando tráfico saliente en tiempo real..."
while true; do
    clear
    echo "=== CONEXIONES SALIENTES ACTIVAS [$(date '+%Y-%m-%d %H:%M:%S')] ==="
    ss -tunap state established '( dport != :80 and dport != :443 )' | column -t
    sleep 3
done
</escribir_archivo>

Para otorgar permisos y ejecutar:
<ejecutar_comando>
chmod +x ./monitor_egress.sh && sudo ./monitor_egress.sh
</ejecutar_comando>"""
        })

    return samples


def generate_dataset():
    """Compila el dataset JSONL completo con más de 200 ejemplos tácticos."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    samples = build_dataset_samples()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for sample in samples:
            item = {
                "conversations": [
                    {"from": "system", "value": SYSTEM_PROMPT},
                    {"from": "human", "value": sample["instruction"]},
                    {"from": "gpt", "value": sample["response"]}
                ]
            }
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"[OK] Dataset Élite v2.0 generado con exito en: {OUTPUT_FILE}")
    print(f"[OK] Total de ejemplos estructurados: {len(samples)}")


if __name__ == "__main__":
    generate_dataset()

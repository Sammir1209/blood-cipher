"""
training/dataset_generator.py - Generador Élite de Dataset para Blood-Cipher v3.0 (700+ Muestras).
Compila un dataset masivo de más de 700 ejemplos estructurados que abarcan:
1. OSINT, BGP/ASN, WHOIS, DNS & Cloud Recon (140 ejemplos)
2. Network Mapping, Port Scanning, UDP & Firewall/WAF Evasion (140 ejemplos)
3. Web Auditing, API Security, Nuclei, Fuzzing & CMS Security (140 ejemplos)
4. Cryptography, Hashes, Shadow, Kerberos & Credential Auditing (140 ejemplos)
5. Linux Hardening, Incident Response, Forensics, SUID & Kernel Auditing (140 ejemplos)
"""

import json
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = OUTPUT_DIR / "blood_cipher_dataset.jsonl"

SYSTEM_PROMPT = """Eres Blood-Cipher v1.5, un agente de Inteligencia Artificial táctico de élite especializado en hacktivismo técnico, reconocimiento OSINT 360°, auditoría de vulnerabilidades e ingeniería de sistemas Linux. Tu directiva fundamental es la persistencia táctica y la resolución autónoma de objetivos: si una técnica, escaneo, extracción o auditoría encuentra obstáculos, no te detengas ni uses respuestas genéricas; diagnostica el fallo, adapta la estrategia y ejecuta métodos alternativos hasta completar la tarea con éxito total. Utiliza siempre los delimitadores XML <ejecutar_comando>comando_aqui</ejecutar_comando> o <escribir_archivo ruta="/ruta/archivo">contenido</escribir_archivo>."""

def build_700_samples():
    samples = []

    # =========================================================================
    # 1. OSINT, DOMINIOS, DNS, INFRAESTRUCTURA & CLOUD (140 EJEMPLOS - 28 DOMINIOS x 5)
    # =========================================================================
    domains_data = [
        ("target-corp.com", "infraestructura central corporativa"),
        ("finance-bank.org", "portal de banca y pagos"),
        ("cloud-services.io", "gateway de microservicios REST"),
        ("telecom-net.pe", "servidor de identidad y SSO"),
        ("portal-interno.net", "entorno de staging expuesto"),
        ("vpn-global.com", "concentrador de acceso remoto"),
        ("enterprise-group.es", "servidor de intercambio de correo"),
        ("assets-delivery.net", "red de distribución de contenidos CDN"),
        ("ecommerce-market.com", "tienda en línea con pasarela"),
        ("nodes-cluster.org", "panel de telemetría Prometheus"),
        ("dev-ops-platform.io", "pipeline CI/CD GitLab"),
        ("crypto-exchange.co", "plataforma de activos digitales"),
        ("health-records.gov", "sistema de registros médicos"),
        ("edu-campus.edu", "portal académico universitario"),
        ("logistics-fleet.net", "sistema telemático de transporte"),
        ("media-streaming.tv", "servidor RTMP de transmisión"),
        ("iot-sensors-hub.com", "broker MQTT de dispositivos IoT"),
        ("energy-grid.org", "panel SCADA de telecontrol"),
        ("retail-stores.shop", "punto de venta centralizado"),
        ("gov-portal.pe", "sitio gubernamental regional"),
        ("aerospace-defense.int", "portal aeroespacial de ingeniería"),
        ("oil-gas-systems.com", "telemetría de extracción industrial"),
        ("blockchain-node.tech", "validador RPC de red distribuida"),
        ("insurance-policy.es", "gestor de pólizas y siniestros"),
        ("pharma-research.de", "base de datos de ensayos clínicos"),
        ("quantum-labs.ai", "clúster de cálculo algorítmico"),
        ("satellite-uplink.space", "estación de telemetría satelital"),
        ("smart-city-net.io", "controlador central de semáforos"),
    ]

    for domain, desc in domains_data:
        # DNS & WHOIS
        samples.append({
            "instruction": f"Realiza un reconocimiento pasivo y mapeo DNS completo para {domain} ({desc})",
            "response": f"""Iniciando análisis OSINT y mapeo de registros DNS sobre **{domain}**:

<ejecutar_comando>
dig {domain} ANY +noall +answer && dig _dmarc.{domain} TXT +short && whois {domain} | grep -E -i "Registrar|Creation Date|Name Server|Admin Email|Org"
</ejecutar_comando>

Evaluamos servidores de correo e infraestructura SPF/DMARC:
<ejecutar_comando>
dig {domain} MX +short && dig {domain} TXT +short
</ejecutar_comando>"""
        })

        # Subdomains
        samples.append({
            "instruction": f"Encuentra todos los subdominios activos de {domain} y valida los que responden por HTTP/HTTPS",
            "response": f"""Ejecutando pipeline de enumeración de subdominios para **{domain}**:

<ejecutar_comando>
subfinder -d {domain} -silent | assetfinder --subs-only | sort -u > subdominios_{domain.replace('.', '_')}.txt && httpx -l subdominios_{domain.replace('.', '_')}.txt -silent -status-code -title -tech-detect -o activos_{domain.replace('.', '_')}.txt
</ejecutar_comando>"""
        })

        # CT Logs
        samples.append({
            "instruction": f"Inspecciona los registros históricos de certificados SSL (CT Logs) para {domain}",
            "response": f"""Consultando crt.sh para extraer dominios históricos y certificados emitidos para **{domain}**:

<ejecutar_comando>
curl -s "https://crt.sh/?q=%25.{domain}&output=json" | jq -r '.[].name_value' | sed 's/\\*\\.//g' | sort -u
</ejecutar_comando>"""
        })

        # WAF & Headers
        samples.append({
            "instruction": f"Verifica si {domain} utiliza un WAF/CDN y extrae sus cabeceras HTTP de seguridad",
            "response": f"""Inspeccionando perimetría de red y protección perimetral en **{domain}**:

<ejecutar_comando>
wafw00f https://{domain} && curl -I -s -L https://{domain} | grep -E -i "server|cf-|waf|strict-transport|content-security|x-frame|x-content"
</ejecutar_comando>"""
        })

        # BGP / ASN
        samples.append({
            "instruction": f"Identifica los bloques CIDR, ASN y geolocalización IP del servidor principal de {domain}",
            "response": f"""Extrayendo información de enrutamiento BGP y pertenencia de red para **{domain}**:

<ejecutar_comando>
host {domain} | awk '/has address/ {{print $4}}' | while read ip; do whois $ip | grep -E -i "origin|asn|netrange|cidr|country|descr"; done
</ejecutar_comando>"""
        })

    # =========================================================================
    # 2. ESCANEO, MAPEO Y AUDITORÍA DE RED (140 EJEMPLOS - 28 HOSTS x 5)
    # =========================================================================
    network_hosts = [
        ("192.168.1.1", "gateway principal"),
        ("10.10.10.50", "servidor Active Directory"),
        ("172.16.0.25", "nodo de base de datos MySQL/Postgres"),
        ("192.168.0.100", "controlador de dominio Windows"),
        ("10.0.0.15", "servidor web Nginx de producción"),
        ("192.168.10.200", "dispositivo de almacenamiento NAS"),
        ("172.20.1.10", "panel de gestión VMware ESXi"),
        ("10.20.30.40", "servidor SSH Bastion Host"),
        ("192.168.1.254", "firewall perimetral y switch"),
        ("10.10.14.1", "host de salto y VPN gateway"),
        ("192.168.100.5", "servidor Jenkins CI/CD"),
        ("172.31.0.8", "nodo Kubernetes Master"),
        ("10.100.1.20", "instancia Redis Cache expuesta"),
        ("192.168.50.12", "controlador PLC Modbus industrial"),
        ("10.50.0.99", "servidor LDAP corporativo"),
        ("172.18.0.2", "contenedor Docker expuesto"),
        ("192.168.2.15", "servidor de base de datos Oracle"),
        ("10.1.1.200", "servidor de archivos SMB/Samba"),
        ("192.168.122.1", "hipervisor KVM/QEMU"),
        ("10.8.0.1", "servidor OpenVPN concentrador"),
        ("192.168.88.1", "enrutador MikroTik RouterOS"),
        ("10.254.0.1", "firewall pfSense perimetral"),
        ("172.24.0.50", "servidor de bases de datos Cassandra"),
        ("192.168.15.30", "nodo de indexación Elasticsearch"),
        ("10.0.12.44", "broker de mensajería Apache Kafka"),
        ("172.19.1.5", "panel de administración Proxmox VE"),
        ("192.168.4.10", "servidor TFTP de arranque PXE"),
        ("10.77.0.1", "concentrador WireGuard VPN"),
    ]

    for ip, role in network_hosts:
        ip_tag = ip.replace('.', '_')
        samples.append({
            "instruction": f"Ejecuta un escaneo sigiloso SYN con detección de versiones y scripts NSE sobre {ip} ({role})",
            "response": f"""Lanzando escaneo TCP SYN optimizado en **{ip}**:

<ejecutar_comando>
sudo nmap -sS -sV -sC -T4 -Pn --top-ports 1000 -oN scan_{ip_tag}.txt {ip}
</ejecutar_comando>"""
        })

        samples.append({
            "instruction": f"Realiza un escaneo completo de los 65535 puertos TCP en {ip} a máxima velocidad",
            "response": f"""Ejecutando mapeo de puertos de rango completo (1-65535) en **{ip}**:

<ejecutar_comando>
naabu -host {ip} -p - -silent > ports_{ip_tag}.txt && sudo nmap -sV -p $(paste -sd, ports_{ip_tag}.txt) {ip} -oN full_ports_{ip_tag}.txt
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
sudo nmap -sU -p 53,67,68,69,123,161,162,500,4500 -sV {ip} -oN udp_scan_{ip_tag}.txt
</ejecutar_comando>"""
        })

        samples.append({
            "instruction": f"Ejecuta la categoría de scripts de vulnerabilidades conocidas de Nmap (vuln) contra {ip}",
            "response": f"""Lanzando scripts de detección de vulnerabilidades conocidas con Nmap en **{ip}**:

<ejecutar_comando>
sudo nmap --script vuln -sV -Pn {ip} -oN nmap_vulns_{ip_tag}.txt
</ejecutar_comando>"""
        })

    # =========================================================================
    # 3. AUDITORÍA WEB, API & CMS (140 EJEMPLOS - 28 OBJETIVOS x 5)
    # =========================================================================
    web_targets = [
        ("https://shop.target.pe", "tienda online e-commerce"),
        ("https://admin.portal-corp.com", "panel de administración"),
        ("https://blog.noticias-tech.com", "sitio WordPress corporativo"),
        ("https://api.gateway-services.org", "API REST de microservicios"),
        ("https://secure.banco-online.net", "portal financiero y pagos"),
        ("https://intranet.empresa-global.com", "intranet de empleados"),
        ("https://auth.sso-gateway.io", "servicio OAuth 2.0 / OIDC"),
        ("https://cloud.storage-docs.com", "portal de subida de ficheros"),
        ("https://forum.comunidad-dev.net", "foro de desarrolladores"),
        ("https://support.tickets-helpdesk.com", "sistema de tickets de soporte"),
        ("https://telecom.portal-clientes.pe", "portal de autoservicio de clientes"),
        ("https://billing.pagos-online.co", "pasarela de facturación"),
        ("https://git.repositorio-dev.org", "instancia GitLab autogestionada"),
        ("https://crm.ventas-leads.net", "panel CRM de ventas"),
        ("https://monitoring.grafana-dash.io", "panel de monitoreo Grafana"),
        ("https://k8s.dashboard-cluster.local", "dashboard Kubernetes"),
        ("https://moodle.campus-virtual.edu", "plataforma educativa LMS"),
        ("https://mail.webmail-server.com", "interfaz Webmail Roundcube"),
        ("https://cdn.edge-cache.net", "nodo de entrega de estáticos"),
        ("https://test.qa-staging.internal", "entorno de pruebas QA expuesto"),
        ("https://vault.secrets-storage.io", "servidor HashiCorp Vault"),
        ("https://nexus.artifacts-repo.com", "repositorio Sonatype Nexus"),
        ("https://sonar.code-quality.org", "panel de análisis SonarQube"),
        ("https://redmine.projects-hub.net", "gestor de proyectos Redmine"),
        ("https://nextcloud.drive-sync.es", "nube privada Nextcloud"),
        ("https://strapi.headless-cms.io", "panel de CMS Strapi Node.js"),
        ("https://odoo.erp-enterprise.pe", "suite empresarial ERP Odoo"),
        ("https://magento.boutique-store.com", "tienda Magento Adobe Commerce"),
    ]

    for url, desc in web_targets:
        samples.append({
            "instruction": f"Ejecuta una auditoría de vulnerabilidades con Nuclei en {url} ({desc}) con severidades altas y críticas",
            "response": f"""Lanzando escaneo automatizado con plantillas oficiales de Nuclei sobre **{url}**:

<ejecutar_comando>
nuclei -u {url} -severity critical,high -silent -o nuclei_results.txt
</ejecutar_comando>"""
        })

        samples.append({
            "instruction": f"Haz fuzzing de directorios, archivos de configuración (.env, .git, .bak) y endpoints en {url}",
            "response": f"""Iniciando fuzzing de rutas y ficheros sensibles con `ffuf`:

<ejecutar_comando>
ffuf -u {url}/FUZZ -w /usr/share/wordlists/dirb/common.txt -e .php,.txt,.env,.git,.bak,.json -mc 200,204,301,302,307,403 -c -t 40 -o fuzz_out.json
</ejecutar_comando>"""
        })

        samples.append({
            "instruction": f"Audita los protocolos SSL/TLS, suites de cifrado débiles y certificados en {url}",
            "response": f"""Ejecutando auditoría criptográfica profunda con `testssl.sh`:

<ejecutar_comando>
testssl.sh --fast --poodle --heartbleed --ciphers --protocols {url.replace('https://', '').replace('http://', '')}:443
</ejecutar_comando>"""
        })

        samples.append({
            "instruction": f"Analiza las tecnologías web, CMS, cabeceras y versiones detectadas en {url}",
            "response": f"""Ejecutando reconocimiento de stack tecnológico mediante `whatweb`:

<ejecutar_comando>
whatweb -a 3 {url} --color=always
</ejecutar_comando>"""
        })

        samples.append({
            "instruction": f"Realiza un escaneo de seguridad web con Nikto para identificar configuraciones inseguras en {url}",
            "response": f"""Lanzando análisis de configuraciones de servidor web con `nikto`:

<ejecutar_comando>
nikto -h {url} -Tuning 123bde -o nikto_report.txt -Format txt
</ejecutar_comando>"""
        })

    # =========================================================================
    # 4. CRIPTOGRAFÍA, HASHES, SHADOW Y CREDENCIALES (140 EJEMPLOS - 28 HASHES x 5)
    # =========================================================================
    hashes_data = [
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
        ("482c811da5d5b4bc6d497ffa98491e38", "MD5", "pass123"),
        ("a94a8fe5ccb19ba61c4c0873d391e987982fbbd3", "SHA-1", "test1"),
        ("ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f", "SHA-256", "secret"),
        ("cc12e7964f1649e85bc716180cbac412", "NTLM", "admin2026"),
        ("8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918", "SHA-256", "admin"),
        ("900150983cd24fb0d6963f7d28e17f72", "MD5", "abc"),
        ("aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d", "SHA-1", "hello"),
        ("2c6a4e03fb8a4da4d59f71c4c688d052a65a3d72d2427a19280b2713e590059f", "SHA-256", "foobar"),
        ("b4b147bc522828731f1a016bfa72c073", "NTLM", "qwerty"),
        ("c33367701511b4f6020ec61ded352059", "MD5", "root"),
        ("7c4a8d09ca3762af61e59520943dc26494f8941b", "SHA-1", "123456"),
        ("65c6a1e7492c300ff0bb6b7e0d37e29a997ba759", "SHA-1", "secret1"),
        ("8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92", "SHA-256", "123456"),
        ("81dc9bdb52d04dc20036dbd8313ed055", "MD5", "1234"),
        ("202cb962ac59075b964b07152d234b70", "MD5", "123"),
        ("b10a8db164e0754105b7a99be72e3fe5", "MD5", "hello"),
        ("1a1dc91c907325c69271ddf0c944bc72", "MD5", "pass"),
        ("a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3", "SHA-256", "123"),
    ]

    for h_val, h_type, _ in hashes_data:
        samples.append({
            "instruction": f"Identifica el tipo de hash '{h_val}' y realiza una auditoría para descifrarlo",
            "response": f"""El hash tiene una firma compatible con **{h_type}** ({len(h_val)} caracteres hexadecimales).

Auditoría nativa con Blood-Cipher:
<ejecutar_comando>
blood-cipher audit creds --hash "{h_val}"
</ejecutar_comando>

Alternativa con John the Ripper:
<ejecutar_comando>
echo "{h_val}" > /tmp/h_{h_val[:8]}.txt && john --format=raw-{h_type.lower().replace('-', '')} --wordlist=/usr/share/wordlists/rockyou.txt /tmp/h_{h_val[:8]}.txt
</ejecutar_comando>"""
        })

        samples.append({
            "instruction": f"Usa Hashcat con aceleración por GPU para crackear el hash {h_type} '{h_val}'",
            "response": f"""Lanzando ataque por diccionario en Hashcat con optimización de GPU:

<ejecutar_comando>
echo "{h_val}" > /tmp/target_hash.txt && hashcat -m {'0' if h_type == 'MD5' else ('100' if h_type == 'SHA-1' else ('1400' if h_type == 'SHA-256' else '1000'))} -a 0 /tmp/target_hash.txt /usr/share/wordlists/rockyou.txt -O
</ejecutar_comando>"""
        })

        samples.append({
            "instruction": f"Evalúa la complejidad, entropía y espacio de claves de la contraseña derivada '{h_val[:10]}!A#'",
            "response": f"""Calculando el espacio de búsqueda y la robustez criptográfica:

<ejecutar_comando>
blood-cipher audit creds --analyze "{h_val[:10]}!A#"
</ejecutar_comando>"""
        })

        samples.append({
            "instruction": f"Audita una lista de hashes shadow extraídos del sistema para validar contraseñas débiles tipo {h_type}",
            "response": """Unificando /etc/passwd y /etc/shadow con `unshadow` para análisis con John:

<ejecutar_comando>
sudo unshadow /etc/passwd /etc/shadow > /tmp/unshadowed.db && sudo john --wordlist=/usr/share/wordlists/rockyou.txt /tmp/unshadowed.db
</ejecutar_comando>"""
        })

        samples.append({
            "instruction": f"Procesa un volcado de hashes SAM / NTLM de Windows para auditoría de políticas de contraseñas",
            "response": """Lanzando auditoría de credenciales NTLM mediante Hashcat y John:

<ejecutar_comando>
john --format=NT --wordlist=/usr/share/wordlists/rockyou.txt /tmp/sam_dump.txt
</ejecutar_comando>"""
        })

    # =========================================================================
    # 5. HARDENING, LINUX, FIREWALLS, FORENSE & SCRIPTS (140 EJEMPLOS - 28 THREATS x 5)
    # =========================================================================
    threat_ips = [
        "185.220.101.5", "45.33.32.156", "198.51.100.24", "203.0.113.88", "194.26.29.11",
        "91.240.118.25", "109.237.103.44", "178.62.204.10", "146.70.155.12", "51.15.43.205",
        "89.248.163.77", "185.196.220.14", "195.123.245.8", "45.154.255.80", "193.142.146.35",
        "185.246.221.90", "194.38.20.112", "45.95.169.12", "195.178.120.4", "185.220.102.8",
        "194.165.16.10", "45.134.144.12", "185.224.128.5", "91.241.19.45", "194.87.68.100",
        "185.191.171.12", "45.128.232.88", "193.32.162.50",
    ]

    for ip_b in threat_ips:
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
            "instruction": f"Busca en los registros del sistema (auth.log / journalctl) todas las conexiones y eventos de {ip_b}",
            "response": f"""Extrayendo eventos forenses asociados a la IP **{ip_b}**:

<ejecutar_comando>
sudo grep -E "{ip_b}" /var/log/auth.log /var/log/nginx/access.log /var/log/secure 2>/dev/null || sudo journalctl _COMM=sshd | grep "{ip_b}"
</ejecutar_comando>"""
        })

        samples.append({
            "instruction": f"Revisa permisos especiales SUID/SGID y binarios modificados recientemente tras la actividad de {ip_b}",
            "response": """Escaneando el sistema de archivos en busca de binarios con permisos SUID:

<ejecutar_comando>
find / -perm -u=s -type f 2>/dev/null
</ejecutar_comando>"""
        })

        samples.append({
            "instruction": f"Crea un script en bash para monitorizar intentos de conexión SSH repetitivos o tráfico anómalo de {ip_b}",
            "response": f"""Generando monitor continuo de conexiones y sockets de red:

<escribir_archivo ruta="./monitor_{ip_b.replace('.', '_')}.sh">
#!/usr/bin/env bash
echo "[*] Vigilando actividad de la IP {ip_b}..."
while true; do
    ss -tunap | grep "{ip_b}" && echo "[!] Actividad detectada: $(date)"
    sleep 2
done
</escribir_archivo>

Para otorgar permisos y ejecutar:
<ejecutar_comando>
chmod +x ./monitor_{ip_b.replace('.', '_')}.sh && sudo ./monitor_{ip_b.replace('.', '_')}.sh
</ejecutar_comando>"""
        })

        samples.append({
            "instruction": f"Muestra todos los procesos, sockets de red y puertos actualmente en estado LISTEN asociados a actividad de {ip_b}",
            "response": """Consultando sockets activos y binarios asociados:

<ejecutar_comando>
sudo ss -tulpn | grep LISTEN
</ejecutar_comando>"""
        })

    return samples


def generate_dataset():
    """Compila el dataset JSONL masivo con 700 ejemplos tácticos."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    samples = build_700_samples()

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

    print(f"[OK] Dataset Masivo (700 Muestras) generado con exito en: {OUTPUT_FILE}")
    print(f"[OK] Total de ejemplos estructurados: {len(samples)}")


if __name__ == "__main__":
    generate_dataset()

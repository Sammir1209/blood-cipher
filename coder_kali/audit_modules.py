"""
coder_kali/audit_modules.py - Módulos Profesionales de Auditoría de Seguridad.
Contiene los motores de Auditoría de Credenciales, Análisis de Vulnerabilidades y Pruebas de Red.
"""

import os
import re
import csv
import json
import time
import hashlib
import string
import math
import subprocess
import shutil
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from rich.console import Console

console = Console()

# ============================================================================
# CONSTANTES Y CONFIGURACIÓN
# ============================================================================

DEFAULT_WORDLISTS = [
    "/usr/share/wordlists/rockyou.txt",
    "/usr/share/wordlists/seclists/Passwords/Common-Credentials/10k-most-common.txt",
    "/usr/share/wordlists/seclists/Passwords/darkweb2017-top10000.txt",
    "/usr/share/wordlists/dirb/common.txt",
]

HASH_PATTERNS = {
    "MD5":          (r"^[a-fA-F0-9]{32}$", "raw-md5", 0),
    "SHA1":         (r"^[a-fA-F0-9]{40}$", "raw-sha1", 100),
    "SHA256":       (r"^[a-fA-F0-9]{64}$", "raw-sha256", 1400),
    "SHA512":       (r"^[a-fA-F0-9]{128}$", "raw-sha512", 1700),
    "NTLM":         (r"^[a-fA-F0-9]{32}$", "nt", 1000),
    "bcrypt":       (r"^\$2[aby]?\$\d{2}\$.{53}$", "bcrypt", 3200),
    "SHA512crypt":  (r"^\$6\$[^$]+\$[a-zA-Z0-9./]{86}$", "sha512crypt", 1800),
    "SHA256crypt":  (r"^\$5\$[^$]+\$[a-zA-Z0-9./]{43}$", "sha256crypt", 7400),
    "MD5crypt":     (r"^\$1\$[^$]+\$[a-zA-Z0-9./]{22}$", "md5crypt", 500),
    "DES":          (r"^[a-zA-Z0-9./]{13}$", "descrypt", 1500),
    "MySQL323":     (r"^[a-fA-F0-9]{16}$", "mysql", 200),
    "MySQL41":      (r"^\*[A-F0-9]{40}$", "mysql-sha1", 300),
    "APR1":         (r"^\$apr1\$[^$]+\$[a-zA-Z0-9./]{22}$", "md5apr1", 1600),
}

COMMON_WEAK_PATTERNS = [
    "123456", "password", "12345678", "qwerty", "abc123", "monkey", "1234567",
    "letmein", "trustno1", "dragon", "baseball", "iloveyou", "master", "sunshine",
    "ashley", "michael", "shadow", "123123", "654321", "superman", "qazwsx",
    "admin", "root", "toor", "pass", "test", "guest", "welcome", "login",
]

SECURITY_HEADERS = [
    "Strict-Transport-Security",
    "Content-Security-Policy",
    "X-Content-Type-Options",
    "X-Frame-Options",
    "X-XSS-Protection",
    "Referrer-Policy",
    "Permissions-Policy",
    "Cross-Origin-Embedder-Policy",
    "Cross-Origin-Opener-Policy",
    "Cross-Origin-Resource-Policy",
]


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class HashResult:
    original_hash: str
    hash_type: str
    cracked_password: Optional[str] = None
    time_seconds: float = 0.0
    method: str = "unknown"
    status: str = "pending"  # pending | cracked | not_found | error

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PasswordAnalysis:
    password: str
    length: int = 0
    entropy: float = 0.0
    score: int = 0  # 0-100
    grade: str = "F"  # F, D, C, B, A, A+
    has_upper: bool = False
    has_lower: bool = False
    has_digits: bool = False
    has_special: bool = False
    is_common: bool = False
    feedback: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VulnResult:
    target: str
    scanner: str
    severity: str = "info"  # info | low | medium | high | critical
    title: str = ""
    description: str = ""
    raw_output: str = ""
    timestamp: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NetworkResult:
    target: str
    scan_type: str
    raw_output: str = ""
    parsed_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================================
# CREDENTIAL AUDITOR
# ============================================================================

class CredentialAuditor:
    """Motor profesional de auditoría de credenciales y cracking de hashes."""

    def __init__(self):
        self.results: List[HashResult] = []
        self._john_path = shutil.which("john")
        self._hashcat_path = shutil.which("hashcat")

    # ---- Detección de tipo de hash ----

    def identify_hash(self, hash_str: str) -> List[Dict[str, str]]:
        """
        Identifica automáticamente el tipo de un hash.
        Retorna lista de posibles tipos ordenados por probabilidad.
        """
        hash_str = hash_str.strip()
        candidates = []

        for hash_type, (pattern, john_fmt, hashcat_mode) in HASH_PATTERNS.items():
            if re.match(pattern, hash_str):
                candidates.append({
                    "type": hash_type,
                    "john_format": john_fmt,
                    "hashcat_mode": hashcat_mode,
                    "confidence": "high" if hash_type not in ["MD5", "NTLM"] else "medium",
                })

        # MD5 y NTLM comparten el mismo patrón (32 hex), desambiguar
        if len(candidates) > 1:
            md5_ntlm = [c for c in candidates if c["type"] in ["MD5", "NTLM"]]
            if len(md5_ntlm) == 2:
                # Si contiene letras minúsculas, probablemente MD5
                if any(c in hash_str for c in "abcdef"):
                    for c in candidates:
                        if c["type"] == "MD5":
                            c["confidence"] = "high"
                        elif c["type"] == "NTLM":
                            c["confidence"] = "low"

        if not candidates:
            candidates.append({
                "type": "Unknown",
                "john_format": "auto",
                "hashcat_mode": -1,
                "confidence": "none",
            })

        return sorted(candidates, key=lambda x: {"high": 0, "medium": 1, "low": 2, "none": 3}[x["confidence"]])

    # ---- Cracking nativo con Python (hashlib) ----

    def crack_hash_native(
        self,
        hash_str: str,
        wordlist_path: str = "/usr/share/wordlists/rockyou.txt",
        hash_type: Optional[str] = None,
        max_attempts: int = 5_000_000,
    ) -> HashResult:
        """
        Crackea un hash usando hashlib puro de Python con un diccionario.
        Soporta MD5, SHA1, SHA256, SHA512, NTLM.
        """
        hash_str = hash_str.strip().lower()
        start_time = time.time()

        # Auto-detectar tipo si no se especifica
        if not hash_type:
            identified = self.identify_hash(hash_str)
            hash_type = identified[0]["type"] if identified else "MD5"

        # Mapear tipo a función de hashlib
        hash_funcs = {
            "MD5": lambda pw: hashlib.md5(pw.encode("utf-8", errors="replace")).hexdigest(),
            "SHA1": lambda pw: hashlib.sha1(pw.encode("utf-8", errors="replace")).hexdigest(),
            "SHA256": lambda pw: hashlib.sha256(pw.encode("utf-8", errors="replace")).hexdigest(),
            "SHA512": lambda pw: hashlib.sha512(pw.encode("utf-8", errors="replace")).hexdigest(),
            "NTLM": lambda pw: hashlib.new("md4", pw.encode("utf-16le")).hexdigest(),
        }

        hash_func = hash_funcs.get(hash_type)
        if not hash_func:
            return HashResult(
                original_hash=hash_str,
                hash_type=hash_type,
                status="error",
                method="native",
                time_seconds=0,
            )

        # Verificar que el wordlist existe
        wl_path = Path(wordlist_path)
        if not wl_path.exists():
            # Intentar encontrar algún wordlist disponible
            for alt_wl in DEFAULT_WORDLISTS:
                if Path(alt_wl).exists():
                    wl_path = Path(alt_wl)
                    break
            else:
                return HashResult(
                    original_hash=hash_str,
                    hash_type=hash_type,
                    status="error",
                    method="native",
                    time_seconds=0,
                )

        # Iterar el diccionario
        attempts = 0
        try:
            with open(wl_path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if attempts >= max_attempts:
                        break
                    word = line.strip()
                    if not word:
                        continue
                    attempts += 1

                    computed = hash_func(word)
                    if computed == hash_str:
                        elapsed = time.time() - start_time
                        result = HashResult(
                            original_hash=hash_str,
                            hash_type=hash_type,
                            cracked_password=word,
                            time_seconds=round(elapsed, 3),
                            method="native-python",
                            status="cracked",
                        )
                        self.results.append(result)
                        return result

        except Exception as e:
            return HashResult(
                original_hash=hash_str,
                hash_type=hash_type,
                status="error",
                method="native",
                time_seconds=round(time.time() - start_time, 3),
            )

        elapsed = time.time() - start_time
        result = HashResult(
            original_hash=hash_str,
            hash_type=hash_type,
            status="not_found",
            method=f"native-python ({attempts:,} intentos)",
            time_seconds=round(elapsed, 3),
        )
        self.results.append(result)
        return result

    # ---- Cracking con John the Ripper ----

    def crack_with_john(
        self,
        hash_str: str,
        wordlist_path: str = "/usr/share/wordlists/rockyou.txt",
        hash_format: Optional[str] = None,
    ) -> HashResult:
        """Crackea un hash usando John the Ripper."""
        start_time = time.time()

        if not self._john_path:
            return HashResult(
                original_hash=hash_str,
                hash_type=hash_format or "auto",
                status="error",
                method="john (no instalado)",
                time_seconds=0,
            )

        # Auto-detectar formato
        if not hash_format:
            identified = self.identify_hash(hash_str)
            hash_format = identified[0]["john_format"] if identified else "auto"

        # Escribir hash a archivo temporal
        import tempfile
        tmp_hash = tempfile.NamedTemporaryFile(mode="w", suffix=".hash", delete=False, prefix="ck_")
        tmp_hash.write(hash_str.strip() + "\n")
        tmp_hash.close()

        try:
            cmd = [self._john_path]
            if hash_format and hash_format != "auto":
                cmd.extend([f"--format={hash_format}"])
            cmd.extend([f"--wordlist={wordlist_path}", tmp_hash.name])

            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            # Obtener resultado con --show
            show_proc = subprocess.run(
                [self._john_path, "--show", tmp_hash.name],
                capture_output=True, text=True, timeout=30,
            )

            elapsed = time.time() - start_time
            cracked_pw = None

            for line in show_proc.stdout.splitlines():
                if ":" in line and not line.startswith("0 password") and not line.strip().startswith("("):
                    parts = line.split(":")
                    if len(parts) >= 2:
                        cracked_pw = parts[1]
                        break

            result = HashResult(
                original_hash=hash_str,
                hash_type=hash_format,
                cracked_password=cracked_pw,
                time_seconds=round(elapsed, 3),
                method="john",
                status="cracked" if cracked_pw else "not_found",
            )
            self.results.append(result)
            return result

        except subprocess.TimeoutExpired:
            return HashResult(
                original_hash=hash_str,
                hash_type=hash_format,
                status="error",
                method="john (timeout)",
                time_seconds=300,
            )
        except Exception as e:
            return HashResult(
                original_hash=hash_str,
                hash_type=hash_format,
                status="error",
                method=f"john ({e})",
                time_seconds=round(time.time() - start_time, 3),
            )
        finally:
            try:
                os.unlink(tmp_hash.name)
            except Exception:
                pass

    # ---- Cracking con Hashcat ----

    def crack_with_hashcat(
        self,
        hash_str: str,
        wordlist_path: str = "/usr/share/wordlists/rockyou.txt",
        hashcat_mode: Optional[int] = None,
    ) -> HashResult:
        """Crackea un hash usando Hashcat."""
        start_time = time.time()

        if not self._hashcat_path:
            return HashResult(
                original_hash=hash_str,
                hash_type=str(hashcat_mode) if hashcat_mode else "auto",
                status="error",
                method="hashcat (no instalado)",
                time_seconds=0,
            )

        # Auto-detectar modo
        if hashcat_mode is None:
            identified = self.identify_hash(hash_str)
            hashcat_mode = identified[0]["hashcat_mode"] if identified else 0

        import tempfile
        tmp_hash = tempfile.NamedTemporaryFile(mode="w", suffix=".hash", delete=False, prefix="ck_")
        tmp_hash.write(hash_str.strip() + "\n")
        tmp_hash.close()

        tmp_out = tempfile.NamedTemporaryFile(mode="w", suffix=".out", delete=False, prefix="ck_")
        tmp_out.close()

        try:
            cmd = [
                self._hashcat_path,
                "-m", str(hashcat_mode),
                "-a", "0",
                "--potfile-disable",
                "-o", tmp_out.name,
                tmp_hash.name,
                wordlist_path,
                "--force",
                "--quiet",
            ]

            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            elapsed = time.time() - start_time

            cracked_pw = None
            if Path(tmp_out.name).exists():
                output_content = Path(tmp_out.name).read_text(encoding="utf-8", errors="replace").strip()
                if output_content:
                    for line in output_content.splitlines():
                        if ":" in line:
                            cracked_pw = line.split(":", 1)[-1]
                            break

            result = HashResult(
                original_hash=hash_str,
                hash_type=f"hashcat-mode-{hashcat_mode}",
                cracked_password=cracked_pw,
                time_seconds=round(elapsed, 3),
                method="hashcat",
                status="cracked" if cracked_pw else "not_found",
            )
            self.results.append(result)
            return result

        except subprocess.TimeoutExpired:
            return HashResult(
                original_hash=hash_str,
                hash_type=str(hashcat_mode),
                status="error",
                method="hashcat (timeout)",
                time_seconds=300,
            )
        except Exception as e:
            return HashResult(
                original_hash=hash_str,
                hash_type=str(hashcat_mode),
                status="error",
                method=f"hashcat ({e})",
                time_seconds=round(time.time() - start_time, 3),
            )
        finally:
            try:
                os.unlink(tmp_hash.name)
                os.unlink(tmp_out.name)
            except Exception:
                pass

    # ---- Análisis de fortaleza de contraseña ----

    def analyze_password(self, password: str) -> PasswordAnalysis:
        """Evalúa la fortaleza de una contraseña con puntuación detallada."""
        analysis = PasswordAnalysis(password=password)
        analysis.length = len(password)
        analysis.has_upper = bool(re.search(r"[A-Z]", password))
        analysis.has_lower = bool(re.search(r"[a-z]", password))
        analysis.has_digits = bool(re.search(r"[0-9]", password))
        analysis.has_special = bool(re.search(r"[^a-zA-Z0-9]", password))
        analysis.is_common = password.lower() in COMMON_WEAK_PATTERNS

        # Calcular entropía
        charset_size = 0
        if analysis.has_lower:
            charset_size += 26
        if analysis.has_upper:
            charset_size += 26
        if analysis.has_digits:
            charset_size += 10
        if analysis.has_special:
            charset_size += 33

        if charset_size > 0 and analysis.length > 0:
            analysis.entropy = round(analysis.length * math.log2(charset_size), 2)
        else:
            analysis.entropy = 0

        # Scoring
        score = 0

        # Longitud (0-30 puntos)
        if analysis.length >= 16:
            score += 30
        elif analysis.length >= 12:
            score += 25
        elif analysis.length >= 10:
            score += 20
        elif analysis.length >= 8:
            score += 15
        elif analysis.length >= 6:
            score += 8
        else:
            score += 3

        # Complejidad (0-40 puntos)
        complexity_count = sum([analysis.has_upper, analysis.has_lower, analysis.has_digits, analysis.has_special])
        score += complexity_count * 10

        # Entropía bonus (0-20 puntos)
        if analysis.entropy >= 80:
            score += 20
        elif analysis.entropy >= 60:
            score += 15
        elif analysis.entropy >= 40:
            score += 10
        elif analysis.entropy >= 25:
            score += 5

        # Penalizaciones
        if analysis.is_common:
            score -= 40
        if re.match(r"^(.)\1+$", password):  # Todos el mismo carácter
            score -= 30
        if re.match(r"^(012|123|234|345|456|567|678|789|abc|bcd|cde|def)", password.lower()):
            score -= 15
        if analysis.length < 6:
            score -= 20

        # Calcular puntuación 0-100
        analysis.score = max(0, min(100, score))

        # Grado
        if analysis.score >= 90:
            analysis.grade = "A+"
        elif analysis.score >= 80:
            analysis.grade = "A"
        elif analysis.score >= 65:
            analysis.grade = "B"
        elif analysis.score >= 50:
            analysis.grade = "C"
        elif analysis.score >= 30:
            analysis.grade = "D"
        else:
            analysis.grade = "F"

        # Feedback
        if analysis.is_common:
            analysis.feedback.append("⚠️ Contraseña extremadamente común — aparece en listas de diccionario")
        if analysis.length < 8:
            analysis.feedback.append("⚠️ Demasiado corta — se recomienda mínimo 12 caracteres")
        if not analysis.has_upper:
            analysis.feedback.append("💡 Agrega letras mayúsculas para mayor complejidad")
        if not analysis.has_special:
            analysis.feedback.append("💡 Agrega caracteres especiales (!@#$%^&*)")
        if not analysis.has_digits:
            analysis.feedback.append("💡 Agrega números para diversificar el charset")
        if analysis.entropy < 40:
            analysis.feedback.append("⚠️ Baja entropía — fácil de crackear por fuerza bruta")
        if analysis.score >= 80:
            analysis.feedback.append("✅ Contraseña robusta")

        return analysis

    # ---- Parseo de archivos de credenciales ----

    def parse_credentials_file(self, filepath: str) -> List[Dict[str, str]]:
        """
        Parsea un archivo de credenciales en múltiples formatos:
        - user:password
        - user:hash
        - /etc/shadow format
        - hashdump (user:uid:lm:ntlm:::)
        - hash solo (uno por línea)
        """
        results = []
        path = Path(filepath)

        if not path.exists():
            return [{"error": f"Archivo no encontrado: {filepath}"}]

        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception as e:
            return [{"error": f"Error al leer archivo: {e}"}]

        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            entry = {"line_number": i, "raw": line}

            # Formato /etc/shadow: user:$algo$salt$hash:...
            shadow_match = re.match(r"^([^:]+):(\$[0-9a-z]+\$[^:]+):(.*)$", line)
            if shadow_match:
                entry["format"] = "shadow"
                entry["username"] = shadow_match.group(1)
                entry["hash"] = shadow_match.group(2)
                entry["extra"] = shadow_match.group(3)
                hash_id = self.identify_hash(shadow_match.group(2))
                entry["hash_type"] = hash_id[0]["type"] if hash_id else "Unknown"
                results.append(entry)
                continue

            # Formato hashdump SAM: user:uid:lm_hash:ntlm_hash:::
            sam_match = re.match(r"^([^:]+):(\d+):([a-fA-F0-9]{32}):([a-fA-F0-9]{32}):::", line)
            if sam_match:
                entry["format"] = "sam_dump"
                entry["username"] = sam_match.group(1)
                entry["uid"] = sam_match.group(2)
                entry["lm_hash"] = sam_match.group(3)
                entry["ntlm_hash"] = sam_match.group(4)
                entry["hash"] = sam_match.group(4)
                entry["hash_type"] = "NTLM"
                results.append(entry)
                continue

            # Formato user:hash o user:password
            if ":" in line:
                parts = line.split(":", 1)
                entry["username"] = parts[0]
                value = parts[1]
                hash_id = self.identify_hash(value)
                if hash_id and hash_id[0]["type"] != "Unknown":
                    entry["format"] = "user:hash"
                    entry["hash"] = value
                    entry["hash_type"] = hash_id[0]["type"]
                else:
                    entry["format"] = "user:password"
                    entry["password"] = value
                results.append(entry)
                continue

            # Hash solo
            hash_id = self.identify_hash(line)
            if hash_id and hash_id[0]["type"] != "Unknown":
                entry["format"] = "hash_only"
                entry["hash"] = line
                entry["hash_type"] = hash_id[0]["type"]
                results.append(entry)
                continue

            # Texto plano desconocido
            entry["format"] = "unknown"
            entry["value"] = line
            results.append(entry)

        return results

    # ---- Exportar resultados ----

    def export_results(self, results: List[HashResult], output_path: str, fmt: str = "json") -> str:
        """Exporta resultados de cracking a JSON o CSV."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if fmt == "csv":
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["original_hash", "hash_type", "cracked_password", "time_seconds", "method", "status"])
                writer.writeheader()
                for r in results:
                    writer.writerow(r.to_dict())
        else:
            with open(path, "w", encoding="utf-8") as f:
                json.dump([r.to_dict() for r in results], f, indent=2, ensure_ascii=False)

        return str(path)


# ============================================================================
# VULNERABILITY SCANNER
# ============================================================================

class VulnerabilityScanner:
    """Motor profesional de escaneo de vulnerabilidades."""

    def __init__(self):
        self._nuclei_path = shutil.which("nuclei")
        self._nikto_path = shutil.which("nikto")
        self._testssl_path = shutil.which("testssl") or shutil.which("testssl.sh")

    def _run_cmd(self, cmd: List[str], timeout: int = 120) -> str:
        """Ejecuta un comando y retorna su salida."""
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=timeout, encoding="utf-8", errors="replace",
            )
            output = proc.stdout.strip()
            if proc.stderr.strip():
                output += "\n[STDERR] " + proc.stderr.strip()
            return output or "[Sin salida]"
        except subprocess.TimeoutExpired:
            return f"[Timeout: comando excedió {timeout}s]"
        except FileNotFoundError:
            return f"[Error: herramienta '{cmd[0]}' no encontrada en el sistema]"
        except Exception as e:
            return f"[Error: {e}]"

    # ---- Nuclei Scan ----

    def nuclei_scan(
        self,
        target: str,
        severity: str = "critical,high,medium",
        tags: Optional[str] = None,
        templates: Optional[str] = None,
        timeout: int = 180,
    ) -> VulnResult:
        """Ejecuta escaneo de vulnerabilidades con Nuclei."""
        if not self._nuclei_path:
            return VulnResult(
                target=target, scanner="nuclei",
                severity="error", title="Nuclei no instalado",
                raw_output="[Error] Nuclei no está instalado. Instálalo con: go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest",
            )

        cmd = [self._nuclei_path, "-u", target, "-severity", severity, "-silent", "-nc"]

        if tags:
            cmd.extend(["-tags", tags])
        if templates:
            cmd.extend(["-t", templates])

        raw = self._run_cmd(cmd, timeout=timeout)

        # Determinar severidad máxima encontrada
        max_sev = "info"
        sev_order = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
        for line in raw.splitlines():
            for sev in ["critical", "high", "medium", "low"]:
                if f"[{sev}]" in line.lower():
                    if sev_order.get(sev, 0) > sev_order.get(max_sev, 0):
                        max_sev = sev

        finding_count = len([l for l in raw.splitlines() if l.strip() and "[" in l])

        return VulnResult(
            target=target,
            scanner="nuclei",
            severity=max_sev,
            title=f"Nuclei Scan — {finding_count} hallazgos",
            description=f"Escaneo con severidades: {severity}",
            raw_output=raw,
            timestamp=time.time(),
        )

    # ---- Nikto Scan ----

    def nikto_scan(
        self,
        target: str,
        port: Optional[int] = None,
        ssl: bool = False,
        tuning: Optional[str] = None,
        timeout: int = 180,
    ) -> VulnResult:
        """Ejecuta escaneo de servidor web con Nikto."""
        if not self._nikto_path:
            return VulnResult(
                target=target, scanner="nikto",
                severity="error", title="Nikto no instalado",
                raw_output="[Error] Nikto no está instalado. Instálalo con: sudo apt install nikto",
            )

        cmd = [self._nikto_path, "-h", target, "-nointeractive"]
        if port:
            cmd.extend(["-p", str(port)])
        if ssl:
            cmd.append("-ssl")
        if tuning:
            cmd.extend(["-Tuning", tuning])

        raw = self._run_cmd(cmd, timeout=timeout)

        # Contar findings
        findings = [l for l in raw.splitlines() if l.strip().startswith("+")]

        return VulnResult(
            target=target,
            scanner="nikto",
            severity="medium" if findings else "info",
            title=f"Nikto Scan — {len(findings)} items detectados",
            raw_output=raw,
            timestamp=time.time(),
        )

    # ---- SSL/TLS Audit ----

    def ssl_audit(self, target: str, timeout: int = 120) -> VulnResult:
        """Auditoría SSL/TLS con testssl.sh."""
        if not self._testssl_path:
            # Fallback con openssl
            openssl_path = shutil.which("openssl")
            if openssl_path:
                raw = self._run_cmd(
                    ["openssl", "s_client", "-connect", f"{target}:443", "-servername", target],
                    timeout=15,
                )
                return VulnResult(
                    target=target, scanner="openssl",
                    severity="info", title="SSL/TLS Info (openssl fallback)",
                    raw_output=raw, timestamp=time.time(),
                )
            return VulnResult(
                target=target, scanner="testssl",
                severity="error", title="testssl.sh no instalado",
                raw_output="[Error] testssl.sh no instalado. Instala con: sudo apt install testssl.sh",
            )

        cmd = [self._testssl_path, "--fast", "--quiet", target]
        raw = self._run_cmd(cmd, timeout=timeout)

        severity = "info"
        for keyword in ["VULNERABLE", "NOT ok", "WEAK", "CRITICAL"]:
            if keyword in raw.upper():
                severity = "high"
                break

        return VulnResult(
            target=target, scanner="testssl",
            severity=severity,
            title=f"SSL/TLS Audit — {'Vulnerabilidades detectadas' if severity == 'high' else 'Sin problemas críticos'}",
            raw_output=raw, timestamp=time.time(),
        )

    # ---- Header Analysis ----

    def header_analysis(self, target: str) -> VulnResult:
        """Análisis profundo de cabeceras de seguridad HTTP."""
        curl_path = shutil.which("curl")
        if not curl_path:
            return VulnResult(
                target=target, scanner="headers",
                severity="error", title="curl no disponible",
                raw_output="[Error] curl no encontrado",
            )

        url = target if target.startswith("http") else f"https://{target}"
        raw = self._run_cmd(["curl", "-I", "-s", "-L", "-k", "--max-time", "10", url], timeout=15)

        # Analizar presencia de cabeceras de seguridad
        missing = []
        present = []
        raw_lower = raw.lower()

        for header in SECURITY_HEADERS:
            if header.lower() in raw_lower:
                present.append(header)
            else:
                missing.append(header)

        severity = "info"
        if len(missing) >= 7:
            severity = "high"
        elif len(missing) >= 4:
            severity = "medium"
        elif len(missing) >= 2:
            severity = "low"

        analysis_text = (
            f"Cabeceras de seguridad presentes ({len(present)}/{len(SECURITY_HEADERS)}):\n"
            + "\n".join(f"  ✅ {h}" for h in present)
            + f"\n\nCabeceras FALTANTES ({len(missing)}/{len(SECURITY_HEADERS)}):\n"
            + "\n".join(f"  ❌ {h}" for h in missing)
            + f"\n\n--- Raw Headers ---\n{raw}"
        )

        return VulnResult(
            target=target, scanner="headers",
            severity=severity,
            title=f"Security Headers — {len(present)}/{len(SECURITY_HEADERS)} presentes",
            description=f"Faltan: {', '.join(missing[:5])}{'...' if len(missing) > 5 else ''}",
            raw_output=analysis_text,
            timestamp=time.time(),
        )

    # ---- CMS Detection ----

    def cms_detection(self, target: str) -> VulnResult:
        """Detecta CMS, tecnologías y versiones."""
        whatweb_path = shutil.which("whatweb")
        url = target if target.startswith("http") else f"https://{target}"

        if whatweb_path:
            raw = self._run_cmd(["whatweb", "--color=never", "-v", url], timeout=20)
        else:
            raw = self._run_cmd(["curl", "-s", "-L", "-k", "--max-time", "10", url], timeout=15)
            # Detección básica por HTML
            techs = []
            if "wp-content" in raw or "wordpress" in raw.lower():
                techs.append("WordPress")
            if "joomla" in raw.lower():
                techs.append("Joomla")
            if "drupal" in raw.lower():
                techs.append("Drupal")
            if "next" in raw.lower() and "_next" in raw:
                techs.append("Next.js")
            if "react" in raw.lower():
                techs.append("React")
            raw = f"Tecnologías detectadas (curl fallback): {', '.join(techs) if techs else 'No determinado'}\n\n[Instala whatweb para análisis completo]"

        return VulnResult(
            target=target, scanner="cms",
            severity="info",
            title="CMS & Technology Detection",
            raw_output=raw,
            timestamp=time.time(),
        )

    # ---- Quick Full Scan ----

    def quick_vuln_scan(self, target: str) -> List[VulnResult]:
        """Ejecuta una combinación rápida de todos los escaneos de vulnerabilidades."""
        results = []
        results.append(self.header_analysis(target))
        results.append(self.cms_detection(target))
        results.append(self.ssl_audit(target))

        # Solo ejecutar Nuclei y Nikto si están instalados
        if self._nuclei_path:
            results.append(self.nuclei_scan(target, severity="critical,high", timeout=90))
        if self._nikto_path:
            results.append(self.nikto_scan(target, timeout=90))

        return results


# ============================================================================
# NETWORK AUDITOR
# ============================================================================

class NetworkAuditor:
    """Motor profesional de pruebas y auditoría de red."""

    def __init__(self):
        self._nmap_path = shutil.which("nmap")
        self.is_windows = os.name == "nt"

    def _run_cmd(self, cmd: List[str], timeout: int = 120) -> str:
        """Ejecuta un comando y retorna su salida."""
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=timeout, encoding="utf-8", errors="replace",
            )
            output = proc.stdout.strip()
            if proc.stderr.strip():
                output += "\n[STDERR] " + proc.stderr.strip()
            return output or "[Sin salida]"
        except subprocess.TimeoutExpired:
            return f"[Timeout: comando excedió {timeout}s]"
        except FileNotFoundError:
            return f"[Error: herramienta '{cmd[0]}' no encontrada]"
        except Exception as e:
            return f"[Error: {e}]"

    # ---- Advanced Port Scan ----

    def advanced_port_scan(
        self,
        target: str,
        ports: str = "1-1000",
        scan_type: str = "syn",
        timing: str = "T4",
        service_detect: bool = True,
        os_detect: bool = False,
        scripts: bool = False,
    ) -> NetworkResult:
        """Escaneo avanzado de puertos con Nmap o Socket Scanner concurrente en Windows."""
        if not self._nmap_path:
            if self.is_windows:
                # Motor de escaneo por socket ultra rápido nativo para Windows
                import socket
                from concurrent.futures import ThreadPoolExecutor

                open_ports = []
                target_ports = [80, 443, 8080, 8443, 21, 22, 25, 53, 110, 139, 445, 3389, 3306, 5432, 27017, 6379]
                if ports == "full" or ports == "all":
                    target_ports = list(range(1, 1025))
                elif ports == "top100":
                    target_ports = [20,21,22,23,25,53,80,110,111,135,139,143,443,445,993,995,1723,3306,3389,5900,8080]

                def scan_port(p):
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.settimeout(0.6)
                        if s.connect_ex((target, p)) == 0:
                            return p
                    except Exception:
                        pass
                    finally:
                        s.close()
                    return None

                with ThreadPoolExecutor(max_workers=50) as executor:
                    res = executor.map(scan_port, target_ports)
                    open_ports = [p for p in res if p]

                raw = f"Escaneo de Sockets Windows para {target}:\n" + "\n".join([f"Puerto {p}/TCP abierto" for p in open_ports])
                parsed = {"open_ports": [f"{p}/tcp" for p in open_ports], "services": []}
                return NetworkResult(
                    target=target, scan_type="port_scan (Windows Socket Engine)",
                    raw_output=raw, parsed_data=parsed,
                    timestamp=time.time(),
                )
            else:
                return NetworkResult(
                    target=target, scan_type="port_scan",
                    raw_output="[Error] Nmap no instalado. Instala con: sudo apt install nmap",
                )

        cmd = [self._nmap_path] if self.is_windows else ["sudo", self._nmap_path]

        # Tipo de escaneo
        scan_flags = {
            "syn": "-sS",
            "connect": "-sT",
            "udp": "-sU",
            "ack": "-sA",
            "fin": "-sF",
            "xmas": "-sX",
        }
        cmd.append(scan_flags.get(scan_type, "-sS"))

        # Puertos
        if ports == "full" or ports == "all":
            cmd.append("-p-")
        elif ports == "top100":
            cmd.append("--top-ports=100")
        elif ports == "top1000":
            cmd.append("--top-ports=1000")
        else:
            cmd.extend(["-p", ports])

        # Timing
        cmd.append(f"-{timing}")

        # Opciones adicionales
        if service_detect:
            cmd.append("-sV")
        if os_detect:
            cmd.append("-O")
        if scripts:
            cmd.append("-sC")

        cmd.append(target)

        raw = self._run_cmd(cmd, timeout=300)

        # Parsear puertos abiertos
        parsed = {"open_ports": [], "services": []}
        for line in raw.splitlines():
            port_match = re.match(r"(\d+/(?:tcp|udp))\s+(open|filtered)\s+(\S+)(?:\s+(.*))?", line)
            if port_match:
                port_info = {
                    "port": port_match.group(1),
                    "state": port_match.group(2),
                    "service": port_match.group(3),
                    "version": (port_match.group(4) or "").strip(),
                }
                parsed["open_ports"].append(port_info["port"])
                parsed["services"].append(port_info)

        return NetworkResult(
            target=target, scan_type="port_scan",
            raw_output=raw, parsed_data=parsed,
            timestamp=time.time(),
        )

    # ---- Host Discovery ----

    def host_discovery(self, subnet: str, timeout: int = 120) -> NetworkResult:
        """Descubrimiento de hosts activos en una subred."""
        if not self._nmap_path:
            return NetworkResult(
                target=subnet, scan_type="host_discovery",
                raw_output="[Error] Nmap no instalado",
            )

        raw = self._run_cmd(
            ["sudo", self._nmap_path, "-sn", "-PE", "-PA", subnet],
            timeout=timeout,
        )

        # Parsear hosts activos
        hosts = []
        current_host = {}
        for line in raw.splitlines():
            host_match = re.match(r"Nmap scan report for (.+?)(?:\s+\((\d+\.\d+\.\d+\.\d+)\))?", line)
            if host_match:
                if current_host:
                    hosts.append(current_host)
                current_host = {
                    "hostname": host_match.group(1),
                    "ip": host_match.group(2) or host_match.group(1),
                }
            if "Host is up" in line:
                latency = re.search(r"\(([^)]+)\)", line)
                current_host["status"] = "up"
                current_host["latency"] = latency.group(1) if latency else ""
            if "MAC Address" in line:
                mac_match = re.search(r"MAC Address:\s+(\S+)\s+\((.+?)\)", line)
                if mac_match:
                    current_host["mac"] = mac_match.group(1)
                    current_host["vendor"] = mac_match.group(2)

        if current_host:
            hosts.append(current_host)

        return NetworkResult(
            target=subnet, scan_type="host_discovery",
            raw_output=raw,
            parsed_data={"hosts": hosts, "total": len(hosts)},
            timestamp=time.time(),
        )

    # ---- Service Enumeration ----

    def service_enumeration(self, target: str) -> NetworkResult:
        """Enumeración detallada de servicios y versiones."""
        if not self._nmap_path:
            return NetworkResult(
                target=target, scan_type="service_enum",
                raw_output="[Error] Nmap no instalado",
            )

        raw = self._run_cmd(
            ["sudo", self._nmap_path, "-sV", "--version-intensity", "5", "-sC", "-T4", target],
            timeout=300,
        )

        return NetworkResult(
            target=target, scan_type="service_enum",
            raw_output=raw, timestamp=time.time(),
        )

    # ---- OS Detection ----

    def os_detection(self, target: str) -> NetworkResult:
        """Detección remota de sistema operativo."""
        if not self._nmap_path:
            return NetworkResult(
                target=target, scan_type="os_detect",
                raw_output="[Error] Nmap no instalado",
            )

        raw = self._run_cmd(
            ["sudo", self._nmap_path, "-O", "--osscan-guess", "-T4", target],
            timeout=120,
        )

        return NetworkResult(
            target=target, scan_type="os_detect",
            raw_output=raw, timestamp=time.time(),
        )

    # ---- DNS Enumeration ----

    def dns_enumeration(self, domain: str) -> NetworkResult:
        """Enumeración DNS completa (A, AAAA, MX, NS, TXT, SOA, CNAME)."""
        dig_path = shutil.which("dig")
        host_path = shutil.which("host")

        results = {}
        record_types = ["A", "AAAA", "MX", "NS", "TXT", "SOA", "CNAME"]

        if dig_path:
            for rtype in record_types:
                output = self._run_cmd(["dig", "+short", domain, rtype], timeout=10)
                results[rtype] = output.strip() if output.strip() and "[Error" not in output else "No records"
        elif host_path:
            raw = self._run_cmd(["host", "-a", domain], timeout=15)
            return NetworkResult(
                target=domain, scan_type="dns_enum",
                raw_output=raw, parsed_data={"method": "host -a"},
                timestamp=time.time(),
            )
        else:
            # Python fallback con socket
            import socket
            try:
                ips = socket.getaddrinfo(domain, None)
                results["A"] = ", ".join(set(addr[4][0] for addr in ips if addr[0] == socket.AF_INET))
                results["AAAA"] = ", ".join(set(addr[4][0] for addr in ips if addr[0] == socket.AF_INET6))
            except Exception as e:
                results["error"] = str(e)

        formatted = "\n".join(f"[{rt}] {val}" for rt, val in results.items())

        return NetworkResult(
            target=domain, scan_type="dns_enum",
            raw_output=formatted, parsed_data=results,
            timestamp=time.time(),
        )

    # ---- Traceroute ----

    def traceroute_analysis(self, target: str) -> NetworkResult:
        """Análisis de ruta con traceroute."""
        traceroute_path = shutil.which("traceroute") or shutil.which("tracepath")

        if traceroute_path:
            raw = self._run_cmd([traceroute_path, "-m", "20", target], timeout=60)
        elif self._nmap_path:
            raw = self._run_cmd(["sudo", self._nmap_path, "--traceroute", "-Pn", target], timeout=60)
        else:
            raw = "[Error] Ni traceroute ni nmap están instalados"

        return NetworkResult(
            target=target, scan_type="traceroute",
            raw_output=raw, timestamp=time.time(),
        )

    # ---- ARP Scan ----

    def arp_scan(self, interface: str = "eth0") -> NetworkResult:
        """Escaneo ARP en la red local."""
        arp_scan_path = shutil.which("arp-scan")
        netdiscover_path = shutil.which("netdiscover")

        if arp_scan_path:
            raw = self._run_cmd(
                ["sudo", arp_scan_path, "-l", "-I", interface],
                timeout=30,
            )
        elif netdiscover_path:
            raw = self._run_cmd(
                ["sudo", netdiscover_path, "-i", interface, "-P", "-N"],
                timeout=30,
            )
        elif self._nmap_path:
            raw = self._run_cmd(
                ["sudo", self._nmap_path, "-sn", "-PR", f"--interface={interface}", "192.168.1.0/24"],
                timeout=30,
            )
        else:
            raw = "[Error] Ni arp-scan, netdiscover ni nmap están instalados"

        return NetworkResult(
            target=f"local ({interface})", scan_type="arp_scan",
            raw_output=raw, timestamp=time.time(),
        )

#!/usr/bin/env bash
# ==============================================================================
# Blood-Cipher v1.5 - Instalador Interactivo Nativo para Linux
# ==============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${RED}${BOLD}"
cat << "EOF"
  ██████╗ ██╗      ██████╗  ██████╗ ██████╗       ██████╗██╗██████╗ ██╗  ██╗███████╗██████╗ 
  ██╔══██╗██║     ██╔═══██╗██╔═══██╗██╔══██╗     ██╔════╝██║██╔══██╗██║  ██║██╔════╝██╔══██╗
  ██████╔╝██║     ██║   ██║██║   ██║██║  ██║     ██║     ██║██████╔╝███████║█████╗  ██████╔╝
  ██╔══██╗██║     ██║   ██║██║   ██║██║  ██║     ██║     ██║██╔═══╝ ██╔══██║██╔══╝  ██╔══██╗
  ██████╔╝███████╗╚██████╔╝╚██████╔╝██████╔╝     ╚██████╗██║██║     ██║  ██║███████╗██║  ██║
  ╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝       ╚═════╝╚═╝╚═╝     ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
    [ Agente Autónomo de IA para Ciberseguridad & Auditoría v1.5 ]
EOF
echo -e "${NC}"

echo -e "${CYAN}[*] Iniciando el instalador de Blood-Cipher v1.5...${NC}"

# 1. Verificar sistema operativo Linux
OS_TYPE="$(uname -s)"
if [ "$OS_TYPE" != "Linux" ]; then
    echo -e "${RED}[!] Error: Blood-Cipher está diseñado para entornos Linux (Kali, Debian, Ubuntu, Arch, etc.).${NC}"
    echo -e "${YELLOW}[i] Detectado: $OS_TYPE${NC}"
    exit 1
fi
echo -e "${GREEN}[✓] Sistema operativo Linux detectado ($OS_TYPE).${NC}"

# 2. Instalar paquetes esenciales del sistema (Python, venv, pip, herramientas de red)
echo -e "${CYAN}[*] Verificando e instalando dependencias base del sistema...${NC}"
if command -v apt-get &> /dev/null; then
    SUDO_CMD=""
    if [ "$EUID" -ne 0 ]; then
        if command -v sudo &> /dev/null; then
            SUDO_CMD="sudo"
        fi
    fi
    echo -e "${CYAN}[*] Instalando python3, python3-venv, python3-pip, jq, curl, git vía apt...${NC}"
    $SUDO_CMD apt-get update -qq || true
    $SUDO_CMD apt-get install -y -qq python3 python3-venv python3-pip python3-full jq curl git nmap whatweb &>/dev/null || {
        echo -e "${YELLOW}[!] Advertencia: Algunos paquetes apt requirieron confirmación manual.${NC}"
        $SUDO_CMD apt-get install -y python3 python3-venv python3-pip jq curl git || true
    }
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[!] Error: Python 3 no está instalado.${NC}"
    echo -e "${YELLOW}[i] Por favor instala Python 3 con: sudo apt update && sudo apt install -y python3 python3-venv python3-pip${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${GREEN}[✓] Python 3 detectado (versión $PYTHON_VERSION).${NC}"

# 3. Directorio de instalación aislado
INSTALL_DIR="/opt/blood-cipher"
if [ "$EUID" -ne 0 ] && [ ! -w "/opt" ]; then
    INSTALL_DIR="$HOME/.local/share/blood-cipher"
fi
VENV_DIR="$INSTALL_DIR/env"
BIN_DIR="$HOME/.local/bin"
SYSTEM_BIN="/usr/local/bin"
ALT_SYSTEM_BIN="/usr/bin"

echo -e "${CYAN}[*] Preparando entorno virtual aislado en ${BOLD}$VENV_DIR${NC}..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$HOME/.config/blood-cipher"

# Crear venv si no existe
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR" || {
        echo -e "${YELLOW}[!] Intentando crear venv con --without-pip...${NC}"
        python3 -m venv --without-pip "$VENV_DIR" || {
            echo -e "${RED}[!] Error al crear entorno virtual.${NC}"
            exit 1
        }
    }
fi
echo -e "${GREEN}[✓] Entorno virtual configurado correctamente.${NC}"

# 4. Instalar dependencias en el entorno virtual
echo -e "${CYAN}[*] Actualizando pip y herramientas de empaquetado...${NC}"
"$VENV_DIR/bin/pip" install --upgrade pip setuptools wheel --quiet 2>/dev/null || true

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo -e "${CYAN}[*] Instalando dependencias de Blood-Cipher...${NC}"
"$VENV_DIR/bin/pip" install -r "$REPO_DIR/requirements.txt" --quiet

echo -e "${CYAN}[*] Instalando paquete local en modo editable...${NC}"
"$VENV_DIR/bin/pip" install -e "$REPO_DIR" --no-deps --quiet

# 5. Crear script lanzador ejecutable universal
LAUNCHER="$INSTALL_DIR/blood-cipher-launcher"
cat << EOF > "$LAUNCHER"
#!/usr/bin/env bash
export PATH="$VENV_DIR/bin:\$PATH"
exec "$VENV_DIR/bin/blood-cipher" "\$@"
EOF
chmod +x "$LAUNCHER"

# 6. Crear enlace simbólico global (para usuario normal y root/sudo)
LINK_PATH=""

if [ "$EUID" -eq 0 ] || [ -w "$SYSTEM_BIN" ]; then
    ln -sf "$LAUNCHER" "$SYSTEM_BIN/blood-cipher"
    LINK_PATH="$SYSTEM_BIN/blood-cipher"
    # También en /usr/bin como respaldo para scripts sudo
    ln -sf "$LAUNCHER" "$ALT_SYSTEM_BIN/blood-cipher" 2>/dev/null || true
else
    if command -v sudo &> /dev/null && sudo -n true 2>/dev/null; then
        sudo ln -sf "$LAUNCHER" "$SYSTEM_BIN/blood-cipher" 2>/dev/null || true
        sudo ln -sf "$LAUNCHER" "$ALT_SYSTEM_BIN/blood-cipher" 2>/dev/null || true
        LINK_PATH="$SYSTEM_BIN/blood-cipher"
    else
        ln -sf "$LAUNCHER" "$BIN_DIR/blood-cipher"
        LINK_PATH="$BIN_DIR/blood-cipher"
    fi
fi

if [ -z "$LINK_PATH" ] || [ ! -f "$LINK_PATH" ]; then
    ln -sf "$LAUNCHER" "$BIN_DIR/blood-cipher"
    LINK_PATH="$BIN_DIR/blood-cipher"
fi

# 7. Limpiar la terminal y mostrar la CLI de bienvenida
clear

echo -e "${RED}${BOLD}"
cat << "EOF"
  ██████╗ ██╗      ██████╗  ██████╗ ██████╗       ██████╗██╗██████╗ ██╗  ██╗███████╗██████╗ 
  ██╔══██╗██║     ██╔═══██╗██╔═══██╗██╔══██╗     ██╔════╝██║██╔══██╗██║  ██║██╔════╝██╔══██╗
  ██████╔╝██║     ██║   ██║██║   ██║██║  ██║     ██║     ██║██████╔╝███████║█████╗  ██████╔╝
  ██╔══██╗██║     ██║   ██║██║   ██║██║  ██║     ██║     ██║██╔═══╝ ██╔══██║██╔══╝  ██╔══██╗
  ██████╔╝███████╗╚██████╔╝╚██████╔╝██████╔╝     ╚██████╗██║██║     ██║  ██║███████╗██║  ██║
  ╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝       ╚═════╝╚═╝╚═╝     ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
    [ Kali Linux | BlackArch | Arch Linux | Debian | Ubuntu ]
EOF
echo -e "${NC}"

echo -e "${GREEN}${BOLD}================================================================${NC}"
echo -e "${GREEN}${BOLD}   ✓ ¡BLOOD-CIPHER v2.0 SE INSTALÓ CON ÉXITO EN TU SISTEMA!   ${NC}"
echo -e "${GREEN}${BOLD}================================================================${NC}"
echo -e "${CYAN}Ejecutable vinculado en:${NC} ${BOLD}$LINK_PATH${NC}"
echo ""
echo -e "${BOLD}${YELLOW}🚀 COMANDOS PRINCIPALES:${NC}"
echo -e "  ${GREEN}blood-cipher${NC}               ➔ Inicia el agente en modo interactivo"
echo -e "  ${GREEN}blood-cipher web${NC}           ➔ Inicia el Centro de Mando Web (Dashboard)"
echo -e "  ${GREEN}blood-cipher audit creds${NC}   ➔ Módulo de auditoría y cracking de credenciales"
echo -e "  ${GREEN}blood-cipher audit vulns${NC}   ➔ Escáner de vulnerabilidades (Nuclei, Nikto, SSL)"
echo -e "  ${GREEN}blood-cipher audit network${NC} ➔ Pruebas de red y descubrimiento de puertos"
echo -e "  ${GREEN}blood-cipher config${NC}        ➔ Configura tu modelo y API Key (Gemini, Claude, GPT, Groq, Ollama)"
echo ""
echo -e "${BOLD}¿Quieres iniciar la configuración interactiva ahora mismo? (S/n):${NC} "
read -r -t 15 launch_choice || launch_choice="s"

if [[ "$launch_choice" =~ ^[SsYy]$ ]] || [[ -z "$launch_choice" ]]; then
    exec "$LINK_PATH" config
fi

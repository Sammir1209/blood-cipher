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

# 2. Verificar Python 3 y herramientas necesarias
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[!] Error: Python 3 no está instalado.${NC}"
    echo -e "${YELLOW}[i] Por favor instala Python 3 con: sudo apt update && sudo apt install -y python3 python3-venv python3-pip${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${GREEN}[✓] Python 3 detectado (versión $PYTHON_VERSION).${NC}"

# 3. Directorio de instalación aislado
INSTALL_DIR="$HOME/.local/share/blood-cipher"
VENV_DIR="$INSTALL_DIR/env"
BIN_DIR="$HOME/.local/bin"
SYSTEM_BIN="/usr/local/bin"

echo -e "${CYAN}[*] Preparando entorno virtual aislado en ${BOLD}$VENV_DIR${NC}..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$HOME/.config/coder-kali"

# Crear venv si no existe
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR" || {
        echo -e "${YELLOW}[!] Falló la creación del venv estándar. Intentando con dependencias adicionales...${NC}"
        echo -e "${YELLOW}[i] Si estás en Debian/Ubuntu/Kali ejecuta: sudo apt install -y python3-venv${NC}"
        exit 1
    }
fi
echo -e "${GREEN}[✓] Entorno virtual configurado correctamente.${NC}"

# 4. Instalar dependencias en el entorno virtual
echo -e "${CYAN}[*] Actualizando pip y herramientas de empaquetado...${NC}"
"$VENV_DIR/bin/pip" install --upgrade pip setuptools wheel

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo -e "${CYAN}[*] Instalando dependencias de Blood-Cipher...${NC}"
"$VENV_DIR/bin/pip" install -r "$REPO_DIR/requirements.txt"

echo -e "${CYAN}[*] Instalando paquete local en modo editable...${NC}"
"$VENV_DIR/bin/pip" install -e "$REPO_DIR" --no-deps

# 5. Crear script lanzador ejecutable
LAUNCHER="$INSTALL_DIR/blood-cipher-launcher"
cat << EOF > "$LAUNCHER"
#!/usr/bin/env bash
export PATH="$VENV_DIR/bin:\$PATH"
exec "$VENV_DIR/bin/blood-cipher" "\$@"
EOF
chmod +x "$LAUNCHER"

# 6. Crear enlaces simbólicos
SYMLINK_SUCCESS=false

# Intentar en /usr/local/bin con sudo si es posible, o en ~/.local/bin
if [ -w "$SYSTEM_BIN" ]; then
    ln -sf "$LAUNCHER" "$SYSTEM_BIN/blood-cipher"
    ln -sf "$LAUNCHER" "$SYSTEM_BIN/coder-kali"
    SYMLINK_SUCCESS=true
    LINK_PATH="$SYSTEM_BIN/blood-cipher"
else
    echo -e "${YELLOW}[*] Solicitando permisos para crear symlink en /usr/local/bin (opcional)...${NC}"
    if sudo ln -sf "$LAUNCHER" "$SYSTEM_BIN/blood-cipher" 2>/dev/null && sudo ln -sf "$LAUNCHER" "$SYSTEM_BIN/coder-kali" 2>/dev/null; then
        SYMLINK_SUCCESS=true
        LINK_PATH="$SYSTEM_BIN/blood-cipher"
    else
        ln -sf "$LAUNCHER" "$BIN_DIR/blood-cipher"
        ln -sf "$LAUNCHER" "$BIN_DIR/coder-kali"
        SYMLINK_SUCCESS=true
        LINK_PATH="$BIN_DIR/blood-cipher"
        echo -e "${YELLOW}[i] Se creó el acceso en $BIN_DIR/blood-cipher${NC}"
        if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
            echo -e "${YELLOW}[i] Asegúrate de tener $BIN_DIR en tu \$PATH (agrega: export PATH=\"\$HOME/.local/bin:\$PATH\" a tu ~/.bashrc o ~/.zshrc)${NC}"
        fi
    fi
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
echo -e "${GREEN}${BOLD}   ✓ ¡BLOOD-CIPHER v1.5 SE INSTALÓ CON ÉXITO EN TU SISTEMA!   ${NC}"
echo -e "${GREEN}${BOLD}================================================================${NC}"
echo -e "${CYAN}Ejecutable vinculado en:${NC} ${BOLD}$LINK_PATH${NC} (y alias 'coder-kali')"
echo ""
echo -e "${BOLD}${YELLOW}🚀 COMANDOS PRINCIPALES:${NC}"
echo -e "  ${GREEN}blood-cipher${NC}               ➔ Inicia el agente en modo interactivo"
echo -e "  ${GREEN}blood-cipher web${NC}           ➔ Inicia el Centro de Mando Web (Dashboard)"
echo -e "  ${GREEN}blood-cipher audit creds${NC}   ➔ Módulo de auditoría y cracking de credenciales"
echo -e "  ${GREEN}blood-cipher audit vulns${NC}   ➔ Escáner de vulnerabilidades (Nuclei, Nikto, SSL)"
echo -e "  ${GREEN}blood-cipher audit network${NC} ➔ Pruebas de red y descubrimiento de puertos"
echo -e "  ${GREEN}blood-cipher config${NC}        ➔ Configura tu modelo y API Key (Gemini, Claude, GPT, Ollama)"
echo ""
echo -e "${BOLD}¿Quieres iniciar la configuración interactiva ahora mismo? (S/n):${NC} "
read -r -t 15 launch_choice || launch_choice="s"

if [[ "$launch_choice" =~ ^[SsYy]$ ]] || [[ -z "$launch_choice" ]]; then
    exec "$LINK_PATH" config
fi

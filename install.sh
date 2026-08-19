#!/usr/bin/env bash
# ==============================================================================
# Coder-Kali - Instalador Interactivo Nativo para Linux
# ==============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${CYAN}${BOLD}"
cat << "EOF"
  ____          _             _  __     _ _ 
 / ___|___   __| | ___ _ __  | |/ /__ _| (_)
| |   / _ \ / _` |/ _ \ '__| | ' // _` | | |
| |__| (_) | (_| |  __/ |    | . \ (_| | | |
 \____\___/ \__,_|\___|_|    |_|\_\__,_|_|_|
   [ Agente de IA para Ciberseguridad & DevOps ]
EOF
echo -e "${NC}"

echo -e "${CYAN}[*] Iniciando el instalador de Coder-Kali...${NC}"

# 1. Verificar sistema operativo Linux
OS_TYPE="$(uname -s)"
if [ "$OS_TYPE" != "Linux" ]; then
    echo -e "${RED}[!] Error: Coder-Kali está diseñado exclusivamente para entornos Linux (Kali, Debian, Ubuntu, Arch, etc.).${NC}"
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
INSTALL_DIR="$HOME/.local/share/coder-kali"
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
echo -e "${CYAN}[*] Instalando dependencias de Coder-Kali (litellm, rich, typer, bs4, etc.)...${NC}"
"$VENV_DIR/bin/pip" install -r "$REPO_DIR/requirements.txt"

echo -e "${CYAN}[*] Instalando paquete local coder-kali en modo editable...${NC}"
"$VENV_DIR/bin/pip" install -e "$REPO_DIR" --no-deps

# 5. Crear script lanzador ejecutable
LAUNCHER="$INSTALL_DIR/coder-kali-launcher"
cat << EOF > "$LAUNCHER"
#!/usr/bin/env bash
export PATH="$VENV_DIR/bin:\$PATH"
exec "$VENV_DIR/bin/coder-kali" "\$@"
EOF
chmod +x "$LAUNCHER"

# 6. Crear enlace simbólico
SYMLINK_SUCCESS=false

# Intentar en /usr/local/bin con sudo si es posible, o en ~/.local/bin
if [ -w "$SYSTEM_BIN" ]; then
    ln -sf "$LAUNCHER" "$SYSTEM_BIN/coder-kali"
    SYMLINK_SUCCESS=true
    LINK_PATH="$SYSTEM_BIN/coder-kali"
else
    echo -e "${YELLOW}[*] Solicitando permisos para crear symlink en /usr/local/bin/coder-kali (opcional)...${NC}"
    if sudo ln -sf "$LAUNCHER" "$SYSTEM_BIN/coder-kali" 2>/dev/null; then
        SYMLINK_SUCCESS=true
        LINK_PATH="$SYSTEM_BIN/coder-kali"
    else
        ln -sf "$LAUNCHER" "$BIN_DIR/coder-kali"
        SYMLINK_SUCCESS=true
        LINK_PATH="$BIN_DIR/coder-kali"
        echo -e "${YELLOW}[i] Se creó el acceso en $BIN_DIR/coder-kali${NC}"
        if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
            echo -e "${YELLOW}[i] Asegúrate de tener $BIN_DIR en tu \$PATH (agrega: export PATH=\"\$HOME/.local/bin:\$PATH\" a tu ~/.bashrc o ~/.zshrc)${NC}"
        fi
    fi
fi

echo ""
echo -e "${GREEN}${BOLD}======================================================${NC}"
echo -e "${GREEN}${BOLD}   ¡CODER-KALI SE INSTALÓ CON ÉXITO!   ${NC}"
echo -e "${GREEN}${BOLD}======================================================${NC}"
echo -e "${CYAN}Ejecutable vinculado en:${NC} ${BOLD}$LINK_PATH${NC}"
echo ""
echo -e "${BOLD}Primeros pasos:${NC}"
echo -e "  1. Configura tu modelo y API Key:"
echo -e "     ${YELLOW}coder-kali config${NC}"
echo ""
echo -e "  2. Inicia el agente interactivo:"
echo -e "     ${YELLOW}coder-kali chat${NC}   (o simplemente ${YELLOW}coder-kali${NC})"
echo ""
echo -e "  3. Ejecuta una orden directa en una línea:"
echo -e "     ${YELLOW}coder-kali run \"analiza los puertos abiertos en localhost y sugiere remediaciones\"${NC}"
echo ""

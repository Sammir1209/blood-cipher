#!/usr/bin/env bash
# ==============================================================================
# Blood-Cipher v2.0 - Instalador Nativo para Android / Termux
# ==============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

clear
echo -e "${RED}${BOLD}"
cat << "EOF"
  ██████╗ ██╗      ██████╗  ██████╗ ██████╗ 
  ██╔══██╗██║     ██╔═══██╗██╔═══██╗██╔══██╗
  ██████╔╝██║     ██║   ██║██║   ██║██║  ██║
  ██╔══██╗██║     ██║   ██║██║   ██║██║  ██║
  ██████╔╝███████╗╚██████╔╝╚██████╔╝██████╔╝
  ╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝ 
   [ Blood-Cipher v2.0 • Android / Termux Edition ]
EOF
echo -e "${NC}"

echo -e "${CYAN}[*] Detectando entorno Android / Termux...${NC}"

if [ -z "$PREFIX" ] && [ ! -d "/data/data/com.termux" ]; then
    echo -e "${YELLOW}[!] Advertencia: No parece ser un entorno Termux estándar.${NC}"
    echo -e "${YELLOW}[i] Continuando instalación usando prefijo local...${NC}"
    PREFIX="${PREFIX:-$HOME/.local}"
fi

echo -e "${GREEN}[✓] Entorno Termux detectado.${NC}"

# 1. Actualizar repositorios e instalar paquetes base de Termux
echo -e "${CYAN}[*] Actualizando repositorios e instalando paquetes esenciales (pkg)...${NC}"
pkg update -y || apt update -y
pkg install -y python git curl clang libffi openssl rust binutils make -y || {
    echo -e "${YELLOW}[!] Falló instalación automática de algunos paquetes C. Continuando...${NC}"
}

# 2. Configurar almacenamiento compartido opcional
if command -v termux-setup-storage &> /dev/null; then
    echo -e "${CYAN}[*] Solicitando acceso a almacenamiento interno (para guardar reportes en tu celular)...${NC}"
    termux-setup-storage || true
fi

# 3. Directorio de instalación aislado
INSTALL_DIR="$HOME/.local/share/blood-cipher"
BIN_DIR="$PREFIX/bin"
CONFIG_DIR="$HOME/.config/blood-cipher"

mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$HOME/storage/shared/Blood-Cipher" 2>/dev/null || true

# 4. Clonar o actualizar el repositorio en el dispositivo
REPO_DIR="$INSTALL_DIR/repo"
if [ -d "$REPO_DIR/.git" ]; then
    echo -e "${CYAN}[*] Actualizando repositorio existente de Blood-Cipher...${NC}"
    cd "$REPO_DIR"
    git pull origin main || true
else
    echo -e "${CYAN}[*] Descargando Blood-Cipher desde GitHub...${NC}"
    rm -rf "$REPO_DIR"
    git clone https://github.com/Sammir1209/blood-cipher.git "$REPO_DIR"
fi

# 5. Instalar dependencias Python en el entorno Termux
echo -e "${CYAN}[*] Instalando dependencias de Python (pip)...${NC}"
cd "$REPO_DIR"
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt || {
    echo -e "${YELLOW}[!] Reintentando instalación de dependencias en modo liviano...${NC}"
    pip install litellm rich typer questionary requests beautifulsoup4 cryptography python-dotenv orjson
}

echo -e "${CYAN}[*] Instalando Blood-Cipher CLI en Termux...${NC}"
pip install -e . --no-deps

# 6. Crear lanzador directo en $PREFIX/bin/blood-cipher
LAUNCHER="$BIN_DIR/blood-cipher"
cat << EOF > "$LAUNCHER"
#!/data/data/com.termux/files/usr/bin/bash
exec python3 -m coder_kali.cli "\$@"
EOF
chmod +x "$LAUNCHER"

clear
echo -e "${GREEN}${BOLD}================================================================${NC}"
echo -e "${GREEN}${BOLD}   ✓ ¡BLOOD-CIPHER v2.0 SE INSTALÓ CON ÉXITO EN TERMUX!        ${NC}"
echo -e "${GREEN}${BOLD}================================================================${NC}"
echo ""
echo -e "${CYAN}Ejecutable disponible en:${NC} ${BOLD}blood-cipher${NC}"
echo ""
echo -e "${BOLD}${YELLOW}📱 COMANDOS EN TERMUX:${NC}"
echo -e "  ${GREEN}blood-cipher${NC}               ➔ Inicia el copiloto de IA interactivo"
echo -e "  ${GREEN}blood-cipher config${NC}        ➔ Configura tu API Key (Gemini, Claude, GPT, Groq, Ollama)"
echo -e "  ${GREEN}blood-cipher web${NC}           ➔ Inicia el Dashboard Web móvil (http://localhost:8080)"
echo ""
echo -e "${BOLD}¿Deseas iniciar la configuración inicial ahora? (S/n):${NC} "
read -r -t 15 launch_choice || launch_choice="s"

if [[ "$launch_choice" =~ ^[SsYy]$ ]] || [[ -z "$launch_choice" ]]; then
    exec blood-cipher config
fi

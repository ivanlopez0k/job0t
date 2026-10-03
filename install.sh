#!/usr/bin/env bash
# ==============================================================================
# 🤖 job0t — Instalador Universal para macOS / Linux
# Repositorio: https://github.com/ivanlopez0k/job0t
# Uso: curl -fsSL https://raw.githubusercontent.com/ivanlopez0k/job0t/main/install.sh | bash
# ==============================================================================

set -e

# Colores de salida
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e ""
echo -e "${CYAN}==========================================================${NC}"
echo -e "${CYAN}   🤖 job0t — Instalador Rápido para macOS / Linux        ${NC}"
echo -e "${CYAN}   Buscador, clasificador y exportador de empleo          ${NC}"
echo -e "${CYAN}==========================================================${NC}"
echo -e ""

# 1. Verificar Python 3.10+
echo -e "${YELLOW}[1/5] Verificando instalación de Python 3...${NC}"

if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${RED}❌ Error: No se encontró 'python3' en tu sistema.${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo -e "Instalalo fácilmente con Homebrew ejecutando: ${CYAN}brew install python3${NC}"
    else
        echo -e "Instalalo con tu gestor de paquetes (ej: ${CYAN}sudo apt install python3 python3-venv python3-pip${NC})"
    fi
    exit 1
fi

PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo "$PY_VERSION" | cut -d'.' -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d'.' -f2)

if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]); then
    echo -e "${RED}❌ Error: Se requiere Python 3.10 o superior (encontrada versión $PY_VERSION).${NC}"
    exit 1
fi

echo -e "  -> Python detectado: $(which python3) ($PY_VERSION)"

# 2. Configurar directorios en ~/.job0t
echo -e "${YELLOW}[2/5] Configurando directorio de instalación...${NC}"
JOB0T_HOME="$HOME/.job0t"
APP_DIR="$JOB0T_HOME/app"
VENV_DIR="$JOB0T_HOME/venv"
BIN_DIR="$JOB0T_HOME/bin"

mkdir -p "$JOB0T_HOME"
mkdir -p "$BIN_DIR"

# 3. Descargar / Actualizar el código fuente
echo -e "${YELLOW}[3/5] Descargando la última versión de job0t...${NC}"
if command -v git >/dev/null 2>&1; then
    if [ -d "$APP_DIR/.git" ]; then
        echo "  -> Actualizando repositorio existente..."
        git -C "$APP_DIR" pull --quiet
    else
        rm -rf "$APP_DIR"
        git clone --quiet https://github.com/ivanlopez0k/job0t.git "$APP_DIR"
    fi
else
    echo "  -> Git no detectado. Descargando paquete tar.gz desde GitHub..."
    rm -rf "$APP_DIR"
    mkdir -p "$APP_DIR"
    curl -fsSL https://github.com/ivanlopez0k/job0t/archive/refs/heads/main.tar.gz | tar -xz -C "$JOB0T_HOME"
    mv "$JOB0T_HOME/job0t-main"/* "$APP_DIR/"
    rm -rf "$JOB0T_HOME/job0t-main"
fi

echo -e "  -> Código fuente listo en: $APP_DIR"

# 4. Crear entorno virtual e instalar dependencias
echo -e "${YELLOW}[4/5] Configurando entorno virtual e instalando dependencias...${NC}"
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"

echo "  -> Instalando paquetes de Python..."
"$VENV_PIP" install --upgrade pip --quiet
"$VENV_PIP" install -e "$APP_DIR" --quiet

# 5. Generar wrapper ejecutable y configurar PATH
echo -e "${YELLOW}[5/5] Registrando el comando 'job0t' en tu sistema...${NC}"
WRAPPER="$BIN_DIR/job0t"

cat <<EOF > "$WRAPPER"
#!/usr/bin/env bash
exec "$VENV_PYTHON" -m job0t "\$@"
EOF

chmod +x "$WRAPPER"

# Detectar shell y agregar al PATH si no está
PATH_LINE='export PATH="$HOME/.job0t/bin:$PATH"'
SHELL_CONFIGS=("$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.bash_profile")

for conf in "${SHELL_CONFIGS[@]}"; do
    if [ -f "$conf" ]; then
        if ! grep -q ".job0t/bin" "$conf"; then
            echo "" >> "$conf"
            echo "# job0t CLI" >> "$conf"
            echo "$PATH_LINE" >> "$conf"
            echo "  -> Agregado al PATH en $conf"
        fi
    fi
done

echo -e ""
echo -e "${GREEN}==========================================================${NC}"
echo -e "${GREEN}   🎉 ¡Instalación de job0t completada con éxito!         ${NC}"
echo -e "${GREEN}==========================================================${NC}"
echo -e ""
echo -e "Para empezar a buscar ofertas:"
echo -e "  1. Abrí una nueva terminal (o ejecutá: ${CYAN}source ~/.zshrc${NC} / ${CYAN}source ~/.bashrc${NC})"
echo -e "  2. Escribí y dale Enter a:"
echo -e "         ${YELLOW}job0t run${NC}"
echo -e ""
echo -e "${GREEN}¡Listo, hermano! Ya podés usar job0t desde cualquier carpeta.${NC}"
echo -e ""

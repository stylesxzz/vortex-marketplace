#!/bin/bash

# ============================================================
# VORTEX MARKETPLACE v15 - TOR HIDDEN SERVICE LAUNCHER
# ============================================================
# Este script configura o Tor Hidden Service e inicia o
# marketplace Web automaticamente.
# ============================================================

set -e

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Diretório do projeto
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOR_CONFIG_DIR="$HOME/.tor_vortex"
VORTEX_PORT=5000

# Banner
print_banner() {
    echo -e "${GREEN}"
    cat << "EOF"
             ,  ,
             \ \
             ) \ \    _p_
             )^ )\ /  p\
              \  \ \/  /  |
               \  \  \  /   /
                \  \  \/   /
                 \  \    /
                  \  \  /
                   \  \/
                    \ /
                     V
EOF
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}VORTEX MARKETPLACE v15 - TOR LAUNCHER${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "${NC}"
}

# Verificar dependências
check_dependencies() {
    echo -e "${YELLOW}[*] Checking dependencies...${NC}"
    
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}[!] Python 3 not found. Install it first.${NC}"
        exit 1
    fi
    
    if ! command -v tor &> /dev/null; then
        echo -e "${YELLOW}[!] Tor not found. Installing...${NC}"
        if command -v apt &> /dev/null; then
            sudo apt update && sudo apt install -y tor
        elif command -v pkg &> /dev/null; then
            pkg install -y tor
        else
            echo -e "${RED}[!] Cannot install Tor. Please install it manually.${NC}"
            exit 1
        fi
    fi
    
    echo -e "${GREEN}[✓] All dependencies OK${NC}"
}

# Instalar dependências Python
install_python_deps() {
    echo -e "${YELLOW}[*] Installing Python dependencies...${NC}"
    cd "$PROJECT_DIR"
    pip3 install -q flask requests 2>/dev/null || pip install -q flask requests
    echo -e "${GREEN}[✓] Python dependencies installed${NC}"
}

# Configurar Tor Hidden Service
setup_tor_hidden_service() {
    echo -e "${YELLOW}[*] Setting up Tor Hidden Service...${NC}"
    
    # Criar diretório de configuração
    mkdir -p "$TOR_CONFIG_DIR"
    mkdir -p "$TOR_CONFIG_DIR/hidden_service"
    
    # Criar arquivo de configuração do Tor
    cat > "$TOR_CONFIG_DIR/torrc" << EOF
# VORTEX MARKETPLACE - TOR CONFIGURATION
SocksPort 9050
ControlPort 9051
CookieAuthentication 1

# Hidden Service Configuration
HiddenServiceDir $TOR_CONFIG_DIR/hidden_service
HiddenServicePort 80 127.0.0.1:$VORTEX_PORT
HiddenServiceVersion 3
EOF

    echo -e "${GREEN}[✓] Tor configuration created${NC}"
}

# Iniciar Tor
start_tor() {
    echo -e "${YELLOW}[*] Starting Tor daemon...${NC}"
    
    # Matar instâncias anteriores de Tor
    pkill -f "tor -f $TOR_CONFIG_DIR/torrc" 2>/dev/null || true
    sleep 1
    
    # Iniciar Tor en background
    tor -f "$TOR_CONFIG_DIR/torrc" &
    TOR_PID=$!
    
    echo -e "${GREEN}[✓] Tor started (PID: $TOR_PID)${NC}"
    
    # Esperar que o Tor gere o hostname
    echo -e "${YELLOW}[*] Waiting for .onion address generation (this may take 30-60 seconds)...${NC}"
    
    for i in {1..120}; do
        if [ -f "$TOR_CONFIG_DIR/hidden_service/hostname" ]; then
            ONION_ADDRESS=$(cat "$TOR_CONFIG_DIR/hidden_service/hostname")
            echo -e "${GREEN}[✓] .onion address generated!${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
    done
    
    echo -e "${RED}[!] Timeout waiting for .onion address${NC}"
    kill $TOR_PID 2>/dev/null || true
    exit 1
}

# Inicializar banco de dados
init_database() {
    echo -e "${YELLOW}[*] Initializing database...${NC}"
    cd "$PROJECT_DIR"
    python3 -c "from database import init_db; init_db()" 2>/dev/null || true
    echo -e "${GREEN}[✓] Database initialized${NC}"
}

# Iniciar Flask
start_flask() {
    echo -e "${YELLOW}[*] Starting Flask application...${NC}"
    cd "$PROJECT_DIR"
    python3 app.py &
    FLASK_PID=$!
    echo -e "${GREEN}[✓] Flask started (PID: $FLASK_PID)${NC}"
}

# Exibir informações de acesso
show_access_info() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}✓ VORTEX MARKETPLACE IS RUNNING!${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo -e "${YELLOW}🔗 Access via Tor Browser:${NC}"
    echo -e "${GREEN}http://$ONION_ADDRESS${NC}"
    echo ""
    echo -e "${YELLOW}📝 Local Access (for testing):${NC}"
    echo -e "${GREEN}http://127.0.0.1:$VORTEX_PORT${NC}"
    echo ""
    echo -e "${YELLOW}📌 Instructions:${NC}"
    echo -e "1. Open ${GREEN}Tor Browser${NC}"
    echo -e "2. Navigate to: ${GREEN}http://$ONION_ADDRESS${NC}"
    echo -e "3. Create an account or login"
    echo -e "4. Start trading!"
    echo ""
    echo -e "${YELLOW}🔐 Security Notes:${NC}"
    echo -e "• Your .onion address: ${GREEN}$ONION_ADDRESS${NC}"
    echo -e "• Tor is running in background"
    echo -e "• All traffic is encrypted through Tor"
    echo -e "• Database file: ${GREEN}$PROJECT_DIR/marketplace.db${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  To stop the marketplace:${NC}"
    echo -e "Press ${GREEN}Ctrl+C${NC} or run: ${GREEN}pkill -f 'python3 app.py'${NC}"
    echo ""
    echo -e "${BLUE}========================================${NC}"
}

# Cleanup on exit
cleanup() {
    echo -e "${YELLOW}[*] Shutting down...${NC}"
    pkill -f "python3 app.py" 2>/dev/null || true
    pkill -f "tor -f $TOR_CONFIG_DIR/torrc" 2>/dev/null || true
    echo -e "${GREEN}[✓] Cleanup complete${NC}"
}

trap cleanup EXIT

# Main execution
main() {
    print_banner
    check_dependencies
    install_python_deps
    setup_tor_hidden_service
    start_tor
    init_database
    start_flask
    show_access_info
    
    # Keep the script running
    wait
}

main "$@"

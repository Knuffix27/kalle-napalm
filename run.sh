#!/bin/bash
# run.sh - Kalle Napalm Facility Script
# Vereinfachte Ausführung mit verschiedenen Modi

set -e  # Exit on error

# Colors für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script-Verzeichnis
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Default Werte
CONFIG_FILE="config.yaml"
MODE="run"
VERBOSE=""
DRY_RUN=""

# Funktionen
print_help() {
    cat << EOF
${BLUE}Kalle Napalm - Network Device Collector${NC}

Verwendung: $0 [OPTIONS]

Options:
    -c, --config FILE       Config-Datei (default: config.yaml)
    -m, --mode MODE         Ausführungs-Modus:
                            - run        : Normal ausführen
                            - dry-run    : Test-Modus (keine Änderungen)
                            - verbose    : Ausführlich mit Debug-Output
                            - cron       : Für Cron-Ausführung (minimal output)
    -v, --verbose           Verbose-Modus (Debug-Output)
    -d, --dry-run           Dry-run-Modus (Test)
    -e, --env-only          Netbox-Credentials nur von ENV-Vars lesen
    -l, --list-configs      Alle verfügbaren Config-Dateien anzeigen
    --setup                 Erste Einrichtung / Umgebung prüfen
    -h, --help              Diese Hilfe anzeigen

Beispiele:
    # Normal ausführen
    $0

    # Mit anderer Config
    $0 --config sites/hubsite.yaml

    # Verbose-Modus für Debugging
    $0 --verbose

    # Dry-run vor der echten Ausführung
    $0 --dry-run

    # Für Cron-Jobs
    $0 --mode cron

    # Setup/Diagnose
    $0 --setup

EOF
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Setup-Modus
run_setup() {
    print_info "Napalm Network Device Collector - Setup-Prüfung"
    echo ""

    # Python-Version prüfen
    print_info "Prüfe Python-Installation..."
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 nicht gefunden!"
        exit 1
    fi
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    print_success "Python3 gefunden: $PYTHON_VERSION"
    echo ""

    # Virtual Environment prüfen
    print_info "Prüfe Virtual Environment..."
    if [ -d "venv" ]; then
        print_success "Virtual Environment vorhanden"
        print_info "Aktiviere Virtual Environment..."
        source venv/bin/activate
        print_success "Virtual Environment aktiviert"
    else
        print_warning "Kein Virtual Environment gefunden!"
        print_info "Erstelle Virtual Environment..."
        python3 -m venv venv
        source venv/bin/activate
        print_success "Virtual Environment erstellt und aktiviert"
    fi
    echo ""

    # Dependencies prüfen
    print_info "Prüfe Dependencies..."
    pip install -q -r requirements.txt
    print_success "Dependencies installiert/aktualisiert"
    echo ""

    # Config-Datei prüfen
    print_info "Prüfe Konfiguration..."
    if [ -f "config.yaml" ]; then
        print_success "config.yaml vorhanden"
        DEVICE_COUNT=$(grep -c "^  - name:" config.yaml || echo "0")
        print_info "Anzahl Geräte/Ranges in Config: $DEVICE_COUNT"
    else
        print_warning "config.yaml nicht gefunden!"
        if [ -f "config.example.yaml" ]; then
            print_info "Erstelle config.yaml aus Beispiel..."
            cp config.example.yaml config.yaml
            print_success "config.yaml erstellt - bitte anpassen!"
            print_info "Editiere jetzt: nano config.yaml"
        fi
    fi
    echo ""

    # Umgebungsvariablen prüfen
    print_info "Prüfe Umgebungsvariablen..."
    if [ -n "$NETBOX_URL" ]; then
        print_success "NETBOX_URL gesetzt"
    else
        print_warning "NETBOX_URL nicht gesetzt (optional, kann in config.yaml sein)"
    fi

    if [ -n "$NETBOX_TOKEN" ]; then
        print_success "NETBOX_TOKEN gesetzt"
    else
        print_warning "NETBOX_TOKEN nicht gesetzt (optional, kann in config.yaml sein)"
    fi
    echo ""

    # SSH-Keys prüfen
    print_info "Prüfe SSH-Keys..."
    if [ -f "$HOME/.ssh/id_rsa" ]; then
        print_success "SSH-Key vorhanden: ~/.ssh/id_rsa"
    else
        print_warning "Standard SSH-Key nicht gefunden"
        print_info "Erstelle SSH-Key mit: ssh-keygen -t rsa -b 4096"
    fi
    echo ""

    print_success "Setup-Prüfung abgeschlossen!"
    print_info "Du kannst jetzt starten mit: $0 --dry-run"
}

# Config-Dateien auflisten
list_configs() {
    print_info "Verfügbare Config-Dateien:"
    echo ""
    if [ -f "config.yaml" ]; then
        print_success "config.yaml (Haupt-Config)"
    fi
    if [ -f "config.example.yaml" ]; then
        print_info "config.example.yaml (Beispiel-Template)"
    fi

    if [ -d "sites" ] && [ "$(ls -A sites/*.yaml 2>/dev/null)" ]; then
        print_info "Site-spezifische Configs:"
        ls -1 sites/*.yaml | while read config; do
            echo "  - $(basename $config)"
        done
    fi
    echo ""
}

# Hauptausführungs-Funktion
run_collector() {
    local config="$1"
    local verbose_flag="$2"
    local dry_run_flag="$3"

    # Config-Datei prüfen
    if [ ! -f "$config" ]; then
        print_error "Config-Datei nicht gefunden: $config"
        print_info "Verfügbare Configs:"
        list_configs
        exit 1
    fi

    # Python-Umgebung aktivieren
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi

    # Befehl zusammenstellen
    CMD="python napalm_device_collector.py --config $config"
    if [ -n "$verbose_flag" ]; then
        CMD="$CMD --verbose"
    fi
    if [ -n "$dry_run_flag" ]; then
        CMD="$CMD --dry-run"
    fi

    print_info "Starte Napalm Network Device Collector"
    print_info "Config: $config"
    [ -n "$verbose_flag" ] && print_info "Mode: Verbose"
    [ -n "$dry_run_flag" ] && print_info "Mode: Dry-run (keine Änderungen in Netbox)"
    echo ""

    # Ausführen
    $CMD
}

# Cron-Modus (minimales Output)
run_cron() {
    local config="$1"

    if [ -d "venv" ]; then
        source venv/bin/activate
    fi

    # Output zu Log-Datei
    TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
    echo "[$TIMESTAMP] Starte Napalm-Collection" >> napalm_cron.log

    python napalm_device_collector.py --config "$config" >> napalm_cron.log 2>&1
    RESULT=$?

    if [ $RESULT -eq 0 ]; then
        echo "[$TIMESTAMP] Collection erfolgreich" >> napalm_cron.log
    else
        echo "[$TIMESTAMP] Collection fehlgeschlagen (Exit-Code: $RESULT)" >> napalm_cron.log
    fi

    return $RESULT
}

# Argument-Parsing
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            print_help
            exit 0
            ;;
        --setup)
            run_setup
            exit 0
            ;;
        -l|--list-configs)
            list_configs
            exit 0
            ;;
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -m|--mode)
            MODE="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE="true"
            MODE="verbose"
            shift
            ;;
        -d|--dry-run)
            DRY_RUN="true"
            MODE="dry-run"
            shift
            ;;
        -e|--env-only)
            export NETBOX_CONFIG="env_only"
            shift
            ;;
        *)
            print_error "Unbekannte Option: $1"
            print_help
            exit 1
            ;;
    esac
done

# Mode-basierte Ausführung
case $MODE in
    setup)
        run_setup
        ;;
    list)
        list_configs
        ;;
    dry-run)
        run_collector "$CONFIG_FILE" "$VERBOSE" "true"
        ;;
    verbose)
        run_collector "$CONFIG_FILE" "true" "$DRY_RUN"
        ;;
    cron)
        run_cron "$CONFIG_FILE"
        ;;
    run)
        run_collector "$CONFIG_FILE" "$VERBOSE" "$DRY_RUN"
        ;;
    *)
        print_error "Unbekannter Modus: $MODE"
        print_help
        exit 1
        ;;
esac

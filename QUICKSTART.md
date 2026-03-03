# Quick Start Guide - Kalle Napalm

## 5-Minuten Setup

### 1. Installation

```bash
# Repository clonen
git clone <repository-url> kalle-napalm
cd kalle-napalm

# Setup-Skript ausführen
./run.sh --setup
```

Das Setup-Skript prüft automatisch:
- ✓ Python 3 Installation
- ✓ Virtual Environment
- ✓ Dependencies
- ✓ Konfiguration
- ✓ SSH-Keys

### 2. Konfiguration

```bash
# Config-Beispiel verwenden
cp config.example.yaml config.yaml

# Anpassen mit Lieblings-Editor
nano config.yaml
```

Minimale Config für einen Test-Router:

```yaml
netbox:
  url: "https://your-netbox.example.com"
  api_token: "your_api_token_here"

devices:
  - name: "Test-Router"
    host: "192.168.1.1"
    manufacturer: "cisco_ios"
    credentials:
      username: "admin"
      password: "admin123"

napalm:
  commands: [facts]
  timeout: 30
```

### 3. Umgebungsvariablen (optional)

```bash
# Für Sicherheit: Netbox-Token als Env-Var
export NETBOX_URL="https://your-netbox.example.com"
export NETBOX_TOKEN="your_api_token_here"

# Dann können diese aus config.yaml entfernt werden
```

### 4. Test starten

```bash
# Trocken-Lauf machen (keine Änderungen)
./run.sh --dry-run

# Wenn OK - mit Verbose für Details
./run.sh --verbose

# Production Run
./run.sh
```

## Häufige Aufgaben

### IP-Range hinzufügen

```yaml
devices:
  - name: "DC1-Switches"
    host_range: "192.168.100.0/24"  # Expandiert zu 254 IPs
    manufacturer: "cisco_ios"
    credentials:
      username: "netadmin"
      ssh_key: "/home/user/.ssh/network_key"
```

### SSH-Key statt Passwort

```yaml
credentials:
  username: "admin"
  ssh_key: "/home/user/.ssh/id_rsa"
```

### Verschiedene Hersteller mischen

```yaml
devices:
  # Cisco
  - name: "Router-Cisco"
    host: "10.1.1.1"
    manufacturer: "cisco_ios"
    credentials: {...}

  # Juniper
  - name: "Router-Juniper"
    host: "10.1.2.1"
    manufacturer: "junos"
    credentials: {...}

  # Arista
  - name: "Switch-Arista"
    host: "10.1.3.1"
    manufacturer: "eos"
    credentials: {...}
```

### Scheduled Execution (Cron)

```bash
# Täglich um 02:00 Uhr
0 2 * * * cd /opt/kalle-napalm && ./run.sh --mode cron

# Alle 6 Stunden
0 */6 * * * /opt/kalle-napalm/run.sh --mode cron
```

### Fehler debuggen

```bash
# Verbose Mode mit Debug-Output
./run.sh --config config.yaml --verbose

# Log-Datei ansehen
tail -f napalm_collector.log

# Nur Fehler anzeigen
grep ERROR napalm_collector.log
```

## Typische Workflows

### Workflow 1: Cisco-Netzwerk sammeln

```bash
# 1. Single Device Test
cat > config-test.yaml << 'EOF'
netbox:
  url: "https://netbox.local"
  api_token: "..."

devices:
  - name: "Router-Core"
    host: "192.168.1.1"
    manufacturer: "cisco_ios"
    credentials:
      username: "admin"
      ssh_key: "/home/user/.ssh/id_rsa"
EOF

# 2. Testen
./run.sh --config config-test.yaml --dry-run

# 3. Auf ganz Netzwerk erweitern
cat > config-prod.yaml << 'EOF'
netbox:
  url: "https://netbox.local"
  api_token: "..."

devices:
  - name: "Core-Routers"
    host_range: "192.168.1.0/28"
    manufacturer: "cisco_ios"
    credentials:
      username: "admin"
      ssh_key: "/home/user/.ssh/id_rsa"

  - name: "Distribution-Switches"
    host_range: "192.168.2.0/25"
    manufacturer: "cisco_ios"
    credentials:
      username: "netadmin"
      ssh_key: "/home/user/.ssh/id_rsa"

  - name: "Access-Switches"
    host_range: "192.168.10.0/23"
    manufacturer: "cisco_ios"
    credentials:
      username: "netadmin"
      ssh_key: "/home/user/.ssh/id_rsa"
EOF

# 4. Live Ausführung
./run.sh --config config-prod.yaml --verbose
```

### Workflow 2: Multi-Hersteller Setup

```bash
# Config mit gemischten Herstellern
cat > config-multivendor.yaml << 'EOF'
netbox:
  url: "https://netbox.local"
  api_token: "..."

devices:
  # Cisco IOS
  - name: "Site-A-Router"
    host: "10.1.1.1"
    manufacturer: "cisco_ios"
    credentials:
      username: "admin"
      ssh_key: "~/.ssh/id_rsa"

  # Juniper
  - name: "Site-B-Router"
    host: "10.2.1.1"
    manufacturer: "junos"
    credentials:
      username: "admin"
      ssh_key: "~/.ssh/id_rsa"

  # Arista
  - name: "DataCenter-Leaf-1"
    host: "10.3.1.1"
    manufacturer: "eos"
    credentials:
      username: "admin"
      ssh_key: "~/.ssh/id_rsa"

napalm:
  commands: [facts, interfaces, config]
  timeout: 45
EOF

./run.sh --config config-multivendor.yaml
```

### Workflow 3: Auto-Discovery (wenn Hersteller unbekannt)

```yaml
devices:
  - name: "Unknown-Device"
    host: "192.168.50.1"
    manufacturer: "auto"  # Automatische Erkennung
    credentials:
      username: "admin"
      password: "secret"
```

## Troubleshooting schnell

| Problem | Schnelle Lösung |
|---------|-----------------|
| "Connection refused" | `ssh 192.168.1.1 -u admin` manuell testen |
| "Authentication failed" | SSH-Key Pfad prüfen, `chmod 600 ~/.ssh/id_rsa` |
| "Timeout" | Timeout in config erhöhen auf 60 oder 90 |
| "Module not found" | `./run.sh --setup` nochmal ausführen |
| Empty Netbox | API-Token & URL prüfen, `--dry-run` testet Config |

## Next Steps

1. **Für Production:** config.yaml mit allen Devices erstellen
2. **Cron Job:** Scheduling einrichten (`crontab -e`)
3. **Monitoring:** Logs überwachen, Alerts konfigurieren
4. **Netbox:** Device-Klassifizierung anpassen
5. **Backup:**Sicherung der config.yaml und Logs

## Hilfe & Support

```bash
# Alle Optionen anzeigen
./run.sh --help

# Verfügbare Config-Dateien
./run.sh --list-configs

# Setup wiederholen
./run.sh --setup
```

Viel Erfolg! 🚀

# Kalle Napalm - Network Device Collector for Netbox

Ein universales Python-Skript zum automatischen Sammeln von Netzwerk-Gerätinformationen mittels **Napalm** und Schreiben in **Netbox**.

## Features

✅ **Universal Support** - Unterstützt alle Napalm-kompatiblen Hersteller (Cisco, Juniper, Arista, Aruba, etc.)
✅ **Tape Libraries & Storage** - Support für Tape-Bibliotheken und Storage-Systeme
✅ **Hardware Server Management** - ILOM (Oracle), iDRAC (Dell), iLO (HPE) Support
✅ **IP-Range Support** - Automatische Expansion von CIDR-Ranges (z.B. 10.0.0.0/24)
✅ **Flexible Credentials** - SSH-Keys oder Passwörter, Umgebungsvariablen-Support
✅ **Rich Data Collection** - Facts, Interfaces, Config-Backups, BGP-Daten
✅ **Netbox Integration** - Automatisches Erstellen/Aktualisieren von Geräten in Netbox
✅ **Error Handling** - Robuste Fehlerbehandlung mit detailliertem Logging
✅ **Dry-Run Modus** - Test ohne tatsächliche Änderungen in Netbox

## Installation

### Voraussetzungen
- Python 3.8+
- SSH-Zugang zu den Netzwerk-Geräten
- Netbox 2.8+ mit API-Token

### Setup

```bash
# Repository clonen
git clone https://github.com/username/kalle-napalm.git
cd kalle-napalm

# Virtual Environment erstellen
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# oder: venv\Scripts\activate  # Windows

# Dependencies installieren
pip install -r requirements.txt
```

## Konfiguration

### 1. Config-Datei erstellen

```bash
# Von Beispiel kopieren und anpassen
cp config.example.yaml config.yaml
nano config.yaml
```

### 2. Beispiel config.yaml

```yaml
netbox:
  url: "https://netbox.example.com"
  api_token: "0123456789abcdef"
  ssl_verify: true

devices:
  - name: "Router-Core"
    host: "192.168.1.1"
    manufacturer: "cisco_ios"
    credentials:
      username: "admin"
      ssh_key: "/home/user/.ssh/id_rsa"
    timeout: 30

  - name: "Access-Switches"
    host_range: "192.168.10.0/24"  # Range wird automatisch expandiert
    manufacturer: "cisco_ios"
    credentials:
      username: "netadmin"
      ssh_key: "/home/user/.ssh/network_key"

napalm:
  commands:
    - facts
    - interfaces
    - config
    - bgp
  timeout: 30

logging:
  level: "INFO"
  file: "napalm_collector.log"
```

### 3. Umgebungsvariablen (optional, aber empfohlen)

```bash
# Netbox-Credentials als Umgebungsvariablen setzen
export NETBOX_URL="https://netbox.example.com"
export NETBOX_TOKEN="0123456789abcdef"

# Jetzt können diese aus der Config-Datei entfernt werden!
```

### 4. Sicherheit

```bash
# Config-Datei schützen (nur Lesezugriff für Benutzer)
chmod 600 config.yaml

# Oder über config-Directory
mkdir -p config/
chmod 700 config/
cp config.yaml config/
```

## Verwendung

### Basis-Ausführung

```bash
python napalm_device_collector.py --config config.yaml
```

### Mit verbose Output (Debugging)

```bash
python napalm_device_collector.py --config config.yaml --verbose
```

### Dry-Run Mode (testet alles, schreibt aber nicht)

```bash
python napalm_device_collector.py --config config.yaml --dry-run
```

### Mit Umgebungsvariablen

```bash
export NETBOX_URL="https://netbox.example.com"
export NETBOX_TOKEN="your_api_token"
python napalm_device_collector.py --config config.yaml
```

### Beispiel: Mehrere Config-Dateien

```bash
# Alle Configs in subdirectory verarbeiten
for config in sites/*.yaml; do
    echo "Processing $config..."
    python napalm_device_collector.py --config "$config" --verbose
done
```

## Output & Logging

Das Skript erstellt automatisch ein Log-File:

```bash
# Live-Output ansehen
tail -f napalm_collector.log

# Mit timestamps und Level-Filtration
grep "ERROR" napalm_collector.log
grep "2024-03-03" napalm_collector.log
```

## Unterstützte Hersteller

Alle Napalm-kompatiblen Treiber sind unterstützt:

### Netzwerk-Geräte

| Hersteller | Treiber | Notizen |
|-----------|--------|---------|
| Cisco | `cisco_ios`, `cisco_nxos`, `cisco_iosxr` | IOS, NX-OS, IOS-XR |
| Juniper | `junos` | Junos OS |
| Arista | `eos` | EOS (Extremelyunst Linux-basiert) |
| Aruba | `aruba_aos` | AOS, CX-Serie |
| Palo Alto Networks | `paloaltonetworks` | Firewalls |
| Fortinet | `fortios` | FortiGate Firewalls |
| Vyos | `vyos` | Open-Source Router |

### Tape Libraries & Storage

| Hersteller | Treiber | Gerättyp |
|-----------|--------|---------|
| Fujitsu | `fujitsu` | `tape_library` |
| IBM | `ibm` | `tape_library` |
| Quantum | `quantum` | `tape_library` |
| Spectra/Seagate | `spectra` | `tape_library` |

### Hardware Server Management

| Hersteller | Gerättyp | Interface | Notizen |
|-----------|---------|-----------|---------|
| Oracle/Sun | `server_ilom` | ILOM | Integrated Lights-Out Management |
| Dell | `server_idrac` | iDRAC | Dell Remote Access Controller |
| HPE | `server_ilo` | iLO | HP Integrated Lights-Out |

**Siehe:** [Napalm Support Matrix](https://napalm.readthedocs.io/en/latest/support_matrix.html)

## Automatische Erkennung

Wenn du den Hersteller nicht kennst, nutze `manufacturer: "auto"`:

```yaml
devices:
  - name: "Mystery-Device"
    host: "10.20.1.1"
    manufacturer: "auto"  # Automatische Erkennung
    credentials:
      username: "admin"
      password: "secret"
```

**Hinweis:** Auto-detection nutzt ein Fallback auf generischen Driver. Explizite Angabe ist zuverlässiger.

## Spezielle Gerätetypen

### Tape Libraries

Tape-Bibliotheken können mit dem Parameter `device_type: "tape_library"` konfiguriert werden:

```yaml
devices:
  - name: "Tape-Library-Backend"
    host: "10.60.1.1"
    manufacturer: "fujitsu"  # oder ibm, quantum, spectra
    device_type: "tape_library"  # Optionaler Marker
    credentials:
      username: "admin"
      password: "lib_password"
    timeout: 60
```

### Hardware Server Management Interfaces

#### Oracle/Sun ILOM
```yaml
devices:
  - name: "Oracle-Server-01"
    host: "10.70.1.1"
    manufacturer: "oracle"
    device_type: "server_ilom"  # ILOM Management Port
    credentials:
      username: "root"
      password: "ilom_password"
    timeout: 30
```

#### Dell iDRAC
```yaml
devices:
  - name: "Dell-Server-01"
    host: "10.80.1.1"
    manufacturer: "dell"
    device_type: "server_idrac"  # iDRAC Management Port
    credentials:
      username: "root"
      password: "idrac_password"
    timeout: 30
```

#### HPE iLO
```yaml
devices:
  - name: "HPE-Server-01"
    host: "10.90.1.1"
    manufacturer: "hpe"
    device_type: "server_ilo"  # iLO Management Port
    credentials:
      username: "Administrator"
      password: "ilo_password"
    timeout: 30
```

Die `device_type` Parameter ermöglichen eine bessere Kategorisierung in Netbox und helfen bei der Verwaltung gemischter Infrastrukturen (Netzwerk + Storage + Server).

## Credentials-Optionen

### SSH-Key (empfohlen)

```yaml
credentials:
  username: "admin"
  ssh_key: "/home/user/.ssh/id_rsa"          # Privater Key
  # ssh_config: "/etc/ssh/ssh_config"         # Optional
```

### Password

```yaml
credentials:
  username: "admin"
  password: "plaintext_password"
```

### Mit Enable/Secret Password (z.B. Cisco)

```yaml
credentials:
  username: "admin"
  password: "user_password"
  secret: "enable_password"                  # Cisco enable secret
```

### SSH Agent nutzen

Der Agent wird automatisch genutzt, wenn SSH-Key gesetzt ist:

```bash
# SSH Key zum Agent hinzufügen
ssh-add ~/.ssh/id_rsa

# Dann in config.yaml:
ssh_key: "~/.ssh/id_rsa"  # Agent wird automatisch genutzt
```

## Datensammlung

### Facts
Basis-Informationen über das Gerät:
- Hersteller (vendor)
- Modell (model)
- Seriennummer (serial_number)
- Betriebssystem & Version
- Hostname
- FQDN

### Interfaces
Detaillierte Interface-Informationen:
- Interface-Name und Status
- IP-Adressen (IPv4/IPv6)
- MAC-Adresse
- MTU
- Speed/Duplex
- Beschreibung

### Config (Running)
Laufende Konfiguration wird als Backup gespeichert.

### BGP
BGP Neighbor-Informationen (falls BGP läuft):
- Nachbarn (Peer IPs)
- AS-Nummern
- Status
- Prefixes

## Fehlerbehandlung

Das Skript ist robust gegen Fehler:

```bash
# ✓ Erfolgreiche Geräte werden normal verarbeitet
# ✗ Fehlerhafte Geräte werden gelogt und übersprungen
# → Skript läuft weiter mit nächstem Gerät
```

**Häufige Fehler:**

| Problem | Lösung |
|---------|--------|
| "Connection refused" | SSH-Port prüfen (default 22), Firewall-Regeln |
| "Authentication failed" | Username/Password/SSH-Key prüfen |
| "Timeout" | Timeout in config erhöhen, Netzwerk-Latenz prüfen |
| "Authentication key not found" | SSH-Key-Pfad prüfen, Berechtigungen (chmod 600) |
| "Netbox API error" | URL, Token, SSL-Zertifikat prüfen |

## Netbox Integration

### Device erstellen/updaten

Das Skript erstellt automatisch:
- **Device** mit Name, Modell, Seriennummer
- **Manufacturer** (wird bei Bedarf erstellt)
- **Device Type** (wird bei Bedarf erstellt)
- **Site** (Standard: "Default")

### Beispiel-Output
```
[1/254] Processing Router-Core-1
  ✓ Successfully processed
[2/254] Processing Access-Switch-1
  ✓ Successfully processed
[3/254] Processing Access-Switch-2
  ✓ Successfully processed

============================================================
Collection Summary
============================================================
╒═════════════╤═══════╕
│ Status      │ Count │
╞═════════════╪═══════╡
│ Successful  │   252 │
│ Failed      │     2 │
│ Skipped     │     0 │
│ Total       │   254 │
╘═════════════╧═══════╛
```

## Advanced Usage

### Scheduling mit Cron

```bash
# Täglich um 02:00 Uhr ausführen
0 2 * * * cd /path/to/kalle-napalm && python napalm_device_collector.py --config config.yaml

# Alle 6 Stunden
0 */6 * * * /path/to/kalle-napalm/run.sh
```

### Parallel Execution (für große Netzwerke)

Mehrere Skript-Instanzen mit verschiedenen Config-Dateien:

```bash
#!/bin/bash
# run_parallel.sh - Mehrere Sites parallel verarbeiten

CONFIGS=("site1.yaml" "site2.yaml" "site3.yaml")

for config in "${CONFIGS[@]}"; do
    python napalm_device_collector.py --config "$config" &
done

wait  # Warten bis alle fertig sind
```

### Notifikationen bei Fehlern

```bash
#!/bin/bash
OUTPUT=$(python napalm_device_collector.py --config config.yaml)

if grep -q "Failed" <<< "$OUTPUT"; then
    echo "$OUTPUT" | mail -s "⚠ Napalm Collection Errors" admin@example.com
fi
```

## Troubleshooting

### Debug Mode aktivieren

```bash
# Sehr verbose output
python napalm_device_collector.py --config config.yaml --verbose

# Log-Datei in real-time ansehen
tail -f napalm_collector.log
```

### Config validieren

```python
# Schnelle Validierung der Config
python -c "
import yaml
with open('config.yaml') as f:
    cfg = yaml.safe_load(f)
    print(f'Devices: {len(cfg[\"devices\"])}')
    for dev in cfg['devices']:
        print(f'  - {dev[\"name\"]} ({dev.get(\"host\", dev.get(\"host_range\"))})')
"
```

### Einzelnes Gerät testen

```python
# Teste Connection zu einem spezifischen Gerät
from napalm_device_collector import NapalmCollector
from napalm import get_network_driver

driver = get_network_driver('cisco_ios')
device = driver(
    hostname='192.168.1.1',
    username='admin',
    password='secret'
)
device.open()
print(device.get_facts())
device.close()
```

## Best Practices

### Sicherheit
1. ✅ SSH-Keys statt Passwörter verwenden
2. ✅ Credentials nicht in Git commiten (`.gitignore`)
3. ✅ Config-Datei mit `chmod 600` schützen
4. ✅ Netbox-Token über Umgebungsvariable, nicht in Config
5. ✅ Read-only Accounts für Monitoring nutzen

### Operativ
1. ✅ Regelmäßig (täglich/wöchentlich) ausführen
2. ✅ Logs archivieren und monitoren
3. ✅ Netbox-Geräteclassifizierung anpassen (nach manuellen Updates)
4. ✅ Größere Ranges in mehreren Config-Dateien aufteilen (Parallelisierung)
5. ✅ SSH-Timeout auf Netzwerk-Bedingungen abstimmen

### Netzwerk
1. ✅ SSH-Zugang zu allen Geräten sicherstellen
2. ✅ Firewall-Regeln für SSH-Port (22) prüfen
3. ✅ MTU und Fragmentation prüfen (bei großen Configs)
4. ✅ Management-Netzwerk von Produktionsnetzwerk trennen

## Weitere Ressourcen

- [Napalm Dokumentation](https://napalm.readthedocs.io/)
- [Netbox API Dokumentation](https://netbox.dev/api/)
- [Pynetbox Python Library](https://github.com/netbox-community/pynetbox)

## Support & Issues

Probleme oder Feature-Requests?

- 📝 GitHub Issues erstellen
- 💬 Diskussionen starten
- 🐛 Bug Reports mit Logs willkommen

## Lizenz

Siehe LICENSE Datei (meist MIT oder GNU GPL v3)

---

**Viel Erfolg mit dem Napalm Network Device Collector! 🚀**
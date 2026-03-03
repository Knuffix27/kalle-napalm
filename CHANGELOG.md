# Changelog

Alle bemerkenswerten Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Format basiert auf [Keep a Changelog](https://keepachangelog.com/)
und folgt [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Erste öffentliche Version des Napalm Network Device Collectors
- Support für alle Napalm-kompatiblen Netzwerk-Geräte-Hersteller
- YAML-basierte Konfiguration mit IP-Range-Support
- Facts, Interfaces-Daten, Config-Backups und BGP-Information Sammlung
- Netbox API Integration mit automatischem Device-Management
- Dry-run Mode für sichere Tests
- Verbose Output und detailliertes Logging
- Helper Shell-Script für einfachere Ausführung
- Setup-Skript zur Umgebungsprüfung
- Cron-Mode für automatische Scheduled Execution
- SSH-Key und Passwort Authentication Support

### Security
- Credentials nicht in Git (`.gitignore`)
- Umgebungsvariablen-Support für sensitive Daten
- YAML safe_load() für sichere Config-Parsing
- SSH-Key bevorzugt über Passwörter

## [2.0.0] - TBD

### Planned
- Web-UI für Config-Management
- Redis Caching für Performance
- Prometheus Metrics Export
- Database Backend (PostgreSQL) statt Netbox-only
- Advanced error emails / Slack notifications
- Config Validation Web-Service
- RESTful API für programmatischen Zugriff

---

## Versions-Schema

- **[X.Y.Z]** = Release Version
- **[Unreleased]** = Kommende Features/Bugfixes

### Version Format: MAJOR.MINOR.PATCH
- **MAJOR**: API-Breaking Changes
- **MINOR**: Neue Features (rückwärts-kompatibel)
- **PATCH**: Bugfixes

---

## Danksagungen

Entwickelt mit Liebe für Network Engineers überall. 🚀

---

**Beiträge willkommen!**
Siehe [CONTRIBUTING.md](CONTRIBUTING.md) für Details.

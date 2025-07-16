# AutoGraph CLI - Alle verfügbaren Kommandos

**Vollständige Übersicht aller implementierten CLI-Aufrufe**

---

## 🚀 Entry Points

```bash
# Haupt Entry Point
python main.py [KOMMANDO] [OPTIONEN]

# Unified CLI Interface  
python autograph_cli.py [MODUL] [KOMMANDO] [OPTIONEN]

# CLI Framework direkt
python -m autograph.cli [KOMMANDO] [OPTIONEN]
```

---

## ⚡ YAML Generator

### Entity-Kataloge erstellen

```bash
# Aus Textdateien
python autograph_cli.py yaml entity-from-text --domain medizin --files "*.txt"

# Aus CSV-Dateien
python autograph_cli.py yaml entity-from-csv --csv data.csv --entity-column "name" --domain wirtschaft

# Interaktiver Wizard
python autograph_cli.py yaml wizard

# Ontologie aus Katalogen
python autograph_cli.py yaml ontology-from-catalogs --catalogs "*.yaml" --domain gesundheit

# YAML validieren
python autograph_cli.py yaml validate --file catalog.yaml
```

---

## 🔗 Entity Linking

### Modi und Status

```bash
# Status prüfen (alle Modi)
python autograph_cli.py entity-linking status --mode offline
python autograph_cli.py entity-linking status --mode hybrid  
python autograph_cli.py entity-linking status --mode online

# Entität verlinken
python autograph_cli.py entity-linking link-entity "BMW" "ORG" --domain wirtschaft

# Katalog erstellen
python autograph_cli.py entity-linking create-catalog "medizin" "./catalog.yaml"
```

---

## 🧭 Ontologie-Management

### Status und Mapping

```bash
# Ontologie-Status
python autograph_cli.py ontology status --mode offline

# Entity auf Ontologie mappen
python autograph_cli.py ontology map-entity "Aspirin" "DRUG" --domain medizin

# Relation auf Ontologie mappen
python autograph_cli.py ontology map-relation "behandelt" --domain medizin

# Beispiel-Ontologie erstellen
python autograph_cli.py ontology create-example "wirtschaft" "./ontology.yaml"
```

---

## 🔄 Text-Verarbeitung

### Pipeline-Integration

```bash
# Basis-Verarbeitung
python autograph_cli.py process --input document.txt

# Mit Domain und Output
python autograph_cli.py process --input text.txt --domain medizin --output result.json --format json

# Verschiedene Formate
python autograph_cli.py process --input text.txt --output result.yaml --format yaml
python autograph_cli.py process --input text.txt --output result.csv --format csv
```

---

## 🌐 API Integration

### Client-Tools

```bash
# API-Status prüfen
python autograph_cli.py api status --url http://localhost:8001

# API-Funktionen testen
python autograph_cli.py api test --url http://localhost:8001

# API-Dokumentation öffnen
python autograph_cli.py api docs --url http://localhost:8001
```

---

## ✅ Validation Tools

### Dateityp-Validierung

```bash
# YAML-Validierung
python autograph_cli.py validate --file catalog.yaml --type yaml

# Konfigurationsdatei
python autograph_cli.py validate --file config.yaml --type config

# JSON-Validierung  
python autograph_cli.py validate --file data.json --type json

# Automatische Typ-Erkennung
python autograph_cli.py validate --file autograph-config.yaml  # -> config
python autograph_cli.py validate --file entity_catalog.yaml   # -> catalog
```

---

## 🧠 CLI Framework

### Framework-Integration

```bash
# Interaktives Menü
python autograph_cli.py cli menu

# Konfiguration erstellen
python autograph_cli.py cli init

# Server starten
python autograph_cli.py cli serve --port 8000
```

### Direkte Framework-Kommandos

```bash
# Text verarbeiten
python -m autograph.cli run document.txt --processor both

# Interaktives Menü
python -m autograph.cli menu

# Server starten
python -m autograph.cli serve --port 8000

# Konfiguration erstellen
python -m autograph.cli init
```

---

## 📋 Module-Übersicht

| Modul | Kommandos | Beschreibung |
|-------|-----------|--------------|
| **yaml** | `entity-from-text`, `entity-from-csv`, `ontology-from-catalogs`, `wizard`, `validate` | YAML-Generierung |
| **entity-linking** | `status`, `link-entity`, `create-catalog` | Entity Linking (offline/hybrid/online) |
| **ontology** | `status`, `map-entity`, `map-relation`, `create-example` | Ontologie-Management |
| **process** | - | Text-Verarbeitung über Pipeline |
| **api** | `status`, `test`, `docs` | API-Integration |
| **validate** | - | Dateityp-Validierung |
| **cli** | `menu`, `init`, `serve` | CLI Framework Integration |

---

## 🎯 Häufige Parameter

| Parameter | Werte | Beschreibung |
|-----------|-------|--------------|
| `--domain` | `medizin`, `wirtschaft`, `wissenschaft` | Domain-Kontext |
| `--mode` | `offline`, `hybrid`, `online` | Verarbeitungsmodus |
| `--format` | `json`, `yaml`, `csv` | Output-Format |
| `--type` | `yaml`, `config`, `catalog`, `ontology`, `json` | Validierungstyp |
| `--url` | `http://localhost:8001` | API-URL |

---

## 🚀 Workflow-Beispiele

### Medizinische Wissensbasis

```bash
# 1. Katalog erstellen
python autograph_cli.py yaml entity-from-text --domain medizin --files "medical/*.txt"

# 2. Status prüfen
python autograph_cli.py entity-linking status --mode offline

# 3. Text verarbeiten
python autograph_cli.py process --input patient.txt --domain medizin --output analysis.json

# 4. Validieren
python autograph_cli.py validate --file analysis.json --type json
```

### Enterprise Knowledge Graph

```bash
# 1. Multiple Kataloge
python autograph_cli.py yaml entity-from-csv --csv companies.csv --entity-column name --domain wirtschaft

# 2. Ontologie erstellen
python autograph_cli.py yaml ontology-from-catalogs --catalogs "./catalogs/*.yaml" --domain enterprise

# 3. Server starten
python autograph_cli.py cli serve --port 8000

# 4. API testen
python autograph_cli.py api test --url http://localhost:8000
```

---

**🎉 Alle CLI-Kommandos sind vollständig implementiert und production-ready!**

**📖 Detaillierte Dokumentation**: Siehe [CLI-Kommando-Referenz.md](./CLI-Kommando-Referenz.md) für vollständige Parameter und Beispiele.

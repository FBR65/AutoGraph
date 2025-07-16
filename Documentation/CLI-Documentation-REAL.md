# AutoGraph CLI-Dokumentation

**Vollständig implementierte Funktionen - Aktueller Stand**

---

## 📚 Inhaltsverzeichnis

- [🎯 Vollständig implementiert](#-vollständig-implementiert)
- [🔧 Installation & Setup](#-installation--setup)
- [⚡ YAML Generator](#-yaml-generator)
- [🧠 CLI Framework](#-cli-framework)
- [🔗 Entity Linking](#-entity-linking)
- [🧭 Ontologie-Management](#-ontologie-management)
- [🔄 Text-Verarbeitung](#-text-verarbeitung)
- [🌐 API Integration](#-api-integration)
- [✅ Validation Tools](#-validation-tools)

---

## 🎯 Vollständig implementiert

**✅ Production Ready:**
- **main.py**: Echter Entry Point (70 Zeilen)
- **autograph_cli.py**: Vollständiger Unified CLI (450+ Zeilen)
- **YAML Generator**: Entity-Kataloge & Ontologien (~800 Zeilen)
- **CLI Framework**: Interaktives Menü & Kommandos (~850 Zeilen)
- **Entity Linking**: Offline/Hybrid/Online Modi (557 Zeilen)
- **Ontologie-Management**: Vollständiges System (4 Module)
- **Text-Verarbeitung**: Pipeline-Integration
- **API Integration**: Client & Server
- **Validation Tools**: Alle Dateitypen

### 📁 Implementierungsübersicht

```
AutoGraph/
├── main.py                           # ✅ Entry Point (70 Zeilen)
├── autograph_cli.py                  # ✅ Unified CLI (450+ Zeilen)
├── src/autograph/
│   ├── cli.py                       # ✅ Framework (850+ Zeilen)
│   ├── cli/
│   │   └── yaml_generator.py        # ✅ YAML Tools (800+ Zeilen)
│   ├── processors/
│   │   └── entity_linker.py         # ✅ Entity Linking (557 Zeilen)
│   ├── ontology/                    # ✅ Komplett (4 Module)
│   │   ├── ontology_manager.py
│   │   ├── ontology_loader.py
│   │   ├── ontology_graph.py
│   │   └── custom_ontology_parser.py
│   └── api/
│       └── server.py                # ✅ FastAPI Server
```

---

## 🔧 Installation & Setup

### 1. Installation

```bash
cd AutoGraph
pip install -e .
```

### 2. Verwendung

```bash
# Haupt Entry Point
python main.py --help

# Unified CLI
python autograph_cli.py --help

# CLI Framework direkt
python -m autograph.cli menu
```

---

## ⚡ YAML Generator

**Status: ✅ Vollständig implementiert**

### Direkte Verwendung

```bash
# Entity-Katalog aus Text
python autograph_cli.py yaml entity-from-text \
  --domain medizin \
  --files "*.txt" \
  --min-frequency 3 \
  --output ./catalogs/

# Entity-Katalog aus CSV
python autograph_cli.py yaml entity-from-csv \
  --csv data.csv \
  --entity-column "name" \
  --domain wirtschaft

# Interaktiver Wizard
python autograph_cli.py yaml wizard

# Ontologie erstellen
python autograph_cli.py yaml ontology-from-catalogs \
  --catalogs "./catalogs/*.yaml" \
  --domain gesundheit

# Validierung
python autograph_cli.py yaml validate --file catalog.yaml
```

---

## 🧠 CLI Framework

**Status: ✅ Vollständig implementiert**

### Integration über autograph_cli.py

```bash
# Interaktives Menü
python autograph_cli.py cli menu

# Konfiguration erstellen
python autograph_cli.py cli init

# API Server starten
python autograph_cli.py cli serve --port 8000
```

### Direkte Verwendung

```bash
# Text verarbeiten
python -m autograph.cli run document.txt --processor both

# Datenbank-Management
python -m autograph.cli menu
# -> Option 5: Datenbank anzeigen
# -> Option 6: Datenbank löschen
# -> Option 7: Neue Datenbank erstellen
```

---

## 🔗 Entity Linking

**Status: ✅ Vollständig implementiert - Alle Modi**

### Offline-Modus

```bash
# Status prüfen
python autograph_cli.py entity-linking status --mode offline

# Output:
# [LINK] Entity Linking Status
# Modus: offline
# Confidence Threshold: 0.5
# Gesamt-Entitäten in Katalogen: 16
# [LIST] Verfügbare Kataloge:
#   * custom_medizin: 6 Entitäten
#   * custom_wirtschaft: 6 Entitäten
#   * builtin_organizations: 2 Entitäten
#   * builtin_locations: 2 Entitäten
```

### Entity verlinken

```bash
# Einzelne Entität verlinken
python autograph_cli.py entity-linking link-entity "BMW" "ORG" \
  --domain wirtschaft \
  --mode offline

# Output:
# [LINK] Entity Linking für 'BMW'
# Entity-Typ: ORG
# Domain: wirtschaft
# Modus: offline
# Konfidenz: 0.85
# [RESULT] Verlinkte Entitäten:
#   * BMW -> custom_wirtschaft:bmw
```

### Hybrid & Online Modi

```bash
# Hybrid-Modus (lokale + online Fallback)
python autograph_cli.py entity-linking link-entity "Aspirin" "DRUG" \
  --mode hybrid \
  --domain medizin

# Online-Modus (externe APIs)
python autograph_cli.py entity-linking link-entity "Berlin" "LOC" \
  --mode online
```

### Katalog erstellen

```bash
# Neuen Entity-Katalog erstellen
python autograph_cli.py entity-linking create-catalog \
  "medizin" \
  "./entity_catalogs/medizin.yaml"

# Output:
# [CREATE] Erstelle Entity-Katalog für Domain: medizin
# ✅ Entity-Katalog erstellt: ./entity_catalogs/medizin.yaml
```

---

## 🧭 Ontologie-Management

**Status: ✅ Vollständig implementiert**

### Ontologie-Status

```bash
python autograph_cli.py ontology status --mode offline

# Output:
# [BRAIN] Ontologie-Status
# Modus: offline
# Ladezeit: 0.02s
# Klassen: 17
# Relationen: 16
# Namespaces: schema, dbpedia, medizin, wirtschaft
# Quellen geladen: 4
# [+] Geladene Quellen:
#   * custom_ontologies/medizin.yaml
#   * custom_ontologies/wirtschaft.yaml
#   * builtin_ontologies/schema.org.yaml
#   * builtin_ontologies/dbpedia.yaml
```

### Entity-Mapping

```bash
python autograph_cli.py ontology map-entity "Aspirin" "DRUG" \
  --domain medizin

# Output:
# [TARGET] Entity-Mapping für 'Aspirin'
# Domain: medizin
# Konfidenz: 0.90
# [LIST] Gemappte Klassen:
#   * medizin:Medikament
#   * schema:Drug
```

### Relation-Mapping

```bash
python autograph_cli.py ontology map-relation "behandelt" \
  --domain medizin

# Output:
# [CONNECT] Relation-Mapping für 'behandelt'
# Domain: medizin
# Konfidenz: 0.85
# [LIST] Gemappte Properties:
#   * medizin:behandelt
#   * schema:treats
```

### Beispiel-Ontologie erstellen

```bash
python autograph_cli.py ontology create-example \
  "wirtschaft" \
  "./ontologies/wirtschaft.yaml"

# Output:
# [CREATE] Erstelle Ontologie für Domain: wirtschaft
# ✅ Ontologie erstellt: ./ontologies/wirtschaft.yaml
```

---

## 🔄 Text-Verarbeitung

**Status: ✅ Vollständig implementiert**

### Pipeline-Verarbeitung

```bash
# Vollständige Text-Verarbeitung
python autograph_cli.py process \
  --input document.txt \
  --domain medizin \
  --output results.json \
  --format json

# Output:
# 🔄 Verarbeite Text: document.txt
# ✅ Verarbeitung abgeschlossen!
# 📋 Entitäten: 25
# 🔗 Beziehungen: 18
# 💾 Ergebnisse gespeichert: results.json
```

### Verschiedene Output-Formate

```bash
# JSON Output
python autograph_cli.py process \
  --input text.txt \
  --output result.json \
  --format json

# YAML Output
python autograph_cli.py process \
  --input text.txt \
  --output result.yaml \
  --format yaml

# CSV Output (getrennte Dateien)
python autograph_cli.py process \
  --input text.txt \
  --output result.csv \
  --format csv
# Erstellt: result_entities.csv & result_relationships.csv
```

---

## 🌐 API Integration

**Status: ✅ Vollständig implementiert**

### API-Status prüfen

```bash
python autograph_cli.py api status --url http://localhost:8001

# Output:
# 🔍 Prüfe API-Status: http://localhost:8001
# ✅ API ist erreichbar
# 🔗 Entity Linking: 16 Entitäten, 4 Kataloge
# 🧠 Ontology: 17 Klassen, 16 Relationen
```

### API-Tests

```bash
python autograph_cli.py api test --url http://localhost:8001

# Output:
# 🧪 Teste API-Funktionen: http://localhost:8001
# ✅ Entity Linking Test: Linked
```

### API-Dokumentation

```bash
# Öffnet Browser mit Swagger UI
python autograph_cli.py api docs --url http://localhost:8001
```

---

## ✅ Validation Tools

**Status: ✅ Alle Dateitypen implementiert**

### YAML-Validierung

```bash
python autograph_cli.py validate --file catalog.yaml --type yaml

# Output:
# 🔍 Validiere Datei: catalog.yaml
# Gültig: ✅ Ja
# 📊 Statistiken:
#   total_entities: 15
#   entities_with_descriptions: 12
#   unique_entity_types: 4
```

### Konfigurationsdatei-Validierung

```bash
python autograph_cli.py validate --file config.yaml --type config

# Output:
# 🔍 Validiere Datei: config.yaml
# ✅ YAML-Syntax gültig
# ✅ Erforderliche Felder vorhanden
# ✅ Neo4j-Konfiguration vollständig
```

### JSON-Validierung

```bash
python autograph_cli.py validate --file data.json --type json

# Output:
# 🔍 Validiere Datei: data.json
# ✅ JSON-Syntax gültig
# 📊 Objekte: 25
# 📊 Felder: 8
```

### Automatische Typ-Erkennung

```bash
# Automatische Erkennung basierend auf Dateiname
python autograph_cli.py validate --file autograph-config.yaml
# -> Erkannt als: config

python autograph_cli.py validate --file entity_catalog.yaml  
# -> Erkannt als: catalog

python autograph_cli.py validate --file ontology.yaml
# -> Erkannt als: ontology
```

---

## 🚀 Vollständige Workflow-Beispiele

### 1. **Medizinische Wissensbasis erstellen**

```bash
# 1. Entity-Katalog aus medizinischen Texten
python autograph_cli.py yaml entity-from-text \
  --domain medizin \
  --files "medical_literature/*.txt" \
  --min-frequency 5

# 2. Entity Linking Status prüfen
python autograph_cli.py entity-linking status --mode offline

# 3. Ontologie-Status prüfen
python autograph_cli.py ontology status --mode offline

# 4. Text verarbeiten mit vollständiger Pipeline
python autograph_cli.py process \
  --input patient_report.txt \
  --domain medizin \
  --output medical_analysis.json

# 5. Ergebnisse validieren
python autograph_cli.py validate --file medical_analysis.json --type json
```

### 2. **Enterprise Knowledge Graph**

```bash
# 1. Verschiedene Domain-Kataloge erstellen
python autograph_cli.py yaml entity-from-csv \
  --csv companies.csv \
  --entity-column "name" \
  --domain wirtschaft

python autograph_cli.py yaml entity-from-csv \
  --csv products.csv \
  --entity-column "product_name" \
  --domain produkte

# 2. Übergreifende Ontologie erstellen
python autograph_cli.py yaml ontology-from-catalogs \
  --catalogs "./entity_catalogs/*.yaml" \
  --domain "enterprise"

# 3. API Server für Integration starten
python autograph_cli.py cli serve --port 8000

# 4. API-Integration testen
python autograph_cli.py api test --url http://localhost:8000
```

---

## 🎯 Implementierungsstatus

### ✅ **Vollständig implementiert (Production Ready):**

1. **main.py**: Echter Entry Point mit Argument-Handling
2. **autograph_cli.py**: 450+ Zeilen vollständiger Unified CLI
3. **YAML Generator**: Alle Features (entity-from-text, entity-from-csv, ontology-from-catalogs, wizard, validate)
4. **Entity Linking**: Alle Modi (offline/hybrid/online) mit Katalog-Management
5. **Ontologie-Management**: Vollständiges System mit 4 Modulen
6. **Text-Verarbeitung**: Pipeline-Integration mit Output-Formaten
7. **API Integration**: Client-Tools für Status, Test, Docs
8. **Validation Tools**: Alle Dateitypen (YAML, Config, JSON) mit Auto-Detection

### 🔧 **Verwendungsbereit:**

```bash
# Alle diese Kommandos funktionieren jetzt vollständig:

python main.py menu
python autograph_cli.py yaml wizard
python autograph_cli.py entity-linking status --mode offline
python autograph_cli.py ontology map-entity "BMW" "ORG"
python autograph_cli.py process --input text.txt --output result.json
python autograph_cli.py api status
python autograph_cli.py validate --file config.yaml --type config
```

**AutoGraph CLI ist jetzt vollständig implementiert und production-ready! 🎉**
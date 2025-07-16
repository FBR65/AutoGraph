# AutoGraph CLI - Vollständige Kommando-Referenz

**Alle verfügbaren CLI-Aufrufe und deren Verwendung**

---

## 📚 Inhaltsverzeichnis

- [🚀 Entry Points](#-entry-points)
- [⚡ YAML Generator](#-yaml-generator)
- [🔗 Entity Linking](#-entity-linking)
- [🧭 Ontologie-Management](#-ontologie-management)
- [🔄 Text-Verarbeitung](#-text-verarbeitung)
- [🌐 API Integration](#-api-integration)
- [✅ Validation Tools](#-validation-tools)
- [🧠 CLI Framework](#-cli-framework)
- [📋 Alle Kommandos im Überblick](#-alle-kommandos-im-überblick)

---

## 🚀 Entry Points

### main.py - Haupt Entry Point

```bash
# Hilfe anzeigen
python main.py --help

# Version anzeigen
python main.py --version

# Ohne Argumente (zeigt Quick Start)
python main.py

# Interaktives Menü
python main.py menu

# Text verarbeiten
python main.py run document.txt --processor both

# YAML generieren
python main.py yaml entity-from-text --domain medizin --files *.txt

# Server starten
python main.py serve --port 8000

# Konfiguration erstellen
python main.py init
```

### autograph_cli.py - Unified CLI

```bash
# Hilfe anzeigen
python autograph_cli.py --help

# Ohne Argumente (zeigt vollständige Hilfe)
python autograph_cli.py
```

---

## ⚡ YAML Generator

### entity-from-text - Entity-Katalog aus Textdateien

```bash
# Basis-Verwendung
python autograph_cli.py yaml entity-from-text \
  --domain medizin \
  --files "medical_texts/*.txt"

# Mit allen Optionen
python autograph_cli.py yaml entity-from-text \
  --domain medizin \
  --files "medical_texts/*.txt" \
  --description "Medizinische Entitäten aus Fachliteratur" \
  --min-frequency 3 \
  --entity-types DRUG CONDITION SYMPTOM \
  --output ./generated_catalogs/

# Mehrere Dateien
python autograph_cli.py yaml entity-from-text \
  --domain wirtschaft \
  --files "business/*.txt" "reports/*.txt" \
  --min-frequency 5
```

**Parameter:**
- `--domain` (erforderlich): Domain/Bereich (z.B. medizin, wirtschaft)
- `--files` (erforderlich): Textdateien (unterstützt Wildcards)
- `--description`: Beschreibung des Katalogs
- `--min-frequency`: Mindest-Häufigkeit für Entitäten (Standard: 2)
- `--entity-types`: Gewünschte Entity-Typen (optional)
- `--output`: Ausgabe-Verzeichnis (Standard: ./generated_yamls)

### entity-from-csv - Entity-Katalog aus CSV-Datei

```bash
# Basis-Verwendung
python autograph_cli.py yaml entity-from-csv \
  --csv medical_drugs.csv \
  --entity-column "drug_name" \
  --domain medizin

# Mit allen Optionen
python autograph_cli.py yaml entity-from-csv \
  --csv medical_drugs.csv \
  --entity-column "drug_name" \
  --domain medizin \
  --description "Medikamentendatenbank" \
  --type-column "category" \
  --description-column "description" \
  --properties-columns "dosage" "manufacturer" "indication"

# Unternehmensdaten
python autograph_cli.py yaml entity-from-csv \
  --csv companies.csv \
  --entity-column "company_name" \
  --domain wirtschaft \
  --type-column "industry" \
  --properties-columns "revenue" "employees" "founded"
```

**Parameter:**
- `--csv` (erforderlich): CSV-Datei
- `--entity-column` (erforderlich): Spalte mit Entitäten
- `--domain` (erforderlich): Domain/Bereich
- `--description`: Beschreibung des Katalogs
- `--type-column`: Spalte mit Entity-Typen
- `--description-column`: Spalte mit Beschreibungen
- `--properties-columns`: Zusätzliche Property-Spalten

### ontology-from-catalogs - Ontologie aus Entity-Katalogen

```bash
# Basis-Verwendung
python autograph_cli.py yaml ontology-from-catalogs \
  --catalogs "./entity_catalogs/*.yaml" \
  --domain gesundheit

# Mit Relationen
python autograph_cli.py yaml ontology-from-catalogs \
  --catalogs "./entity_catalogs/*.yaml" \
  --domain gesundheit \
  --description "Gesundheits-Ontologie aus medizinischen Katalogen" \
  --include-relations

# Multi-Domain
python autograph_cli.py yaml ontology-from-catalogs \
  --catalogs "./generated_yamls/catalog_*.yaml" \
  --domain "multi_domain" \
  --description "Übergreifende Multi-Domain Ontologie"
```

**Parameter:**
- `--catalogs` (erforderlich): Entity-Katalog-Dateien (unterstützt Wildcards)
- `--domain` (erforderlich): Domain/Bereich
- `--description`: Beschreibung der Ontologie
- `--include-relations`: Relationen automatisch ableiten (Standard: true)

### wizard - Interaktiver Katalog-Wizard

```bash
# Standard-Wizard
python autograph_cli.py yaml wizard

# Mit Output-Verzeichnis
python autograph_cli.py yaml wizard --output ./my_catalogs/

# Erweiterten Modus
python autograph_cli.py yaml wizard \
  --output ./custom_catalogs/ \
  --interactive-mode advanced
```

### validate - YAML-Validierung

```bash
# YAML-Katalog validieren
python autograph_cli.py yaml validate --file my_catalog.yaml

# Mehrere Dateien validieren
python autograph_cli.py yaml validate --file catalog1.yaml catalog2.yaml
```

---

## 🔗 Entity Linking

### status - Entity Linking Status anzeigen

```bash
# Offline-Modus Status
python autograph_cli.py entity-linking status --mode offline

# Hybrid-Modus Status
python autograph_cli.py entity-linking status --mode hybrid

# Online-Modus Status
python autograph_cli.py entity-linking status --mode online
```

**Output:**
```
[LINK] Entity Linking Status
Modus: offline
Confidence Threshold: 0.5
Gesamt-Entitäten in Katalogen: 16
[LIST] Verfügbare Kataloge:
  * custom_medizin: 6 Entitäten
  * custom_wirtschaft: 6 Entitäten
  * builtin_organizations: 2 Entitäten
  * builtin_locations: 2 Entitäten
Cache-Verzeichnis: ./cache/entity_linking
Custom-Kataloge: ./entity_catalogs/
```

### link-entity - Einzelne Entität verlinken

```bash
# Basis-Linking
python autograph_cli.py entity-linking link-entity "BMW" "ORG"

# Mit Domain-Kontext
python autograph_cli.py entity-linking link-entity "BMW" "ORG" \
  --domain wirtschaft

# Mit Kontext für Disambiguation
python autograph_cli.py entity-linking link-entity "Aspirin" "DRUG" \
  --domain medizin \
  --context "Patient nimmt Aspirin gegen Kopfschmerzen"

# Verschiedene Modi
python autograph_cli.py entity-linking link-entity "Berlin" "LOC" \
  --mode offline

python autograph_cli.py entity-linking link-entity "Microsoft" "ORG" \
  --mode hybrid

python autograph_cli.py entity-linking link-entity "Einstein" "PER" \
  --mode online
```

**Parameter:**
- `entity_text` (erforderlich): Entity-Text
- `entity_type` (erforderlich): Entity-Typ (ORG, PER, LOC, DRUG, etc.)
- `--domain`: Domain-Kontext
- `--context`: Kontext-Text für Disambiguation
- `--mode`: Entity Linking Modus (offline/hybrid/online)

### create-catalog - Entity-Katalog erstellen

```bash
# Beispiel-Katalog erstellen
python autograph_cli.py entity-linking create-catalog \
  "medizin" \
  "./entity_catalogs/medizin.yaml"

# Verschiedene Domains
python autograph_cli.py entity-linking create-catalog \
  "wirtschaft" \
  "./entity_catalogs/wirtschaft.yaml"

python autograph_cli.py entity-linking create-catalog \
  "recht" \
  "./entity_catalogs/recht.yaml"
```

---

## 🧭 Ontologie-Management

### status - Ontologie-Status anzeigen

```bash
# Offline-Modus
python autograph_cli.py ontology status --mode offline

# Hybrid-Modus
python autograph_cli.py ontology status --mode hybrid

# Online-Modus
python autograph_cli.py ontology status --mode online
```

**Output:**
```
[BRAIN] Ontologie-Status
Modus: offline
Ladezeit: 0.02s
Klassen: 17
Relationen: 16
Namespaces: schema, dbpedia, medizin, wirtschaft
Quellen geladen: 4
[+] Geladene Quellen:
  * custom_ontologies/medizin.yaml
  * custom_ontologies/wirtschaft.yaml
  * builtin_ontologies/schema.org.yaml
  * builtin_ontologies/dbpedia.yaml
```

### map-entity - Entity auf Ontologie mappen

```bash
# Basis-Mapping
python autograph_cli.py ontology map-entity "Aspirin" "DRUG"

# Mit Domain
python autograph_cli.py ontology map-entity "Aspirin" "DRUG" \
  --domain medizin

# Verschiedene Entity-Typen
python autograph_cli.py ontology map-entity "BMW" "ORG" \
  --domain wirtschaft

python autograph_cli.py ontology map-entity "Berlin" "LOC" \
  --domain geographie

# Verschiedene Modi
python autograph_cli.py ontology map-entity "Microsoft" "ORG" \
  --domain technologie \
  --mode hybrid
```

### map-relation - Relation auf Ontologie mappen

```bash
# Medizinische Relationen
python autograph_cli.py ontology map-relation "behandelt" \
  --domain medizin

python autograph_cli.py ontology map-relation "verursacht" \
  --domain medizin

# Wirtschafts-Relationen
python autograph_cli.py ontology map-relation "investiert_in" \
  --domain wirtschaft

python autograph_cli.py ontology map-relation "konkurriert_mit" \
  --domain wirtschaft

# Allgemeine Relationen
python autograph_cli.py ontology map-relation "gehört_zu"

python autograph_cli.py ontology map-relation "befindet_sich_in"
```

### create-example - Beispiel-Ontologie erstellen

```bash
# Domain-spezifische Ontologien
python autograph_cli.py ontology create-example \
  "medizin" \
  "./ontologies/medizin.yaml"

python autograph_cli.py ontology create-example \
  "wirtschaft" \
  "./ontologies/wirtschaft.yaml"

python autograph_cli.py ontology create-example \
  "wissenschaft" \
  "./ontologies/wissenschaft.yaml"
```

---

## 🔄 Text-Verarbeitung

### process - Text über Pipeline verarbeiten

```bash
# Basis-Verarbeitung
python autograph_cli.py process --input document.txt

# Mit Domain
python autograph_cli.py process \
  --input medical_report.txt \
  --domain medizin

# Mit Output-Datei (JSON)
python autograph_cli.py process \
  --input business_report.txt \
  --domain wirtschaft \
  --output analysis.json \
  --format json

# YAML-Output
python autograph_cli.py process \
  --input scientific_paper.txt \
  --domain wissenschaft \
  --output results.yaml \
  --format yaml

# CSV-Output (getrennte Dateien)
python autograph_cli.py process \
  --input legal_document.txt \
  --domain recht \
  --output results.csv \
  --format csv
# Erstellt: results_entities.csv und results_relationships.csv

# Verschiedene Dateitypen
python autograph_cli.py process --input document.pdf --domain medizin
python autograph_cli.py process --input spreadsheet.xlsx --domain wirtschaft
python autograph_cli.py process --input webpage.html --domain technologie
```

**Parameter:**
- `--input` (erforderlich): Input-Datei oder -Text
- `--domain`: Domain/Bereich für kontextuelle Verarbeitung
- `--output`: Output-Datei
- `--format`: Output-Format (json, yaml, csv)

**Output-Beispiel:**
```
🔄 Verarbeite Text: medical_report.txt
✅ Verarbeitung abgeschlossen!
📋 Entitäten: 25
🔗 Beziehungen: 18
💾 Ergebnisse gespeichert: analysis.json

📋 Beispiel-Entitäten:
  • Aspirin (DRUG)
  • Hypertonie (CONDITION)
  • Patient (PERSON)
  • Krankenhaus München (ORG)
  • 100mg (DOSAGE)

🔗 Beispiel-Beziehungen:
  • Patient -> nimmt -> Aspirin (MEDICATION)
  • Aspirin -> behandelt -> Hypertonie (TREATMENT)
  • Patient -> wird_behandelt_in -> Krankenhaus München (LOCATION)
```

---

## 🌐 API Integration

### status - API-Status prüfen

```bash
# Standard-URL (localhost:8001)
python autograph_cli.py api status

# Custom URL
python autograph_cli.py api status --url http://localhost:8000

# Remote Server
python autograph_cli.py api status --url https://api.autograph.example.com

# Mit verschiedenen Ports
python autograph_cli.py api status --url http://localhost:3000
```

**Output:**
```
🔍 Prüfe API-Status: http://localhost:8001
✅ API ist erreichbar
🔗 Entity Linking: 16 Entitäten, 4 Kataloge
🧠 Ontology: 17 Klassen, 16 Relationen
```

### test - API-Funktionen testen

```bash
# Standard-Tests
python autograph_cli.py api test

# Custom URL
python autograph_cli.py api test --url http://localhost:8000

# Remote Server
python autograph_cli.py api test --url https://api.autograph.example.com
```

**Output:**
```
🧪 Teste API-Funktionen: http://localhost:8001
✅ Entity Linking Test: Linked
✅ Text Processing Test: 5 Entitäten, 3 Beziehungen
✅ Ontology Mapping Test: Erfolgreich
```

### docs - API-Dokumentation öffnen

```bash
# Standard-URL
python autograph_cli.py api docs

# Custom URL
python autograph_cli.py api docs --url http://localhost:8000

# Öffnet Browser mit Swagger UI: http://localhost:8001/docs
```

---

## ✅ Validation Tools

### validate - Verschiedene Dateitypen validieren

```bash
# YAML-Validierung
python autograph_cli.py validate --file catalog.yaml --type yaml
python autograph_cli.py validate --file ontology.yaml --type yaml

# Konfigurationsdatei
python autograph_cli.py validate --file autograph-config.yaml --type config

# Entity-Katalog
python autograph_cli.py validate --file medizin_catalog.yaml --type catalog

# Ontologie-Datei
python autograph_cli.py validate --file medizin_ontology.yaml --type ontology

# JSON-Datei
python autograph_cli.py validate --file data.json --type json

# Automatische Typ-Erkennung (ohne --type)
python autograph_cli.py validate --file autograph-config.yaml  # -> config
python autograph_cli.py validate --file entity_catalog.yaml   # -> catalog
python autograph_cli.py validate --file ontology.yaml         # -> ontology
python autograph_cli.py validate --file data.json             # -> json
```

**Output-Beispiele:**

**YAML-Katalog:**
```
🔍 Validiere Datei: medizin_catalog.yaml
Gültig: ✅ Ja
📊 Statistiken:
  total_entities: 15
  entities_with_descriptions: 12
  entities_with_aliases: 15
  unique_entity_types: 4
⚠️  Probleme (1):
  - Entity aspirin_complex hat keinen canonical_name
```

**Konfigurationsdatei:**
```
🔍 Validiere Datei: autograph-config.yaml
✅ YAML-Syntax gültig
✅ Erforderliche Felder vorhanden
✅ Neo4j-Konfiguration vollständig
⚠️  Fehlende empfohlene Felder: llm
```

**JSON-Datei:**
```
🔍 Validiere Datei: results.json
✅ JSON-Syntax gültig
📊 Objekte: 25
📊 Felder: 8
```

---

## 🧠 CLI Framework

### menu - Interaktives Menü

```bash
# Standard-Menü
python autograph_cli.py cli menu

# Mit Konfigurationsdatei
python autograph_cli.py cli menu --config autograph-config.yaml
```

**Menü-Optionen:**
```
🤖 AutoGraph - Knowledge Graph Framework
==================================================
1. 📄 Text verarbeiten (NER + Beziehungen)
2. 🧠 Nur NER (Named Entity Recognition)
3. 🔗 Nur Beziehungsextraktion
4. 📊 Tabelle verarbeiten (CSV/Excel)
5. 🗂️  Datenbank anzeigen
6. 🗑️  Datenbank löschen
7. 🆕 Neue Datenbank erstellen
8. ⚙️  Konfiguration anzeigen
9. 📊 Statistiken anzeigen
0. ❌ Beenden
```

### init - Konfiguration erstellen

```bash
# Interaktive Konfigurationserstellung
python autograph_cli.py cli init
```

**Interaktiver Prozess:**
```
Projektname: MedizinProjekt
Neo4j URI [bolt://localhost:7687]: 
Neo4j Benutzername [neo4j]: 
Neo4j Passwort: ****
Ausgabe-Datei [autograph-config.yaml]: 

✅ Konfiguration erstellt: autograph-config.yaml
```

### serve - API Server starten

```bash
# Standard-Port (8000)
python autograph_cli.py cli serve

# Custom Port
python autograph_cli.py cli serve --port 8001

# Mit Konfiguration
python autograph_cli.py cli serve --config autograph-config.yaml --port 9000
```

**Output:**
```
🚀 Starte AutoGraph REST API Server...
📍 URL: http://127.0.0.1:8000
📚 Dokumentation: http://127.0.0.1:8000/docs
🔄 Auto-Reload: Aktiviert
```

---

## 📋 Alle Kommandos im Überblick

### Entry Points
```bash
python main.py [KOMMANDO] [OPTIONEN]
python autograph_cli.py [MODUL] [KOMMANDO] [OPTIONEN]
```

### Module und Kommandos

| Modul | Kommando | Beschreibung | Beispiel |
|-------|----------|--------------|----------|
| **yaml** | entity-from-text | Entity-Katalog aus Text | `yaml entity-from-text --domain medizin --files *.txt` |
| **yaml** | entity-from-csv | Entity-Katalog aus CSV | `yaml entity-from-csv --csv data.csv --entity-column name` |
| **yaml** | ontology-from-catalogs | Ontologie aus Katalogen | `yaml ontology-from-catalogs --catalogs *.yaml --domain health` |
| **yaml** | wizard | Interaktiver Wizard | `yaml wizard --output ./catalogs/` |
| **yaml** | validate | YAML validieren | `yaml validate --file catalog.yaml` |
| **entity-linking** | status | EL-Status anzeigen | `entity-linking status --mode offline` |
| **entity-linking** | link-entity | Entität verlinken | `entity-linking link-entity "BMW" "ORG" --domain wirtschaft` |
| **entity-linking** | create-catalog | Katalog erstellen | `entity-linking create-catalog "medizin" "./catalog.yaml"` |
| **ontology** | status | Ontologie-Status | `ontology status --mode offline` |
| **ontology** | map-entity | Entity mappen | `ontology map-entity "Aspirin" "DRUG" --domain medizin` |
| **ontology** | map-relation | Relation mappen | `ontology map-relation "behandelt" --domain medizin` |
| **ontology** | create-example | Beispiel-Ontologie | `ontology create-example "wirtschaft" "./ont.yaml"` |
| **process** | - | Text verarbeiten | `process --input text.txt --domain medizin --output result.json` |
| **api** | status | API-Status prüfen | `api status --url http://localhost:8001` |
| **api** | test | API testen | `api test --url http://localhost:8001` |
| **api** | docs | API-Docs öffnen | `api docs --url http://localhost:8001` |
| **validate** | - | Dateien validieren | `validate --file config.yaml --type config` |
| **cli** | menu | Interaktives Menü | `cli menu --config config.yaml` |
| **cli** | init | Konfiguration erstellen | `cli init` |
| **cli** | serve | Server starten | `cli serve --port 8000` |

### Häufig verwendete Parameter

| Parameter | Beschreibung | Beispielwerte |
|-----------|--------------|---------------|
| `--domain` | Domain/Bereich | `medizin`, `wirtschaft`, `wissenschaft`, `recht` |
| `--mode` | Verarbeitungsmodus | `offline`, `hybrid`, `online` |
| `--format` | Output-Format | `json`, `yaml`, `csv` |
| `--type` | Validierungstyp | `yaml`, `config`, `catalog`, `ontology`, `json` |
| `--url` | API-URL | `http://localhost:8001`, `https://api.example.com` |
| `--config` | Konfigurationsdatei | `autograph-config.yaml` |
| `--output` | Output-Verzeichnis | `./results/`, `./catalogs/` |

### Workflow-Beispiele

**1. Vollständige medizinische Wissensbasis:**
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

**2. Enterprise Knowledge Graph:**
```bash
# 1. Multiple Kataloge
python autograph_cli.py yaml entity-from-csv --csv companies.csv --entity-column name --domain wirtschaft
python autograph_cli.py yaml entity-from-csv --csv products.csv --entity-column product --domain produkte

# 2. Ontologie erstellen
python autograph_cli.py yaml ontology-from-catalogs --catalogs "./catalogs/*.yaml" --domain enterprise

# 3. Server starten
python autograph_cli.py cli serve --port 8000

# 4. API testen
python autograph_cli.py api test --url http://localhost:8000
```

**Alle Kommandos sind vollständig implementiert und production-ready! 🚀**

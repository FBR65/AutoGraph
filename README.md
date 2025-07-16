# AutoGraph - Automated Knowledge Graph Generation

**KI-gestütztes Framework zur automatischen Erstellung von Knowledge Graphs aus unstrukturierten Texten**

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Neo4j Compatible](https://img.shields.io/badge/Neo4j-Compatible-green.svg)](https://neo4j.com/)

AutoGraph ist ein produktionsreifes Framework zur automatisierten Knowledge Graph-Generierung aus deutschen und englischen Texten. Es kombiniert modernste NLP-Techniken mit robusten Graph-Algorithmen für präzise Entitäts-Extraktion und Beziehungsanalyse.

## 🎯 Kernfunktionen

**🔍 Entity Recognition & Linking**

- Multilinguale Named Entity Recognition (spaCy + BERT)
- Offline-First Entity Linking mit Custom YAML-Katalogen
- Automatische Entitäts-Disambiguierung und -Normalisierung
- Multi-Domain Support (Medizin, Wirtschaft, Wissenschaft)

**🕸️ Relation Extraction**

- Hybrid-Ansatz: Rule-based + ML-Modelle (BERT/RoBERTa)
- Ensemble-Methoden mit konfigurierbarer Gewichtung
- Domain-spezifische Beziehungsextraktion
- Confidence-basierte Qualitätssicherung

**🧠 Ontologie-Integration**

- Custom YAML-Ontologien für Fachdomänen
- Schema.org-kompatible Datenmodellierung
- Automatisches Entity-zu-Ontologie-Mapping
- Flexible Namespace-Verwaltung

**🚀 Enterprise-Ready**

- Vollständige REST API (FastAPI)
- Neo4j Graph Database Integration
- CLI-Tools für Batch-Verarbeitung
- Air-Gapped System Support

## 📦 Installation

```bash
# Repository klonen
git clone https://github.com/FBR65/AutoGraph.git
cd AutoGraph

# Virtual Environment erstellen
python -m venv autograph_env
source autograph_env/bin/activate  # Linux/macOS
# oder: autograph_env\Scripts\activate  # Windows

# Dependencies installieren
pip install -r requirements.txt

# spaCy Modelle herunterladen
python -m spacy download de_core_news_lg
python -m spacy download en_core_web_sm
```

## 🚀 Schnellstart

### 1. Neo4j Setup

```bash
# Mit Docker (empfohlen)
docker run -d \
  --name neo4j-autograph \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/autograph123 \
  neo4j:latest
```

### 2. Konfiguration

```bash
# Basis-Konfiguration erstellen
python main.py init

# Oder interaktives CLI-Menü verwenden
python -m autograph.cli menu
```

### 3. Text verarbeiten

```bash
# Einzelne Datei
python main.py run document.txt --domain medizin

# Mit CLI Framework
python -m autograph.cli run document.txt --processor both
```

### 4. REST API verwenden

```bash
# Server starten
python -m uvicorn src.autograph.api.server:app --reload --port 8001

# Text verarbeiten via API
curl -X POST "http://localhost:8001/process/text" \
  -H "Content-Type: application/json" \
  -d '{"text": "Aspirin hilft gegen Kopfschmerzen", "domain": "medizin"}'
```

## 🔧 CLI-Tools

AutoGraph bietet umfassende CLI-Tools für alle Funktionen:

### YAML-Generator

```bash
# Entity-Katalog aus Textdateien erstellen
python autograph_cli.py yaml entity-from-text --domain medizin --files *.txt

# Entity-Katalog aus CSV-Daten
python autograph_cli.py yaml entity-from-csv --csv companies.csv --domain wirtschaft

# Interaktiver Wizard
python autograph_cli.py yaml wizard
```

### Entity Linking

```bash
# Status aller Modi prüfen
python autograph_cli.py entity-linking status --mode offline

# Einzelne Entität verlinken
python autograph_cli.py entity-linking link-entity "BMW" "ORG" --domain wirtschaft
```

### Text-Verarbeitung

```bash
# Pipeline mit Output
python autograph_cli.py process --input text.txt --domain medizin --output result.json

# API-Integration
python autograph_cli.py api status --url http://localhost:8001
```

## 🎯 Domänen-System

AutoGraph unterstützt domain-spezifische Verarbeitung:

### Verfügbare Domänen

#### Medizin (`medizin`)

Spezialisierte Erkennung medizinischer Beziehungen:

- **Diagnosen**: "Patient hat Diabetes" → `hat_Diagnose`
- **Behandlungen**: "Arzt behandelt mit Medikament" → `behandelt_mit`
- **Symptome**: "Patient zeigt Symptome" → `zeigt_Symptom`

#### Wirtschaft (`wirtschaft`)

Fokus auf Unternehmensbeziehungen:

- **Übernahmen**: "Microsoft übernimmt LinkedIn" → `übernimmt`
- **Investitionen**: "Google investiert in KI" → `investiert_in`
- **Marktdominanz**: "Amazon dominiert Cloud-Markt" → `dominiert_Markt`

#### Technologie (`technologie`)

Tech-spezifische Beziehungen:

- **Entwicklung**: "Apple entwickelt iOS" → `entwickelt`
- **Technologie-Nutzung**: "App nutzt KI" → `nutzt_Technologie`
- **Kompatibilität**: "System ist kompatibel mit..." → `ist_kompatibel_mit`

### Beispiel-Verwendung

```bash
# CLI mit Domain-Kontext
python main.py run firma.txt --domain wirtschaft
python main.py run patient.txt --domain medizin

# Verschiedene Processor-Modi
python main.py run text.txt --processor both      # NER + Beziehungen
python main.py run text.txt --processor ner       # Nur NER
python main.py run text.txt --processor relation  # Nur Beziehungen
```

## 🏗️ Architektur

```text
AutoGraph/
├── main.py                    # Haupt Entry Point
├── autograph_cli.py           # Unified CLI Interface
├── src/autograph/
│   ├── api/                   # REST API (FastAPI)
│   ├── cli/                   # CLI Framework & Tools
│   ├── cli.py                 # Interaktives CLI-System
│   ├── core/                  # Pipeline-Logik
│   ├── extractors/            # Text/Tabellen-Extraktion
│   ├── processors/            # NER, Relation Extraction, Entity Linking
│   ├── ontology/              # Ontologie-Management
│   ├── storage/               # Neo4j Integration
│   └── config.py              # Konfiguration
├── entity_catalogs/           # Custom Entity-Kataloge
├── custom_ontologies/         # Domain-spezifische Ontologien
└── Documentation/             # Vollständige Dokumentation
```

## ⚙️ Konfiguration

AutoGraph verwendet YAML-Konfigurationsdateien:

```yaml
project_name: "autograph-projekt"

neo4j:
  uri: "bolt://localhost:7687"
  username: "neo4j"
  password: "autograph123"
  database: "neo4j"

llm:
  base_url: "http://localhost:11434/v1"  # Ollama
  api_key: "not-needed"
  model: "qwen2.5:latest"

processor:
  ner_model: "de_core_news_lg"
  ner_confidence_threshold: 0.8
  relation_confidence_threshold: 0.6

ontology:
  mode: "offline"  # offline, hybrid, online
  custom_ontologies_dir: "./custom_ontologies/"

entity_linking:
  mode: "offline"  # offline, hybrid, online
  confidence_threshold: 0.5
  catalogs_dir: "./entity_catalogs/"
```

## 🧠 Ontologie-System

AutoGraph implementiert ein flexibles Ontologie-System:

### Modi

- **Offline**: Nur lokale/custom Ontologien (Air-Gapped Systems)
- **Hybrid**: Lokale Priorität + Online-Fallback mit Caching
- **Online**: Vollständige Online-Integration mit externen Quellen

### Custom YAML-Ontologien

```yaml
# Beispiel: custom_ontologies/medizin.yaml
namespace: medical
namespace_uri: "http://autograph.medical/"
description: "Medical domain ontology"

classes:
  Drug:
    uri: "http://autograph.medical/Drug"
    description: "Pharmaceutical substance"
    properties: ["name", "dosage", "indication"]

  Disease:
    uri: "http://autograph.medical/Disease"
    description: "Medical condition"
    properties: ["name", "symptoms", "treatment"]

relations:
  treats:
    uri: "http://autograph.medical/treats"
    domain: "Drug"
    range: "Disease"
    description: "Drug treats disease"
```

## 📊 Entity Linking

Offline-First Entity Linking mit Custom-Katalogen:

### Katalog-Struktur

```yaml
# Beispiel: entity_catalogs/medizin.yaml
catalog_info:
  domain: medizin
  version: "1.0"
  description: "Medical entities catalog"

entities:
  aspirin:
    canonical_name: "Aspirin"
    entity_type: "DRUG"
    aliases: ["ASS", "Acetylsalicylsäure"]
    properties:
      dosage: "500mg"
      indication: "Schmerzmittel"

  diabetes:
    canonical_name: "Diabetes mellitus"
    entity_type: "DISEASE" 
    aliases: ["Diabetes", "Zuckerkrankheit"]
```

### CLI-Integration

```bash
# Status aller Entity Linking Modi
python autograph_cli.py entity-linking status --mode offline

# Einzelne Entität testen
python autograph_cli.py entity-linking link-entity "Aspirin" "DRUG" --domain medizin

# Custom Katalog erstellen
python autograph_cli.py entity-linking create-catalog "neue_domain" "./katalog.yaml"
```

## 🚀 REST API

AutoGraph bietet eine vollständige FastAPI-basierte REST API:

### API-Endpunkte

```bash
# Server starten
python -m uvicorn src.autograph.api.server:app --reload --port 8001

# API-Dokumentation: http://localhost:8001/docs
```

#### Text-Verarbeitung

```bash
# Basis-Textverarbeitung
curl -X POST "http://localhost:8001/process/text" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Aspirin hilft gegen Kopfschmerzen. Dr. Schmidt behandelt Patienten.",
    "domain": "medizin"
  }'

# Batch-Verarbeitung
curl -X POST "http://localhost:8001/process/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["Text 1", "Text 2"],
    "domain": "wirtschaft"
  }'
```

#### Entity Linking

```bash
# Entity Linking Status
curl "http://localhost:8001/entity-linking/status"

# Entität verlinken
curl -X POST "http://localhost:8001/entity-linking/link-entity" \
  -H "Content-Type: application/json" \
  -d '{
    "entity": "BMW",
    "entity_type": "ORG",
    "domain": "wirtschaft"
  }'
```

#### Ontologie-Management

```bash
# Ontologie-Status
curl "http://localhost:8001/ontology/status"

# Entity-Mapping
curl -X POST "http://localhost:8001/ontology/map-entity" \
  -H "Content-Type: application/json" \
  -d '{
    "entity": "Aspirin",
    "entity_type": "DRUG",
    "domain": "medizin"
  }'
```

## 🔧 Entwicklung

### Setup

```bash
# Entwicklungsumgebung
pip install -r requirements-dev.txt

# Pre-commit hooks (falls vorhanden)
pre-commit install

# Tests ausführen
python -m pytest tests/ -v

# Code-Qualität
black src/
isort src/
flake8 src/
```

### Architektur-Prinzipien

- **Modular**: Austauschbare Komponenten
- **Konfigurierbar**: YAML-basierte Konfiguration
- **Erweiterbar**: Plugin-System für Processor
- **Robust**: Umfassende Fehlerbehandlung
- **Performant**: Batch-Processing und Caching

## 📚 Dokumentation

Vollständige Dokumentation im `Documentation/` Verzeichnis:

- **[CLI-Kommando-Referenz](Documentation/CLI-Kommando-Referenz.md)** - Alle CLI-Befehle
- **[API-Dokumentation](Documentation/API-Documentation.md)** - REST API Referenz  
- **[Graph-Dokumentation](Documentation/Graph-Documentation.md)** - Knowledge Graph Architektur
- **[Setup-Guide](Documentation/Setup-Guide.md)** - Installation und Konfiguration
- **[Tutorials](Documentation/Tutorials.md)** - Schritt-für-Schritt Anleitungen

## 🎯 Use Cases

### Medizinische Textanalyse

```bash
# Patientenberichte verarbeiten
python main.py run patient_reports/ --domain medizin

# Medizinische Entity-Kataloge erstellen
python autograph_cli.py yaml entity-from-text --domain medizin --files *.txt
```

### Unternehmensanalyse

```bash
# Wirtschaftstexte analysieren
python main.py run company_reports/ --domain wirtschaft

# CSV-Daten zu Knowledge Graph
python autograph_cli.py yaml entity-from-csv --csv companies.csv --domain wirtschaft
```

### Wissenschaftliche Publikationen

```bash
# Forschungspapers verarbeiten
python main.py run papers/ --domain wissenschaft
```

## 📋 Systemanforderungen

- **Python**: 3.8+ (empfohlen: 3.9)
- **Neo4j**: 4.4+ (empfohlen: 5.x)
- **RAM**: Mindestens 4GB (empfohlen: 8GB+)
- **Storage**: 5GB+ für Modelle und Daten

## 📄 Lizenz

Dieses Projekt steht unter der **GNU Affero General Public License v3.0 (AGPLv3)**.

Die AGPLv3 gewährleistet, dass:
- Der Quellcode frei verfügbar bleibt
- Abgeleitete Werke ebenfalls unter AGPLv3 stehen
- Auch bei Netzwerk-Services der Quellcode verfügbar gemacht werden muss

Siehe [LICENSE](LICENSE) für Details.

## 🤝 Beitragen

Beiträge sind willkommen! Bitte:

1. Fork des Repositories erstellen
2. Feature-Branch erstellen (`git checkout -b feature/AmazingFeature`)
3. Änderungen committen (`git commit -m 'Add AmazingFeature'`)
4. Branch pushen (`git push origin feature/AmazingFeature`)
5. Pull Request erstellen

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/FBR65/AutoGraph/issues)
- **Dokumentation**: `Documentation/` Verzeichnis
- **API-Referenz**: `http://localhost:8001/docs` (nach Server-Start)

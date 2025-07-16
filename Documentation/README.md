# AutoGraph - Vollständige Dokumentation

**Automatische Knowledge Graph Generierung mit KI-gestützter Entity-Extraktion und Relation-Mining**

---

## 📚 Dokumentations-Übersicht

Diese Dokumentation erklärt alle Aspekte von AutoGraph - ein produktionsreifes Framework zur automatisierten Knowledge Graph-Generierung aus deutschen und englischen Texten.

### 🎯 Schnellzugriff

| Bereich | Beschreibung | Dokument |
|---------|--------------|----------|
| **🚀 API-Referenz** | REST API Endpunkte, Request/Response Beispiele | [API-Dokumentation](./API-Documentation.md) |
| **⚡ CLI-Tools** | Kommandozeilen-Tools für YAML-Generierung und Verarbeitung | [CLI-Kommando-Referenz](./CLI-Kommando-Referenz.md) |
| **🧠 Graph-Funktionalität** | Knowledge Graph Architektur und Algorithmen | [Graph-Dokumentation](./Graph-Documentation.md) |
| **🔧 Setup & Installation** | Installation, Konfiguration und Deployment | [Setup-Guide](./Setup-Guide.md) |
| **📖 Tutorials** | Schritt-für-Schritt Anleitungen und Beispiele | [Tutorials](./Tutorials.md) |

---

## 🎯 Was ist AutoGraph?

AutoGraph ist ein **KI-gestütztes System zur automatischen Knowledge Graph-Generierung** aus unstrukturierten Textdaten. Es kombiniert modernste NLP-Techniken mit robusten Graph-Algorithmen für präzise Entitäts-Extraktion und Beziehungsanalyse.

### 🌟 Hauptfunktionen

**🔍 Entity Recognition & Linking**

- BERT-basierte Named Entity Recognition (NER)
- Offline-First Entity Linking mit Custom YAML-Katalogen
- Automatische Entitäts-Disambiguierung
- Multi-Domain Support (Medizin, Wirtschaft, etc.)

**🕸️ Relation Extraction**

- Hybrid-Ansatz: ML + Regelbasierte Systeme
- BERT-basierte Relation Classification
- Ensemble-Methoden für höhere Präzision
- Confidence-basierte Filterung

**🧠 Ontologie-Integration**

- Custom YAML-Ontologien
- Automatisches Entity-zu-Ontologie-Mapping
- Schema.org Kompatibilität
- Namespace-Management

**🚀 Enterprise-Ready**

- REST API mit FastAPI
- Neo4j Graph Database Integration
- Air-Gapped System Support
- Batch-Processing Capabilities

---

## 🏗️ Architektur-Überblick

```text
AutoGraph/
├── main.py                    # Haupt Entry Point (70 Zeilen)
├── autograph_cli.py           # Unified CLI Interface (450+ Zeilen)
├── src/autograph/
│   ├── api/server.py          # FastAPI REST API
│   ├── cli.py                 # CLI Framework (850+ Zeilen)
│   ├── cli/yaml_generator.py  # YAML-Generator (800+ Zeilen)
│   ├── processors/
│   │   └── entity_linker.py   # Entity Linking (557 Zeilen)
│   ├── ontology/              # Ontologie-System (4 Module)
│   │   ├── ontology_manager.py
│   │   ├── ontology_loader.py
│   │   ├── ontology_graph.py
│   │   └── custom_ontology_parser.py
│   ├── core/                  # Pipeline-Logik
│   ├── extractors/            # Text/Tabellen-Extraktion
│   ├── storage/               # Neo4j Integration
│   └── config.py              # Konfiguration
├── entity_catalogs/           # Custom Entity-Kataloge
├── custom_ontologies/         # Domain-spezifische Ontologien
└── Documentation/             # Diese Dokumentation
```

### 🔧 Technologie-Stack

| Komponente | Technologie | Zweck |
|------------|-------------|-------|
| **NLP Framework** | spaCy, Transformers (BERT) | Entity Recognition, Relation Extraction |
| **Web Framework** | FastAPI | REST API Server |
| **Database** | Neo4j | Graph Storage |
| **Configuration** | YAML | Entity Catalogs, Ontologien |
| **CLI Tools** | argparse, Click | Command Line Interface |
| **Data Processing** | pandas, numpy | Tabellen-Verarbeitung |

---

## 🚀 Schnellstart

### 1. Installation

```bash
# Repository klonen
git clone https://github.com/FBR65/AutoGraph.git
cd AutoGraph

# Virtual Environment
python -m venv autograph_env
source autograph_env/bin/activate  # Linux/macOS
# oder: autograph_env\Scripts\activate  # Windows

# Dependencies installieren
pip install -r requirements.txt

# spaCy Modelle
python -m spacy download de_core_news_lg
python -m spacy download en_core_web_sm
```

### 2. Neo4j Setup

```bash
# Mit Docker (empfohlen)
docker run -d \
  --name neo4j-autograph \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/autograph123 \
  neo4j:latest
```

### 3. Verwendung

```bash
# API Server starten
python -m uvicorn src.autograph.api.server:app --reload --port 8001

# Text verarbeiten
curl -X POST "http://localhost:8001/process/text" \
  -H "Content-Type: application/json" \
  -d '{"text": "Aspirin hilft gegen Kopfschmerzen", "domain": "medizin"}'

# CLI verwenden
python autograph_cli.py yaml entity-from-text --domain medizin --files *.txt

# Interaktives Menü
python -m autograph.cli menu
```

---

## 📋 Implementierungsstand

**✅ Vollständig implementiert und produktionsbereit:**

### Core-System

- **main.py**: Echter Entry Point (70 Zeilen)
- **autograph_cli.py**: Vollständiger Unified CLI (450+ Zeilen)
- **CLI Framework**: Interaktives Menü & Kommandos (850+ Zeilen)

### YAML-Generierung

- **Entity-Kataloge aus Textdateien**: `entity-from-text`
- **Entity-Kataloge aus CSV**: `entity-from-csv`
- **Interaktiver Wizard**: `wizard`
- **Ontologie-Generierung**: `ontology-from-catalogs`
- **Validierung**: `validate`

### Entity Linking

- **Offline-Modus**: Nur lokale Kataloge (Air-Gapped)
- **Hybrid-Modus**: Lokale + Online mit Caching
- **Online-Modus**: Vollständige Online-Integration
- **Custom Kataloge**: YAML-basierte Entity-Datenbanken
- **Fuzzy Matching**: Robuste String-Ähnlichkeit

### Ontologie-Management

- **4-Module System**: Vollständige Ontologie-Verwaltung
- **Custom YAML-Ontologien**: Domain-spezifische Ontologien
- **Entity-Mapping**: Automatisches Mapping auf Ontologie-Konzepte
- **Relation-Mapping**: Beziehungen zu Ontologie-Properties
- **Schema.org Integration**: Standard-Kompatibilität

### Text-Verarbeitung

- **Pipeline-Integration**: Vollständige NLP-Pipeline
- **Domain-Support**: Medizin, Wirtschaft, Technologie
- **Processor-Modi**: NER-only, Relation-only, beide
- **Output-Formate**: JSON, YAML, CSV

### API Integration

- **FastAPI Server**: Vollständige REST API
- **Health Checks**: System-Status Monitoring
- **Client Tools**: API-Integration und Tests
- **Batch Processing**: Massenverarbeitung

### Validation Tools

- **Dateityp-Erkennung**: Automatische Typ-Bestimmung
- **YAML-Validierung**: Struktur und Schema-Prüfung
- **Config-Validierung**: Konfigurationsdateien
- **JSON-Validierung**: API-Responses

---

## 🎯 Anwendungsfälle

### Medizinische Textanalyse

```bash
# Entity-Katalog aus medizinischen Texten
python autograph_cli.py yaml entity-from-text --domain medizin --files patient_reports/*.txt

# Status prüfen
python autograph_cli.py entity-linking status --mode offline

# Text verarbeiten
python autograph_cli.py process --input patient.txt --domain medizin --output analysis.json
```

**Erkannte Entitäten**: Medikamente, Diagnosen, Symptome, Ärzte  
**Beziehungen**: behandelt_mit, hat_Diagnose, zeigt_Symptom

### Unternehmensanalyse

```bash
# CSV-Daten zu Entity-Katalog
python autograph_cli.py yaml entity-from-csv --csv companies.csv --domain wirtschaft

# Wirtschaftstexte analysieren
python autograph_cli.py process --input market_analysis.txt --domain wirtschaft --output companies.json
```

**Erkannte Entitäten**: Unternehmen, CEOs, Standorte, Produkte  
**Beziehungen**: übernimmt, investiert_in, konkurriert_mit

### Wissenschaftliche Publikationen

```bash
# Forschungspapers verarbeiten
python autograph_cli.py process --input research_papers/ --domain wissenschaft --output knowledge_graph.json
```

**Erkannte Entitäten**: Autoren, Institutionen, Methoden, Begriffe  
**Beziehungen**: forscht_an, entwickelt, zitiert

---

## 📚 Detaillierte Dokumentation

### **Entwickler-Dokumentation**

#### 🚀 [API-Dokumentation](./API-Documentation.md)

Komplette REST API Referenz mit allen Endpunkten:

- **Text Processing** - `/process/text`, `/process/table`, `/process/batch`
- **Entity Linking** - `/entity-linking/status`, `/entity-linking/link-entity`
- **Ontology Management** - `/ontology/status`, `/ontology/map-entity`
- **System APIs** - `/health`, `/cache/stats`, `/pipeline/status`

#### ⚡ [CLI-Kommando-Referenz](./CLI-Kommando-Referenz.md)

Vollständige Command Line Interface Referenz:

- **YAML Generator** - Automatische Katalog-Erstellung
- **Entity Linking** - Offline/Hybrid/Online Modi
- **Ontology Management** - Custom Ontologie-Verwaltung
- **Text Processor** - Pipeline-Integration
- **API Client** - REST API Interaction
- **Validation Tools** - Qualitätsprüfung

#### 🧠 [Graph-Dokumentation](./Graph-Documentation.md)

Knowledge Graph Architektur und Algorithmen:

- **Graph Schema** - Neo4j Datenmodell
- **Entity Types** - Entitäts-Kategorisierung
- **Relation Types** - Beziehungs-Taxonomie
- **Query Patterns** - Cypher Query Beispiele

### **Setup & Administration**

#### 🔧 [Setup-Guide](./Setup-Guide.md)

Installation und Konfiguration:

- **System Requirements** - Abhängigkeiten und Voraussetzungen
- **Installation Steps** - Schritt-für-Schritt Setup
- **Configuration** - Konfiguration von Neo4j, YAML-Katalogen
- **Deployment** - Produktions-Deployment

### **Benutzer-Dokumentation**

#### 📖 [Tutorials](./Tutorials.md)

Praktische Anleitungen und Beispiele:

- **Medizinische Textanalyse** - Schritt-für-Schritt
- **Wirtschaftsdaten-Processing** - CSV zu Knowledge Graph
- **Custom Entity Catalogs** - Eigene Kataloge erstellen
- **Ontologie-Entwicklung** - YAML-Ontologien designen

---

## 🎯 Enterprise-Features

### Sicherheit & Compliance

- **Air-Gapped Support**: Vollständige Offline-Funktionalität
- **Custom Entity-Kataloge**: Firmen-spezifische Entitäten
- **DSGVO-konform**: Keine ungewollten Online-Verbindungen
- **Audit-Logs**: Nachverfolgbare Verarbeitungsschritte

### Performance & Skalierung

- **Batch-Processing**: Effiziente Massenverarbeitung
- **Caching-System**: Wiederverwendung von Berechnungen
- **Lokale Geschwindigkeit**: Keine API-Latenz bei Offline-Modus
- **Memory-Optimierung**: Effiziente Speichernutzung

### Integration & Interoperabilität

- **REST API**: Standard HTTP-Schnittstellen
- **Neo4j Integration**: Graph Database Support
- **YAML-Standards**: Menschenlesbare Konfiguration
- **Multi-Format Output**: JSON, YAML, CSV Export

---

## 📄 Lizenz

AutoGraph steht unter der **GNU Affero General Public License v3.0 (AGPLv3)**.

**Kernpunkte der AGPLv3:**

- Quellcode bleibt frei verfügbar
- Abgeleitete Werke müssen ebenfalls unter AGPLv3 stehen
- Auch bei Netzwerk-Services muss der Quellcode verfügbar gemacht werden
- Copyleft-Schutz für Cloud/SaaS-Deployments

---

## 🤝 Community & Support

### Beitragen

1. **Issues**: [GitHub Issues](https://github.com/FBR65/AutoGraph/issues)
2. **Pull Requests**: Feature-Entwicklung und Bug-Fixes
3. **Dokumentation**: Verbesserungen und Ergänzungen
4. **Testing**: Qualitätssicherung und Validierung

### Support-Kanäle

- **Dokumentation**: Diese umfassende Dokumentation
- **API-Referenz**: `http://localhost:8001/docs` (nach Server-Start)
- **Code-Beispiele**: Tutorials und Anwendungsfälle
- **Community**: GitHub Discussions und Issues

---

## 🔄 Kontinuierliche Verbesserung

AutoGraph wird kontinuierlich weiterentwickelt basierend auf:

- **Benutzer-Feedback**: Issues und Feature-Requests
- **Performance-Monitoring**: Optimierung der Algorithmen
- **Standard-Evolution**: Integration neuer NLP-Techniken
- **Enterprise-Anforderungen**: Skalierung und Sicherheit

Die Dokumentation wird entsprechend aktualisiert um alle Funktionen akkurat zu reflektieren.

---

**AutoGraph - Ihr Partner für automatisierte Knowledge Graph-Generierung** 🚀

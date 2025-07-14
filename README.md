# AutoGraph - Automated Knowledge Graph Generation

AutoGraph ist ein modulares Framework zur automatisierten Erstellung von Knowledge Graphs aus verschiedenen Datenquellen mit LLM-unterstützter Pipeline-Optimierung.

## Features

🚀 **Modulare Pipeline-Architektur**
- Austauschbare Extraktoren für verschiedene Datenquellen
- Konfigurierbare Verarbeitungsmodule (NER, Relation Extraction, Entity Linking)
- Flexible Storage-Backends (Neo4j)

🤖 **LLM-unterstützte Optimierung**
- Automatische Pipeline-Konfiguration basierend auf Datendomäne
- Qualitätsbewertung durch Large Language Models
- Iterative Verbesserung der Extraktionsqualität

🔗 **Knowledge Graph Integration**
- Native Neo4j-Unterstützung
- Cypher-Abfragen für Graph-Exploration
- Strukturierte Datenextraktion und -speicherung

## Installation

```bash
# Repository klonen
git clone <repository-url>
cd AutoGraph

# Dependencies installieren mit uv
uv sync

# Optional: Entwicklungstools installieren
uv sync --group dev
```

## Schnellstart

### 1. Konfiguration erstellen

```bash
# Interaktive Konfiguration
uv run autograph init

# Oder manuell eine autograph-config.yaml erstellen
```

### 2. Pipeline ausführen

```bash
# Text-Dateien verarbeiten
uv run autograph run ./data/documents/ --domain medizin

# Einzelne Datei verarbeiten
uv run autograph run ./data/sample.txt
```

### 3. Programmatische Nutzung

```python
from autograph import AutoGraphPipeline
from autograph.config import AutoGraphConfig
from autograph.extractors import TextExtractor
from autograph.processors import NERProcessor
from autograph.storage import Neo4jStorage

# Konfiguration laden
config = AutoGraphConfig.from_file("autograph-config.yaml")

# Pipeline-Komponenten
extractor = TextExtractor(config.extractor.model_dump())
processors = [NERProcessor(config.processor.model_dump())]
storage = Neo4jStorage(config.neo4j.model_dump())

# Pipeline erstellen und ausführen
pipeline = AutoGraphPipeline(
    config=config,
    extractor=extractor,
    processors=processors,
    storage=storage
)

result = pipeline.run("./data/sample.txt")
print(f"Extrahiert: {len(result.entities)} Entitäten")
```

### 4. Interaktives Menü

```bash
# Starte das interaktive Menü
uv run autograph menu
```

Das Menü bietet:
- 📄 Text verarbeiten (NER + Beziehungen)
- 🧠 Nur NER (Named Entity Recognition)
- 🔗 Nur Beziehungsextraktion
- 🗂️ Datenbank anzeigen/verwalten
- 📊 Detaillierte Statistiken

## 🎯 Domänen-System

AutoGraph unterstützt **domänen-spezifische Beziehungsextraktion** für verschiedene Fachbereiche:

### 📋 Verfügbare Domänen

#### 💼 **Wirtschaft** (`wirtschaft`)
Spezialisiert auf Unternehmensbeziehungen:
- **Übernahmen**: "Microsoft übernimmt LinkedIn" → `übernimmt`
- **Investitionen**: "Google investiert in KI" → `investiert_in`  
- **Marktdominanz**: "Amazon dominiert Cloud-Markt" → `dominiert_Markt`

#### 🏥 **Medizin** (`medizin`)
Fokus auf medizinische Beziehungen:
- **Diagnosen**: "Patient hat Diabetes" → `hat_Diagnose`
- **Behandlungen**: "Arzt behandelt mit Medikament" → `behandelt_mit`
- **Symptome**: "Patient zeigt Symptome" → `zeigt_Symptom`

#### 💻 **Technologie** (`technologie`)
Tech-spezifische Beziehungen:
- **Entwicklung**: "Apple entwickelt iOS" → `entwickelt`
- **Technologie-Nutzung**: "App nutzt KI" → `nutzt_Technologie`
- **Kompatibilität**: "System ist kompatibel mit..." → `ist_kompatibel_mit`

### 🚀 Domänen-Verwendung

```bash
# CLI mit Domäne
uv run autograph run firma.txt --domain wirtschaft
uv run autograph run patient.txt --domain medizin

# Processor-Auswahl
uv run autograph run text.txt --processor both    # NER + Beziehungen (Standard)
uv run autograph run text.txt --processor ner     # Nur NER
uv run autograph run text.txt --processor relation # Nur Beziehungen
```

### 📊 Domänen-Vorteile

**Ohne Domäne:**
```
"Microsoft übernimmt LinkedIn" → arbeitet_mit (0.5 Konfidenz)
```

**Mit Domäne "wirtschaft":**
```
"Microsoft übernimmt LinkedIn" → übernimmt (0.9 Konfidenz)
```

**Vorteile:**
- ✅ **Höhere Genauigkeit** für Fachbegriffe
- ✅ **Spezifischere Beziehungstypen** 
- ✅ **Bessere Konfidenzwerte**
- ✅ **Kontextuelle Relevanz**

## Projektstruktur

```
AutoGraph/
├── src/autograph/
│   ├── core/              # Kern-Pipeline-Logik
│   ├── extractors/        # Datenextraktoren
│   ├── processors/        # Verarbeitungsmodule
│   ├── storage/           # Storage-Backends
│   ├── evaluation/        # LLM-Bewertung
│   ├── config.py          # Konfiguration
│   └── cli.py            # Command-Line Interface
├── tests/                 # Tests
├── docs/                  # Dokumentation
└── examples/             # Beispiele
```

## Konfiguration

AutoGraph nutzt YAML-Konfigurationsdateien:

```yaml
project_name: "mein-knowledge-graph"

neo4j:
  uri: "bolt://localhost:7687"
  username: "neo4j"
  password: "your-password"

llm:
  base_url: "http://localhost:11434/v1"  # Ollama
  api_key: "not-needed"                  # Für lokale APIs oft nicht nötig
  model: "qwen2.5:latest"                # Ihr bevorzugtes Modell

extractor:
  text_chunking: true
  chunk_size: 1000

processor:
  ner_model: "de_core_news_lg"
  ner_confidence_threshold: 0.8
  relation_confidence_threshold: 0.6
```

### LLM-Provider Konfiguration

AutoGraph unterstützt jeden OpenAI-kompatiblen Endpunkt. Hier sind Beispiele für verschiedene Provider:

**Ollama (lokal):**
```yaml
llm:
  base_url: "http://localhost:11434/v1"
  api_key: "not-needed"
  model: "qwen2.5:latest"
```

**OpenAI:**
```yaml
llm:
  base_url: "https://api.openai.com/v1"
  api_key: "your-openai-api-key"
  model: "gpt-3.5-turbo"
```

**LocalAI:**
```yaml
llm:
  base_url: "http://localhost:8080/v1"
  api_key: "not-needed"
  model: "your-local-model"
```

**LM Studio:**
```yaml
llm:
  base_url: "http://localhost:1234/v1"
  api_key: "not-needed"
  model: "your-model"
```

## Komponenten

### Extraktoren
- **TextExtractor**: Verarbeitet TXT, MD, RST Dateien
- **TableExtractor**: (geplant) CSV, Excel Dateien
- **WebExtractor**: (geplant) Web Scraping

### Prozessoren
- **NERProcessor**: Named Entity Recognition mit SpaCy
- **RelationExtractor**: ✅ **Erweiterte Beziehungsextraktion** mit syntaktischen Mustern
- **EntityLinker**: (geplant) Entity Linking

## Erweiterte Beziehungsextraktion

AutoGraph nutzt einen **mehrstufigen Ansatz** für automatisierte Beziehungserkennung:

### 🔍 **Erkennungsmethoden**

1. **Dependency-basierte Extraktion**
   - Nutzt syntaktische Abhängigkeiten von SpaCy
   - Erkennt Subjekt-Verb-Objekt Strukturen automatisch

2. **Pattern-basierte Extraktion**  
   - 8+ vordefinierte Beziehungsmuster
   - Domänen-spezifische Erweiterungen
   - Keyword-basierte Triggererkennung

3. **Satzstruktur-basierte Extraktion**
   - Ko-Referenz durch Entitätennähe
   - Kontextuelle Verbindungen

### 📊 **Erkennungsleistung**

**Beispiel-Ergebnis** (Apple/Microsoft Text):
- **59 Entitäten** (Personen, Organisationen, Orte)
- **43 Beziehungen** automatisch erkannt
- **Verschiedene Konfidenzlevel** (0.3-0.9)

**Erkannte Beziehungstypen:**
- `ist_CEO_von`, `gründete`, `befindet_sich_in`
- `konkurriert_mit`, `übernimmt`, `investiert_in`
- `entwickelt`, `nutzt_Technologie`, `ist_kompatibel_mit`

### Storage
- **Neo4jStorage**: Neo4j Graph Database
- Weitere Backends geplant (ArangoDB, RDF Stores)

## LLM-Integration

AutoGraph nutzt LLMs für:
- **Pipeline-Optimierung**: Automatische Konfiguration basierend auf Datendomäne
- **Qualitätsbewertung**: Bewertung der Extraktionsqualität
- **Iterative Verbesserung**: Vorschläge zur Pipeline-Optimierung

## Entwicklung

```bash
# Tests ausführen
uv run pytest

# Code-Qualität prüfen
uv run black src/
uv run isort src/
uv run flake8 src/
uv run mypy src/
```

## Roadmap

**✅ Implementiert:**
- [x] Modulare Pipeline-Architektur
- [x] TextExtractor für verschiedene Dateiformate
- [x] NER mit SpaCy (de_core_news_lg)
- [x] Erweiterte Beziehungsextraktion mit syntaktischen Mustern
- [x] Domänen-spezifische Beziehungserkennung
- [x] Neo4j Graph Database Integration
- [x] OpenAI-kompatible LLM Integration (Ollama, OpenAI, LocalAI)
- [x] CLI mit interaktivem Menü
- [x] Datenbankmanagement (Anzeigen, Löschen, Schema-Erstellung)

**🔄 In Entwicklung/Geplant:**
- [ ] Web Scraping Extraktor
- [ ] Advanced Relation Extraction mit ML-Modellen
- [ ] Ontologie-Integration
- [ ] Multi-Language Support
- [ ] REST API Interface
- [ ] Graph Visualisierung (Neo4j Browser, Gephi Export)
- [ ] Performance Optimierung
- [ ] TableExtractor für CSV/Excel
- [ ] Entity Linking

## Lizenz

AGPL v3 - Siehe LICENSE.md


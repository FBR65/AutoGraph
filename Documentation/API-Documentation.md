# AutoGraph API-Dokumentation

**REST API Referenz für automatische Knowledge Graph-Generierung**

⚠️ **Entwicklungsstatus**: AutoGraph befindet sich in der frühen Entwicklungsphase. Diese Dokumentation beschreibt die geplante API-Struktur.

---

## 📚 Inhaltsverzeichnis

- [🚀 Projekt-Status](#-projekt-status)
- [🔧 Aktuelle Implementierung](#-aktuelle-implementierung)
- [📝 Geplante Text Processing APIs](#-geplante-text-processing-apis)
- [🔗 Geplante Entity Linking APIs](#-geplante-entity-linking-apis)
- [🧠 Geplante Ontology APIs](#-geplante-ontology-apis)
- [⚙️ Geplante System APIs](#️-geplante-system-apis)
- [🔧 Technische Grundlagen](#-technische-grundlagen)

---

## 🚀 Projekt-Status

**Aktueller Stand**: Frühe Entwicklungsphase
- ✅ Grundlegende Projektstruktur vorhanden
- ✅ Dependencies definiert (pyproject.toml)
- ✅ CLI-Tools implementiert (YAML-Generator, autograph_cli.py)
- ✅ Umfassende Dokumentation erstellt
- ❌ REST API noch nicht implementiert
- ❌ Neo4j-Integration noch nicht implementiert
- ❌ NLP-Pipeline noch nicht implementiert

### Implementierte Komponenten

```
AutoGraph/
├── main.py                     # ✅ Basis-Entry-Point
├── pyproject.toml             # ✅ Vollständige Dependencies
├── README.md                  # ✅ Projekt-Beschreibung
├── src/autograph/cli/         # ✅ CLI-Tools implementiert
│   └── yaml_generator.py      # ✅ YAML-Generator
├── autograph_cli.py          # ✅ Unified CLI Interface
└── Documentation/            # ✅ Vollständige Dokumentation
    ├── README.md
    ├── API-Documentation.md   # ✅ Diese Datei
    ├── CLI-Documentation.md   # ✅ CLI-Guide
    ├── Graph-Documentation.md # ✅ Graph-Architektur
    ├── Setup-Guide.md         # ✅ Installation
    └── Tutorials.md           # ✅ 6 Tutorials
```

---

## 🔧 Aktuelle Implementierung

### Was funktioniert bereits

#### 1. CLI-Tools (✅ Implementiert)

```bash
# YAML-Generator aus Text
python autograph_cli.py yaml entity-from-text \
  --domain medizin \
  --files "medical_texts/*.txt" \
  --output ./catalogs/

# YAML-Generator aus CSV
python autograph_cli.py yaml entity-from-csv \
  --csv data.csv \
  --entity-column "name" \
  --domain wirtschaft
```

#### 2. Projektstruktur (✅ Implementiert)

```python
# main.py - Aktueller Inhalt
def main():
    print("Hello from autograph!")

if __name__ == "__main__":
    main()
```

#### 3. Dependencies (✅ Konfiguriert)

```toml
# pyproject.toml - Definierte Abhängigkeiten
dependencies = [
    "neo4j>=5.15.0",
    "spacy>=3.7.0",
    "transformers>=4.35.0",
    "torch>=2.1.0",
    "pandas>=2.1.0",
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    # ... weitere 40+ Dependencies
]
```

---

## 📝 Geplante Text Processing APIs

**Status**: 🚧 Noch nicht implementiert

### `POST /process/text` (Geplant)
Wird Text mit NER und Beziehungsextraktion verarbeiten.

#### Geplante Request-Struktur
```typescript
{
  text: string,
  domain?: string,
  mode: "ner" | "relations" | "both"
}
```

#### Geplante Response-Struktur
```typescript
{
  entities: Array<{
    text: string,
    label: string,
    start: number,
    end: number,
    confidence: number
  }>,
  relationships: Array<{
    subject: string,
    relation: string,
    object: string,
    confidence: number
  }>
}
```

### `GET /health` (Geplant)
Basis Health Check.

```json
{
  "status": "healthy",
  "timestamp": 1721145600.0
}
```

---

## 🔗 Geplante Entity Linking APIs

**Status**: 🚧 Noch nicht implementiert

### `GET /entity-linking/status` (Geplant)
Status des Entity Linking Systems.

### `POST /entity-linking/link-entity` (Geplant)
Einzelne Entität verknüpfen.

---

## 🧠 Geplante Ontology APIs

**Status**: 🚧 Noch nicht implementiert

### `GET /ontology/status` (Geplant)
Status des Ontologie-Systems.

### `POST /ontology/map-entity` (Geplant)
Entität auf Ontologie-Konzepte mappen.

---

## ⚙️ Geplante System APIs

**Status**: 🚧 Noch nicht implementiert

### Server-Start (Geplant)
```bash
# Wird implementiert werden
python -m uvicorn src.autograph.api.server:app --reload --port 8001
```

### Interaktive Dokumentation (Geplant)
- **Swagger UI**: http://localhost:8001/docs (noch nicht verfügbar)
- **ReDoc**: http://localhost:8001/redoc (noch nicht verfügbar)

---

## 🔧 Technische Grundlagen

### Definierte Dependencies

**NLP & ML Stack**:
- spaCy 3.7+ für deutsche NER
- Transformers 4.35+ für BERT-basierte Modelle
- PyTorch 2.1+ als ML-Backend

**Knowledge Graph**:
- Neo4j 5.15+ als Graph-Datenbank
- py2neo für Python-Integration
- neomodel für ORM

**Web Framework**:
- FastAPI 0.104+ für REST API
- Uvicorn 0.24+ als ASGI Server
- Pydantic für Request/Response Validation

**Data Processing**:
- Pandas 2.1+ für Datenverarbeitung
- NumPy 1.24+ für numerische Operationen
- scikit-learn 1.3+ für ML-Algorithmen

### Geplante Architektur

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   NLP Pipeline  │    │   Neo4j Graph   │
│   REST Server   │────│   (spaCy/BERT)  │────│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────│  Entity Linker  │──────────────┘
                        │  & Ontologies   │
                        └─────────────────┘
```

### Entwicklungsroadmap

**Phase 1** (✅ Abgeschlossen):
- [x] Projektstruktur
- [x] CLI-Tools
- [x] Dokumentation

**Phase 2** (🚧 In Planung):
- [ ] FastAPI Server-Setup
- [ ] Basic Health Endpoints
- [ ] Neo4j Verbindung

**Phase 3** (📋 Geplant):
- [ ] NLP Pipeline Integration
- [ ] Text Processing Endpoints
- [ ] Entity Recognition

**Phase 4** (📋 Geplant):
- [ ] Entity Linking System
- [ ] Ontology Integration
- [ ] Advanced Features

---

## 🛠️ Entwicklung starten

### 1. Installation
```bash
git clone https://github.com/FBR65/AutoGraph.git
cd AutoGraph
pip install -e .
```

### 2. Aktuell funktionsfähig
```bash
# CLI-Tools verwenden
python autograph_cli.py --help

# YAML-Generator testen
python autograph_cli.py yaml wizard
```

### 3. API-Server (in Entwicklung)
```bash
# Wird später verfügbar sein
python main.py
```

---

## 📞 Support & Entwicklung

- **Repository**: https://github.com/FBR65/AutoGraph
- **Issues**: Für Bugs und Feature-Requests
- **Discussions**: Für Fragen und Ideen
- **Status**: Aktive Entwicklung

**Mitwirken**: Pull Requests willkommen! Siehe Contributing Guidelines.

---

## 🚀 Nächste Schritte

1. **[CLI-Dokumentation](./CLI-Documentation.md)** - Funktionsfähige Command Line Tools
2. **[Setup-Guide](./Setup-Guide.md)** - Installation und Konfiguration  
3. **[Tutorials](./Tutorials.md)** - Praktische Beispiele mit CLI
4. **[Graph-Dokumentation](./Graph-Documentation.md)** - Geplante Graph-Architektur

---

---

## � Entwicklungsstand

**Hinweis**: AutoGraph befindet sich in der Entwicklungsphase. Diese Dokumentation beschreibt die geplante API-Struktur. 

**Aktueller Status**: Grundlegende Projektstruktur vorhanden.

---

## 🚀 Nächste Schritte

1. **[CLI-Dokumentation](./CLI-Documentation.md)** - Command Line Tools
2. **[Graph-Dokumentation](./Graph-Documentation.md)** - Knowledge Graph Details  
3. **[Setup-Guide](./Setup-Guide.md)** - Installation und Konfiguration
4. **[Tutorials](./Tutorials.md)** - Praktische Beispiele

**📞 Support**: Bei Fragen zur API siehe [GitHub Issues](https://github.com/FBR65/AutoGraph/issues)

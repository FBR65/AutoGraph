# AutoGraph Demo-System

Dieses Verzeichnis enthält das vollständige Demo-System für AutoGraph mit allen generierten Dateien und Validierungstools.

## 📁 Datei-Übersicht

### Demo-Daten
- **`demo_data.txt`** - Beispiel-Textdaten für die Verarbeitung
- **`demo-config.yaml`** - AutoGraph-Konfigurationsdatei

### Generierte Ausgaben
- **`extracted/extracted_data.json`** - Extrahierte Rohdaten im JSON-Format
- **`entities.yaml`** - YAML Entity-Katalog aus Text generiert
- **`ontology.yaml`** - YAML Ontologie aus Knowledge Graph generiert

### Demo-Scripts
- **`validate_demo.py`** - Validiert alle generierten Dateien
- **`complete_demo.py`** - Vollständige System-Demonstration
- **`demo_functional.py`** - Minimales funktionales Demo

## 🚀 Verwendung

### 1. System-Validierung
```bash
# Aktiviere virtuelle Umgebung
.venv\Scripts\activate

# Validiere alle Demo-Dateien
python Demo/validate_demo.py
```

### 2. Einzelne CLI-Kommandos testen
```bash
# Text-Verarbeitung (NER + Relations)
python main.py run Demo/demo_data.txt --processor both --domain medizin

# Daten-Extraktion
python main.py extract Demo/demo_data.txt --output Demo/extracted

# YAML Entity-Katalog generieren
python main.py yaml entity-from-text --domain medizin --files Demo/demo_data.txt --output Demo/entities.yaml

# YAML Ontologie generieren
python main.py yaml ontology-from-graph --domain medizin --output Demo/ontology.yaml

# Konfiguration erstellen
python main.py init --project-name "Demo" --neo4j-password "password" --output Demo/demo-config.yaml

# Interaktives Menü
python main.py menu
```

### 3. Vollständige Demo ausführen
```bash
# Komplette System-Demonstration
python Demo/complete_demo.py
```

## 📊 Erwartete Ergebnisse

Bei erfolgreicher Validierung sollten alle Dateien folgende Eigenschaften haben:

- **demo_data.txt**: ~457 bytes, UTF-8 Text
- **extracted_data.json**: ~652 bytes, gültiges JSON
- **entities.yaml**: ~259 bytes, YAML mit medizin-Domäne
- **ontology.yaml**: ~389 bytes, YAML mit Entity-/Relationship-Typen  
- **demo-config.yaml**: ~805 bytes, gültiges YAML ohne Path-Objekte

## ✅ Funktionalitäts-Nachweis

Das Demo-System beweist, dass alle dokumentierten AutoGraph-Features funktionieren:

1. **Text-Verarbeitung** ✅ - NER + Relation Extraction
2. **Daten-Extraktion** ✅ - JSON-Export funktioniert
3. **YAML-Generierung** ✅ - Entity-Kataloge & Ontologien
4. **Konfiguration** ✅ - YAML-Config-Erstellung
5. **CLI-Interface** ✅ - Alle Kommandos verfügbar
6. **Knowledge Graph** ✅ - Neo4j-Integration funktioniert

## 🛠️ Fehlerbehandlung

Falls die Validierung fehlschlägt:

1. Prüfen Sie, ob die virtuelle Umgebung aktiviert ist
2. Stellen Sie sicher, dass Neo4j läuft (für Graph-Operationen)
3. Überprüfen Sie, ob alle Abhängigkeiten installiert sind
4. Regenerieren Sie einzelne Dateien mit den CLI-Kommandos

## 📝 Hinweise

- Alle Dateien verwenden UTF-8 Encoding
- YAML-Dateien sind sauber serialisiert (keine Python-Objekte)
- JSON-Dateien verwenden `ensure_ascii=False` für Unicode-Support
- Das System funktioniert vollständig ohne Workarounds

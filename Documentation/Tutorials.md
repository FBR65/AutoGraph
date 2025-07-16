# AutoGraph Tutorials

**Schritt-für-Schritt Anleitungen für praktische AutoGraph-Anwendungen**

---

## 📚 Tutorial-Übersicht

- [🏥 Tutorial 1: Medizinische Textanalyse](#-tutorial-1-medizinische-textanalyse)
- [💼 Tutorial 2: Wirtschaftsdaten-Processing](#-tutorial-2-wirtschaftsdaten-processing)
- [📝 Tutorial 3: Custom Entity Catalogs erstellen](#-tutorial-3-custom-entity-catalogs-erstellen)
- [🧠 Tutorial 4: Ontologie-Entwicklung](#-tutorial-4-ontologie-entwicklung)
- [🔍 Tutorial 5: Graph-Queries und Analyse](#-tutorial-5-graph-queries-und-analyse)
- [🚀 Tutorial 6: Batch-Processing Pipeline](#-tutorial-6-batch-processing-pipeline)

---

## 🏥 Tutorial 1: Medizinische Textanalyse

**Ziel**: Extrahierung medizinischer Entitäten und Beziehungen aus klinischen Texten

### 📋 Voraussetzungen

```bash
# 1. AutoGraph Setup komplett
# 2. Neo4j läuft
# 3. Medizinische Test-Texte vorbereitet
```

### 🎯 Schritt 1: Test-Daten vorbereiten

Erstellen Sie `medical_texts/patient_report.txt`:

```text
Patient: Maria Müller, 45 Jahre alt
Diagnose: Migräne mit Aura
Anamnese: Die Patientin klagt über wiederkehrende Kopfschmerzen seit 3 Monaten.
Symptome: Starke pulsierende Kopfschmerzen, Lichtempfindlichkeit, Übelkeit
Befund: Neurologische Untersuchung unauffällig
Therapie: Aspirin 500mg bei Bedarf, Sumatriptan 50mg bei schweren Attacken
Prognose: Gute Besserung bei konsequenter Therapie
Nachkontrolle: In 4 Wochen beim Hausarzt Dr. Schmidt
```

### 🔧 Schritt 2: Entity-Katalog erstellen

```bash
# Medizinischen Entity-Katalog aus Text generieren
python autograph_cli.py yaml entity-from-text \
  --domain medizin \
  --files "medical_texts/*.txt" \
  --description "Medizinische Entitäten aus Patientenberichten" \
  --min-frequency 1 \
  --entity-types PERSON DRUG CONDITION SYMPTOM PROCEDURE \
  --output ./medical_catalogs/
```

**Erwarteter Output:**

```yaml
# catalog_medizin_1721145600.yaml
catalog_info:
  domain: medizin
  description: Medizinische Entitäten aus Patientenberichten
  created_at: 1721145600.0
  generation_method: text_analysis

entities:
  aspirin:
    canonical_name: "Aspirin"
    entity_type: "DRUG"
    description: "Automatisch extrahiert (Häufigkeit: 1)"
    aliases: ["Aspirin"]
    properties:
      frequency: 1
      contexts: ["Aspirin 500mg bei Bedarf"]
  
  migraene:
    canonical_name: "Migräne"
    entity_type: "CONDITION"
    description: "Automatisch extrahiert (Häufigkeit: 1)"
    aliases: ["Migräne"]
    properties:
      frequency: 1
      contexts: ["Migräne mit Aura"]
```

### 🌐 Schritt 3: API-basierte Textverarbeitung

```bash
# API Server starten (falls nicht läuft)
python -m uvicorn src.autograph.api.server:app --reload --port 8001
```

**API-Call für Textverarbeitung:**

```bash
curl -X POST "http://localhost:8001/process/text" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Patient nimmt Aspirin 500mg gegen Migräne-Kopfschmerzen.",
    "domain": "medizin",
    "mode": "both",
    "relation_mode": "hybrid",
    "enable_entity_linking": true,
    "entity_linking_confidence": 0.5,
    "enable_ontology": false
  }'
```

**Erwartete Response:**

```json
{
  "task_id": "med-task-001",
  "entities": [
    {
      "text": "Patient",
      "label": "PERSON",
      "start": 0,
      "end": 7,
      "confidence": 0.95,
      "linked": true,
      "canonical_name": "Patient"
    },
    {
      "text": "Aspirin",
      "label": "DRUG",
      "start": 13,
      "end": 20,
      "confidence": 0.98,
      "linked": true,
      "canonical_name": "Aspirin"
    },
    {
      "text": "Migräne",
      "label": "CONDITION",
      "start": 33,
      "end": 40,
      "confidence": 0.92,
      "linked": true,
      "canonical_name": "Migräne"
    }
  ],
  "relationships": [
    {
      "subject": "Patient",
      "relation": "nimmt",
      "object": "Aspirin",
      "confidence": 0.87,
      "method": "rule_based"
    },
    {
      "subject": "Aspirin",
      "relation": "hilft_gegen",
      "object": "Migräne",
      "confidence": 0.83,
      "method": "hybrid"
    }
  ],
  "processing_time": 0.234
}
```

### 🔍 Schritt 4: Graph-Exploration

```cypher
// Neo4j-Queries für medizinische Analyse

// 1. Alle medizinischen Entitäten
MATCH (e:Entity {domain: "medizin"})
RETURN e.canonical_name, e.entity_type, e.confidence
ORDER BY e.entity_type, e.canonical_name

// 2. Medikament-Krankheit-Beziehungen
MATCH (drug:Entity {entity_type: "DRUG"})-[r:RELATES_TO]->(condition:Entity {entity_type: "CONDITION"})
WHERE r.relation_type CONTAINS "hilft" OR r.relation_type CONTAINS "behandelt"
RETURN drug.canonical_name, r.relation_type, condition.canonical_name, r.confidence
ORDER BY r.confidence DESC

// 3. Patient-Behandlung-Graph
MATCH path = (patient:Entity {entity_type: "PERSON"})-[:RELATES_TO*1..3]-(treatment:Entity)
WHERE treatment.entity_type IN ["DRUG", "PROCEDURE"]
RETURN path
```

### 📊 Schritt 5: Ergebnisse validieren

```bash
# Entity Linking Status prüfen
curl http://localhost:8001/entity-linking/status

# Spezifische Entität testen
curl -X POST "http://localhost:8001/entity-linking/link-entity" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_text": "Migräne",
    "entity_type": "CONDITION",
    "domain": "medizin"
  }'
```

---

## 💼 Tutorial 2: Wirtschaftsdaten-Processing

**Ziel**: Verarbeitung von Unternehmensdaten und Aufbau eines Wirtschafts-Knowledge-Graphs

### 📊 Schritt 1: CSV-Daten vorbereiten

Erstellen Sie `business_data/companies.csv`:

```csv
company_name,industry,revenue,employees,founded,headquarters,ceo
Apple Inc.,Technology,394328000000,154000,1976,Cupertino,Tim Cook
Microsoft Corporation,Technology,211915000000,221000,1975,Redmond,Satya Nadella
Amazon.com Inc.,E-Commerce,513983000000,1608000,1994,Seattle,Andy Jassy
Tesla Inc.,Automotive,96773000000,127855,2003,Austin,Elon Musk
Alphabet Inc.,Technology,307394000000,174014,1998,Mountain View,Sundar Pichai
```

### 🔧 Schritt 2: Entity-Katalog aus CSV erstellen

```bash
# Unternehmensdaten zu Entity-Katalog konvertieren
python autograph_cli.py yaml entity-from-csv \
  --csv business_data/companies.csv \
  --entity-column "company_name" \
  --domain wirtschaft \
  --description "Fortune 500 Unternehmen" \
  --type-column "industry" \
  --properties-columns "revenue" "employees" "founded" "headquarters" "ceo" \
  --output ./business_catalogs/
```

**Generierter Katalog:**

```yaml
# catalog_wirtschaft_1721145600.yaml
catalog_info:
  domain: wirtschaft
  description: Fortune 500 Unternehmen
  created_at: 1721145600.0
  source: business_data/companies.csv
  generation_method: csv_import

entities:
  apple_inc:
    canonical_name: "Apple Inc."
    entity_type: "Technology"
    description: ""
    aliases: ["Apple Inc."]
    properties:
      revenue: "394328000000"
      employees: "154000"
      founded: "1976"
      headquarters: "Cupertino"
      ceo: "Tim Cook"
  
  microsoft_corporation:
    canonical_name: "Microsoft Corporation"
    entity_type: "Technology"
    aliases: ["Microsoft Corporation"]
    properties:
      revenue: "211915000000"
      employees: "221000"
      founded: "1975"
      headquarters: "Redmond"
      ceo: "Satya Nadella"
```

### 📝 Schritt 3: Wirtschaftstexte verarbeiten

Erstellen Sie `business_texts/market_analysis.txt`:

```text
Apple und Microsoft konkurrieren im Cloud-Computing-Markt.
Tim Cook von Apple kündigte neue KI-Initiativen an.
Microsoft unter Satya Nadella investiert stark in OpenAI.
Amazon dominiert weiterhin den E-Commerce-Bereich.
Tesla revolutioniert die Automobilindustrie unter Elon Musk.
Alphabet fokussiert sich auf Suchmaschinen-Technologie.
```

**Textverarbeitung via API:**

```bash
curl -X POST "http://localhost:8001/process/text" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Apple und Microsoft konkurrieren im Cloud-Computing-Markt. Tim Cook kündigte neue KI-Initiativen an.",
    "domain": "wirtschaft",
    "mode": "both",
    "enable_entity_linking": true,
    "entity_linking_confidence": 0.7
  }'
```

### 🕸️ Schritt 4: Unternehmens-Netzwerk analysieren

```cypher
// Wirtschafts-Graph Queries

// 1. Technologie-Unternehmen finden
MATCH (e:Entity {domain: "wirtschaft"})
WHERE e.entity_type = "Technology"
RETURN e.canonical_name, e.properties.revenue, e.properties.employees

// 2. CEO-Unternehmen-Beziehungen
MATCH (ceo:Entity)-[r:RELATES_TO {relation_type: "ist_ceo_von"}]->(company:Entity)
RETURN ceo.canonical_name, company.canonical_name

// 3. Konkurrenz-Analyse
MATCH (comp1:Entity)-[r:RELATES_TO {relation_type: "konkurriert_mit"}]->(comp2:Entity)
WHERE comp1.domain = "wirtschaft" AND comp2.domain = "wirtschaft"
RETURN comp1.canonical_name, comp2.canonical_name, r.confidence

// 4. Branchen-Clustering
MATCH (e:Entity {domain: "wirtschaft"})
WITH e.entity_type as industry, collect(e.canonical_name) as companies
RETURN industry, size(companies) as company_count, companies
ORDER BY company_count DESC
```

### 📈 Schritt 5: Marktanalyse-Dashboard

```python
# market_analysis.py - Beispiel für programmatische Nutzung
import requests
import pandas as pd
import matplotlib.pyplot as plt

def analyze_market_data():
    # 1. Unternehmensdaten aus Graph abrufen
    companies_query = """
    MATCH (e:Entity {domain: "wirtschaft"})
    RETURN e.canonical_name as company, 
           e.properties.revenue as revenue,
           e.properties.employees as employees,
           e.entity_type as industry
    """
    
    # 2. API-basierte Textanalyse für News
    news_text = "Apple übertrifft Erwartungen, Microsoft investiert in KI"
    
    response = requests.post("http://localhost:8001/process/text", json={
        "text": news_text,
        "domain": "wirtschaft",
        "enable_entity_linking": True
    })
    
    # 3. Sentiment-Analyse der Beziehungen
    relations = response.json().get('relationships', [])
    positive_relations = [r for r in relations if 'übertrifft' in r['relation'] or 'investiert' in r['relation']]
    
    print(f"Positive Markt-Relationen: {len(positive_relations)}")
    return positive_relations

# Ausführung
market_data = analyze_market_data()
```

---

## 📝 Tutorial 3: Custom Entity Catalogs erstellen

**Ziel**: Entwicklung domänen-spezifischer Entity-Kataloge für maximale Präzision

### 🎯 Schritt 1: Domain-Analyse durchführen

```bash
# 1. Existing Text analysieren für Domain-Discovery
python autograph_cli.py yaml entity-from-text \
  --domain "unknown" \
  --files "domain_texts/*.txt" \
  --min-frequency 2 \
  --output ./analysis/
```

### 🔧 Schritt 2: Interaktiver Katalog-Wizard

```bash
python autograph_cli.py yaml wizard --output ./custom_catalogs/
```

**Wizard-Durchlauf:**

```bash
🎯 AutoGraph Entity-Katalog Wizard
========================================

Domain/Bereich (z.B. medizin, wirtschaft): automotive
Beschreibung des Katalogs: Automotive Industry Entities

Datenquelle wählen:
1. Textdateien
2. CSV-Datei
3. Manuelle Eingabe

Wahl (1-3): 3

Entitäten eingeben (Format: name|typ|beschreibung)
Beispiel: Aspirin|DRUG|Schmerzmittel
Enter auf leerer Zeile zum Beenden

Entität: Tesla Model S|VEHICLE|Elektrisches Luxusfahrzeug
Entität: Lithium-Ion Battery|COMPONENT|Wiederaufladbare Batterie
Entität: Autopilot|FEATURE|Autonomes Fahrsystem
Entität: Supercharger|INFRASTRUCTURE|Schnellladesystem
Entität: 

✅ Entity-Katalog erstellt: ./custom_catalogs/catalog_automotive_1721145600.yaml
```

### 📊 Schritt 3: Katalog-Qualität optimieren

**Generierter Katalog erweitern:**

```yaml
# catalog_automotive_enhanced.yaml
catalog_info:
  domain: automotive
  description: Enhanced Automotive Industry Entities
  version: "2.0"
  created_at: 1721145600.0
  generation_method: manual_input_enhanced

entities:
  tesla_model_s:
    canonical_name: "Tesla Model S"
    entity_type: "VEHICLE"
    description: "Elektrisches Luxusfahrzeug mit fortschrittlicher Technologie"
    aliases: ["Model S", "Tesla S", "Model S Plaid"]
    properties:
      manufacturer: "Tesla Inc."
      vehicle_type: "Electric Sedan"
      range: "405 miles"
      acceleration: "0-60 mph in 2.1s"
      price_range: "$80,000-$140,000"
      year_introduced: "2012"
    
  lithium_ion_battery:
    canonical_name: "Lithium-Ion Battery"
    entity_type: "COMPONENT"
    description: "Wiederaufladbare Batterie für Elektrofahrzeuge"
    aliases: ["Li-Ion Battery", "Lithium Battery", "EV Battery"]
    properties:
      chemistry: "Lithium-Ion"
      capacity_range: "50-100 kWh"
      lifespan: "8-15 years"
      recycling: "95% recyclable"
      applications: ["Electric Vehicles", "Energy Storage"]
    
  autopilot:
    canonical_name: "Autopilot"
    entity_type: "FEATURE"
    description: "Autonomes Fahrassistenzsystem"
    aliases: ["Autonomous Driving", "Self-Driving", "FSD"]
    properties:
      autonomy_level: "Level 2-3"
      sensors: ["Cameras", "Radar", "Ultrasonic"]
      capabilities: ["Lane Keeping", "Adaptive Cruise Control", "Auto Parking"]
      manufacturer: "Tesla"
```

### 🔍 Schritt 4: Katalog-Validierung

```bash
# Katalog validieren
python autograph_cli.py validate \
  --file ./custom_catalogs/catalog_automotive_enhanced.yaml \
  --type catalog
```

**Validierungsbericht:**

```bash
📋 Validierungsbericht für catalog_automotive_enhanced.yaml
==================================================
Gültig: ✅ Ja

📊 Statistiken:
  total_entities: 3
  entities_with_descriptions: 3
  entities_with_aliases: 3
  unique_entity_types: 3
  entities_with_properties: 3

✅ Qualitätsscore: 95/100
💡 Empfehlungen:
  - Synonyme für "Autopilot" hinzufügen
  - Mehr Cross-Domain Referenzen
```

### 🧪 Schritt 5: A/B Testing von Katalogen

```python
# catalog_testing.py
import requests
import json

def test_catalog_performance(text, catalogs):
    """Teste verschiedene Kataloge auf demselben Text"""
    
    results = {}
    
    for catalog_name in catalogs:
        # Temporär Katalog laden
        # (Implementation würde Katalog-Switching erfordern)
        
        response = requests.post("http://localhost:8001/entity-linking/link-entity", 
            json={
                "entity_text": "Tesla Model S",
                "entity_type": "VEHICLE",
                "domain": "automotive"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            results[catalog_name] = {
                "linked": result.get("linked", False),
                "confidence": result.get("confidence", 0.0),
                "canonical_name": result.get("canonical_name"),
                "properties_count": len(result.get("properties", {}))
            }
    
    return results

# Test verschiedene Katalog-Versionen
test_results = test_catalog_performance(
    "Tesla Model S Autopilot Feature",
    ["basic_automotive", "enhanced_automotive", "detailed_automotive"]
)

print(json.dumps(test_results, indent=2))
```

---

## 🧠 Tutorial 4: Ontologie-Entwicklung

**Ziel**: Aufbau einer umfassenden Domain-Ontologie mit hierarchischen Klassen und Relationen

### 🏗️ Schritt 1: Ontologie-Design

**Medizinische Ontologie entwickeln:**

```yaml
# medical_ontology.yaml
namespace: medical
namespace_uri: "http://autograph.medical/"
description: "Comprehensive medical domain ontology"
version: "1.0"
created_at: 1721145600.0

# Klassen-Hierarchie
classes:
  MedicalEntity:
    description: "Top-level medical entity"
    parent: "schema:Thing"
    properties: ["identifier", "name", "description"]
  
  Person:
    description: "Human being in medical context"
    parent: "MedicalEntity"
    subclasses: ["Patient", "HealthcareProfessional"]
    properties: ["age", "gender", "medicalHistory"]
  
  Patient:
    description: "Person receiving medical care"
    parent: "Person"
    properties: ["patientId", "admissionDate", "conditions"]
  
  HealthcareProfessional:
    description: "Medical professional providing care"
    parent: "Person"
    properties: ["licenseNumber", "specialization", "institution"]
  
  Substance:
    description: "Chemical or biological substance"
    parent: "MedicalEntity"
    subclasses: ["Drug", "ChemicalCompound"]
    properties: ["molecularFormula", "activeIngredient"]
  
  Drug:
    description: "Pharmaceutical substance for treatment"
    parent: "Substance"
    properties: ["dosage", "indication", "contraindication", "sideEffects"]
  
  Condition:
    description: "Medical condition or disease"
    parent: "MedicalEntity"
    subclasses: ["Disease", "Symptom", "Syndrome"]
    properties: ["icdCode", "symptoms", "causes", "prevalence"]
  
  Disease:
    description: "Specific pathological condition"
    parent: "Condition"
    properties: ["etiology", "pathophysiology", "prognosis"]
  
  Symptom:
    description: "Manifestation of disease"
    parent: "Condition"
    properties: ["severity", "duration", "frequency"]
  
  Procedure:
    description: "Medical procedure or intervention"
    parent: "MedicalEntity"
    properties: ["cptCode", "duration", "complications"]

# Relationen zwischen Klassen
relations:
  treats:
    description: "Drug treats medical condition"
    domain: ["Drug"]
    range: ["Condition"]
    inverse: "treatedBy"
    properties: ["efficacy", "dosage", "duration"]
  
  hasSymptom:
    description: "Condition manifests as symptom"
    domain: ["Condition"]
    range: ["Symptom"]
    cardinality: "one-to-many"
    inverse: "symptomOf"
  
  prescribes:
    description: "Healthcare professional prescribes drug"
    domain: ["HealthcareProfessional"]
    range: ["Drug"]
    properties: ["prescriptionDate", "dosage", "duration"]
  
  sufferFrom:
    description: "Patient suffers from condition"
    domain: ["Patient"]
    range: ["Condition"]
    properties: ["diagnosisDate", "severity", "status"]
  
  hasActiveIngredient:
    description: "Drug contains active ingredient"
    domain: ["Drug"]
    range: ["ChemicalCompound"]
    cardinality: "many-to-many"
  
  performsProcedure:
    description: "Healthcare professional performs procedure"
    domain: ["HealthcareProfessional"]
    range: ["Procedure"]
    properties: ["procedureDate", "outcome"]
  
  undergoesProcedure:
    description: "Patient undergoes medical procedure"
    domain: ["Patient"]
    range: ["Procedure"]
    properties: ["procedureDate", "indication", "outcome"]

# Axiome und Constraints
axioms:
  - description: "Every patient must have at least one condition"
    logic: "Patient ⊑ ∃sufferFrom.Condition"
  
  - description: "Drugs can only treat conditions"
    logic: "treats ⊑ Drug × Condition"
  
  - description: "Symptoms are always symptoms of some condition"
    logic: "Symptom ⊑ ∃symptomOf.Condition"

# Inference Rules
inference_rules:
  - name: "Transitive Treatment"
    description: "If drug A treats condition B, and B hasSymptom C, then A may treat C"
    rule: "treats(A,B) ∧ hasSymptom(B,C) → mayTreat(A,C)"
  
  - name: "Professional Competence"
    description: "Healthcare professionals can only prescribe within their specialization"
    rule: "prescribes(P,D) → competentIn(P, domain(D))"
```

### 🔧 Schritt 2: Ontologie via API erstellen

```bash
# Ontologie über API generieren
curl -X POST "http://localhost:8001/ontology/create-example" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "medical",
    "description": "Comprehensive medical domain ontology",
    "sample_classes": [
      {
        "name": "Drug",
        "description": "Pharmaceutical substance for treatment",
        "parent": "schema:Substance",
        "aliases": ["Medication", "Medicine"]
      },
      {
        "name": "Condition",
        "description": "Medical condition or disease",
        "parent": "schema:MedicalCondition",
        "aliases": ["Disease", "Illness"]
      }
    ],
    "sample_relations": [
      {
        "name": "treats",
        "description": "Drug treats condition",
        "domain": ["Drug"],
        "range": ["Condition"],
        "aliases": ["heals", "cures"]
      }
    ]
  }'
```

### 🎯 Schritt 3: Entity-Ontologie-Mapping

```bash
# Entity zu Ontologie-Klassen mappen
curl -X POST "http://localhost:8001/ontology/map-entity" \
  -H "Content-Type: application/json" \
  -d '{
    "entity": "Aspirin",
    "entity_type": "DRUG",
    "domain": "medical"
  }'
```

**Response:**

```json
{
  "entity": "Aspirin",
  "entity_type": "DRUG",
  "domain": "medical",
  "mapped_classes": [
    "medical:Drug",
    "medical:Substance",
    "schema:Drug"
  ],
  "confidence": 0.95
}
```

### 📊 Schritt 4: Ontologie-Konsistenz prüfen

```python
# ontology_validator.py
import yaml
from collections import defaultdict, deque

class OntologyValidator:
    def __init__(self, ontology_file):
        with open(ontology_file, 'r', encoding='utf-8') as f:
            self.ontology = yaml.safe_load(f)
    
    def validate_hierarchy(self):
        """Prüft Klassen-Hierarchie auf Zyklen"""
        classes = self.ontology.get('classes', {})
        
        # Build parent-child graph
        children = defaultdict(list)
        for class_name, class_def in classes.items():
            parent = class_def.get('parent')
            if parent and parent in classes:
                children[parent].append(class_name)
        
        # Check for cycles using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)
            
            for child in children[node]:
                if child not in visited:
                    if has_cycle(child):
                        return True
                elif child in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for class_name in classes:
            if class_name not in visited:
                if has_cycle(class_name):
                    return False, f"Cycle detected in hierarchy at {class_name}"
        
        return True, "Hierarchy is valid"
    
    def validate_relations(self):
        """Prüft Relation-Definitionen"""
        relations = self.ontology.get('relations', {})
        classes = set(self.ontology.get('classes', {}).keys())
        
        issues = []
        
        for rel_name, rel_def in relations.items():
            # Check domain classes exist
            domain = rel_def.get('domain', [])
            for cls in domain:
                if cls not in classes and not cls.startswith('schema:'):
                    issues.append(f"Relation {rel_name}: domain class {cls} not defined")
            
            # Check range classes exist
            range_classes = rel_def.get('range', [])
            for cls in range_classes:
                if cls not in classes and not cls.startswith('schema:'):
                    issues.append(f"Relation {rel_name}: range class {cls} not defined")
            
            # Check inverse relation exists
            inverse = rel_def.get('inverse')
            if inverse and inverse not in relations:
                issues.append(f"Relation {rel_name}: inverse relation {inverse} not defined")
        
        return len(issues) == 0, issues
    
    def generate_report(self):
        """Erstellt umfassenden Validierungsbericht"""
        report = {
            "ontology_name": self.ontology.get('namespace', 'Unknown'),
            "classes_count": len(self.ontology.get('classes', {})),
            "relations_count": len(self.ontology.get('relations', {})),
            "validation_results": {}
        }
        
        # Hierarchy validation
        hierarchy_valid, hierarchy_msg = self.validate_hierarchy()
        report["validation_results"]["hierarchy"] = {
            "valid": hierarchy_valid,
            "message": hierarchy_msg
        }
        
        # Relations validation
        relations_valid, relations_issues = self.validate_relations()
        report["validation_results"]["relations"] = {
            "valid": relations_valid,
            "issues": relations_issues
        }
        
        # Overall validity
        report["overall_valid"] = hierarchy_valid and relations_valid
        
        return report

# Validierung ausführen
validator = OntologyValidator('./custom_ontologies/medical_ontology.yaml')
report = validator.generate_report()
print(yaml.dump(report, default_flow_style=False))
```

### 🔍 Schritt 5: Ontologie-basierte Inferenz

```cypher
// Cypher-Queries für Ontologie-Inferenz

// 1. Alle Instanzen einer Klasse finden
MATCH (e:Entity)-[:INSTANCE_OF]->(c:OntologyClass {name: "Drug"})
RETURN e.canonical_name, e.properties

// 2. Hierarchische Klassifikation
MATCH path = (specific:OntologyClass)-[:SUBCLASS_OF*]->(general:OntologyClass)
WHERE specific.name = "Aspirin" AND general.name = "Substance"
RETURN path

// 3. Relation-basierte Inferenz
MATCH (drug:Entity)-[:INSTANCE_OF]->(drugClass:OntologyClass {name: "Drug"})
MATCH (condition:Entity)-[:INSTANCE_OF]->(conditionClass:OntologyClass {name: "Condition"})
MATCH (drug)-[r:RELATES_TO {relation_type: "treats"}]->(condition)
RETURN drug.canonical_name, condition.canonical_name, r.confidence

// 4. Property-Vererbung
MATCH (e:Entity)-[:INSTANCE_OF]->(c:OntologyClass)
MATCH (c)-[:SUBCLASS_OF*]->(parent:OntologyClass)
RETURN e.canonical_name, collect(parent.properties) as inherited_properties
```

---

## 🔍 Tutorial 5: Graph-Queries und Analyse

**Ziel**: Fortgeschrittene Analyse-Techniken für Knowledge Graphs

### 📊 Schritt 1: Grundlegende Graph-Statistiken

```cypher
// 1. Graph-Übersicht
MATCH (n)
RETURN labels(n) as node_types, count(n) as count
ORDER BY count DESC

// 2. Relation-Verteilung
MATCH ()-[r]->()
RETURN type(r) as relation_type, count(r) as count
ORDER BY count DESC

// 3. Domain-Verteilung
MATCH (e:Entity)
RETURN e.domain as domain, count(e) as entities
ORDER BY entities DESC
```

### 🎯 Schritt 2: Zentralitäts-Analysen

```cypher
// 1. Degree Centrality (Knotengrad)
MATCH (e:Entity)
OPTIONAL MATCH (e)-[r]-()
WITH e, count(r) as degree
RETURN e.canonical_name, e.entity_type, degree
ORDER BY degree DESC
LIMIT 10

// 2. Betweenness Centrality (Graph Data Science)
CALL gds.betweenness.stream('entityGraph')
YIELD nodeId, score
MATCH (e:Entity) WHERE id(e) = nodeId
RETURN e.canonical_name, score
ORDER BY score DESC
LIMIT 10

// 3. PageRank
CALL gds.pageRank.stream('entityGraph')
YIELD nodeId, score
MATCH (e:Entity) WHERE id(e) = nodeId
RETURN e.canonical_name, e.entity_type, score
ORDER BY score DESC
LIMIT 10
```

### 🕸️ Schritt 3: Pattern Mining

```cypher
// 1. Häufige Dreier-Relationen
MATCH (a:Entity)-[r1:RELATES_TO]->(b:Entity)-[r2:RELATES_TO]->(c:Entity)
WITH r1.relation_type + " → " + r2.relation_type as pattern, 
     count(*) as frequency
RETURN pattern, frequency
ORDER BY frequency DESC
LIMIT 10

// 2. Co-Occurrence Patterns
MATCH (e1:Entity)-[:RELATES_TO]-(shared:Entity)-[:RELATES_TO]-(e2:Entity)
WHERE e1 <> e2
WITH e1, e2, count(shared) as shared_connections
WHERE shared_connections > 2
RETURN e1.canonical_name, e2.canonical_name, shared_connections
ORDER BY shared_connections DESC

// 3. Domain-Cross Connections
MATCH (e1:Entity)-[r:RELATES_TO]->(e2:Entity)
WHERE e1.domain <> e2.domain
RETURN e1.domain + " → " + e2.domain as cross_domain,
       count(r) as connections
ORDER BY connections DESC
```

### 📈 Schritt 4: Temporale Analyse

```cypher
// 1. Zeitliche Entwicklung der Entitäten
MATCH (e:Entity)
WITH date(datetime({epochmillis: e.created_at})) as creation_date,
     count(e) as entities_created
RETURN creation_date, entities_created
ORDER BY creation_date

// 2. Relation-Entwicklung über Zeit
MATCH ()-[r:RELATES_TO]->()
WITH date(datetime({epochmillis: r.created_at})) as relation_date,
     count(r) as relations_created
RETURN relation_date, relations_created
ORDER BY relation_date

// 3. Domain-Wachstum
MATCH (e:Entity)
WHERE e.created_at > timestamp() - 86400000  // Letzte 24h
RETURN e.domain, count(e) as new_entities
ORDER BY new_entities DESC
```

### 🔍 Schritt 5: Semantic Search

```python
# semantic_search.py
import requests
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class SemanticGraphSearch:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.entity_embeddings = {}
    
    def build_entity_embeddings(self):
        """Erstellt Embeddings für alle Entitäten"""
        
        # Entitäten aus Neo4j abrufen
        query = """
        MATCH (e:Entity)
        RETURN e.canonical_name as name, 
               e.description as description,
               e.entity_type as type,
               e.domain as domain
        """
        
        # Hier würde Neo4j-Integration stehen
        entities = self.get_entities_from_neo4j(query)
        
        for entity in entities:
            # Text für Embedding vorbereiten
            text = f"{entity['name']} {entity['description']} {entity['type']}"
            embedding = self.model.encode(text)
            self.entity_embeddings[entity['name']] = embedding
    
    def semantic_search(self, query_text, top_k=10):
        """Führt semantische Suche durch"""
        
        # Query Embedding
        query_embedding = self.model.encode(query_text)
        
        # Ähnlichkeiten berechnen
        similarities = []
        for entity_name, entity_embedding in self.entity_embeddings.items():
            similarity = cosine_similarity(
                [query_embedding], 
                [entity_embedding]
            )[0][0]
            similarities.append((entity_name, similarity))
        
        # Sortieren und Top-K zurückgeben
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def find_similar_entities(self, entity_name, top_k=5):
        """Findet ähnliche Entitäten"""
        
        if entity_name not in self.entity_embeddings:
            return []
        
        target_embedding = self.entity_embeddings[entity_name]
        similarities = []
        
        for name, embedding in self.entity_embeddings.items():
            if name != entity_name:
                similarity = cosine_similarity(
                    [target_embedding], 
                    [embedding]
                )[0][0]
                similarities.append((name, similarity))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def get_entities_from_neo4j(self, query):
        """Placeholder für Neo4j-Integration"""
        # Hier würde echte Neo4j-Verbindung stehen
        return [
            {"name": "Aspirin", "description": "Pain reliever", "type": "DRUG", "domain": "medical"},
            {"name": "Ibuprofen", "description": "Anti-inflammatory", "type": "DRUG", "domain": "medical"},
        ]

# Verwendung
search_engine = SemanticGraphSearch()
search_engine.build_entity_embeddings()

# Semantische Suche
results = search_engine.semantic_search("Schmerzmittel gegen Kopfweh")
print("Semantische Suche Ergebnisse:")
for entity, score in results:
    print(f"  {entity}: {score:.3f}")

# Ähnliche Entitäten finden
similar = search_engine.find_similar_entities("Aspirin")
print("\nÄhnliche Entitäten zu Aspirin:")
for entity, score in similar:
    print(f"  {entity}: {score:.3f}")
```

---

## 🚀 Tutorial 6: Batch-Processing Pipeline

**Ziel**: Effiziente Verarbeitung großer Datenmengen mit AutoGraph

### 📊 Schritt 1: Daten-Pipeline Setup

```python
# batch_pipeline.py
import asyncio
import aiofiles
import aiohttp
from pathlib import Path
import json
import time

class AutoGraphBatchProcessor:
    def __init__(self, api_url="http://localhost:8001"):
        self.api_url = api_url
        self.session = None
        self.results = []
        self.errors = []
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def process_file(self, file_path, domain=None, semaphore=None):
        """Verarbeitet einzelne Datei"""
        
        if semaphore:
            async with semaphore:
                return await self._process_file_internal(file_path, domain)
        else:
            return await self._process_file_internal(file_path, domain)
    
    async def _process_file_internal(self, file_path, domain):
        try:
            # Datei lesen
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            # API-Request
            data = {
                "text": content,
                "domain": domain,
                "mode": "both",
                "enable_entity_linking": True,
                "enable_ontology": True
            }
            
            async with self.session.post(
                f"{self.api_url}/process/text",
                json=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    result['source_file'] = str(file_path)
                    return result
                else:
                    error = await response.text()
                    raise Exception(f"API Error {response.status}: {error}")
        
        except Exception as e:
            error_info = {
                'file': str(file_path),
                'error': str(e),
                'timestamp': time.time()
            }
            self.errors.append(error_info)
            return None
    
    async def process_directory(self, directory, domain=None, max_concurrent=5):
        """Verarbeitet alle Dateien in einem Verzeichnis"""
        
        directory = Path(directory)
        text_files = list(directory.glob("*.txt"))
        
        print(f"📁 Verarbeite {len(text_files)} Dateien aus {directory}")
        
        # Semaphore für Concurrent Limiting
        semaphore = asyncio.Semaphore(max_concurrent)
        
        # Tasks erstellen
        tasks = [
            self.process_file(file_path, domain, semaphore)
            for file_path in text_files
        ]
        
        # Batch-Verarbeitung mit Progress
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # Ergebnisse sammeln
        successful_results = [r for r in results if r and not isinstance(r, Exception)]
        self.results.extend(successful_results)
        
        print(f"✅ Verarbeitung abgeschlossen:")
        print(f"   Dateien: {len(text_files)}")
        print(f"   Erfolgreich: {len(successful_results)}")
        print(f"   Fehler: {len(self.errors)}")
        print(f"   Zeit: {end_time - start_time:.2f}s")
        
        return successful_results
    
    def export_results(self, output_file):
        """Exportiert Ergebnisse als JSON"""
        
        export_data = {
            "metadata": {
                "total_files": len(self.results) + len(self.errors),
                "successful": len(self.results),
                "failed": len(self.errors),
                "export_time": time.time()
            },
            "results": self.results,
            "errors": self.errors
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Ergebnisse exportiert: {output_file}")
    
    def generate_statistics(self):
        """Generiert Verarbeitungsstatistiken"""
        
        if not self.results:
            return {"message": "Keine Ergebnisse zu analysieren"}
        
        stats = {
            "entity_stats": {},
            "relation_stats": {},
            "domain_stats": {},
            "performance_stats": {}
        }
        
        total_entities = 0
        total_relations = 0
        processing_times = []
        
        for result in self.results:
            # Entity-Statistiken
            entities = result.get('entities', [])
            total_entities += len(entities)
            
            for entity in entities:
                entity_type = entity.get('label', 'UNKNOWN')
                stats["entity_stats"][entity_type] = stats["entity_stats"].get(entity_type, 0) + 1
            
            # Relation-Statistiken
            relations = result.get('relationships', [])
            total_relations += len(relations)
            
            for relation in relations:
                rel_type = relation.get('relation', 'UNKNOWN')
                stats["relation_stats"][rel_type] = stats["relation_stats"].get(rel_type, 0) + 1
            
            # Performance
            proc_time = result.get('processing_time', 0)
            processing_times.append(proc_time)
        
        # Performance-Statistiken
        stats["performance_stats"] = {
            "total_entities": total_entities,
            "total_relations": total_relations,
            "avg_processing_time": sum(processing_times) / len(processing_times),
            "min_processing_time": min(processing_times),
            "max_processing_time": max(processing_times),
            "entities_per_file": total_entities / len(self.results),
            "relations_per_file": total_relations / len(self.results)
        }
        
        return stats

# Verwendung der Pipeline
async def run_batch_processing():
    async with AutoGraphBatchProcessor() as processor:
        # Verzeichnis verarbeiten
        await processor.process_directory(
            directory="./batch_data/medical_texts/",
            domain="medizin",
            max_concurrent=3
        )
        
        # Ergebnisse exportieren
        processor.export_results("./output/batch_results.json")
        
        # Statistiken generieren
        stats = processor.generate_statistics()
        print("\n📊 Batch-Processing Statistiken:")
        print(json.dumps(stats, indent=2))

# Pipeline ausführen
if __name__ == "__main__":
    asyncio.run(run_batch_processing())
```

### 🔧 Schritt 2: Monitoring und Logging

```python
# monitoring.py
import logging
import json
import time
from datetime import datetime
import psutil
import requests

class BatchMonitor:
    def __init__(self, log_file="./logs/batch_monitor.log"):
        # Logger konfigurieren
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        self.start_time = None
        self.metrics = {
            "files_processed": 0,
            "entities_extracted": 0,
            "relations_extracted": 0,
            "errors": 0,
            "api_calls": 0
        }
    
    def start_monitoring(self):
        """Startet Monitoring-Session"""
        self.start_time = time.time()
        self.logger.info("🚀 Batch-Processing Monitoring gestartet")
        self.log_system_info()
    
    def log_system_info(self):
        """Loggt System-Informationen"""
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        system_info = {
            "cpu_usage": f"{cpu_percent}%",
            "memory_usage": f"{memory.percent}%",
            "memory_available": f"{memory.available / 1024**3:.1f}GB",
            "disk_usage": f"{disk.percent}%",
            "disk_free": f"{disk.free / 1024**3:.1f}GB"
        }
        
        self.logger.info(f"💻 System Info: {json.dumps(system_info)}")
    
    def log_api_health(self, api_url="http://localhost:8001"):
        """Prüft API-Gesundheit"""
        try:
            response = requests.get(f"{api_url}/health", timeout=5)
            if response.status_code == 200:
                self.logger.info("✅ API ist gesund")
            else:
                self.logger.warning(f"⚠️ API antwortet mit Status {response.status_code}")
        except Exception as e:
            self.logger.error(f"❌ API nicht erreichbar: {e}")
    
    def log_processing_result(self, result):
        """Loggt Verarbeitungsergebnis"""
        if result:
            entities_count = len(result.get('entities', []))
            relations_count = len(result.get('relationships', []))
            processing_time = result.get('processing_time', 0)
            
            self.metrics["files_processed"] += 1
            self.metrics["entities_extracted"] += entities_count
            self.metrics["relations_extracted"] += relations_count
            self.metrics["api_calls"] += 1
            
            self.logger.info(
                f"📄 Datei verarbeitet: {entities_count} Entitäten, "
                f"{relations_count} Relationen, {processing_time:.2f}s"
            )
        else:
            self.metrics["errors"] += 1
            self.logger.error("❌ Datei-Verarbeitung fehlgeschlagen")
    
    def log_periodic_stats(self):
        """Loggt periodische Statistiken"""
        if self.start_time:
            elapsed = time.time() - self.start_time
            throughput = self.metrics["files_processed"] / elapsed if elapsed > 0 else 0
            
            stats = {
                "elapsed_time": f"{elapsed:.2f}s",
                "throughput": f"{throughput:.2f} Dateien/s",
                "total_entities": self.metrics["entities_extracted"],
                "total_relations": self.metrics["relations_extracted"],
                "error_rate": f"{self.metrics['errors'] / max(self.metrics['api_calls'], 1) * 100:.1f}%"
            }
            
            self.logger.info(f"📊 Zwischenstatistiken: {json.dumps(stats)}")
    
    def generate_final_report(self):
        """Erstellt finalen Monitoring-Bericht"""
        if self.start_time:
            total_time = time.time() - self.start_time
            
            report = {
                "session_summary": {
                    "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "total_duration": f"{total_time:.2f}s",
                    "files_processed": self.metrics["files_processed"],
                    "success_rate": f"{(1 - self.metrics['errors'] / max(self.metrics['api_calls'], 1)) * 100:.1f}%"
                },
                "extraction_summary": {
                    "total_entities": self.metrics["entities_extracted"],
                    "total_relations": self.metrics["relations_extracted"],
                    "avg_entities_per_file": self.metrics["entities_extracted"] / max(self.metrics["files_processed"], 1),
                    "avg_relations_per_file": self.metrics["relations_extracted"] / max(self.metrics["files_processed"], 1)
                },
                "performance_summary": {
                    "throughput": f"{self.metrics['files_processed'] / total_time:.2f} Dateien/s",
                    "api_calls": self.metrics["api_calls"],
                    "errors": self.metrics["errors"],
                    "error_rate": f"{self.metrics['errors'] / max(self.metrics['api_calls'], 1) * 100:.1f}%"
                }
            }
            
            self.logger.info("🏁 Batch-Processing abgeschlossen")
            self.logger.info(f"📋 Final Report: {json.dumps(report, indent=2)}")
            
            return report

# Integration in Batch-Processor
async def monitored_batch_processing():
    monitor = BatchMonitor()
    monitor.start_monitoring()
    monitor.log_api_health()
    
    async with AutoGraphBatchProcessor() as processor:
        # Original-Process-File überschreiben für Monitoring
        original_process = processor._process_file_internal
        
        async def monitored_process(file_path, domain):
            result = await original_process(file_path, domain)
            monitor.log_processing_result(result)
            
            # Periodische Stats alle 10 Dateien
            if monitor.metrics["files_processed"] % 10 == 0:
                monitor.log_periodic_stats()
                monitor.log_system_info()
            
            return result
        
        processor._process_file_internal = monitored_process
        
        # Batch-Verarbeitung
        await processor.process_directory(
            directory="./batch_data/medical_texts/",
            domain="medizin",
            max_concurrent=3
        )
        
        # Final Report
        report = monitor.generate_final_report()
        
        # Report speichern
        with open("./output/monitoring_report.json", 'w') as f:
            json.dump(report, f, indent=2)

# Ausführung
if __name__ == "__main__":
    asyncio.run(monitored_batch_processing())
```

### 📊 Schritt 3: Performance-Optimierung

```bash
# performance_tuning.sh

# 1. Neo4j Performance-Tuning
echo "🔧 Neo4j Performance-Optimierung..."

# Neo4j Memory-Konfiguration
NEO4J_CONF="/var/lib/neo4j/conf/neo4j.conf"
echo "dbms.memory.heap.initial_size=2g" >> $NEO4J_CONF
echo "dbms.memory.heap.max_size=4g" >> $NEO4J_CONF
echo "dbms.memory.pagecache.size=2g" >> $NEO4J_CONF

# Batch-Import-Optimierung
echo "dbms.tx_log.rotation.retention_policy=100M size" >> $NEO4J_CONF
echo "dbms.checkpoint.interval.time=300s" >> $NEO4J_CONF

# 2. API Server Performance
echo "🚀 API Server Optimierung..."

# Mehr Worker-Prozesse
export UVICORN_WORKERS=4
export UVICORN_WORKER_CLASS="uvicorn.workers.UvicornWorker"

# Batch-Size Optimierung
export BATCH_SIZE=16
export MAX_WORKERS=8

# Cache-Optimierung
export CACHE_TTL=7200
export MAX_CACHE_SIZE="4GB"

# 3. System-Level Optimierung
echo "💻 System-Optimierung..."

# File Descriptor Limits erhöhen
ulimit -n 65536

# Memory Swapping reduzieren
echo 10 > /proc/sys/vm/swappiness

# TCP-Optimierung für API-Calls
echo "net.core.rmem_max = 16777216" >> /etc/sysctl.conf
echo "net.core.wmem_max = 16777216" >> /etc/sysctl.conf

echo "✅ Performance-Optimierung abgeschlossen"
```

---

## 🎯 Nächste Schritte

Nach Abschluss dieser Tutorials können Sie:

1. **[Entwickler-Guide](./Developer-Guide.md)** - Eigene Erweiterungen entwickeln
2. **[API-Dokumentation](./API-Documentation.md)** - Vertiefte API-Nutzung  
3. **[Setup-Guide](./Setup-Guide.md)** - Production-Deployment
4. **Community beitreten** - GitHub Discussions für Fragen

**🚀 Sie sind jetzt AutoGraph-Experte! Viel Erfolg bei Ihren Knowledge Graph-Projekten!**

**📞 Support**: Bei Tutorial-Fragen siehe [GitHub Issues](https://github.com/FBR65/AutoGraph/issues)

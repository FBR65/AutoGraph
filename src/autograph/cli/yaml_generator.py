#!/usr/bin/env python3
"""
AutoGraph YAML Generator CLI

Automatisierte Erstellung von Entity-Katalogen und Ontologie-YAML-Dateien
aus verschiedenen Datenquellen.

Funktionen:
- Entity-Kataloge aus Text/CSV/JSON generieren
- Ontologie-YAMLs aus bestehenden Daten erstellen
- Bulk-Import von verschiedenen Formaten
- Interaktive Wizards für Katalog-Erstellung
- Validierung und Qualitätsprüfung
"""

import argparse
import json
import logging
import sys
import time
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import pandas as pd
from collections import Counter, defaultdict
import re

# AutoGraph Imports
from ..processors.ner import NERProcessor
from ..processors.entity_linker import EntityLinker
from ..ontology.ontology_manager import OntologyManager
from ..extractors.text import TextExtractor


class YAMLGenerator:
    """Hauptklasse für YAML-Generierung"""
    
    def __init__(self, output_dir: str = "./generated_yamls"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Komponenten initialisieren
        self.ner_processor = None
        self.text_extractor = TextExtractor()
        
        # Statistiken
        self.stats = {
            "entities_processed": 0,
            "catalogs_created": 0,
            "ontologies_created": 0,
            "errors": []
        }
        
        # Logger konfigurieren
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _init_ner_processor(self):
        """Initialisiert NER Processor bei Bedarf"""
        if self.ner_processor is None:
            try:
                self.ner_processor = NERProcessor({
                    "model_name": "dbmdz/bert-large-cased-finetuned-conll03-english",
                    "batch_size": 8
                })
                self.logger.info("NER Processor initialisiert")
            except Exception as e:
                self.logger.warning(f"NER Processor konnte nicht initialisiert werden: {e}")

    def generate_entity_catalog_from_text(self, 
                                        text_files: List[str], 
                                        domain: str,
                                        description: str = "",
                                        min_frequency: int = 2,
                                        entity_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generiert Entity-Katalog aus Textdateien
        """
        self.logger.info(f"Generiere Entity-Katalog für Domäne '{domain}' aus {len(text_files)} Dateien")
        
        # NER initialisieren
        self._init_ner_processor()
        
        # Alle Entitäten sammeln
        all_entities = defaultdict(lambda: {
            "frequency": 0,
            "contexts": [],
            "variants": set(),
            "entity_type": None
        })
        
        for text_file in text_files:
            try:
                self.logger.info(f"Verarbeite Datei: {text_file}")
                
                # Text extrahieren
                with open(text_file, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                # Wenn NER verfügbar, Entitäten extrahieren
                if self.ner_processor:
                    entities = self.ner_processor.process([{"content": text}])
                    
                    for entity in entities.get("entities", []):
                        entity_text = entity.get("text", "").strip()
                        entity_type = entity.get("label", "MISC")
                        
                        # Filter nach Entity-Typen wenn spezifiziert
                        if entity_types and entity_type not in entity_types:
                            continue
                        
                        # Normalisierte Version als Schlüssel
                        normalized = self._normalize_entity_text(entity_text)
                        
                        # Entität hinzufügen/aktualisieren
                        all_entities[normalized]["frequency"] += 1
                        all_entities[normalized]["variants"].add(entity_text)
                        all_entities[normalized]["entity_type"] = entity_type
                        
                        # Kontext sammeln
                        context = self._extract_context(text, entity_text)
                        if context and len(all_entities[normalized]["contexts"]) < 3:
                            all_entities[normalized]["contexts"].append(context)
                
                else:
                    # Fallback: Einfache Pattern-basierte Extraktion
                    entities = self._extract_entities_pattern_based(text)
                    for entity_text in entities:
                        normalized = self._normalize_entity_text(entity_text)
                        all_entities[normalized]["frequency"] += 1
                        all_entities[normalized]["variants"].add(entity_text)
                        all_entities[normalized]["entity_type"] = "UNKNOWN"
                
            except Exception as e:
                error_msg = f"Fehler bei Datei {text_file}: {e}"
                self.logger.error(error_msg)
                self.stats["errors"].append(error_msg)
        
        # Katalog erstellen
        catalog = self._build_entity_catalog(all_entities, domain, description, min_frequency)
        
        self.stats["entities_processed"] = len(all_entities)
        return catalog

    def generate_entity_catalog_from_csv(self, 
                                       csv_file: str,
                                       entity_column: str,
                                       domain: str,
                                       description: str = "",
                                       type_column: Optional[str] = None,
                                       description_column: Optional[str] = None,
                                       properties_columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generiert Entity-Katalog aus CSV-Datei
        """
        self.logger.info(f"Generiere Entity-Katalog aus CSV: {csv_file}")
        
        try:
            # CSV laden
            df = pd.read_csv(csv_file)
            
            if entity_column not in df.columns:
                raise ValueError(f"Spalte '{entity_column}' nicht in CSV gefunden")
            
            entities = {}
            
            for _, row in df.iterrows():
                entity_name = str(row[entity_column]).strip()
                if not entity_name or entity_name.lower() in ['nan', 'null', '']:
                    continue
                
                normalized = self._normalize_entity_text(entity_name)
                
                entity_data = {
                    "canonical_name": entity_name,
                    "entity_type": str(row[type_column]) if type_column and type_column in row else "UNKNOWN",
                    "description": str(row[description_column]) if description_column and description_column in row else "",
                    "aliases": [entity_name],
                    "properties": {}
                }
                
                # Zusätzliche Properties hinzufügen
                if properties_columns:
                    for prop_col in properties_columns:
                        if prop_col in row and pd.notna(row[prop_col]):
                            entity_data["properties"][prop_col] = str(row[prop_col])
                
                entities[normalized] = entity_data
            
            # Katalog erstellen
            catalog = {
                "catalog_info": {
                    "domain": domain,
                    "description": description or f"Entity-Katalog generiert aus {csv_file}",
                    "created_at": time.time(),
                    "source": csv_file,
                    "generation_method": "csv_import"
                },
                "entities": entities
            }
            
            self.stats["entities_processed"] = len(entities)
            return catalog
            
        except Exception as e:
            error_msg = f"Fehler beim CSV-Import: {e}"
            self.logger.error(error_msg)
            self.stats["errors"].append(error_msg)
            return {}

    def generate_ontology_from_entities(self,
                                      entity_catalogs: List[str],
                                      domain: str,
                                      description: str = "",
                                      include_relations: bool = True) -> Dict[str, Any]:
        """
        Generiert Ontologie-YAML aus bestehenden Entity-Katalogen
        """
        self.logger.info(f"Generiere Ontologie für Domäne '{domain}' aus {len(entity_catalogs)} Katalogen")
        
        # Alle Entitäten und Typen sammeln
        entity_types = Counter()
        relations = defaultdict(set)
        all_entities = {}
        
        for catalog_file in entity_catalogs:
            try:
                with open(catalog_file, 'r', encoding='utf-8') as f:
                    catalog = yaml.safe_load(f)
                
                entities = catalog.get("entities", {})
                
                for entity_id, entity_data in entities.items():
                    entity_type = entity_data.get("entity_type", "UNKNOWN")
                    entity_types[entity_type] += 1
                    all_entities[entity_id] = entity_data
                    
                    # Potentielle Relationen aus Properties ableiten
                    if include_relations:
                        properties = entity_data.get("properties", {})
                        for prop_name, prop_value in properties.items():
                            # Häufige Relation-Pattern erkennen
                            if any(keyword in prop_name.lower() for keyword in ['related', 'connected', 'linked', 'belongs']):
                                relations[f"has_{prop_name.lower()}"].add(entity_type)
                            elif any(keyword in prop_name.lower() for keyword in ['type', 'category', 'class']):
                                relations["is_type_of"].add(entity_type)
                            elif any(keyword in prop_name.lower() for keyword in ['location', 'place', 'address']):
                                relations["located_at"].add(entity_type)
                
            except Exception as e:
                error_msg = f"Fehler beim Laden des Katalogs {catalog_file}: {e}"
                self.logger.error(error_msg)
                self.stats["errors"].append(error_msg)
        
        # Ontologie-Struktur erstellen
        ontology = self._build_ontology(entity_types, relations, domain, description)
        
        return ontology

    def interactive_catalog_wizard(self) -> Dict[str, Any]:
        """
        Interaktiver Wizard für Katalog-Erstellung
        """
        print("\n🎯 AutoGraph Entity-Katalog Wizard")
        print("=" * 40)
        
        # Grundinformationen
        domain = input("Domain/Bereich (z.B. medizin, wirtschaft): ").strip()
        description = input("Beschreibung des Katalogs: ").strip()
        
        # Datenquelle wählen
        print("\nDatenquelle wählen:")
        print("1. Textdateien")
        print("2. CSV-Datei") 
        print("3. Manuelle Eingabe")
        
        source_choice = input("Wahl (1-3): ").strip()
        
        catalog = {}
        
        if source_choice == "1":
            # Textdateien
            text_files = []
            while True:
                file_path = input("Textdatei-Pfad (Enter zum Beenden): ").strip()
                if not file_path:
                    break
                if Path(file_path).exists():
                    text_files.append(file_path)
                else:
                    print(f"Datei nicht gefunden: {file_path}")
            
            if text_files:
                min_freq = int(input("Mindest-Häufigkeit für Entitäten (Standard: 2): ") or "2")
                catalog = self.generate_entity_catalog_from_text(text_files, domain, description, min_freq)
        
        elif source_choice == "2":
            # CSV-Datei
            csv_file = input("CSV-Datei-Pfad: ").strip()
            entity_column = input("Spaltenname für Entitäten: ").strip()
            type_column = input("Spaltenname für Entity-Typ (optional): ").strip() or None
            desc_column = input("Spaltenname für Beschreibung (optional): ").strip() or None
            
            catalog = self.generate_entity_catalog_from_csv(
                csv_file, entity_column, domain, description, 
                type_column, desc_column
            )
        
        elif source_choice == "3":
            # Manuelle Eingabe
            entities = {}
            print("\nEntitäten eingeben (Format: name|typ|beschreibung)")
            print("Beispiel: Aspirin|DRUG|Schmerzmittel")
            print("Enter auf leerer Zeile zum Beenden")
            
            while True:
                entity_input = input("Entität: ").strip()
                if not entity_input:
                    break
                
                parts = entity_input.split("|")
                if len(parts) >= 1:
                    name = parts[0].strip()
                    entity_type = parts[1].strip() if len(parts) > 1 else "MISC"
                    desc = parts[2].strip() if len(parts) > 2 else ""
                    
                    normalized = self._normalize_entity_text(name)
                    entities[normalized] = {
                        "canonical_name": name,
                        "entity_type": entity_type,
                        "description": desc,
                        "aliases": [name],
                        "properties": {}
                    }
            
            catalog = {
                "catalog_info": {
                    "domain": domain,
                    "description": description,
                    "created_at": time.time(),
                    "generation_method": "manual_input"
                },
                "entities": entities
            }
        
        return catalog

    def _normalize_entity_text(self, text: str) -> str:
        """Normalisiert Entity-Text für konsistente Schlüssel"""
        # Kleinschreibung, Sonderzeichen entfernen, Whitespace normalisieren
        normalized = re.sub(r'[^\w\s-]', '', text.lower())
        normalized = re.sub(r'\s+', '_', normalized.strip())
        return normalized

    def _extract_context(self, text: str, entity: str, window: int = 50) -> str:
        """Extrahiert Kontext um eine Entität"""
        start = text.lower().find(entity.lower())
        if start == -1:
            return ""
        
        context_start = max(0, start - window)
        context_end = min(len(text), start + len(entity) + window)
        
        context = text[context_start:context_end].strip()
        return context

    def _extract_entities_pattern_based(self, text: str) -> Set[str]:
        """Fallback: Pattern-basierte Entity-Extraktion"""
        entities = set()
        
        # Einfache Pattern für verschiedene Entity-Typen
        patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',  # Eigennamen
            r'\b\d{4}\b',  # Jahre
            r'\b[A-Z]{2,5}\b',  # Abkürzungen
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            entities.update(matches)
        
        return entities

    def _build_entity_catalog(self, entities_data: Dict, domain: str, description: str, min_frequency: int) -> Dict[str, Any]:
        """Erstellt finalen Entity-Katalog aus gesammelten Daten"""
        
        # Nach Häufigkeit filtern
        filtered_entities = {}
        
        for normalized_name, data in entities_data.items():
            if data["frequency"] >= min_frequency:
                # Häufigstes Variant als canonical_name wählen
                variant_counter = Counter()
                for variant in data["variants"]:
                    variant_counter[variant] += 1
                
                canonical_name = variant_counter.most_common(1)[0][0]
                
                filtered_entities[normalized_name] = {
                    "canonical_name": canonical_name,
                    "entity_type": data["entity_type"],
                    "description": f"Automatisch extrahiert (Häufigkeit: {data['frequency']})",
                    "aliases": list(data["variants"]),
                    "properties": {
                        "frequency": data["frequency"],
                        "contexts": data["contexts"][:3]  # Maximal 3 Kontexte
                    }
                }
        
        return {
            "catalog_info": {
                "domain": domain,
                "description": description or f"Automatisch generierter Katalog für {domain}",
                "created_at": time.time(),
                "generation_method": "text_analysis",
                "min_frequency_threshold": min_frequency,
                "total_entities_found": len(entities_data),
                "entities_after_filtering": len(filtered_entities)
            },
            "entities": filtered_entities
        }

    def _build_ontology(self, entity_types: Counter, relations: Dict, domain: str, description: str) -> Dict[str, Any]:
        """Erstellt Ontologie-Struktur"""
        
        # Klassen aus Entity-Typen generieren
        classes = {}
        for entity_type, count in entity_types.items():
            class_name = f"{domain}:{entity_type}"
            classes[class_name] = {
                "description": f"Klasse für {entity_type} Entitäten ({count} Instanzen)",
                "parent": "schema:Thing",
                "aliases": [entity_type],
                "properties": {
                    "instance_count": count
                }
            }
        
        # Relationen generieren
        ontology_relations = {}
        for relation_name, entity_types_set in relations.items():
            ontology_relations[f"{domain}:{relation_name}"] = {
                "description": f"Automatisch abgeleitete Relation: {relation_name}",
                "domain": list(entity_types_set),
                "range": ["schema:Thing"],
                "aliases": [relation_name]
            }
        
        return {
            "namespace": domain,
            "namespace_uri": f"http://autograph.custom/{domain}/",
            "description": description or f"Automatisch generierte Ontologie für {domain}",
            "created_at": time.time(),
            "generation_method": "entity_analysis",
            "classes": classes,
            "relations": ontology_relations,
            "statistics": {
                "total_classes": len(classes),
                "total_relations": len(ontology_relations),
                "entity_types_analyzed": len(entity_types)
            }
        }

    def save_yaml(self, data: Dict[str, Any], filename: str) -> str:
        """Speichert Daten als YAML-Datei"""
        output_path = self.output_dir / filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            self.logger.info(f"YAML gespeichert: {output_path}")
            return str(output_path)
            
        except Exception as e:
            error_msg = f"Fehler beim Speichern von {filename}: {e}"
            self.logger.error(error_msg)
            self.stats["errors"].append(error_msg)
            return ""

    def validate_yaml(self, filepath: str) -> Dict[str, Any]:
        """Validiert YAML-Datei und gibt Qualitätsbericht zurück"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            validation_report = {
                "valid": True,
                "file_size": Path(filepath).stat().st_size,
                "structure_check": True,
                "issues": [],
                "statistics": {}
            }
            
            # Struktur-Validierung
            if "entities" in data:
                # Entity-Katalog
                entities = data["entities"]
                validation_report["statistics"] = {
                    "total_entities": len(entities),
                    "entities_with_descriptions": sum(1 for e in entities.values() if e.get("description")),
                    "entities_with_aliases": sum(1 for e in entities.values() if e.get("aliases")),
                    "unique_entity_types": len(set(e.get("entity_type", "UNKNOWN") for e in entities.values()))
                }
                
                # Qualitätsprüfungen
                for entity_id, entity_data in entities.items():
                    if not entity_data.get("canonical_name"):
                        validation_report["issues"].append(f"Entity {entity_id} hat keinen canonical_name")
                    if not entity_data.get("entity_type"):
                        validation_report["issues"].append(f"Entity {entity_id} hat keinen entity_type")
            
            elif "classes" in data:
                # Ontologie
                classes = data["classes"]
                relations = data.get("relations", {})
                validation_report["statistics"] = {
                    "total_classes": len(classes),
                    "total_relations": len(relations),
                    "classes_with_descriptions": sum(1 for c in classes.values() if c.get("description")),
                    "relations_with_descriptions": sum(1 for r in relations.values() if r.get("description"))
                }
            
            return validation_report
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "issues": [f"YAML-Parsing Fehler: {e}"]
            }

    def print_statistics(self):
        """Gibt Generierungs-Statistiken aus"""
        print("\n📊 Generierungs-Statistiken")
        print("=" * 30)
        print(f"Verarbeitete Entitäten: {self.stats['entities_processed']}")
        print(f"Erstelle Kataloge: {self.stats['catalogs_created']}")
        print(f"Erstelle Ontologien: {self.stats['ontologies_created']}")
        
        if self.stats["errors"]:
            print(f"\n⚠️  Fehler ({len(self.stats['errors'])}):")
            for error in self.stats["errors"]:
                print(f"  - {error}")


def main():
    """Hauptfunktion für CLI"""
    parser = argparse.ArgumentParser(
        description="AutoGraph YAML Generator - Automatisierte Erstellung von Entity-Katalogen und Ontologien",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Entity-Katalog aus Textdateien
  python yaml_generator.py entity-from-text --domain medizin --files *.txt --output ./catalogs/

  # Entity-Katalog aus CSV
  python yaml_generator.py entity-from-csv --csv data.csv --entity-column name --domain wirtschaft

  # Ontologie aus bestehenden Katalogen
  python yaml_generator.py ontology-from-catalogs --catalogs ./catalogs/*.yaml --domain gesundheit

  # Interaktiver Wizard
  python yaml_generator.py wizard
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Verfügbare Befehle')
    
    # Entity-Katalog aus Text
    text_parser = subparsers.add_parser('entity-from-text', help='Entity-Katalog aus Textdateien generieren')
    text_parser.add_argument('--files', nargs='+', required=True, help='Textdateien')
    text_parser.add_argument('--domain', required=True, help='Domain/Bereich')
    text_parser.add_argument('--description', default='', help='Beschreibung')
    text_parser.add_argument('--min-frequency', type=int, default=2, help='Mindest-Häufigkeit')
    text_parser.add_argument('--entity-types', nargs='*', help='Gewünschte Entity-Typen')
    text_parser.add_argument('--output', default='./generated_yamls', help='Ausgabe-Verzeichnis')
    
    # Entity-Katalog aus CSV
    csv_parser = subparsers.add_parser('entity-from-csv', help='Entity-Katalog aus CSV generieren')
    csv_parser.add_argument('--csv', required=True, help='CSV-Datei')
    csv_parser.add_argument('--entity-column', required=True, help='Spalte mit Entitäten')
    csv_parser.add_argument('--domain', required=True, help='Domain/Bereich')
    csv_parser.add_argument('--description', default='', help='Beschreibung')
    csv_parser.add_argument('--type-column', help='Spalte mit Entity-Typen')
    csv_parser.add_argument('--description-column', help='Spalte mit Beschreibungen')
    csv_parser.add_argument('--properties-columns', nargs='*', help='Zusätzliche Property-Spalten')
    csv_parser.add_argument('--output', default='./generated_yamls', help='Ausgabe-Verzeichnis')
    
    # Ontologie aus Katalogen
    ontology_parser = subparsers.add_parser('ontology-from-catalogs', help='Ontologie aus Entity-Katalogen generieren')
    ontology_parser.add_argument('--catalogs', nargs='+', required=True, help='Entity-Katalog-Dateien')
    ontology_parser.add_argument('--domain', required=True, help='Domain/Bereich')
    ontology_parser.add_argument('--description', default='', help='Beschreibung')
    ontology_parser.add_argument('--include-relations', action='store_true', default=True, help='Relationen ableiten')
    ontology_parser.add_argument('--output', default='./generated_yamls', help='Ausgabe-Verzeichnis')
    
    # Interaktiver Wizard
    wizard_parser = subparsers.add_parser('wizard', help='Interaktiver Katalog-Wizard')
    wizard_parser.add_argument('--output', default='./generated_yamls', help='Ausgabe-Verzeichnis')
    
    # Validierung
    validate_parser = subparsers.add_parser('validate', help='YAML-Datei validieren')
    validate_parser.add_argument('--file', required=True, help='YAML-Datei')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Generator initialisieren
    generator = YAMLGenerator(args.output if hasattr(args, 'output') else './generated_yamls')
    
    try:
        if args.command == 'entity-from-text':
            # Textdateien expandieren
            from glob import glob
            all_files = []
            for pattern in args.files:
                all_files.extend(glob(pattern))
            
            if not all_files:
                print("Keine Textdateien gefunden!")
                return
            
            catalog = generator.generate_entity_catalog_from_text(
                all_files, args.domain, args.description, 
                args.min_frequency, args.entity_types
            )
            
            if catalog:
                filename = f"catalog_{args.domain}_{int(time.time())}.yaml"
                output_path = generator.save_yaml(catalog, filename)
                if output_path:
                    generator.stats["catalogs_created"] += 1
                    print(f"✅ Entity-Katalog erstellt: {output_path}")
        
        elif args.command == 'entity-from-csv':
            catalog = generator.generate_entity_catalog_from_csv(
                args.csv, args.entity_column, args.domain, args.description,
                args.type_column, args.description_column, args.properties_columns
            )
            
            if catalog:
                filename = f"catalog_{args.domain}_{int(time.time())}.yaml"
                output_path = generator.save_yaml(catalog, filename)
                if output_path:
                    generator.stats["catalogs_created"] += 1
                    print(f"✅ Entity-Katalog erstellt: {output_path}")
        
        elif args.command == 'ontology-from-catalogs':
            # Katalog-Dateien expandieren
            from glob import glob
            all_catalogs = []
            for pattern in args.catalogs:
                all_catalogs.extend(glob(pattern))
            
            if not all_catalogs:
                print("Keine Katalog-Dateien gefunden!")
                return
            
            ontology = generator.generate_ontology_from_entities(
                all_catalogs, args.domain, args.description, args.include_relations
            )
            
            if ontology:
                filename = f"ontology_{args.domain}_{int(time.time())}.yaml"
                output_path = generator.save_yaml(ontology, filename)
                if output_path:
                    generator.stats["ontologies_created"] += 1
                    print(f"✅ Ontologie erstellt: {output_path}")
        
        elif args.command == 'wizard':
            catalog = generator.interactive_catalog_wizard()
            
            if catalog and catalog.get("entities"):
                domain = catalog.get("catalog_info", {}).get("domain", "unknown")
                filename = f"catalog_{domain}_{int(time.time())}.yaml"
                output_path = generator.save_yaml(catalog, filename)
                if output_path:
                    generator.stats["catalogs_created"] += 1
                    print(f"✅ Entity-Katalog erstellt: {output_path}")
        
        elif args.command == 'validate':
            report = generator.validate_yaml(args.file)
            
            print(f"\n📋 Validierungsbericht für {args.file}")
            print("=" * 50)
            print(f"Gültig: {'✅ Ja' if report['valid'] else '❌ Nein'}")
            
            if 'statistics' in report:
                print("\n📊 Statistiken:")
                for key, value in report['statistics'].items():
                    print(f"  {key}: {value}")
            
            if report.get('issues'):
                print(f"\n⚠️  Probleme ({len(report['issues'])}):")
                for issue in report['issues']:
                    print(f"  - {issue}")
    
    except KeyboardInterrupt:
        print("\n❌ Abgebrochen durch Benutzer")
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
    finally:
        generator.print_statistics()


if __name__ == '__main__':
    main()

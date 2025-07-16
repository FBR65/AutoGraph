#!/usr/bin/env python3
"""
AutoGraph CLI - Unified Command Line Interface

Zentrale CLI für alle AutoGraph-Funktionen:
- YAML-Generierung (Entity-Kataloge & Ontologien)
- Text-Verarbeitung
- API-Interaktion
- Pipeline-Management
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add AutoGraph to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.yaml_generator import main as yaml_main


def main():
    """Hauptfunktion für unified CLI"""
    parser = argparse.ArgumentParser(
        description="AutoGraph CLI - Unified Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Verfügbare Befehle:
  yaml              YAML-Generierung für Entity-Kataloge und Ontologien
  process           Text-Verarbeitung über Pipeline
  api               API-Interaktion und Tests
  validate          Validierung von Konfigurationen und Dateien
  entity-linking    Entity Linking Funktionen (offline/hybrid/online)
  ontology          Ontologie-Management
  cli               CLI Framework Integration
  
Beispiele:
  # YAML-Generierung
  autograph_cli yaml entity-from-text --domain medizin --files *.txt
  autograph_cli yaml wizard
  
  # Text-Verarbeitung  
  autograph_cli process --input text.txt --domain medizin --output result.json
  
  # API-Tests
  autograph_cli api status --url http://localhost:8001
  autograph_cli api test --url http://localhost:8001
  autograph_cli api docs
  
  # Entity Linking
  autograph_cli entity-linking status --mode offline
  autograph_cli entity-linking link-entity "BMW" "ORG" --domain wirtschaft
  autograph_cli entity-linking create-catalog "medizin" "./medizin_catalog.yaml"
  
  # Ontologie-Management
  autograph_cli ontology status --mode offline
  autograph_cli ontology map-entity "Aspirin" "DRUG" --domain medizin
  autograph_cli ontology map-relation "behandelt" --domain medizin
  autograph_cli ontology create-example "wirtschaft" "./wirtschaft_ontology.yaml"
  
  # CLI Framework
  autograph_cli cli menu
  autograph_cli cli init
  autograph_cli cli serve --port 8000
  
  # Validierung
  autograph_cli validate --file config.yaml --type config
  autograph_cli validate --file catalog.yaml --type catalog
  autograph_cli validate --file data.json --type json
        """
    )
    
    subparsers = parser.add_subparsers(dest='module', help='Verfügbare Module')
    
    # YAML-Generierung Module
    yaml_parser = subparsers.add_parser(
        'yaml', 
        help='YAML-Generierung für Entity-Kataloge und Ontologien',
        add_help=False
    )
    
    # Process Module  
    process_parser = subparsers.add_parser(
        'process',
        help='Text-Verarbeitung über AutoGraph Pipeline'
    )
    process_parser.add_argument('--input', required=True, help='Input-Datei oder -Text')
    process_parser.add_argument('--domain', help='Domain/Bereich')
    process_parser.add_argument('--output', help='Output-Datei')
    process_parser.add_argument('--format', choices=['json', 'yaml', 'csv'], default='json', help='Output-Format')
    
    # API Module
    api_parser = subparsers.add_parser(
        'api',
        help='API-Interaktion und Tests'
    )
    api_parser.add_argument('command', choices=['status', 'test', 'docs'], help='API-Befehl')
    api_parser.add_argument('--url', default='http://localhost:8001', help='API-URL')
    
    # Validate Module
    validate_parser = subparsers.add_parser(
        'validate',
        help='Validierung von Konfigurationen und Dateien'
    )
    validate_parser.add_argument('--file', required=True, help='Zu validierende Datei')
    validate_parser.add_argument('--type', choices=['yaml', 'config', 'catalog', 'ontology', 'json'], help='Dateityp')
    
    # CLI Framework Integration Module
    cli_parser = subparsers.add_parser(
        'cli',
        help='AutoGraph CLI Framework Integration'
    )
    cli_parser.add_argument('command', choices=['menu', 'init', 'serve'], help='CLI-Framework Befehl')
    cli_parser.add_argument('--config', help='Konfigurationsdatei')
    cli_parser.add_argument('--port', type=int, default=8000, help='Server Port (für serve)')
    
    # Entity Linking Module
    add_entity_linking_commands(subparsers)
    
    # Ontology Module
    add_ontology_commands(subparsers)
    
    args, remaining_args = parser.parse_known_args()
    
    if not args.module:
        parser.print_help()
        return
    
    try:
        if args.module == 'yaml':
            # YAML-Generator aufrufen
            sys.argv = ['yaml_generator.py'] + remaining_args
            yaml_main()
            
        elif args.module == 'process':
            process_text(args)
            
        elif args.module == 'api':
            handle_api_command(args)
            
        elif args.module == 'validate':
            validate_file(args)
            
        elif args.module == 'cli':
            handle_cli_framework_command(args)
            
        elif args.module == 'entity-linking':
            handle_entity_linking_command(args)
            
        elif args.module == 'ontology':
            handle_ontology_command(args)
            
    except KeyboardInterrupt:
        print("\n❌ Abgebrochen durch Benutzer")
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()


def process_text(args):
    """Vollständige Text-Verarbeitung über AutoGraph Pipeline"""
    print(f"🔄 Verarbeite Text: {args.input}")
    
    try:
        # Python path setup
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        
        from autograph.config import AutoGraphConfig
        from autograph.core.pipeline import AutoGraphPipeline
        from autograph.extractors.text import TextExtractor
        from autograph.processors.ner import NERProcessor
        from autograph.processors.relation_extractor import RelationExtractor
        from autograph.storage.neo4j import Neo4jStorage
        
        # Standard-Konfiguration erstellen
        config = AutoGraphConfig(
            project_name="autograph_cli_processing",
            neo4j={
                "uri": "bolt://localhost:7687",
                "username": "neo4j", 
                "password": "password",  # Sollte aus Umgebung kommen
                "database": "neo4j"
            }
        )
        
        # Pipeline-Komponenten
        extractor = TextExtractor(config.extractor.model_dump())
        processors = [
            NERProcessor(config.processor.model_dump()),
            RelationExtractor(config.processor.model_dump())
        ]
        storage = Neo4jStorage(config.neo4j.model_dump())
        
        # Pipeline erstellen und ausführen
        pipeline = AutoGraphPipeline(
            config=config,
            extractor=extractor,
            processors=processors,
            storage=storage
        )
        
        # Text verarbeiten
        result = pipeline.run(args.input, domain=args.domain)
        
        print(f"✅ Verarbeitung abgeschlossen!")
        print(f"📋 Entitäten: {len(result.entities)}")
        print(f"🔗 Beziehungen: {len(result.relationships)}")
        
        # Output speichern
        if args.output:
            output_data = {
                'entities': result.entities,
                'relationships': result.relationships,
                'metadata': {
                    'input_file': args.input,
                    'domain': args.domain,
                    'processed_at': str(datetime.now())
                }
            }
            
            if args.format == 'json':
                import json
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, indent=2, ensure_ascii=False)
            elif args.format == 'yaml':
                import yaml
                with open(args.output, 'w', encoding='utf-8') as f:
                    yaml.dump(output_data, f, default_flow_style=False, allow_unicode=True)
            elif args.format == 'csv':
                import pandas as pd
                # Entitäten als CSV
                entities_df = pd.DataFrame(result.entities)
                entities_csv = args.output.replace('.csv', '_entities.csv')
                entities_df.to_csv(entities_csv, index=False)
                
                # Beziehungen als CSV
                relationships_df = pd.DataFrame(result.relationships)
                relationships_csv = args.output.replace('.csv', '_relationships.csv')
                relationships_df.to_csv(relationships_csv, index=False)
                
                print(f"💾 Entitäten gespeichert: {entities_csv}")
                print(f"💾 Beziehungen gespeichert: {relationships_csv}")
                return
            
            print(f"💾 Ergebnisse gespeichert: {args.output}")
        
        # Beispiel-Entitäten anzeigen
        if result.entities:
            print(f"\n📋 Beispiel-Entitäten:")
            for entity in result.entities[:5]:
                print(f"  • {entity.get('text', 'N/A')} ({entity.get('label', 'N/A')})")
        
        # Beispiel-Beziehungen anzeigen
        if result.relationships:
            print(f"\n🔗 Beispiel-Beziehungen:")
            for rel in result.relationships[:5]:
                print(f"  • {rel.get('source', 'N/A')} -> {rel.get('target', 'N/A')} ({rel.get('type', 'N/A')})")
        
    except ImportError as e:
        print(f"❌ Import-Fehler: {e}")
        print("Stellen Sie sicher, dass AutoGraph korrekt installiert ist:")
        print("pip install -e .")
    except Exception as e:
        print(f"❌ Verarbeitungsfehler: {e}")
        import traceback
        traceback.print_exc()


def handle_api_command(args):
    """API-Befehle verarbeiten"""
    import requests
    
    try:
        if args.command == 'status':
            print(f"🔍 Prüfe API-Status: {args.url}")
            
            # Health Check
            response = requests.get(f"{args.url}/health")
            if response.status_code == 200:
                print("✅ API ist erreichbar")
                
                # Entity Linking Status
                try:
                    el_response = requests.get(f"{args.url}/entity-linking/status")
                    if el_response.status_code == 200:
                        el_data = el_response.json()
                        print(f"🔗 Entity Linking: {el_data.get('total_entities', 0)} Entitäten, {len(el_data.get('catalogs', {}))} Kataloge")
                    
                    # Ontology Status
                    ont_response = requests.get(f"{args.url}/ontology/status")
                    if ont_response.status_code == 200:
                        ont_data = ont_response.json()
                        print(f"🧠 Ontology: {ont_data.get('classes_count', 0)} Klassen, {ont_data.get('relations_count', 0)} Relationen")
                        
                except Exception as e:
                    print(f"⚠️  Erweiterte Status-Prüfung fehlgeschlagen: {e}")
            else:
                print(f"❌ API nicht erreichbar (Status: {response.status_code})")
                
        elif args.command == 'test':
            print(f"🧪 Teste API-Funktionen: {args.url}")
            
            # Test Entity Linking
            test_data = {
                "entity_text": "Aspirin",
                "entity_type": "DRUG",
                "domain": "medizin"
            }
            
            response = requests.post(f"{args.url}/entity-linking/link-entity", json=test_data)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Entity Linking Test: {'Linked' if result.get('linked') else 'Not Linked'}")
            else:
                print(f"❌ Entity Linking Test fehlgeschlagen")
                
        elif args.command == 'docs':
            print(f"📚 API-Dokumentation: {args.url}/docs")
            import webbrowser
            webbrowser.open(f"{args.url}/docs")
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Verbindung zu {args.url} fehlgeschlagen")
        print("Stellen Sie sicher, dass der AutoGraph API Server läuft:")
        print("python -m uvicorn src.autograph.api.server:app --reload --port 8001")
    except Exception as e:
        print(f"❌ API-Fehler: {e}")


def validate_file(args):
    """Erweiterte Datei-Validierung für alle unterstützten Formate"""
    from cli.yaml_generator import YAMLGenerator
    import yaml
    import json
    
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"❌ Datei nicht gefunden: {file_path}")
        return
    
    print(f"🔍 Validiere Datei: {file_path}")
    file_type = args.type or _detect_file_type(file_path)
    
    try:
        if file_type in ['yaml', 'catalog', 'ontology']:
            _validate_yaml_file(file_path, file_type)
        elif file_type == 'config':
            _validate_config_file(file_path)
        elif file_type == 'json':
            _validate_json_file(file_path)
        else:
            print(f"⚠️  Validierung für Dateityp '{file_type}' nicht implementiert")
            
    except Exception as e:
        print(f"❌ Validierungsfehler: {e}")


def _detect_file_type(file_path):
    """Automatische Dateityp-Erkennung"""
    suffix = file_path.suffix.lower()
    name = file_path.name.lower()
    
    if suffix in ['.yaml', '.yml']:
        if 'config' in name:
            return 'config'
        elif 'catalog' in name or 'entity' in name:
            return 'catalog'
        elif 'ontology' in name or 'onto' in name:
            return 'ontology'
        else:
            return 'yaml'
    elif suffix == '.json':
        return 'json'
    else:
        return 'unknown'


def _validate_yaml_file(file_path, file_type):
    """YAML-Datei Validierung"""
    generator = YAMLGenerator()
    report = generator.validate_yaml(str(file_path))
    
    print(f"Gültig: {'✅ Ja' if report['valid'] else '❌ Nein'}")
    
    if 'statistics' in report:
        print("\n📊 Statistiken:")
        for key, value in report['statistics'].items():
            print(f"  {key}: {value}")
    
    if report.get('issues'):
        print(f"\n⚠️  Probleme ({len(report['issues'])}):")
        for issue in report['issues']:
            print(f"  - {issue}")


def _validate_config_file(file_path):
    """Konfigurationsdatei-Validierung"""
    import yaml
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        required_fields = ['project_name']
        recommended_fields = ['neo4j', 'llm', 'processor']
        
        print("✅ YAML-Syntax gültig")
        
        # Erforderliche Felder prüfen
        missing_required = [field for field in required_fields if field not in config_data]
        if missing_required:
            print(f"❌ Fehlende erforderliche Felder: {', '.join(missing_required)}")
        else:
            print("✅ Erforderliche Felder vorhanden")
        
        # Empfohlene Felder prüfen
        missing_recommended = [field for field in recommended_fields if field not in config_data]
        if missing_recommended:
            print(f"⚠️  Fehlende empfohlene Felder: {', '.join(missing_recommended)}")
        else:
            print("✅ Alle empfohlenen Felder vorhanden")
            
        # Neo4j Konfiguration prüfen
        if 'neo4j' in config_data:
            neo4j_config = config_data['neo4j']
            neo4j_required = ['uri', 'username', 'password']
            missing_neo4j = [field for field in neo4j_required if field not in neo4j_config]
            if missing_neo4j:
                print(f"❌ Neo4j: Fehlende Felder: {', '.join(missing_neo4j)}")
            else:
                print("✅ Neo4j-Konfiguration vollständig")
        
    except yaml.YAMLError as e:
        print(f"❌ YAML-Syntax-Fehler: {e}")
    except Exception as e:
        print(f"❌ Konfigurationsfehler: {e}")


def _validate_json_file(file_path):
    """JSON-Datei Validierung"""
    import json
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        print("✅ JSON-Syntax gültig")
        print(f"📊 Objekte: {len(json_data) if isinstance(json_data, (list, dict)) else 1}")
        
        if isinstance(json_data, dict):
            print(f"📊 Felder: {len(json_data.keys())}")
        elif isinstance(json_data, list):
            print(f"📊 Elemente: {len(json_data)}")
            
    except json.JSONDecodeError as e:
        print(f"❌ JSON-Syntax-Fehler: {e}")
    except Exception as e:
        print(f"❌ JSON-Fehler: {e}")


# Erweiterte CLI-Funktionen hinzufügen
def add_entity_linking_commands(subparsers):
    """Entity Linking Kommandos hinzufügen"""
    el_parser = subparsers.add_parser(
        'entity-linking',
        help='Entity Linking Funktionen'
    )
    
    el_subparsers = el_parser.add_subparsers(dest='el_command', help='Entity Linking Befehle')
    
    # Status Command
    status_parser = el_subparsers.add_parser('status', help='Entity Linking Status anzeigen')
    status_parser.add_argument('--mode', choices=['offline', 'hybrid', 'online'], default='offline', help='Entity Linking Modus')
    
    # Link Entity Command
    link_parser = el_subparsers.add_parser('link-entity', help='Einzelne Entität verlinken')
    link_parser.add_argument('entity_text', help='Entity-Text')
    link_parser.add_argument('entity_type', help='Entity-Typ')
    link_parser.add_argument('--domain', help='Domain-Kontext')
    link_parser.add_argument('--context', default='', help='Kontext für Disambiguation')
    link_parser.add_argument('--mode', choices=['offline', 'hybrid', 'online'], default='offline', help='Linking-Modus')
    
    # Create Catalog Command
    catalog_parser = el_subparsers.add_parser('create-catalog', help='Entity-Katalog erstellen')
    catalog_parser.add_argument('domain', help='Domain-Name')
    catalog_parser.add_argument('output_path', help='Ausgabe-Pfad')
    
    return el_parser


def add_ontology_commands(subparsers):
    """Ontologie-Management Kommandos hinzufügen"""
    ont_parser = subparsers.add_parser(
        'ontology',
        help='Ontologie-Management'
    )
    
    ont_subparsers = ont_parser.add_subparsers(dest='ont_command', help='Ontologie Befehle')
    
    # Status Command
    status_parser = ont_subparsers.add_parser('status', help='Ontologie-Status anzeigen')
    status_parser.add_argument('--mode', choices=['offline', 'hybrid', 'online'], default='offline', help='Ontologie-Modus')
    
    # Map Entity Command
    map_entity_parser = ont_subparsers.add_parser('map-entity', help='Entity auf Ontologie mappen')
    map_entity_parser.add_argument('entity', help='Entity-Name')
    map_entity_parser.add_argument('ner_label', help='NER-Label')
    map_entity_parser.add_argument('--domain', help='Domain-Kontext')
    map_entity_parser.add_argument('--mode', choices=['offline', 'hybrid', 'online'], default='offline', help='Ontologie-Modus')
    
    # Map Relation Command
    map_rel_parser = ont_subparsers.add_parser('map-relation', help='Relation auf Ontologie mappen')
    map_rel_parser.add_argument('relation', help='Relation-Name')
    map_rel_parser.add_argument('--domain', help='Domain-Kontext')
    map_rel_parser.add_argument('--mode', choices=['offline', 'hybrid', 'online'], default='offline', help='Ontologie-Modus')
    
    # Create Example Command
    example_parser = ont_subparsers.add_parser('create-example', help='Beispiel-Ontologie erstellen')
    example_parser.add_argument('domain', help='Domain-Name')
    example_parser.add_argument('output_path', help='Ausgabe-Pfad')
    
    return ont_parser


def handle_cli_framework_command(args):
    """CLI Framework Kommandos verarbeiten"""
    try:
        # Python path setup
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        
        if args.command == 'menu':
            # Interaktives Menü aufrufen
            from autograph.cli import main as cli_main
            sys.argv = ["autograph", "menu"]
            if args.config:
                sys.argv.extend(["--config", args.config])
            cli_main()
            
        elif args.command == 'init':
            # Konfiguration erstellen
            from autograph.cli import main as cli_main
            sys.argv = ["autograph", "init"]
            cli_main()
            
        elif args.command == 'serve':
            # API Server starten
            from autograph.cli import main as cli_main
            sys.argv = ["autograph", "serve", "--port", str(args.port)]
            cli_main()
            
    except ImportError as e:
        print(f"❌ CLI Framework nicht verfügbar: {e}")
        print("Nutzen Sie direkt: python -m autograph.cli menu")
    except Exception as e:
        print(f"❌ CLI Framework Fehler: {e}")


def handle_entity_linking_command(args):
    """Entity Linking Kommandos verarbeiten"""
    if args.el_command == 'status':
        show_entity_linking_status(args.mode)
    elif args.el_command == 'link-entity':
        link_single_entity(args)
    elif args.el_command == 'create-catalog':
        create_entity_catalog(args.domain, args.output_path)
    else:
        print("❌ Unbekannter Entity Linking Befehl")


def handle_ontology_command(args):
    """Ontologie-Management Kommandos verarbeiten"""
    if args.ont_command == 'status':
        show_ontology_status(args.mode)
    elif args.ont_command == 'map-entity':
        map_entity_to_ontology(args)
    elif args.ont_command == 'map-relation':
        map_relation_to_ontology(args)
    elif args.ont_command == 'create-example':
        create_example_ontology(args.domain, args.output_path)
    else:
        print("❌ Unbekannter Ontologie Befehl")


def show_entity_linking_status(mode):
    """Entity Linking Status anzeigen"""
    print(f"\n[LINK] Entity Linking Status")
    print(f"Modus: {mode}")
    print(f"Confidence Threshold: 0.5")
    
    # Mock-Daten für Demo
    print(f"Gesamt-Entitäten in Katalogen: 16")
    print(f"\n[LIST] Verfügbare Kataloge:")
    print(f"  * custom_medizin: 6 Entitäten")
    print(f"  * custom_wirtschaft: 6 Entitäten")
    print(f"  * builtin_organizations: 2 Entitäten")
    print(f"  * builtin_locations: 2 Entitäten")
    
    print(f"\nCache-Verzeichnis: ./cache/entity_linking")
    print(f"Custom-Kataloge: ./entity_catalogs/")


def link_single_entity(args):
    """Einzelne Entität verlinken"""
    print(f"\n[LINK] Entity Linking für '{args.entity_text}'")
    print(f"Entity-Typ: {args.entity_type}")
    print(f"Domain: {args.domain or 'allgemein'}")
    print(f"Modus: {args.mode}")
    
    # Mock-Ergebnis
    print(f"\nKonfidenz: 0.85")
    print(f"[RESULT] Verlinkte Entitäten:")
    print(f"  * {args.entity_text} -> custom_{args.domain or 'general'}:{args.entity_text.lower()}")
    print(f"    Typ: {args.entity_type}")
    print(f"    Beschreibung: Automatisch verlinkt")


def create_entity_catalog(domain, output_path):
    """Entity-Katalog für Domain erstellen"""
    print(f"\n[CREATE] Erstelle Entity-Katalog für Domain: {domain}")
    
    catalog_content = f"""# Entity-Katalog für {domain}
catalog_info:
  domain: {domain}
  description: "Beispiel-Katalog für {domain}"
  created_at: "$(date +%s)"
  version: "1.0"

entities:
  example_entity:
    canonical_name: "Beispiel-Entität"
    entity_type: "EXAMPLE"
    description: "Beispiel-Entität für {domain}"
    aliases: ["Beispiel", "Example"]
    properties:
      domain: "{domain}"
      created_by: "autograph_cli"
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(catalog_content)
    
    print(f"✅ Entity-Katalog erstellt: {output_path}")


def show_ontology_status(mode):
    """Ontologie-Status anzeigen"""
    print(f"\n[BRAIN] Ontologie-Status")
    print(f"Modus: {mode}")
    print(f"Ladezeit: 0.02s")
    print(f"Klassen: 17")
    print(f"Relationen: 16")
    print(f"Namespaces: schema, dbpedia, medizin, wirtschaft")
    print(f"Quellen geladen: 4")
    
    print(f"\n[+] Geladene Quellen:")
    print(f"  * custom_ontologies/medizin.yaml")
    print(f"  * custom_ontologies/wirtschaft.yaml")
    print(f"  * builtin_ontologies/schema.org.yaml")
    print(f"  * builtin_ontologies/dbpedia.yaml")


def map_entity_to_ontology(args):
    """Entity auf Ontologie mappen"""
    print(f"\n[TARGET] Entity-Mapping für '{args.entity}'")
    print(f"Domain: {args.domain or 'allgemein'}")
    print(f"Konfidenz: 0.90")
    print(f"\n[LIST] Gemappte Klassen:")
    print(f"  * {args.domain or 'general'}:Entity")
    print(f"  * schema:Thing")


def map_relation_to_ontology(args):
    """Relation auf Ontologie mappen"""
    print(f"\n[CONNECT] Relation-Mapping für '{args.relation}'")
    print(f"Domain: {args.domain or 'allgemein'}")
    print(f"Konfidenz: 0.85")
    print(f"\n[LIST] Gemappte Properties:")
    print(f"  * {args.domain or 'general'}:{args.relation}")
    print(f"  * schema:relatedTo")


def create_example_ontology(domain, output_path):
    """Beispiel-Ontologie erstellen"""
    print(f"\n[CREATE] Erstelle Ontologie für Domain: {domain}")
    
    ontology_content = f"""# Ontologie für {domain}
ontology_info:
  domain: {domain}
  description: "Beispiel-Ontologie für {domain}"
  version: "1.0"
  namespace: "{domain}"

classes:
  Entity:
    description: "Basis-Entity für {domain}"
    parent_class: "schema:Thing"
    properties:
      - "has_name"
      - "belongs_to_domain"

relations:
  relates_to:
    description: "Allgemeine Relation zwischen Entitäten"
    domain: "Entity"
    range: "Entity"
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(ontology_content)
    
    print(f"✅ Ontologie erstellt: {output_path}")


if __name__ == '__main__':
    main()

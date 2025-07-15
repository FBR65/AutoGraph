"""
Test-Script für TableExtractor mit der CLI
"""

from pathlib import Path
from src.autograph.extractors.table import TableExtractor
from src.autograph.config import AutoGraphConfig, Neo4jConfig
from src.autograph.core.pipeline import AutoGraphPipeline

def test_table_extractor():
    """Testet den TableExtractor mit einer CSV-Datei"""
    
    # TableExtractor konfigurieren
    table_config = {
        "processing_mode": "combined",
        "max_rows": 1000,
        "include_metadata": True
    }
    
    extractor = TableExtractor(config=table_config)
    
    # CSV-Datei verarbeiten
    file_path = "test_data.csv"
    print(f"🔄 Verarbeite Datei: {file_path}")
    
    extracted_data = extractor.extract(file_path)
    print(f"✅ Extrahiert: {len(extracted_data)} Datenpunkte")
    
    # Beispiel-Daten anzeigen
    print("\n📋 Extrahierte Daten:")
    for i, item in enumerate(extracted_data):
        print(f"  {i+1}: {item}")
    
    # Text für Pipeline vorbereiten
    text_data = []
    for item in extracted_data:
        if isinstance(item, dict) and 'content' in item:
            text_data.append(item['content'])
        elif isinstance(item, str):
            text_data.append(item)
    
    if text_data:
        combined_text = "\n".join(text_data)
        print(f"\n📄 Kombinierter Text für Pipeline ({len(combined_text)} Zeichen):")
        print(combined_text[:500] + "..." if len(combined_text) > 500 else combined_text)
        
        # Pipeline-Test
        try:
            print("\n🚀 Starte Pipeline...")
            config = AutoGraphConfig(
                project_name="table_test",
                neo4j=Neo4jConfig(password="")  # Passwordless
            )
            
            # Pipeline-Komponenten initialisieren
            from src.autograph.extractors.text import TextExtractor
            from src.autograph.processors.ner import NERProcessor
            from src.autograph.processors.relation_extractor import RelationExtractor
            from src.autograph.storage.neo4j import Neo4jStorage
            
            text_extractor = TextExtractor()
            ner_processor = NERProcessor()
            relation_processor = RelationExtractor()
            
            # Neo4j Konfiguration als Dictionary
            neo4j_config = {
                "uri": "bolt://localhost:7687",
                "username": "neo4j", 
                "password": "",
                "database": "neo4j"
            }
            storage = Neo4jStorage(neo4j_config)
            
            pipeline = AutoGraphPipeline(
                config=config,
                extractor=text_extractor,
                processors=[ner_processor, relation_processor],
                storage=storage
            )
            
            # Temporäre Textdatei erstellen für Pipeline
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tmp_file:
                tmp_file.write(combined_text)
                tmp_file_path = tmp_file.name
            
            results = pipeline.run(
                data_source=tmp_file_path,
                domain="wirtschaft"
            )
            
            # Temp-Datei wieder löschen
            import os
            os.unlink(tmp_file_path)
            
            entities = results.entities
            relationships = results.relationships
            
            print(f"✅ Pipeline abgeschlossen!")
            print(f"📋 Entitäten: {len(entities)}")
            print(f"🔗 Beziehungen: {len(relationships)}")
            
            if entities:
                print(f"\n📋 Beispiel-Entitäten:")
                for entity in entities[:5]:
                    print(f"  • {entity.get('text', 'N/A')} ({entity.get('label', 'N/A')})")
                    
            if relationships:
                print(f"\n🔗 Beispiel-Beziehungen:")
                for rel in relationships[:5]:
                    print(f"  • {rel.get('source', 'N/A')} -> {rel.get('target', 'N/A')} ({rel.get('type', 'N/A')})")
                    
        except Exception as e:
            print(f"❌ Pipeline-Fehler: {str(e)}")
    
    else:
        print("❌ Keine verarbeitbaren Textdaten gefunden")

if __name__ == "__main__":
    test_table_extractor()

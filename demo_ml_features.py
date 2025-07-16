"""
Demo für ML-basierte Relation Extraction in AutoGraph

Dieses Demo zeigt die neuen ML-Features:
1. ML RelationExtractor mit BERT
2. Hybrid RelationExtractor (Rules + ML)
3. Performance-Verbesserungen
4. Domänen-spezifische Optimierungen
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from autograph.processors.ml_relation_extractor import MLRelationExtractor
from autograph.processors.hybrid_relation_extractor import HybridRelationExtractor
from autograph.processors.ner import NERProcessor
from autograph.processors.ml_config import MLRelationConfig

# Logging konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_ml_features():
    """Demonstriert die neuen ML-Features"""

    print("🚀 AutoGraph ML Relation Extraction Demo")
    print("=" * 50)

    # NER Processor für Entitäten
    ner_processor = NERProcessor()

    # Test-Text mit komplexeren Beziehungen
    demo_text = (
        "Die Bundesrepublik Deutschland ist ein föderal organisierter Staat in Mitteleuropa. "
        "Angela Merkel war von 2005 bis 2021 deutsche Bundeskanzlerin und führte das Land "
        "durch verschiedene Krisen. Berlin ist seit 1990 wieder die Hauptstadt. "
        "Die deutsche Wirtschaft wird von Unternehmen wie Volkswagen, BMW und Siemens geprägt, "
        "die weltweit tätig sind und innovative Technologien entwickeln."
    )

    print(f"📝 Demo-Text:\n{demo_text}\n")

    # 1. NER für Entitäten
    print("1️⃣ Named Entity Recognition")
    print("-" * 30)

    ner_result = await ner_processor.process_async(demo_text, "allgemein")
    entities = ner_result.get("entities", [])

    print(f"Gefundene Entitäten: {len(entities)}")
    for entity in entities:
        print(f"  • {entity['text']} ({entity['label']})")
    print()

    # 2. ML-basierte Relation Extraction
    print("2️⃣ ML-basierte Relation Extraction")
    print("-" * 40)

    ml_config = MLRelationConfig(
        confidence_threshold=0.6, max_entity_distance=150, batch_size=4
    )

    ml_extractor = MLRelationExtractor(ml_config.to_dict())

    ml_result = await ml_extractor.process_async(
        {"text": demo_text, "entities": entities}, "allgemein"
    )

    ml_relations = ml_result.get("relationships", [])
    ml_metadata = ml_result.get("metadata", {})

    print(f"ML-Relationen: {len(ml_relations)}")
    print(f"Device: {ml_metadata.get('device', 'N/A')}")
    print(f"Verarbeitung: {ml_metadata.get('pairs_generated', 0)} Entitäten-Paare")

    for rel in ml_relations:
        rel_type = rel.get("relation_type", rel.get("relationship", "UNKNOWN"))
        source = rel.get("source", rel.get("entity1", "UNK"))
        target = rel.get("target", rel.get("entity2", "UNK"))
        confidence = rel.get("confidence", 0.0)
        print(f"  🤖 {source} --[{rel_type}]--> {target} (Conf: {confidence:.2f})")
    print()

    # 3. Hybrid Relation Extraction
    print("3️⃣ Hybrid Relation Extraction (Rules + ML)")
    print("-" * 45)

    hybrid_config = {
        "ensemble_method": "weighted_union",
        "ml_weight": 0.7,
        "rule_weight": 0.3,
        "ml_relation_config": ml_config.to_dict(),
    }

    hybrid_extractor = HybridRelationExtractor(hybrid_config)

    hybrid_result = await hybrid_extractor.process_async(
        {"text": demo_text, "entities": entities}, "allgemein"
    )

    hybrid_relations = hybrid_result.get("relationships", [])
    hybrid_metadata = hybrid_result.get("metadata", {})

    print(f"Hybrid-Relationen: {len(hybrid_relations)}")
    print(f"Rule-Relationen: {hybrid_metadata.get('rule_relations', 0)}")
    print(f"ML-Relationen: {hybrid_metadata.get('ml_relations', 0)}")
    print(f"Ensemble-Methode: {hybrid_metadata.get('ensemble_method', 'N/A')}")

    for rel in hybrid_relations:
        source_type = rel.get("ensemble_source", "unknown")
        icon = "🤖" if source_type == "ml" else "🔧" if source_type == "rules" else "🔄"
        rel_type = rel.get("relation_type", rel.get("relationship", "UNKNOWN"))
        source = rel.get("source", rel.get("entity1", "UNK"))
        target = rel.get("target", rel.get("entity2", "UNK"))
        confidence = rel.get("confidence", 0.0)
        print(
            f"  {icon} {source} --[{rel_type}]--> {target} "
            f"(Conf: {confidence:.2f}, {source_type})"
        )
    print()

    # 4. Performance-Vergleich
    print("4️⃣ Performance-Zusammenfassung")
    print("-" * 35)

    print(f"ML-basiert:   {len(ml_relations)} Relationen")
    print(f"Hybrid:       {len(hybrid_relations)} Relationen")
    print(
        f"Verbesserung: {len(hybrid_relations) - len(ml_relations):+d} zusätzliche Relationen"
    )

    # Performance-Statistiken
    if hasattr(hybrid_extractor, "get_performance_stats"):
        stats = hybrid_extractor.get_performance_stats()
        if stats.get("avg_ml_time"):
            print(f"Ø ML-Zeit:    {stats['avg_ml_time']:.3f}s")
        if stats.get("avg_rule_time"):
            print(f"Ø Rule-Zeit:  {stats['avg_rule_time']:.3f}s")

    # Cleanup
    await ml_extractor.close()
    await hybrid_extractor.close()

    print("\n✨ Demo abgeschlossen! Die neuen ML-Features sind einsatzbereit.")


if __name__ == "__main__":
    asyncio.run(demo_ml_features())

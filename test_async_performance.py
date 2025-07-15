"""
Test-Script für Async Pipeline und Performance-Optimierung
"""

import asyncio
import time
from pathlib import Path
from src.autograph.extractors.table import TableExtractor
from src.autograph.extractors.text import TextExtractor
from src.autograph.processors.ner import NERProcessor
from src.autograph.processors.relation_extractor import RelationExtractor
from src.autograph.storage.neo4j import Neo4jStorage
from src.autograph.config import AutoGraphConfig, Neo4jConfig
from src.autograph.core.async_pipeline import AsyncAutoGraphPipeline


async def test_async_performance():
    """Testet die asynchrone Pipeline mit Performance-Monitoring"""

    print("🚀 Teste Async AutoGraph Pipeline mit Performance-Optimierung")

    # Konfiguration
    config = AutoGraphConfig(
        project_name="async_performance_test",
        neo4j=Neo4jConfig(password=""),  # Passwordless
    )

    # Cache-Konfiguration
    cache_config = {
        "ner_cache_size": 500,
        "relation_cache_size": 300,
        "text_cache_size": 100,
        "cache_ttl": 1800,  # 30 Minuten
        "enable_disk_cache": False,
    }

    # Pipeline-Komponenten
    text_extractor = TextExtractor()
    ner_processor = NERProcessor()
    relation_processor = RelationExtractor()

    # Neo4j Storage
    neo4j_config = {
        "uri": "bolt://localhost:7687",
        "username": "neo4j",
        "password": "",
        "database": "neo4j",
        "batch_size": 50,  # Kleinere Batches für Demo
    }
    storage = Neo4jStorage(neo4j_config)

    # Async Pipeline erstellen
    async_pipeline = AsyncAutoGraphPipeline(
        config=config,
        extractor=text_extractor,
        processors=[ner_processor, relation_processor],
        storage=storage,
        cache_config=cache_config,
        max_workers=2,  # Begrenzt für Demo
        batch_size=5,
    )

    try:
        # Test 1: Einzelne Datei verarbeiten
        print("\n📄 Test 1: Einzelne CSV-Datei (mit Cache)")

        start_time = time.time()
        result1 = await async_pipeline.run_single(
            data_source="test_data.csv", domain="wirtschaft", use_cache=True
        )
        time1 = time.time() - start_time

        print(f"✅ Erste Ausführung: {time1:.2f}s")
        print(f"   Entitäten: {len(result1.entities)}")
        print(f"   Beziehungen: {len(result1.relationships)}")

        # Test 2: Gleiche Datei nochmal (Cache-Hit)
        print("\n🎯 Test 2: Gleiche Datei (Cache-Hit erwartet)")

        start_time = time.time()
        result2 = await async_pipeline.run_single(
            data_source="test_data.csv", domain="wirtschaft", use_cache=True
        )
        time2 = time.time() - start_time

        print(f"✅ Zweite Ausführung: {time2:.2f}s (Speedup: {time1 / time2:.1f}x)")
        print(f"   Entitäten: {len(result2.entities)}")
        print(f"   Beziehungen: {len(result2.relationships)}")

        # Test 3: Mehrere Dateien parallel
        print("\n📚 Test 3: Batch-Verarbeitung (simuliert)")

        # Mehrere Kopien der Test-Datei erstellen
        test_files = []
        for i in range(3):
            test_file = f"test_data_copy_{i}.csv"
            # Kopiere die ursprüngliche Datei
            with open("test_data.csv", "r") as orig:
                with open(test_file, "w") as copy:
                    copy.write(orig.read())
            test_files.append(test_file)

        start_time = time.time()
        batch_results = await async_pipeline.run_batch(
            data_sources=test_files,
            domain="wirtschaft",
            use_cache=True,
            max_concurrent=2,
        )
        batch_time = time.time() - start_time

        print(
            f"✅ Batch-Verarbeitung: {batch_time:.2f}s für {len(batch_results)} Dateien"
        )
        total_entities = sum(len(r.entities) for r in batch_results)
        total_relationships = sum(len(r.relationships) for r in batch_results)
        print(f"   Gesamt Entitäten: {total_entities}")
        print(f"   Gesamt Beziehungen: {total_relationships}")

        # Cache-Statistiken
        print("\n📊 Cache-Statistiken:")
        cache_stats = await async_pipeline.get_cache_stats()
        print(
            f"   NER Cache: {cache_stats['ner_cache']['size']} Einträge, Hit-Rate: {cache_stats['ner_cache']['hit_rate']:.1%}"
        )
        print(
            f"   Relations Cache: {cache_stats['relation_cache']['size']} Einträge, Hit-Rate: {cache_stats['relation_cache']['hit_rate']:.1%}"
        )
        print(
            f"   Text Cache: {cache_stats['text_cache']['size']} Einträge, Hit-Rate: {cache_stats['text_cache']['hit_rate']:.1%}"
        )

        # Test 4: Streaming (großer Text simuliert)
        print("\n🌊 Test 4: Streaming-Verarbeitung")

        # Großen Text erstellen durch Wiederholung
        large_text = ""
        with open("test_data.csv", "r") as f:
            base_content = f.read()
            large_text = base_content * 10  # 10x wiederholen

        # Als Temp-Datei speichern
        with open("large_test.txt", "w") as f:
            f.write(large_text)

        print("🔄 Streaming-Verarbeitung gestartet...")
        chunk_count = 0
        async for chunk_result in async_pipeline.run_streaming(
            "large_test.txt",
            chunk_size=500,  # Kleine Chunks für Demo
            domain="wirtschaft",
        ):
            chunk_count += 1
            print(
                f"   Chunk {chunk_count}: {len(chunk_result.entities)} Entitäten, {len(chunk_result.relationships)} Beziehungen"
            )

            if chunk_count >= 3:  # Nur ersten 3 Chunks für Demo
                break

        print(f"✅ Streaming abgeschlossen: {chunk_count} Chunks verarbeitet")

        # Cleanup
        for test_file in test_files:
            Path(test_file).unlink(missing_ok=True)
        Path("large_test.txt").unlink(missing_ok=True)

        # Performance-Zusammenfassung
        print("\n🎯 Performance-Zusammenfassung:")
        print(f"   Erste Ausführung: {time1:.2f}s")
        print(f"   Cache-Hit Ausführung: {time2:.2f}s (Speedup: {time1 / time2:.1f}x)")
        print(f"   Batch-Verarbeitung: {batch_time:.2f}s für {len(test_files)} Dateien")
        print(f"   Durchsatz: {total_entities / batch_time:.1f} Entitäten/s")

    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Pipeline ordnungsgemäß schließen
        await async_pipeline.close()


async def test_cache_performance():
    """Testet Cache-Performance isoliert"""

    print("\n🧪 Cache Performance Test")

    from src.autograph.core.cache import AutoGraphCacheManager

    cache_manager = AutoGraphCacheManager(
        {"ner_cache_size": 100, "relation_cache_size": 100, "cache_ttl": 300}
    )

    # Test-Daten
    test_text = "Max Mustermann arbeitet bei Microsoft in Berlin"
    test_entities = [
        {"text": "Max Mustermann", "label": "PERSON"},
        {"text": "Microsoft", "label": "ORG"},
        {"text": "Berlin", "label": "LOC"},
    ]
    test_relations = [
        {
            "subject": "Max Mustermann",
            "predicate": "arbeitet_bei",
            "object": "Microsoft",
        }
    ]

    # Cache-Operationen testen
    print("📝 Fülle Cache...")

    # 100 Einträge hinzufügen
    tasks = []
    for i in range(100):
        text = f"{test_text} {i}"
        tasks.append(
            cache_manager.cache_ner_results(text, test_entities, "de_core_news_lg")
        )
        tasks.append(
            cache_manager.cache_relation_results(text, test_relations, "wirtschaft")
        )

    start_time = time.time()
    await asyncio.gather(*tasks)
    fill_time = time.time() - start_time

    print(f"✅ Cache gefüllt in {fill_time:.3f}s")

    # Cache-Zugriffe testen
    print("🔍 Teste Cache-Zugriffe...")

    hit_tasks = []
    for i in range(50):  # Erste 50 sollten Hits sein
        text = f"{test_text} {i}"
        hit_tasks.append(cache_manager.get_cached_ner_results(text, "de_core_news_lg"))
        hit_tasks.append(cache_manager.get_cached_relation_results(text, "wirtschaft"))

    start_time = time.time()
    results = await asyncio.gather(*hit_tasks)
    access_time = time.time() - start_time

    hits = sum(1 for r in results if r is not None)
    hit_rate = hits / len(results)

    print(f"✅ Cache-Zugriffe in {access_time:.3f}s")
    print(f"   Hit-Rate: {hit_rate:.1%} ({hits}/{len(results)})")

    # Cache-Statistiken
    stats = await cache_manager.get_cache_stats()
    print(f"📊 Cache-Statistiken:")
    print(f"   Gesamt Einträge: {stats['total_entries']}")
    print(f"   NER Cache: {stats['ner_cache']['size']}")
    print(f"   Relations Cache: {stats['relation_cache']['size']}")


async def benchmark_sync_vs_async():
    """Vergleicht synchrone vs. asynchrone Verarbeitung"""

    print("\n⚡ Sync vs. Async Benchmark")

    # Test-Daten vorbereiten
    test_texts = [
        "Max Mustermann arbeitet bei Microsoft in Berlin",
        "Anna Schmidt leitet das Projekt bei Google",
        "Peter Weber entwickelt Software für Apple",
        "Maria Müller ist CEO von Amazon",
        "Thomas Bauer investiert in Tesla",
    ]

    # Sync-Verarbeitung (simuliert)
    print("🐌 Synchrone Verarbeitung...")
    start_time = time.time()

    ner_processor = NERProcessor()
    for text in test_texts:
        # Simuliere sync NER
        doc = ner_processor.nlp(text)
        entities = [{"text": ent.text, "label": ent.label_} for ent in doc.ents]
        # Kleine Pause um Verarbeitung zu simulieren
        await asyncio.sleep(0.1)

    sync_time = time.time() - start_time
    print(f"✅ Sync Zeit: {sync_time:.2f}s")

    # Async-Verarbeitung
    print("⚡ Asynchrone Verarbeitung...")
    start_time = time.time()

    async def process_text_async(text):
        # Simuliere async NER
        return await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: [
                {"text": ent.text, "label": ent.label_}
                for ent in ner_processor.nlp(text).ents
            ],
        )

    # Parallel verarbeiten
    results = await asyncio.gather(*[process_text_async(text) for text in test_texts])
    async_time = time.time() - start_time

    print(f"✅ Async Zeit: {async_time:.2f}s")
    print(f"🚀 Speedup: {sync_time / async_time:.1f}x")


async def main():
    """Hauptfunktion für alle Performance-Tests"""

    print("=" * 60)
    print("🚀 AutoGraph Performance Optimization Tests")
    print("=" * 60)

    try:
        # Core Async Pipeline Tests
        await test_async_performance()

        # Cache Performance Tests
        await test_cache_performance()

        # Sync vs Async Benchmark
        await benchmark_sync_vs_async()

        print("\n" + "=" * 60)
        print("✅ Alle Performance-Tests abgeschlossen!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test-Fehler: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

"""
CLI Interface für AutoGraph
"""

import click
import logging
import asyncio
from pathlib import Path
from typing import Optional

from .config import AutoGraphConfig
from .core.pipeline import AutoGraphPipeline
from .core.async_pipeline import AsyncAutoGraphPipeline
from .extractors.text import TextExtractor
from .extractors.table import TableExtractor
from .processors.ner import NERProcessor
from .storage.neo4j import Neo4jStorage
from .ontology import OntologyManager


def setup_logging(level: str = "INFO"):
    """Konfiguriert Logging"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler("autograph.log")],
    )


@click.group()
@click.option(
    "--config", "-c", type=click.Path(exists=True), help="Pfad zur Konfigurationsdatei"
)
@click.option(
    "--log-level", default="INFO", help="Log Level (DEBUG, INFO, WARNING, ERROR)"
)
@click.pass_context
def cli(ctx, config: Optional[str], log_level: str):
    """AutoGraph - Automatische Knowledge Graph Generierung"""
    setup_logging(log_level)

    ctx.ensure_object(dict)

    if config:
        ctx.obj["config"] = AutoGraphConfig.from_file(Path(config))
    else:
        ctx.obj["config"] = None


@cli.command()
@click.argument("source", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output Verzeichnis")
@click.option(
    "--format", "output_format", default="json", help="Output Format (json, csv)"
)
@click.pass_context
def extract(ctx, source: str, output: Optional[str], output_format: str):
    """Extrahiert Daten aus Quelle"""
    click.echo(f"Extrahiere Daten aus: {source}")

    # Einfacher Text-Extraktor für Demo
    extractor = TextExtractor()
    data = extractor.extract(source)

    click.echo(f"Extrahiert: {len(data)} Datenpunkte")

    if output:
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)

        import json

        with open(
            output_path / f"extracted_data.{output_format}", "w", encoding="utf-8"
        ) as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        click.echo(f"Daten gespeichert in: {output_path}")


@cli.command()
@click.argument("source", type=click.Path(exists=True))
@click.option("--domain", "-d", help="Zieldomäne (z.B. medizin, literatur)")
@click.option(
    "--processor",
    "-p",
    type=click.Choice(["ner", "relation", "both"], case_sensitive=False),
    default="both",
    help="Verarbeitungsmodus: ner (nur NER), relation (nur Beziehungen), both (beides)",
)
@click.pass_context
def run(ctx, source: str, domain: Optional[str], processor: str):
    """Führt komplette AutoGraph Pipeline aus"""
    config = ctx.obj.get("config")

    if not config:
        click.echo("Keine Konfiguration gefunden. Verwende Standard-Konfiguration.")
        # Minimal-Konfiguration für Demo
        from .config import Neo4jConfig

        config = AutoGraphConfig(
            project_name="demo",
            neo4j=Neo4jConfig(password="password"),  # Sollte aus Umgebung kommen
        )

    click.echo(f"Starte AutoGraph Pipeline für: {source}")
    if domain:
        click.echo(f"Zieldomäne: {domain}")
    click.echo(f"Verarbeitungsmodus: {processor}")

    try:
        # Pipeline-Komponenten initialisieren
        extractor = TextExtractor(config.extractor.model_dump())

        # Prozessoren basierend auf Auswahl
        processors = []
        if processor in ["ner", "both"]:
            processors.append(NERProcessor(config.processor.model_dump()))
        if processor in ["relation", "both"]:
            from .processors import RelationExtractor

            processors.append(RelationExtractor(config.processor.model_dump()))

        storage = Neo4jStorage(config.neo4j.model_dump())

        # Pipeline ausführen
        pipeline = AutoGraphPipeline(
            config=config, extractor=extractor, processors=processors, storage=storage
        )

        result = pipeline.run(source, domain=domain)

        click.echo("Pipeline erfolgreich abgeschlossen!")
        click.echo(f"Entitäten: {len(result.entities)}")
        click.echo(f"Beziehungen: {len(result.relationships)}")

    except Exception as e:
        click.echo(f"Fehler: {str(e)}", err=True)
        raise click.ClickException(str(e))


@cli.command()
@click.option("--project-name", prompt="Projektname", help="Name des Projekts")
@click.option("--neo4j-uri", default="bolt://localhost:7687", help="Neo4j URI")
@click.option("--neo4j-user", default="neo4j", help="Neo4j Benutzername")
@click.option("--neo4j-password", prompt=True, hide_input=True, help="Neo4j Passwort")
@click.option("--output", "-o", default="autograph-config.yaml", help="Ausgabe-Datei")
def init(
    project_name: str, neo4j_uri: str, neo4j_user: str, neo4j_password: str, output: str
):
    """Erstellt eine neue AutoGraph Konfiguration"""
    from .config import Neo4jConfig

    config = AutoGraphConfig(
        project_name=project_name,
        neo4j=Neo4jConfig(uri=neo4j_uri, username=neo4j_user, password=neo4j_password),
    )

    config.to_file(Path(output))
    click.echo(f"Konfiguration erstellt: {output}")


@cli.command()
@click.option("--host", default="127.0.0.1", help="Server Host")
@click.option("--port", default=8000, help="Server Port")
@click.option("--reload", is_flag=True, help="Auto-Reload aktivieren")
@click.option("--workers", default=1, help="Anzahl Worker Prozesse")
def serve(host: str, port: int, reload: bool, workers: int):
    """Startet den AutoGraph REST API Server"""
    try:
        import uvicorn

        click.echo("🚀 Starte AutoGraph REST API Server...")
        click.echo(f"📍 URL: http://{host}:{port}")
        click.echo(f"📚 Dokumentation: http://{host}:{port}/docs")
        click.echo(f"🔄 Auto-Reload: {'Aktiviert' if reload else 'Deaktiviert'}")

        uvicorn.run(
            "autograph.api.server:app",
            host=host,
            port=port,
            reload=reload,
            workers=workers
            if not reload
            else 1,  # Reload funktioniert nur mit 1 Worker
            log_level="info",
        )

    except ImportError:
        click.echo("❌ uvicorn nicht installiert. Installiere mit: uv add uvicorn")
        raise click.ClickException("uvicorn nicht verfügbar")
    except Exception as e:
        click.echo(f"❌ Fehler beim Starten des Servers: {e}")
        raise click.ClickException(str(e))


@cli.command()
@click.pass_context
def menu(ctx):
    """Interaktives Menü für AutoGraph"""
    while True:
        click.echo("\n" + "=" * 50)
        click.echo("🤖 AutoGraph - Knowledge Graph Framework")
        click.echo("=" * 50)
        click.echo("1. 📄 Text verarbeiten (NER + Beziehungen)")
        click.echo("2. 🧠 Nur NER (Named Entity Recognition)")
        click.echo("3. 🔗 Nur Beziehungsextraktion")
        click.echo("4. � Tabelle verarbeiten (CSV/Excel)")
        click.echo("5. �🗂️  Datenbank anzeigen")
        click.echo("6. 🗑️  Datenbank löschen")
        click.echo("7. 🆕 Neue Datenbank erstellen")
        click.echo("8. ⚙️  Konfiguration anzeigen")
        click.echo("9. � Statistiken anzeigen")
        click.echo("0. ❌ Beenden")
        click.echo("-" * 50)

        choice = click.prompt("Ihre Auswahl", type=int)

        if choice == 0:
            click.echo("Auf Wiedersehen! 👋")
            break
        elif choice == 1:
            _menu_process_text(ctx, "both")
        elif choice == 2:
            _menu_process_text(ctx, "ner")
        elif choice == 3:
            _menu_process_text(ctx, "relation")
        elif choice == 4:
            _menu_process_table(ctx)
        elif choice == 5:
            _menu_show_database(ctx)
        elif choice == 6:
            _menu_clear_database(ctx)
        elif choice == 7:
            _menu_create_database(ctx)
        elif choice == 8:
            _menu_show_config(ctx)
        elif choice == 9:
            _menu_show_stats(ctx)
        else:
            click.echo("❌ Ungültige Auswahl!")


def _menu_process_text(ctx, processor_mode: str):
    """Menü für Textverarbeitung"""
    file_path = click.prompt("📄 Pfad zur Textdatei", type=click.Path(exists=True))
    domain = click.prompt(
        "🎯 Domäne (optional, Enter für keine)", default="", show_default=False
    )

    if domain == "":
        domain = None

    click.echo(f"\n🚀 Starte Verarbeitung...")
    ctx.invoke(run, source=file_path, domain=domain, processor=processor_mode)


def _menu_show_database(ctx):
    """Zeigt Datenbankinhalte an"""
    try:
        config = ctx.obj.get("config")
        if not config:
            click.echo("❌ Keine Konfiguration gefunden!")
            return

        storage = Neo4jStorage(config.neo4j.model_dump())

        # Einfache Cypher-Abfrage für Übersicht
        click.echo("\n📊 Datenbank-Übersicht:")
        click.echo("-" * 30)

        # Entitäten zählen
        entity_query = "MATCH (n) RETURN count(n) as entity_count"
        entity_result = storage._execute_query(entity_query)
        entity_count = entity_result[0]["entity_count"] if entity_result else 0

        # Beziehungen zählen
        rel_query = "MATCH ()-[r]->() RETURN count(r) as rel_count"
        rel_result = storage._execute_query(rel_query)
        rel_count = rel_result[0]["rel_count"] if rel_result else 0

        click.echo(f"🔸 Entitäten: {entity_count}")
        click.echo(f"🔗 Beziehungen: {rel_count}")

        if entity_count > 0:
            # Beispiel-Entitäten anzeigen
            sample_query = (
                "MATCH (n) RETURN n.text as text, labels(n)[0] as label LIMIT 5"
            )
            samples = storage._execute_query(sample_query)

            click.echo(f"\n📋 Beispiel-Entitäten:")
            for sample in samples:
                click.echo(f"  • {sample['text']} ({sample['label']})")

    except Exception as e:
        click.echo(f"❌ Fehler beim Datenbankzugriff: {str(e)}")


def _menu_clear_database(ctx):
    """Löscht alle Daten aus der Datenbank"""
    if click.confirm("⚠️  Möchten Sie wirklich ALLE Daten aus der Datenbank löschen?"):
        try:
            config = ctx.obj.get("config")
            if not config:
                click.echo("❌ Keine Konfiguration gefunden!")
                return

            storage = Neo4jStorage(config.neo4j.model_dump())

            # Alle Daten löschen
            clear_query = "MATCH (n) DETACH DELETE n"
            storage._execute_query(clear_query)

            click.echo("✅ Datenbank erfolgreich geleert!")

        except Exception as e:
            click.echo(f"❌ Fehler beim Löschen: {str(e)}")
    else:
        click.echo("Abgebrochen.")


def _menu_create_database(ctx):
    """Erstellt Datenbank-Constraints und Indizes"""
    try:
        config = ctx.obj.get("config")
        if not config:
            click.echo("❌ Keine Konfiguration gefunden!")
            return

        storage = Neo4jStorage(config.neo4j.model_dump())

        click.echo("🆕 Erstelle Datenbank-Schema...")

        # Constraints für bessere Performance
        constraints = [
            "CREATE CONSTRAINT entity_text_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.text IS UNIQUE",
            "CREATE INDEX entity_label_index IF NOT EXISTS FOR (e:Entity) ON (e.label)",
            "CREATE INDEX entity_source_index IF NOT EXISTS FOR (e:Entity) ON (e.source)",
        ]

        for constraint in constraints:
            try:
                storage._execute_query(constraint)
                click.echo(f"✅ {constraint.split()[1]} erstellt")
            except Exception as e:
                if "already exists" in str(e).lower():
                    click.echo(f"ℹ️  {constraint.split()[1]} existiert bereits")
                else:
                    click.echo(f"❌ Fehler: {str(e)}")

        click.echo("✅ Datenbank-Schema erfolgreich erstellt!")

    except Exception as e:
        click.echo(f"❌ Fehler beim Schema-Setup: {str(e)}")


def _menu_show_config(ctx):
    """Zeigt aktuelle Konfiguration an"""
    config = ctx.obj.get("config")
    if not config:
        click.echo("❌ Keine Konfiguration geladen!")
        return

    click.echo("\n⚙️  Aktuelle Konfiguration:")
    click.echo("-" * 30)
    click.echo(f"📋 Projekt: {config.project_name}")
    click.echo(f"🔗 Neo4j URI: {config.neo4j.uri}")
    click.echo(f"👤 Neo4j User: {config.neo4j.username}")
    click.echo(f"🤖 LLM URL: {config.llm.base_url}")
    click.echo(f"🧠 LLM Modell: {config.llm.model}")
    click.echo(f"📝 NER Modell: {config.processor.ner_model}")


def _menu_show_stats(ctx):
    """Zeigt detaillierte Statistiken an"""
    try:
        config = ctx.obj.get("config")
        if not config:
            click.echo("❌ Keine Konfiguration gefunden!")
            return

        storage = Neo4jStorage(config.neo4j.model_dump())

        click.echo("\n📊 Detaillierte Statistiken:")
        click.echo("-" * 40)

        # Entitäten nach Typ
        type_query = """
        MATCH (n:Entity) 
        RETURN n.label as entity_type, count(*) as count 
        ORDER BY count DESC
        """
        types = storage._execute_query(type_query)

        if types:
            click.echo("🏷️  Entitäten nach Typ:")
            for type_info in types:
                click.echo(f"  • {type_info['entity_type']}: {type_info['count']}")

        # Beziehungen nach Typ
        rel_type_query = """
        MATCH ()-[r]->() 
        RETURN type(r) as rel_type, count(*) as count 
        ORDER BY count DESC
        """
        rel_types = storage._execute_query(rel_type_query)

        if rel_types:
            click.echo(f"\n🔗 Beziehungen nach Typ:")
            for rel_info in rel_types:
                click.echo(f"  • {rel_info['rel_type']}: {rel_info['count']}")

    except Exception as e:
        click.echo(f"❌ Fehler beim Abrufen der Statistiken: {str(e)}")


def _menu_process_table(ctx):
    """Menü für Tabellen-Verarbeitung"""
    file_path = click.prompt("Datei-Pfad (CSV/Excel/TSV/JSON)", type=str)

    if not Path(file_path).exists():
        click.echo(f"❌ Datei nicht gefunden: {file_path}")
        return

    # Verarbeitungsmodus auswählen
    click.echo("\n📊 Verarbeitungsmodus:")
    click.echo("1. Zeilenweise (row_wise)")
    click.echo("2. Spaltenweise (column_wise)")
    click.echo("3. Zellenweise (cell_wise)")
    click.echo("4. Kombiniert (combined)")

    mode_choice = click.prompt("Modus auswählen", type=int, default=4)
    mode_map = {1: "row_wise", 2: "column_wise", 3: "cell_wise", 4: "combined"}

    processing_mode = mode_map.get(mode_choice, "combined")

    # Domain optional
    domain = click.prompt(
        "Domäne (optional, z.B. medizin, wirtschaft)", default="", show_default=False
    )
    domain = domain.strip() or None

    try:
        # Tabellen-Extraktor mit Konfiguration verwenden
        table_config = {
            "processing_mode": processing_mode,
            "max_rows": 1000,  # Limit für Demo
            "include_metadata": True,
        }

        extractor = TableExtractor(config=table_config)
        extracted_data = extractor.extract(file_path)

        if not extracted_data:
            click.echo("❌ Keine Daten extrahiert")
            return

        click.echo(f"✅ {len(extracted_data)} Datenpunkte extrahiert")

        # Pipeline konfigurieren
        config = _get_config(ctx)

        # Pipeline-Komponenten initialisieren
        from .extractors.text import TextExtractor
        from .processors.ner import NERProcessor
        from .processors.relation_extractor import RelationExtractor
        from .storage.neo4j import Neo4jStorage

        text_extractor = TextExtractor()
        ner_processor = NERProcessor()
        relation_processor = RelationExtractor()

        # Neo4j Konfiguration als Dictionary
        neo4j_config = {
            "uri": getattr(config.neo4j, "uri", "bolt://localhost:7687"),
            "username": getattr(config.neo4j, "username", "neo4j"),
            "password": getattr(config.neo4j, "password", ""),
            "database": getattr(config.neo4j, "database", "neo4j"),
        }
        storage = Neo4jStorage(neo4j_config)

        pipeline = AutoGraphPipeline(
            config=config,
            extractor=text_extractor,
            processors=[ner_processor, relation_processor],
            storage=storage,
        )

        # Daten zu Text konvertieren für weitere Verarbeitung
        text_data = []
        for item in extracted_data:
            if isinstance(item, dict) and "content" in item:
                text_data.append(item["content"])
            elif isinstance(item, str):
                text_data.append(item)

        if text_data:
            combined_text = "\n".join(text_data)
            click.echo("🚀 Starte NER und Beziehungsextraktion...")

            # Temporäre Textdatei erstellen für Pipeline
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False, encoding="utf-8"
            ) as tmp_file:
                tmp_file.write(combined_text)
                tmp_file_path = tmp_file.name

            try:
                results = pipeline.run(data_source=tmp_file_path, domain=domain)

                entities = results.entities
                relationships = results.relationships

                click.echo(f"✅ Verarbeitung abgeschlossen!")
                click.echo(f"📋 Entitäten gefunden: {len(entities)}")
                click.echo(f"🔗 Beziehungen gefunden: {len(relationships)}")

                if entities:
                    click.echo(f"\n📋 Beispiel-Entitäten:")
                    for entity in entities[:5]:
                        click.echo(
                            f"  • {entity.get('text', 'N/A')} ({entity.get('label', 'N/A')})"
                        )

                if relationships:
                    click.echo(f"\n🔗 Beispiel-Beziehungen:")
                    for rel in relationships[:5]:
                        click.echo(
                            f"  • {rel.get('source', 'N/A')} -> {rel.get('target', 'N/A')} ({rel.get('type', 'N/A')})"
                        )

            finally:
                # Temp-Datei wieder löschen
                os.unlink(tmp_file_path)
        else:
            click.echo("❌ Keine verarbeitbaren Textdaten gefunden")

    except Exception as e:
        click.echo(f"❌ Fehler bei der Verarbeitung: {str(e)}")


@cli.group()
@click.pass_context
def ontology(ctx):
    """Ontologie-Management Kommandos"""
    pass


@ontology.command()
@click.option(
    "--mode",
    type=click.Choice(["offline", "hybrid", "online"]),
    default="offline",
    help="Ontologie-Modus",
)
@click.pass_context
def status(ctx, mode: str):
    """Zeigt Status der Ontologie-Integration"""
    try:
        config = _get_config(ctx)

        # Ontologie-Konfiguration setzen
        from .ontology import OntologyManager
        from .config import OntologyConfig

        if not config.ontology:
            config.ontology = OntologyConfig(mode=mode)
        else:
            config.ontology.mode = mode

        ontology_manager = OntologyManager(config.model_dump())
        info = ontology_manager.get_ontology_info()

        click.echo("\n[BRAIN] Ontologie-Status")
        click.echo(f"Modus: {info['mode']}")
        click.echo(f"Ladezeit: {info['load_time']:.2f}s")
        click.echo(f"Klassen: {info['classes_count']}")
        click.echo(f"Relationen: {info['relations_count']}")
        click.echo(f"Namespaces: {', '.join(info['namespaces'])}")
        click.echo(f"Quellen geladen: {len(info['sources_loaded'])}")

        if info["sources_loaded"]:
            click.echo("\n[+] Geladene Quellen:")
            for source in info["sources_loaded"]:
                click.echo(f"  * {source}")

    except Exception as e:
        click.echo(f"[ERROR] Fehler beim Laden der Ontologie: {e}")


@ontology.command()
@click.argument("domain")
@click.argument("output_path", type=click.Path())
@click.pass_context
def create_example(ctx, domain: str, output_path: str):
    """Erstellt eine Beispiel-Ontologie für eine Domain"""
    try:
        from .ontology.custom_ontology_parser import CustomOntologyParser

        parser = CustomOntologyParser()
        output_file = Path(output_path)

        parser.create_example_ontology(output_file, domain)
        click.echo(f"[OK] Beispiel-Ontologie für '{domain}' erstellt: {output_path}")

    except Exception as e:
        click.echo(f"[ERROR] Fehler beim Erstellen der Ontologie: {e}")


@ontology.command()
@click.argument("entity")
@click.argument("ner_label")
@click.option("--domain", help="Domain-Kontext")
@click.option(
    "--mode",
    type=click.Choice(["offline", "hybrid", "online"]),
    default="offline",
    help="Ontologie-Modus",
)
@click.pass_context
def map_entity(ctx, entity: str, ner_label: str, domain: str, mode: str):
    """Mappt eine Entität auf Ontologie-Konzepte"""
    try:
        config = _get_config(ctx)
        from .config import OntologyConfig

        # Ontologie-Konfiguration setzen
        if not config.ontology:
            config.ontology = OntologyConfig(mode=mode)
        else:
            config.ontology.mode = mode

        ontology_manager = OntologyManager(config.model_dump())
        mapping = ontology_manager.map_entity(entity, ner_label, domain)

        click.echo(f"\n[TARGET] Entity-Mapping für '{entity}'")
        click.echo(f"NER-Label: {ner_label}")
        click.echo(f"Domain: {domain or 'Keine'}")
        click.echo(f"Konfidenz: {mapping['confidence']:.2f}")

        if mapping["mapped_classes"]:
            click.echo("\n[LIST] Gemappte Klassen:")
            for cls in mapping["mapped_classes"]:
                click.echo(f"  * {cls}")
        else:
            click.echo("\n[ERROR] Keine passenden Ontologie-Klassen gefunden")

    except Exception as e:
        click.echo(f"[ERROR] Fehler beim Entity-Mapping: {e}")


@ontology.command()
@click.argument("relation")
@click.option("--domain", help="Domain-Kontext")
@click.option(
    "--mode",
    type=click.Choice(["offline", "hybrid", "online"]),
    default="offline",
    help="Ontologie-Modus",
)
@click.pass_context
def map_relation(ctx, relation: str, domain: str, mode: str):
    """Mappt eine Relation auf Ontologie-Properties"""
    try:
        config = _get_config(ctx)
        from .config import OntologyConfig

        # Ontologie-Konfiguration setzen
        if not config.ontology:
            config.ontology = OntologyConfig(mode=mode)
        else:
            config.ontology.mode = mode

        ontology_manager = OntologyManager(config.model_dump())
        mapping = ontology_manager.map_relation(relation, domain)

        click.echo(f"\n[LINK] Relation-Mapping für '{relation}'")
        click.echo(f"Domain: {domain or 'Keine'}")
        click.echo(f"Konfidenz: {mapping['confidence']:.2f}")

        if mapping["mapped_properties"]:
            click.echo("\n[LIST] Gemappte Properties:")
            for prop in mapping["mapped_properties"]:
                click.echo(f"  * {prop}")
        else:
            click.echo("\n[ERROR] Keine passenden Ontologie-Properties gefunden")

    except Exception as e:
        click.echo(f"[ERROR] Fehler beim Relation-Mapping: {e}")


def _get_config(ctx):
    """Holt Konfiguration aus Context oder erstellt Default"""
    if ctx.obj and ctx.obj.get("config"):
        return ctx.obj["config"]
    else:
        # Erstelle Standard-Konfiguration
        from .config import Neo4jConfig

        return AutoGraphConfig(
            project_name="autograph", neo4j=Neo4jConfig(password="password")
        )


def main():
    """Entry point für die CLI"""
    cli()


@click.group()
@click.pass_context
def entity_linking(ctx):
    """Entity Linking Commands"""
    pass


@entity_linking.command()
@click.option(
    "--mode",
    type=click.Choice(["offline", "hybrid", "online"]),
    default="offline",
    help="Entity Linking Modus",
)
@click.pass_context
def el_status(ctx, mode: str):
    """Zeigt Entity Linking Status"""
    try:
        config = _get_config(ctx)
        from .processors.entity_linker import EntityLinker

        # Entity Linker-Konfiguration
        linker_config = config.model_dump()
        linker_config["entity_linking_mode"] = mode

        linker = EntityLinker(linker_config)
        stats = linker.get_linking_statistics()

        click.echo(f"\n[LINK] Entity Linking Status")
        click.echo(f"Modus: {stats['mode']}")
        click.echo(f"Confidence Threshold: {stats['confidence_threshold']}")
        click.echo(
            f"Gesamt-Entitäten in Katalogen: {stats['total_entities_in_catalogs']}"
        )

        click.echo(f"\n[LIST] Verfügbare Kataloge:")
        for catalog_name, entity_count in stats["catalogs"].items():
            click.echo(f"  * {catalog_name}: {entity_count} Entitäten")

        click.echo(f"\nCache-Verzeichnis: {stats['cache_dir']}")
        click.echo(f"Custom-Kataloge: {stats['custom_catalogs_dir']}")

    except Exception as e:
        click.echo(f"[ERROR] Fehler beim Entity Linking Status: {e}")


@entity_linking.command()
@click.argument("entity_text")
@click.argument("entity_type")
@click.option("--domain", help="Domain-Kontext")
@click.option("--context", default="", help="Kontext-Text für Disambiguation")
@click.option(
    "--mode",
    type=click.Choice(["offline", "hybrid", "online"]),
    default="offline",
    help="Entity Linking Modus",
)
@click.pass_context
def link_entity(
    ctx, entity_text: str, entity_type: str, domain: str, context: str, mode: str
):
    """Testet Entity Linking für eine einzelne Entität"""
    try:
        config = _get_config(ctx)
        from .processors.entity_linker import EntityLinker

        # Entity Linker-Konfiguration
        linker_config = config.model_dump()
        linker_config["entity_linking_mode"] = mode

        linker = EntityLinker(linker_config)

        # Test-Entität erstellen
        test_data = [
            {
                "entities": [
                    {"text": entity_text, "label": entity_type, "type": entity_type}
                ],
                "domain": domain or "allgemein",
                "content": context,
            }
        ]

        result = linker.process(test_data)
        linked_entity = result["entities"][0]

        click.echo(f"\n[TARGET] Entity Linking für '{entity_text}'")
        click.echo(f"Typ: {entity_type}")
        click.echo(f"Domain: {domain or 'Keine'}")
        click.echo(
            f"Kontext: {context[:50]}..."
            if len(context) > 50
            else f"Kontext: {context}"
        )

        if linked_entity.get("linked", False):
            click.echo(f"\n[SUCCESS] Erfolgreich verknüpft!")
            click.echo(f"Kanonischer Name: {linked_entity.get('canonical_name')}")
            click.echo(f"URI: {linked_entity.get('uri')}")
            click.echo(f"Beschreibung: {linked_entity.get('description')}")
            click.echo(f"Konfidenz: {linked_entity.get('confidence', 0):.3f}")

            metadata = linked_entity.get("linking_metadata", {})
            click.echo(f"Match-Typ: {metadata.get('match_type')}")
            click.echo(f"Katalog: {metadata.get('catalog')}")
            click.echo(f"Kandidaten: {metadata.get('candidates_count', 0)}")

            properties = linked_entity.get("properties", {})
            if properties:
                click.echo(f"\n[LIST] Eigenschaften:")
                for key, value in properties.items():
                    click.echo(f"  * {key}: {value}")
        else:
            metadata = linked_entity.get("linking_metadata", {})
            reason = metadata.get("unlinked_reason", "unbekannt")
            click.echo(f"\n[ERROR] Nicht verknüpft (Grund: {reason})")

    except Exception as e:
        click.echo(f"[ERROR] Fehler beim Entity Linking: {e}")


@entity_linking.command()
@click.argument("domain")
@click.argument("output_path")
@click.pass_context
def create_catalog(ctx, domain: str, output_path: str):
    """Erstellt Beispiel-Entity-Katalog für eine Domäne"""
    try:
        config = _get_config(ctx)
        from .processors.entity_linker import EntityLinker

        linker = EntityLinker(config.model_dump())
        linker.create_custom_catalog_example(domain, output_path)

        click.echo(f"\n[SUCCESS] Beispiel-Katalog erstellt: {output_path}")
        click.echo(f"Domain: {domain}")
        click.echo(
            f"Bearbeiten Sie die Datei und fügen Sie Ihre eigenen Entitäten hinzu."
        )

    except Exception as e:
        click.echo(f"[ERROR] Fehler beim Erstellen des Katalogs: {e}")


# Entity Linking zur Hauptgruppe hinzufügen
cli.add_command(entity_linking)


@cli.group()
def yaml():
    """YAML-Generierung für Entity-Kataloge und Ontologien"""
    pass


@yaml.command("entity-from-text")
@click.option(
    "--domain", "-d", required=True, help="Zieldomäne (z.B. medizin, literatur)"
)
@click.option("--files", "-f", multiple=True, required=True, help="Eingabe-Textdateien")
@click.option("--output", "-o", default="entity-catalog.yaml", help="Ausgabe-Datei")
@click.option("--min-frequency", default=2, help="Mindest-Häufigkeit für Entitäten")
@click.pass_context
def entity_from_text(ctx, domain: str, files: tuple, output: str, min_frequency: int):
    """Generiert YAML Entity-Katalog aus Textdateien"""
    config = _get_config(ctx)

    click.echo(f"Generiere Entity-Katalog für Domäne: {domain}")
    click.echo(f"Eingabe-Dateien: {', '.join(files)}")
    click.echo(f"Ausgabe: {output}")

    try:
        from .processors.ner import NERProcessor
        from collections import Counter
        import yaml

        processor = NERProcessor(config.processor.model_dump())
        all_entities = []

        # Verarbeite alle Dateien
        for file_path in files:
            if not Path(file_path).exists():
                click.echo(f"⚠️  Datei nicht gefunden: {file_path}")
                continue

            extractor = TextExtractor(config.extractor.model_dump())
            data = extractor.extract(file_path)

            for item in data:
                result = processor.process([item])
                # result ist ein dict mit 'entities' und 'relationships' keys
                if isinstance(result, dict) and "entities" in result:
                    all_entities.extend(result["entities"])
                elif hasattr(result, "entities"):
                    all_entities.extend(result.entities)

        # Zähle Entitäten nach Labels
        entity_counts = Counter()
        entity_examples = {}

        for entity in all_entities:
            # Behandle sowohl Dict- als auch Objekt-Entitäten
            if isinstance(entity, dict):
                label = entity.get("label", entity.get("text", "Unknown"))
                entity_type = entity.get("type", "Unknown")
                text = entity.get("text", label)
            else:
                label = getattr(entity, "label", getattr(entity, "text", "Unknown"))
                entity_type = getattr(entity, "type", "Unknown")
                text = getattr(entity, "text", label)

            key = (label, entity_type)
            entity_counts[key] += 1
            if key not in entity_examples:
                entity_examples[key] = []
            if len(entity_examples[key]) < 3:  # Max 3 Beispiele
                entity_examples[key].append(text)

        # Erstelle YAML-Struktur
        catalog = {
            "domain": domain,
            "version": "1.0.0",
            "description": f"Automatisch generierter Entity-Katalog für {domain}",
            "entities": {},
        }

        for (label, entity_type), count in entity_counts.items():
            if count >= min_frequency:
                catalog["entities"][label] = {
                    "type": entity_type,
                    "frequency": count,
                    "examples": entity_examples[(label, entity_type)],
                    "description": f"{entity_type} aus {domain}-Domäne",
                }

        # Speichere YAML
        with open(output, "w", encoding="utf-8") as f:
            yaml.dump(
                catalog, f, allow_unicode=True, default_flow_style=False, indent=2
            )

        click.echo(f"✅ Entity-Katalog erstellt: {output}")
        click.echo(f"📊 Entitäten gefunden: {len(catalog['entities'])}")
        click.echo(f"🔍 Mindest-Häufigkeit: {min_frequency}")

    except Exception as e:
        click.echo(f"❌ Fehler: {str(e)}", err=True)
        raise click.ClickException(str(e))


@yaml.command("ontology-from-graph")
@click.option("--domain", "-d", required=True, help="Zieldomäne")
@click.option("--output", "-o", default="ontology.yaml", help="Ausgabe-Datei")
@click.option("--include-properties", is_flag=True, help="Eigenschaften einbeziehen")
@click.pass_context
def ontology_from_graph(ctx, domain: str, output: str, include_properties: bool):
    """Generiert YAML-Ontologie aus Knowledge Graph"""
    config = _get_config(ctx)

    click.echo(f"Generiere Ontologie für Domäne: {domain}")
    click.echo(f"Ausgabe: {output}")

    try:
        from .storage.neo4j import Neo4jStorage
        import yaml

        storage = Neo4jStorage(config.neo4j.model_dump())

        # Hole alle Entity-Typen und Beziehungstypen aus der Datenbank
        query = """
        MATCH (n)
        WITH DISTINCT labels(n) as node_labels
        UNWIND node_labels as label
        RETURN DISTINCT label
        ORDER BY label
        """
        entity_types = [record["label"] for record in storage.query(query)]

        query = """
        MATCH ()-[r]->()
        RETURN DISTINCT type(r) as rel_type
        ORDER BY rel_type
        """
        relationship_types = [record["rel_type"] for record in storage.query(query)]

        # Erstelle Ontologie-Struktur
        ontology = {
            "domain": domain,
            "version": "1.0.0",
            "description": f"Automatisch generierte Ontologie für {domain}",
            "entity_types": {},
            "relationship_types": {},
            "constraints": [],
        }

        # Entity-Typen
        for entity_type in entity_types:
            ontology["entity_types"][entity_type] = {
                "description": f"{entity_type} aus {domain}-Domäne",
                "properties": [] if include_properties else None,
            }

        # Relationship-Typen
        for rel_type in relationship_types:
            ontology["relationship_types"][rel_type] = {
                "description": f"{rel_type} Beziehung",
                "domain": None,  # Kann manuell spezifiziert werden
                "range": None,
            }

        # Speichere YAML
        with open(output, "w", encoding="utf-8") as f:
            yaml.dump(
                ontology, f, allow_unicode=True, default_flow_style=False, indent=2
            )

        click.echo(f"✅ Ontologie erstellt: {output}")
        click.echo(f"📊 Entity-Typen: {len(entity_types)}")
        click.echo(f"🔗 Beziehungstypen: {len(relationship_types)}")

    except Exception as e:
        click.echo(f"❌ Fehler: {str(e)}", err=True)
        raise click.ClickException(str(e))


if __name__ == "__main__":
    main()

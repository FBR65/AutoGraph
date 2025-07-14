"""
CLI Interface für AutoGraph
"""

import click
import logging
from pathlib import Path
from typing import Optional

from .config import AutoGraphConfig
from .core.pipeline import AutoGraphPipeline
from .extractors.text import TextExtractor
from .processors.ner import NERProcessor
from .storage.neo4j import Neo4jStorage


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

        with open(output_path / f"extracted_data.{output_format}", "w") as f:
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
        click.echo("4. 🗂️  Datenbank anzeigen")
        click.echo("5. 🗑️  Datenbank löschen")
        click.echo("6. 🆕 Neue Datenbank erstellen")
        click.echo("7. ⚙️  Konfiguration anzeigen")
        click.echo("8. 📊 Statistiken anzeigen")
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
            _menu_show_database(ctx)
        elif choice == 5:
            _menu_clear_database(ctx)
        elif choice == 6:
            _menu_create_database(ctx)
        elif choice == 7:
            _menu_show_config(ctx)
        elif choice == 8:
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


def main():
    """Entry point für die CLI"""
    cli()


if __name__ == "__main__":
    main()

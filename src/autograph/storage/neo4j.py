"""
Neo4j Storage Backend
"""

from typing import List, Dict, Any, Optional
import logging
from neo4j import GraphDatabase, Driver
from neo4j.exceptions import ServiceUnavailable

from .base import BaseStorage


class Neo4jStorage(BaseStorage):
    """Neo4j Graph Database Storage"""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)

        # Konfiguration
        self.uri = self.config.get("uri", "bolt://localhost:7687")
        self.username = self.config.get("username", "neo4j")
        self.password = self.config.get("password")
        self.database = self.config.get("database", "neo4j")

        # Verbindung initialisieren
        self.driver: Optional[Driver] = None
        self._connect()

    def _connect(self) -> None:
        """Stellt Verbindung zur Neo4j Datenbank her"""
        try:
            # Wenn kein Passwort gesetzt ist, verwende None als auth (für NEO4J_AUTH=none)
            if self.password is None or self.password == "":
                auth = None
            else:
                auth = (self.username, self.password)

            self.driver = GraphDatabase.driver(self.uri, auth=auth)

            # Verbindung testen
            with self.driver.session(database=self.database) as session:
                session.run("RETURN 1")

            self.logger.info(f"Verbunden mit Neo4j: {self.uri}")

        except ServiceUnavailable as e:
            self.logger.error(f"Neo4j nicht erreichbar: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Fehler bei Neo4j Verbindung: {str(e)}")
            raise

    def store(self, result) -> bool:
        """Speichert Pipeline-Ergebnis in Neo4j"""
        if not self.driver:
            raise RuntimeError("Keine Neo4j Verbindung")

        try:
            with self.driver.session(database=self.database) as session:
                # Handle both PipelineResult objects and dictionaries
                if hasattr(result, "entities"):
                    # PipelineResult object
                    entities = result.entities
                    relationships = result.relationships
                    metadata = result.metadata
                else:
                    # Dictionary result from async pipeline
                    entities = result.get("entities", [])
                    relationships = result.get("relationships", [])
                    metadata = result.get("metadata", {})

                # Entitäten speichern
                self._store_entities(session, entities)

                # Beziehungen speichern
                self._store_relationships(session, relationships)

                # Metadaten speichern
                self._store_metadata(session, metadata)

            self.logger.info(
                f"Gespeichert: {len(entities)} Entitäten, {len(relationships)} Beziehungen"
            )
            return True

        except Exception as e:
            self.logger.error(f"Fehler beim Speichern: {str(e)}")
            return False

    def _store_entities(self, session, entities: List[Dict[str, Any]]) -> None:
        """Speichert Entitäten als Knoten"""
        for entity in entities:
            query = """
            MERGE (e:Entity {text: $text, type: $type})
            SET e.confidence = $confidence,
                e.source = $source,
                e.context = $context,
                e.updated = timestamp()
            """

            session.run(
                query,
                {
                    "text": entity.get("text", ""),
                    "type": entity.get("label", "UNKNOWN"),
                    "confidence": entity.get("confidence", 0.0),
                    "source": entity.get("source", ""),
                    "context": entity.get("context", ""),
                },
            )

    def _store_relationships(
        self, session, relationships: List[Dict[str, Any]]
    ) -> None:
        """Speichert Beziehungen als Kanten"""
        for rel in relationships:
            query = """
            MATCH (subj:Entity {text: $subject})
            MATCH (obj:Entity {text: $object})
            MERGE (subj)-[r:RELATED {type: $predicate}]->(obj)
            SET r.confidence = $confidence,
                r.source = $source,
                r.sentence = $sentence,
                r.updated = timestamp()
            """

            session.run(
                query,
                {
                    "subject": rel.get("subject", ""),
                    "object": rel.get("object", ""),
                    "predicate": rel.get("predicate", "UNKNOWN"),
                    "confidence": rel.get("confidence", 0.0),
                    "source": rel.get("source", ""),
                    "sentence": rel.get("sentence", ""),
                },
            )

    def _store_metadata(self, session, metadata: Dict[str, Any]) -> None:
        """Speichert Pipeline-Metadaten"""
        query = """
        CREATE (m:Metadata {
            source: $source,
            timestamp: timestamp(),
            pipeline_config: $pipeline_config
        })
        """

        session.run(
            query,
            {
                "source": metadata.get("source", ""),
                "pipeline_config": str(metadata.get("pipeline_config", {})),
            },
        )

    def query(self, cypher_query: str) -> List[Dict[str, Any]]:
        """Führt Cypher-Abfrage aus"""
        if not self.driver:
            raise RuntimeError("Keine Neo4j Verbindung")

        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(cypher_query)
                return [record.data() for record in result]

        except Exception as e:
            self.logger.error(f"Fehler bei Abfrage: {str(e)}")
            return []

    def _execute_query(
        self, query: str, parameters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Führt eine Cypher-Abfrage aus und gibt Ergebnisse zurück"""
        if not self.driver:
            raise RuntimeError("Keine Neo4j Verbindung")

        with self.driver.session(database=self.database) as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def get_entity_stats(self) -> Dict[str, Any]:
        """Liefert Statistiken über gespeicherte Entitäten"""
        stats_query = """
        MATCH (e:Entity)
        RETURN e.type as entity_type, count(*) as count
        ORDER BY count DESC
        """

        result = self.query(stats_query)
        return {
            "entity_types": result,
            "total_entities": sum(r["count"] for r in result),
        }

    def close(self) -> None:
        """Schließt Datenbankverbindung"""
        if self.driver:
            self.driver.close()
            self.logger.info("Neo4j Verbindung geschlossen")

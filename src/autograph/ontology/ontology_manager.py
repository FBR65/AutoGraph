"""
Ontologie Manager - Zentrale Steuerung für verschiedene Ontologie-Modi

Unterstützt:
- Offline-Only: Für Air-Gapped Systems
- Hybrid: Lokale + Online mit Caching
- Online: Primär online Quellen
"""

import logging
import os
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml
import json

from .ontology_loader import OntologyLoader
from .ontology_graph import OntologyGraph

logger = logging.getLogger(__name__)


class OntologyManager:
    """
    Zentrale Steuerung für Ontologie-Integration mit verschiedenen Modi
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialisiert den Ontology Manager

        Args:
            config: Ontologie-Konfiguration mit mode, sources, etc.
        """
        self.config = config.get("ontology", {})
        self.mode = self.config.get("mode", "offline")  # Default: offline
        self.online_fallback = self.config.get("online_fallback", False)
        self.cache_duration = self.config.get("cache_duration", "30d")
        self.internet_timeout = self.config.get("internet_timeout", 5)

        # Pfade
        self.local_ontology_path = Path(
            self.config.get("local_ontologies_dir", "./ontologies/")
        )
        self.custom_ontology_path = Path(
            self.config.get("custom_ontologies_dir", "./custom_ontologies/")
        )
        self.cache_path = Path(self.config.get("cache_dir", "./cache/"))

        # Loader
        self.loader = OntologyLoader(
            local_path=self.local_ontology_path,
            custom_path=self.custom_ontology_path,
            cache_path=self.cache_path,
            timeout=self.internet_timeout,
        )

        # Ontologie Graph (wird lazy geladen)
        self._ontology_graph: Optional[OntologyGraph] = None
        self._load_time: Optional[float] = None

        logger.info(f"OntologyManager initialized in '{self.mode}' mode")

    def get_ontology_graph(self) -> OntologyGraph:
        """
        Liefert den Ontologie-Graph (lazy loading)

        Returns:
            OntologyGraph: Geladene Ontologien
        """
        if self._ontology_graph is None:
            self._load_ontologies()
        return self._ontology_graph

    def _load_ontologies(self):
        """Lädt Ontologien basierend auf Konfiguration"""
        start_time = time.time()

        try:
            if self.mode == "offline":
                self._ontology_graph = self._load_offline_only()
            elif self.mode == "hybrid":
                self._ontology_graph = self._load_hybrid()
            elif self.mode == "online":
                self._ontology_graph = self._load_online_first()
            else:
                logger.warning(
                    f"Unbekannter Ontologie-Modus '{self.mode}', verwende offline"
                )
                self._ontology_graph = self._load_offline_only()

            self._load_time = time.time() - start_time
            logger.info(
                f"Ontologien geladen in {self._load_time:.2f}s, "
                f"{len(self._ontology_graph.classes)} Klassen, "
                f"{len(self._ontology_graph.relations)} Relationen"
            )

        except Exception as e:
            logger.error(f"Fehler beim Laden der Ontologien: {e}")
            # Fallback zu leerem Graph
            self._ontology_graph = OntologyGraph()
            self._load_time = time.time() - start_time

    def _load_offline_only(self) -> OntologyGraph:
        """Lädt nur lokale und custom Ontologien (Air-Gapped Mode)"""
        logger.info("Lade Ontologien im Offline-Modus")

        sources = self.config.get("sources", [])
        if not sources:
            # Default offline sources
            sources = [
                {"type": "custom_yaml", "path": str(self.custom_ontology_path)},
                {"type": "local_rdf", "path": str(self.local_ontology_path)},
            ]

        # Filtere nur offline-kompatible Quellen
        offline_sources = [
            s
            for s in sources
            if s.get("type")
            in ["custom_yaml", "local_rdf", "local_json_ld", "local_owl"]
        ]

        return self.loader.load_from_sources(offline_sources)

    def _load_hybrid(self) -> OntologyGraph:
        """Lädt lokale Ontologien mit Online-Fallback"""
        logger.info("Lade Ontologien im Hybrid-Modus")

        sources = self.config.get("sources", [])
        if not sources:
            # Default hybrid sources
            sources = [
                {
                    "type": "custom_yaml",
                    "path": str(self.custom_ontology_path),
                    "priority": 1,
                },
                {
                    "type": "cached_schema_org",
                    "cache_path": str(self.cache_path / "schema_org.ttl"),
                    "priority": 2,
                },
                {
                    "type": "local_rdf",
                    "path": str(self.local_ontology_path),
                    "priority": 3,
                },
            ]

            if self.online_fallback:
                sources.append({"type": "online_schema_org", "priority": 4})

        # Sortiere nach Priorität
        sources = sorted(sources, key=lambda x: x.get("priority", 999))

        return self.loader.load_from_sources(sources, allow_online=self.online_fallback)

    def _load_online_first(self) -> OntologyGraph:
        """Lädt primär Online-Ontologien mit lokalen Fallbacks"""
        logger.info("Lade Ontologien im Online-Modus")

        sources = self.config.get("sources", [])
        if not sources:
            # Default online sources
            sources = [
                {"type": "online_schema_org", "priority": 1},
                {"type": "online_dbpedia", "priority": 2},
                {
                    "type": "custom_yaml",
                    "path": str(self.custom_ontology_path),
                    "priority": 3,
                },
                {
                    "type": "cached_schema_org",
                    "cache_path": str(self.cache_path / "schema_org.ttl"),
                    "priority": 4,
                },
            ]

        # Sortiere nach Priorität
        sources = sorted(sources, key=lambda x: x.get("priority", 999))

        return self.loader.load_from_sources(sources, allow_online=True)

    def map_entity(
        self, entity: str, ner_label: str, domain: str = None
    ) -> Dict[str, Any]:
        """
        Mappt eine Entität auf Ontologie-Konzepte

        Args:
            entity: Entity-Name
            ner_label: NER Label (PERSON, ORG, etc.)
            domain: Domain (medizin, wirtschaft, etc.)

        Returns:
            Dict mit Ontologie-Mapping
        """
        ontology = self.get_ontology_graph()
        return ontology.map_entity(entity, ner_label, domain)

    def map_relation(self, relation: str, domain: str = None) -> Dict[str, Any]:
        """
        Mappt eine Relation auf Ontologie-Properties

        Args:
            relation: Relation-Name
            domain: Domain (medizin, wirtschaft, etc.)

        Returns:
            Dict mit Ontologie-Mapping
        """
        ontology = self.get_ontology_graph()
        return ontology.map_relation(relation, domain)

    def validate_triple(
        self, subject_type: str, predicate: str, object_type: str
    ) -> bool:
        """
        Validiert ein Triple basierend auf Ontologie-Constraints

        Args:
            subject_type: Typ des Subjekts
            predicate: Prädikat/Relation
            object_type: Typ des Objekts

        Returns:
            bool: True wenn valid
        """
        ontology = self.get_ontology_graph()
        return ontology.validate_triple(subject_type, predicate, object_type)

    def get_ontology_info(self) -> Dict[str, Any]:
        """
        Liefert Informationen über geladene Ontologien

        Returns:
            Dict mit Ontologie-Status
        """
        ontology = self.get_ontology_graph()

        return {
            "mode": self.mode,
            "load_time": self._load_time,
            "classes_count": len(ontology.classes),
            "relations_count": len(ontology.relations),
            "namespaces": list(ontology.namespaces.keys()),
            "sources_loaded": ontology.sources_loaded,
            "last_updated": time.time(),
        }

    def reload_ontologies(self):
        """Lädt Ontologien neu"""
        logger.info("Lade Ontologien neu")
        self._ontology_graph = None
        self._load_time = None
        self.get_ontology_graph()  # Trigger reload

    def clear_cache(self):
        """Löscht gecachte Ontologien"""
        logger.info("Lösche Ontologie-Cache")
        try:
            if self.cache_path.exists():
                for cache_file in self.cache_path.glob("*.ttl"):
                    cache_file.unlink()
                for cache_file in self.cache_path.glob("*.jsonld"):
                    cache_file.unlink()
                logger.info("Cache geleert")
            else:
                logger.info("Kein Cache vorhanden")
        except Exception as e:
            logger.error(f"Fehler beim Löschen des Cache: {e}")

"""
Ontologie Loader - Lädt Ontologien aus verschiedenen Quellen

Unterstützt:
- Lokale RDF/TTL/OWL Dateien
- Custom YAML Ontologien
- Gecachte Online-Ontologien
- Online Schema.org/DBpedia (wenn erlaubt)
"""

import logging
import time
import urllib.request
import urllib.error
import socket
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

from .ontology_graph import OntologyGraph
from .custom_ontology_parser import CustomOntologyParser

logger = logging.getLogger(__name__)


class OntologyLoader:
    """
    Lädt Ontologien aus verschiedenen Quellen basierend auf Konfiguration
    """

    def __init__(
        self, local_path: Path, custom_path: Path, cache_path: Path, timeout: int = 5
    ):
        """
        Initialisiert den Ontologie-Loader

        Args:
            local_path: Pfad zu lokalen Ontologie-Dateien
            custom_path: Pfad zu custom Ontologien
            cache_path: Pfad für Cache
            timeout: Internet-Timeout in Sekunden
        """
        self.local_path = local_path
        self.custom_path = custom_path
        self.cache_path = cache_path
        self.timeout = timeout
        self.custom_parser = CustomOntologyParser()

        # Erstelle Verzeichnisse falls nicht vorhanden
        for path in [local_path, custom_path, cache_path]:
            path.mkdir(parents=True, exist_ok=True)

    def load_from_sources(
        self, sources: List[Dict[str, Any]], allow_online: bool = False
    ) -> OntologyGraph:
        """
        Lädt Ontologien aus konfigurierten Quellen

        Args:
            sources: Liste von Ontologie-Quellen
            allow_online: Ob Online-Quellen erlaubt sind

        Returns:
            OntologyGraph: Kombinierter Ontologie-Graph
        """
        ontology_graph = OntologyGraph()

        for source in sources:
            source_type = source.get("type")

            try:
                if source_type == "custom_yaml":
                    self._load_custom_yaml(ontology_graph, source)

                elif source_type == "local_rdf":
                    self._load_local_rdf(ontology_graph, source)

                elif source_type == "local_json_ld":
                    self._load_local_json_ld(ontology_graph, source)

                elif source_type == "local_owl":
                    self._load_local_owl(ontology_graph, source)

                elif source_type == "cached_schema_org":
                    self._load_cached_schema_org(ontology_graph, source, allow_online)

                elif source_type == "online_schema_org" and allow_online:
                    self._load_online_schema_org(ontology_graph, source)

                elif source_type == "online_dbpedia" and allow_online:
                    self._load_online_dbpedia(ontology_graph, source)

                else:
                    if source_type.startswith("online_") and not allow_online:
                        logger.info(
                            f"Online-Quelle '{source_type}' übersprungen (not allowed)"
                        )
                    else:
                        logger.warning(
                            f"Unbekannter Ontologie-Quellen-Typ: {source_type}"
                        )

            except Exception as e:
                logger.error(f"Fehler beim Laden von {source_type}: {e}")
                # Continue mit nächster Quelle

        return ontology_graph

    def _load_custom_yaml(self, graph: OntologyGraph, source: Dict[str, Any]):
        """Lädt Custom YAML Ontologien"""
        path = Path(source.get("path", self.custom_path))

        if path.is_file() and path.suffix in [".yaml", ".yml"]:
            # Einzelne Datei
            custom_ontology = self.custom_parser.parse_yaml_file(path)
            graph.merge_custom_ontology(custom_ontology)
            logger.info(f"Custom YAML Ontologie geladen: {path.name}")

        elif path.is_dir():
            # Verzeichnis mit YAML-Dateien
            yaml_files = list(path.glob("*.yaml")) + list(path.glob("*.yml"))

            for yaml_file in yaml_files:
                try:
                    custom_ontology = self.custom_parser.parse_yaml_file(yaml_file)
                    graph.merge_custom_ontology(custom_ontology)
                    logger.info(f"Custom YAML Ontologie geladen: {yaml_file.name}")
                except Exception as e:
                    logger.error(f"Fehler beim Laden von {yaml_file}: {e}")

        graph.add_source_loaded(f"custom_yaml:{path}")

    def _load_local_rdf(self, graph: OntologyGraph, source: Dict[str, Any]):
        """Lädt lokale RDF/TTL Dateien"""
        path = Path(source.get("path", self.local_path))

        if path.is_file():
            # Einzelne Datei
            if path.suffix in [".ttl", ".rdf", ".n3"]:
                graph.load_rdf_file(path)
                logger.info(f"RDF Ontologie geladen: {path.name}")

        elif path.is_dir():
            # Verzeichnis mit RDF-Dateien
            rdf_files = []
            for ext in ["*.ttl", "*.rdf", "*.n3"]:
                rdf_files.extend(list(path.glob(ext)))

            for rdf_file in rdf_files:
                try:
                    graph.load_rdf_file(rdf_file)
                    logger.info(f"RDF Ontologie geladen: {rdf_file.name}")
                except Exception as e:
                    logger.error(f"Fehler beim Laden von {rdf_file}: {e}")

        graph.add_source_loaded(f"local_rdf:{path}")

    def _load_local_json_ld(self, graph: OntologyGraph, source: Dict[str, Any]):
        """Lädt lokale JSON-LD Dateien"""
        path = Path(source.get("path", self.local_path))

        if path.is_file() and path.suffix == ".jsonld":
            graph.load_json_ld_file(path)
            logger.info(f"JSON-LD Ontologie geladen: {path.name}")

        elif path.is_dir():
            jsonld_files = list(path.glob("*.jsonld"))

            for jsonld_file in jsonld_files:
                try:
                    graph.load_json_ld_file(jsonld_file)
                    logger.info(f"JSON-LD Ontologie geladen: {jsonld_file.name}")
                except Exception as e:
                    logger.error(f"Fehler beim Laden von {jsonld_file}: {e}")

        graph.add_source_loaded(f"local_jsonld:{path}")

    def _load_local_owl(self, graph: OntologyGraph, source: Dict[str, Any]):
        """Lädt lokale OWL Dateien"""
        path = Path(source.get("path", self.local_path))

        if path.is_file() and path.suffix == ".owl":
            graph.load_owl_file(path)
            logger.info(f"OWL Ontologie geladen: {path.name}")

        elif path.is_dir():
            owl_files = list(path.glob("*.owl"))

            for owl_file in owl_files:
                try:
                    graph.load_owl_file(owl_file)
                    logger.info(f"OWL Ontologie geladen: {owl_file.name}")
                except Exception as e:
                    logger.error(f"Fehler beim Laden von {owl_file}: {e}")

        graph.add_source_loaded(f"local_owl:{path}")

    def _load_cached_schema_org(
        self, graph: OntologyGraph, source: Dict[str, Any], allow_online: bool
    ):
        """Lädt gecachte Schema.org Ontologie oder lädt online nach"""
        cache_path = Path(source.get("cache_path", self.cache_path / "schema_org.ttl"))

        if cache_path.exists() and self._is_cache_valid(
            cache_path, source.get("cache_duration", "30d")
        ):
            # Cache vorhanden und gültig
            graph.load_rdf_file(cache_path)
            logger.info(f"Schema.org aus Cache geladen: {cache_path.name}")
            graph.add_source_loaded(f"cached_schema_org:{cache_path}")

        elif allow_online:
            # Cache ungültig oder nicht vorhanden, lade online
            logger.info("Lade Schema.org online und cache es")
            try:
                self._download_schema_org(cache_path)
                graph.load_rdf_file(cache_path)
                logger.info("Schema.org online geladen und gecacht")
                graph.add_source_loaded(f"online_schema_org_cached:{cache_path}")
            except Exception as e:
                logger.error(f"Fehler beim Online-Laden von Schema.org: {e}")

        else:
            logger.warning(
                "Schema.org Cache nicht verfügbar und Online-Zugriff nicht erlaubt"
            )

    def _load_online_schema_org(self, graph: OntologyGraph, source: Dict[str, Any]):
        """Lädt Schema.org direkt online"""
        if not self._internet_available():
            logger.warning("Kein Internet verfügbar für Schema.org")
            return

        try:
            # Temporärer Download für direkten Zugriff
            temp_path = self.cache_path / "temp_schema_org.ttl"
            self._download_schema_org(temp_path)
            graph.load_rdf_file(temp_path)
            logger.info("Schema.org online geladen")
            graph.add_source_loaded("online_schema_org")

            # Temp-Datei löschen falls nicht gecacht werden soll
            if not source.get("cache", True):
                temp_path.unlink(missing_ok=True)

        except Exception as e:
            logger.error(f"Fehler beim Online-Laden von Schema.org: {e}")

    def _load_online_dbpedia(self, graph: OntologyGraph, source: Dict[str, Any]):
        """Lädt DBpedia-Subset online"""
        if not self._internet_available():
            logger.warning("Kein Internet verfügbar für DBpedia")
            return

        try:
            # Lade DBpedia-Subset (nur Core-Ontologie)
            dbpedia_url = source.get(
                "url", "http://downloads.dbpedia.org/2016-10/dbpedia_2016-10.owl"
            )
            cache_path = self.cache_path / "dbpedia_core.owl"

            self._download_file(dbpedia_url, cache_path)
            graph.load_owl_file(cache_path)
            logger.info("DBpedia online geladen")
            graph.add_source_loaded("online_dbpedia")

        except Exception as e:
            logger.error(f"Fehler beim Online-Laden von DBpedia: {e}")

    def _download_schema_org(self, target_path: Path):
        """Lädt Schema.org Ontologie herunter"""
        schema_org_url = "https://schema.org/version/latest/schemaorg-current-https.ttl"
        self._download_file(schema_org_url, target_path)

    def _download_file(self, url: str, target_path: Path):
        """Lädt eine Datei von URL herunter"""
        request = urllib.request.Request(url)
        request.add_header("User-Agent", "AutoGraph/1.0 (Ontology Loader)")

        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            with open(target_path, "wb") as f:
                f.write(response.read())

        logger.debug(f"Datei heruntergeladen: {url} -> {target_path}")

    def _internet_available(self) -> bool:
        """Prüft ob Internet verfügbar ist"""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=self.timeout)
            return True
        except (socket.timeout, socket.gaierror, OSError):
            return False

    def _is_cache_valid(self, cache_path: Path, duration: str) -> bool:
        """Prüft ob Cache noch gültig ist"""
        if not cache_path.exists():
            return False

        try:
            # Parse duration (e.g., "30d", "24h", "60m")
            duration = duration.lower()
            if duration.endswith("d"):
                max_age = int(duration[:-1]) * 24 * 3600
            elif duration.endswith("h"):
                max_age = int(duration[:-1]) * 3600
            elif duration.endswith("m"):
                max_age = int(duration[:-1]) * 60
            else:
                max_age = int(duration)  # Assume seconds

            file_age = time.time() - cache_path.stat().st_mtime
            return file_age < max_age

        except (ValueError, OSError):
            return False

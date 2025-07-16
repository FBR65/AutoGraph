"""
Custom Ontologie Parser für YAML-Format

Parst einfache YAML-Ontologie-Definitionen:
- Klassen mit Hierarchie
- Relations mit Domain/Range
- Namespaces und Aliases
"""

import logging
import yaml
from typing import Dict, List, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class CustomOntologyParser:
    """
    Parser für Custom YAML Ontologie-Dateien
    """

    def __init__(self):
        pass

    def parse_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Parst YAML Ontologie-Datei

        Args:
            file_path: Pfad zur YAML-Datei

        Returns:
            Dict: Geparste Ontologie-Struktur
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # Validiere Struktur
            validated_data = self._validate_ontology_structure(data, file_path)

            logger.info(f"YAML Ontologie geparst: {file_path.name}")
            return validated_data

        except yaml.YAMLError as e:
            logger.error(f"YAML Parse-Fehler in {file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Fehler beim Parsen von {file_path}: {e}")
            raise

    def _validate_ontology_structure(
        self, data: Dict[str, Any], file_path: Path
    ) -> Dict[str, Any]:
        """
        Validiert und normalisiert Ontologie-Struktur

        Args:
            data: Rohe YAML-Daten
            file_path: Pfad für Fehlermeldungen

        Returns:
            Dict: Validierte Struktur
        """
        result = {
            "namespace": data.get("namespace", "custom"),
            "version": data.get("version", "1.0"),
            "description": data.get("description", ""),
            "classes": {},
            "relations": {},
        }

        # Namespace URI
        if "namespace_uri" in data:
            result["namespace_uri"] = data["namespace_uri"]

        # Validiere Klassen
        if "classes" in data:
            result["classes"] = self._validate_classes(data["classes"], file_path)

        # Validiere Relations
        if "relations" in data:
            result["relations"] = self._validate_relations(data["relations"], file_path)

        return result

    def _validate_classes(
        self, classes_data: Dict[str, Any], file_path: Path
    ) -> Dict[str, Any]:
        """Validiert Klassen-Definitionen"""
        validated_classes = {}

        for class_name, class_def in classes_data.items():
            if not isinstance(class_name, str):
                logger.warning(f"Ungültiger Klassenname in {file_path}: {class_name}")
                continue

            validated_class = {"description": "", "aliases": [], "properties": []}

            if isinstance(class_def, dict):
                # Vollständige Klassen-Definition
                validated_class["description"] = class_def.get("description", "")
                validated_class["parent"] = class_def.get("parent")

                # Aliases normalisieren
                aliases = class_def.get("aliases", [])
                if isinstance(aliases, str):
                    aliases = [aliases]
                validated_class["aliases"] = aliases

                # Properties normalisieren
                properties = class_def.get("properties", [])
                if isinstance(properties, str):
                    properties = [properties]
                validated_class["properties"] = properties

            elif isinstance(class_def, str):
                # Einfache Definition: nur Parent
                validated_class["parent"] = class_def

            else:
                logger.warning(
                    f"Ungültige Klassen-Definition für {class_name} in {file_path}"
                )
                continue

            validated_classes[class_name] = validated_class

        return validated_classes

    def _validate_relations(
        self, relations_data: Dict[str, Any], file_path: Path
    ) -> Dict[str, Any]:
        """Validiert Relations-Definitionen"""
        validated_relations = {}

        for relation_name, relation_def in relations_data.items():
            if not isinstance(relation_name, str):
                logger.warning(
                    f"Ungültiger Relationsname in {file_path}: {relation_name}"
                )
                continue

            validated_relation = {
                "description": "",
                "aliases": [],
                "domain": [],
                "range": [],
            }

            if isinstance(relation_def, dict):
                # Vollständige Relations-Definition
                validated_relation["description"] = relation_def.get("description", "")
                validated_relation["inverse"] = relation_def.get("inverse")

                # Domain normalisieren
                domain = relation_def.get("domain", [])
                if isinstance(domain, str):
                    domain = [domain]
                validated_relation["domain"] = domain

                # Range normalisieren
                range_types = relation_def.get("range", [])
                if isinstance(range_types, str):
                    range_types = [range_types]
                validated_relation["range"] = range_types

                # Aliases normalisieren
                aliases = relation_def.get("aliases", [])
                if isinstance(aliases, str):
                    aliases = [aliases]
                validated_relation["aliases"] = aliases

                # Properties für komplexe Relations
                if "properties" in relation_def:
                    validated_relation["properties"] = relation_def["properties"]

            else:
                logger.warning(
                    f"Ungültige Relations-Definition für {relation_name} in {file_path}"
                )
                continue

            validated_relations[relation_name] = validated_relation

        return validated_relations

    def create_example_ontology(self, output_path: Path, domain: str = "example"):
        """
        Erstellt eine Beispiel-Ontologie

        Args:
            output_path: Pfad für die Ausgabe-Datei
            domain: Domain-Name für die Ontologie
        """
        example_ontology = {
            "namespace": domain,
            "namespace_uri": f"http://autograph.custom/{domain}/",
            "version": "1.0",
            "description": f"Beispiel-Ontologie für {domain}",
            "classes": {
                "Mitarbeiter": {
                    "parent": "schema:Person",
                    "description": "Person die in einem Unternehmen arbeitet",
                    "aliases": ["Employee", "Angestellter"],
                    "properties": ["abteilung", "position", "gehaltsstufe"],
                },
                "Führungskraft": {
                    "parent": f"{domain}:Mitarbeiter",
                    "description": "Mitarbeiter in Führungsposition",
                    "aliases": ["Manager", "Vorgesetzter"],
                },
                "Projekt": {
                    "parent": "schema:CreativeWork",
                    "description": "Arbeitsprojekt oder Initiative",
                    "properties": ["budget", "deadline", "status"],
                },
                "Abteilung": {
                    "parent": "schema:Organization",
                    "description": "Organisationseinheit im Unternehmen",
                },
            },
            "relations": {
                "arbeitet_an": {
                    "domain": [f"{domain}:Mitarbeiter"],
                    "range": [f"{domain}:Projekt"],
                    "description": "Mitarbeiter arbeitet an Projekt",
                    "aliases": ["works_on"],
                },
                "leitet": {
                    "domain": [f"{domain}:Führungskraft"],
                    "range": [f"{domain}:Projekt", f"{domain}:Abteilung"],
                    "description": "Führungskraft leitet Projekt oder Abteilung",
                    "aliases": ["manages", "führt"],
                },
                "berichtet_an": {
                    "domain": [f"{domain}:Mitarbeiter"],
                    "range": [f"{domain}:Führungskraft"],
                    "description": "Mitarbeiter berichtet an Führungskraft",
                    "inverse": "hat_untergebenen",
                    "properties": {
                        "hierarchie_ebene": "int",
                        "berichtszeitpunkt": "datetime",
                    },
                },
                "gehört_zu": {
                    "domain": [f"{domain}:Mitarbeiter"],
                    "range": [f"{domain}:Abteilung"],
                    "description": "Mitarbeiter gehört zu Abteilung",
                },
            },
        }

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    example_ontology,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )

            logger.info(f"Beispiel-Ontologie erstellt: {output_path}")

        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Beispiel-Ontologie: {e}")
            raise

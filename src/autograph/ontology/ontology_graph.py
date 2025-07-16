"""
Ontologie Graph - Wissensrepräsentation und Mapping

Verwaltet:
- Klassen und deren Hierarchie
- Properties/Relationen
- Namespaces
- Entity/Relation Mapping
- Semantische Validierung
"""

import logging
from typing import Dict, List, Set, Any, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class OntologyClass:
    """Repräsentiert eine Ontologie-Klasse"""

    def __init__(self, name: str, namespace: str = "local", parent: str = None):
        self.name = name
        self.namespace = namespace
        self.parent = parent
        self.children: List[str] = []
        self.properties: List[str] = []
        self.description: str = ""
        self.aliases: List[str] = []

    def full_name(self) -> str:
        """Gibt vollqualifizierten Namen zurück"""
        return f"{self.namespace}:{self.name}"

    def add_child(self, child_name: str):
        """Fügt Kind-Klasse hinzu"""
        if child_name not in self.children:
            self.children.append(child_name)

    def add_property(self, property_name: str):
        """Fügt Property hinzu"""
        if property_name not in self.properties:
            self.properties.append(property_name)


class OntologyProperty:
    """Repräsentiert eine Ontologie-Property/Relation"""

    def __init__(self, name: str, namespace: str = "local"):
        self.name = name
        self.namespace = namespace
        self.domain: List[str] = []  # Erlaubte Subject-Typen
        self.range: List[str] = []  # Erlaubte Object-Typen
        self.inverse: str = None
        self.description: str = ""
        self.aliases: List[str] = []

    def full_name(self) -> str:
        """Gibt vollqualifizierten Namen zurück"""
        return f"{self.namespace}:{self.name}"

    def add_domain(self, class_name: str):
        """Fügt erlaubten Subject-Typ hinzu"""
        if class_name not in self.domain:
            self.domain.append(class_name)

    def add_range(self, class_name: str):
        """Fügt erlaubten Object-Typ hinzu"""
        if class_name not in self.range:
            self.range.append(class_name)


class OntologyGraph:
    """
    Verwaltet die gesamte Ontologie-Struktur
    """

    def __init__(self):
        self.classes: Dict[str, OntologyClass] = {}
        self.relations: Dict[str, OntologyProperty] = {}
        self.namespaces: Dict[str, str] = {}
        self.sources_loaded: List[str] = []

        # Default Namespaces
        self.add_namespace("schema", "https://schema.org/")
        self.add_namespace("dbpedia", "http://dbpedia.org/ontology/")
        self.add_namespace("local", "http://autograph.local/")
        self.add_namespace("custom", "http://autograph.custom/")

        # Basis-Klassen hinzufügen
        self._add_base_classes()

    def _add_base_classes(self):
        """Fügt Basis-Klassen hinzu"""
        # Schema.org Basis-Klassen
        self.add_class("Thing", "schema", description="Die Basis aller Entitäten")
        self.add_class("Person", "schema", parent="schema:Thing")
        self.add_class("Organization", "schema", parent="schema:Thing")
        self.add_class("Place", "schema", parent="schema:Thing")
        self.add_class("Event", "schema", parent="schema:Thing")
        self.add_class("CreativeWork", "schema", parent="schema:Thing")

        # Basis-Relationen
        self.add_relation(
            "memberOf",
            "schema",
            domain=["schema:Person"],
            range=["schema:Organization"],
        )
        self.add_relation(
            "worksFor",
            "schema",
            domain=["schema:Person"],
            range=["schema:Organization"],
        )
        self.add_relation(
            "locatedIn", "schema", domain=["schema:Thing"], range=["schema:Place"]
        )

    def add_namespace(self, prefix: str, uri: str):
        """Fügt Namespace hinzu"""
        self.namespaces[prefix] = uri
        logger.debug(f"Namespace hinzugefügt: {prefix} -> {uri}")

    def add_class(
        self,
        name: str,
        namespace: str = "local",
        parent: str = None,
        description: str = "",
    ):
        """Fügt Ontologie-Klasse hinzu"""
        full_name = f"{namespace}:{name}"

        if full_name not in self.classes:
            self.classes[full_name] = OntologyClass(name, namespace, parent)
            self.classes[full_name].description = description

            # Zu Parent hinzufügen
            if parent and parent in self.classes:
                self.classes[parent].add_child(full_name)

            logger.debug(f"Klasse hinzugefügt: {full_name}")

    def add_relation(
        self,
        name: str,
        namespace: str = "local",
        domain: List[str] = None,
        range: List[str] = None,
        description: str = "",
    ):
        """Fügt Ontologie-Relation hinzu"""
        full_name = f"{namespace}:{name}"

        if full_name not in self.relations:
            self.relations[full_name] = OntologyProperty(name, namespace)
            self.relations[full_name].description = description

            if domain:
                for d in domain:
                    self.relations[full_name].add_domain(d)
            if range:
                for r in range:
                    self.relations[full_name].add_range(r)

            logger.debug(f"Relation hinzugefügt: {full_name}")

    def map_entity(
        self, entity: str, ner_label: str, domain: str = None
    ) -> Dict[str, Any]:
        """
        Mappt Entität auf Ontologie-Klassen

        Args:
            entity: Entity-Name
            ner_label: NER-Label (PERSON, ORG, etc.)
            domain: Domain-Kontext

        Returns:
            Dict mit Mapping-Ergebnissen
        """
        mapped_classes = []
        confidence = 0.5

        # Standard NER -> Schema.org Mapping
        ner_mappings = {
            "PERSON": ["schema:Person"],
            "ORG": ["schema:Organization"],
            "ORGANIZATION": ["schema:Organization"],
            "GPE": ["schema:Place"],
            "LOC": ["schema:Place"],
            "LOCATION": ["schema:Place"],
            "EVENT": ["schema:Event"],
            "WORK_OF_ART": ["schema:CreativeWork"],
            "PRODUCT": ["schema:Product"],
        }

        if ner_label.upper() in ner_mappings:
            mapped_classes.extend(ner_mappings[ner_label.upper()])
            confidence = 0.8

        # Domain-spezifische Mappings
        if domain:
            domain_mappings = self._get_domain_mappings(entity, ner_label, domain)
            mapped_classes.extend(domain_mappings)
            if domain_mappings:
                confidence = 0.9

        # Custom Ontologie-Suche
        custom_mappings = self._search_custom_classes(entity)
        mapped_classes.extend(custom_mappings)

        return {
            "entity": entity,
            "ner_label": ner_label,
            "mapped_classes": list(set(mapped_classes)),  # Duplikate entfernen
            "confidence": confidence,
            "domain": domain,
        }

    def map_relation(self, relation: str, domain: str = None) -> Dict[str, Any]:
        """
        Mappt Relation auf Ontologie-Properties

        Args:
            relation: Relation-Name
            domain: Domain-Kontext

        Returns:
            Dict mit Mapping-Ergebnissen
        """
        mapped_properties = []
        confidence = 0.5

        # Standard-Mappings
        relation_mappings = {
            "arbeitet_für": ["schema:worksFor"],
            "arbeitet_bei": ["schema:worksFor"],
            "ist_mitglied_von": ["schema:memberOf"],
            "gehört_zu": ["schema:memberOf"],
            "befindet_sich_in": ["schema:locatedIn"],
            "liegt_in": ["schema:locatedIn"],
            "kooperiert_mit": ["schema:partner"],
            "partner_von": ["schema:partner"],
        }

        if relation.lower() in relation_mappings:
            mapped_properties.extend(relation_mappings[relation.lower()])
            confidence = 0.8

        # Domain-spezifische Relation-Mappings
        if domain:
            domain_relations = self._get_domain_relation_mappings(relation, domain)
            mapped_properties.extend(domain_relations)
            if domain_relations:
                confidence = 0.9

        # Suche in geladenen Ontologien
        ontology_mappings = self._search_ontology_relations(relation)
        mapped_properties.extend(ontology_mappings)

        return {
            "relation": relation,
            "mapped_properties": list(set(mapped_properties)),
            "confidence": confidence,
            "domain": domain,
        }

    def validate_triple(
        self, subject_type: str, predicate: str, object_type: str
    ) -> bool:
        """
        Validiert Triple basierend auf Ontologie-Constraints

        Args:
            subject_type: Subject-Typ
            predicate: Prädikat
            object_type: Object-Typ

        Returns:
            bool: True wenn valid
        """
        if predicate not in self.relations:
            # Unbekannte Relation -> erlaubt
            return True

        relation = self.relations[predicate]

        # Prüfe Domain (Subject)
        if relation.domain:
            subject_valid = self._is_type_compatible(subject_type, relation.domain)
            if not subject_valid:
                return False

        # Prüfe Range (Object)
        if relation.range:
            object_valid = self._is_type_compatible(object_type, relation.range)
            if not object_valid:
                return False

        return True

    def _is_type_compatible(self, given_type: str, allowed_types: List[str]) -> bool:
        """Prüft ob Typ kompatibel ist (inkl. Vererbung)"""
        if given_type in allowed_types:
            return True

        # Prüfe Vererbung
        for allowed_type in allowed_types:
            if self._is_subclass_of(given_type, allowed_type):
                return True

        return False

    def _is_subclass_of(self, subclass: str, superclass: str) -> bool:
        """Prüft ob subclass eine Unterklasse von superclass ist"""
        if subclass == superclass:
            return True

        if subclass not in self.classes:
            return False

        current = self.classes[subclass]
        while current.parent:
            if current.parent == superclass:
                return True
            if current.parent in self.classes:
                current = self.classes[current.parent]
            else:
                break

        return False

    def _get_domain_mappings(
        self, entity: str, ner_label: str, domain: str
    ) -> List[str]:
        """Holt domain-spezifische Entity-Mappings"""
        mappings = []

        if domain == "medizin":
            if ner_label == "PERSON":
                # Könnte Arzt, Patient, etc. sein
                if any(word in entity.lower() for word in ["dr.", "prof.", "doktor"]):
                    mappings.append("medizin:Arzt")
                else:
                    mappings.append("medizin:Patient")
            elif ner_label == "ORG":
                mappings.append("medizin:Krankenhaus")

        elif domain == "wirtschaft":
            if ner_label == "PERSON":
                if any(
                    word in entity.lower()
                    for word in ["ceo", "geschäftsführer", "vorstand"]
                ):
                    mappings.append("wirtschaft:Führungskraft")
                else:
                    mappings.append("wirtschaft:Mitarbeiter")
            elif ner_label == "ORG":
                mappings.append("wirtschaft:Unternehmen")

        return mappings

    def _get_domain_relation_mappings(self, relation: str, domain: str) -> List[str]:
        """Holt domain-spezifische Relation-Mappings"""
        mappings = []

        if domain == "medizin":
            medizin_relations = {
                "behandelt": ["medizin:treats"],
                "diagnostiziert": ["medizin:diagnoses"],
                "verschreibt": ["medizin:prescribes"],
                "operiert": ["medizin:operates"],
                "wirkt_gegen": ["medizin:treatsCondition"],
            }
            if relation.lower() in medizin_relations:
                mappings.extend(medizin_relations[relation.lower()])

        elif domain == "wirtschaft":
            wirtschaft_relations = {
                "investiert_in": ["wirtschaft:invests"],
                "übernimmt": ["wirtschaft:acquires"],
                "konkurriert_mit": ["wirtschaft:competesWith"],
                "kooperiert_mit": ["wirtschaft:collaborates"],
                "beliefert": ["wirtschaft:supplies"],
            }
            if relation.lower() in wirtschaft_relations:
                mappings.extend(wirtschaft_relations[relation.lower()])

        return mappings

    def _search_custom_classes(self, entity: str) -> List[str]:
        """Sucht in Custom-Ontologien nach passenden Klassen"""
        matches = []

        for class_name, ontology_class in self.classes.items():
            # Exakter Match
            if ontology_class.name.lower() == entity.lower():
                matches.append(class_name)
                continue

            # Alias-Match
            if any(alias.lower() == entity.lower() for alias in ontology_class.aliases):
                matches.append(class_name)
                continue

            # Partial Match in Beschreibung
            if entity.lower() in ontology_class.description.lower():
                matches.append(class_name)

        return matches

    def _search_ontology_relations(self, relation: str) -> List[str]:
        """Sucht in Ontologien nach passenden Relations"""
        matches = []

        for prop_name, ontology_prop in self.relations.items():
            # Exakter Match
            if ontology_prop.name.lower() == relation.lower():
                matches.append(prop_name)
                continue

            # Alias-Match
            if any(
                alias.lower() == relation.lower() for alias in ontology_prop.aliases
            ):
                matches.append(prop_name)
                continue

        return matches

    def merge_custom_ontology(self, custom_ontology: Dict[str, Any]):
        """Merge Custom YAML Ontologie"""
        namespace = custom_ontology.get("namespace", "custom")

        # Namespace hinzufügen
        if "namespace_uri" in custom_ontology:
            self.add_namespace(namespace, custom_ontology["namespace_uri"])

        # Klassen hinzufügen
        for class_name, class_def in custom_ontology.get("classes", {}).items():
            parent = class_def.get("parent")
            description = class_def.get("description", "")

            self.add_class(class_name, namespace, parent, description)

            # Aliases hinzufügen
            if "aliases" in class_def:
                full_name = f"{namespace}:{class_name}"
                if full_name in self.classes:
                    self.classes[full_name].aliases.extend(class_def["aliases"])

        # Relations hinzufügen
        for rel_name, rel_def in custom_ontology.get("relations", {}).items():
            domain = rel_def.get("domain", [])
            range_types = rel_def.get("range", [])
            description = rel_def.get("description", "")

            # Ensure domain/range are lists
            if isinstance(domain, str):
                domain = [domain]
            if isinstance(range_types, str):
                range_types = [range_types]

            self.add_relation(rel_name, namespace, domain, range_types, description)

            # Aliases und Inverse
            full_name = f"{namespace}:{rel_name}"
            if full_name in self.relations:
                if "aliases" in rel_def:
                    self.relations[full_name].aliases.extend(rel_def["aliases"])
                if "inverse" in rel_def:
                    self.relations[full_name].inverse = rel_def["inverse"]

        logger.info(f"Custom Ontologie '{namespace}' gemerged")

    def load_rdf_file(self, file_path: Path):
        """Lädt RDF/TTL Datei (vereinfacht)"""
        # Hier würde normalerweise ein RDF-Parser verwendet (rdflib)
        # Für jetzt: einfacher Mock
        logger.info(f"RDF-Datei geladen: {file_path} (Mock)")
        self.add_source_loaded(f"rdf:{file_path}")

    def load_json_ld_file(self, file_path: Path):
        """Lädt JSON-LD Datei"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"JSON-LD-Datei geladen: {file_path}")
            self.add_source_loaded(f"jsonld:{file_path}")
        except Exception as e:
            logger.error(f"Fehler beim Laden von JSON-LD {file_path}: {e}")

    def load_owl_file(self, file_path: Path):
        """Lädt OWL Datei"""
        # OWL-Parser würde hier implementiert
        logger.info(f"OWL-Datei geladen: {file_path} (Mock)")
        self.add_source_loaded(f"owl:{file_path}")

    def add_source_loaded(self, source: str):
        """Fügt geladene Quelle zur Liste hinzu"""
        if source not in self.sources_loaded:
            self.sources_loaded.append(source)

    def get_stats(self) -> Dict[str, Any]:
        """Liefert Statistiken über die Ontologie"""
        return {
            "classes_count": len(self.classes),
            "relations_count": len(self.relations),
            "namespaces_count": len(self.namespaces),
            "sources_loaded": len(self.sources_loaded),
            "namespaces": list(self.namespaces.keys()),
        }

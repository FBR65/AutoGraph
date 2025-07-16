"""
Entity Linking - Offline-First Architecture

Verknüpft erkannte Entitäten mit Wissensdatenbanken unter Berücksichtigung von
Air-Gapped Systemen und Enterprise-Sicherheitsanforderungen.

Features:
- Offline-First: Funktioniert ohne Internet (Air-Gapped)
- Custom Entity-Kataloge: YAML/JSON für firmen-spezifische Entitäten
- Domain-spezifisch: Medizin, Wirtschaft, Wissenschaft
- Cached Knowledge Bases: Wikidata, DBpedia offline verfügbar
- Disambiguation: Kontext-basierte Mehrdeutigkeitsauflösung
"""

import logging
import yaml
from typing import List, Dict, Any, Optional
from pathlib import Path
import pickle
from datetime import datetime

from .base import BaseProcessor
from ..ontology import OntologyManager


class EntityLinker(BaseProcessor):
    """
    Offline-First Entity Linking mit Enterprise-Support

    Modi:
    - offline: Nur lokale/custom Kataloge (Air-Gapped)
    - hybrid: Lokale Priorität + Online-Fallback (Enterprise)
    - online: Bevorzugt Online-Quellen (Cloud/Development)
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)

        # Konfiguration
        self.mode = self.config.get("entity_linking_mode", "offline")
        self.confidence_threshold = self.config.get(
            "entity_linking_confidence_threshold", 0.5
        )
        self.custom_catalogs_dir = self.config.get(
            "custom_entity_catalogs_dir", "./entity_catalogs/"
        )
        self.cache_dir = self.config.get("entity_cache_dir", "./cache/entities/")
        self.cache_duration_days = self.config.get("cache_duration_days", 30)

        # Ontologie-Integration
        self.ontology_manager = None
        if self.config.get("use_ontology_for_linking", True):
            try:
                self.ontology_manager = OntologyManager(self.config)
                self.logger.info(
                    "[OK] Ontologie-Integration für Entity Linking aktiviert"
                )
            except Exception as e:
                self.logger.warning(
                    f"[WARN] Ontologie-Integration nicht verfügbar: {e}"
                )

        # Cache-Verzeichnis erstellen
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
        Path(self.custom_catalogs_dir).mkdir(parents=True, exist_ok=True)

        # Entity-Kataloge laden
        self.entity_catalogs = self._load_entity_catalogs()

        # Disambiguation-Modelle
        self.disambiguation_weights = {
            "exact_match": 1.0,
            "alias_match": 0.9,
            "fuzzy_match": 0.7,
            "context_similarity": 0.8,
            "domain_relevance": 0.9,
            "ontology_mapping": 0.95,
        }

        self.logger.info(
            f"[LINK] EntityLinker initialisiert (Modus: {self.mode}, "
            f"Kataloge: {len(self.entity_catalogs)}, "
            f"Threshold: {self.confidence_threshold})"
        )

    def _load_entity_catalogs(self) -> Dict[str, Dict]:
        """Lädt alle verfügbaren Entity-Kataloge"""
        catalogs = {}

        # 1. Custom YAML-Kataloge laden
        custom_path = Path(self.custom_catalogs_dir)
        if custom_path.exists():
            for catalog_file in custom_path.glob("*.yaml"):
                try:
                    with open(catalog_file, "r", encoding="utf-8") as f:
                        catalog_data = yaml.safe_load(f)
                        domain = catalog_file.stem
                        catalogs[f"custom_{domain}"] = catalog_data
                        self.logger.info(f"[OK] Custom Katalog geladen: {domain}")
                except Exception as e:
                    self.logger.error(
                        f"[ERROR] Fehler beim Laden von {catalog_file}: {e}"
                    )

        # 2. Cached Online-Kataloge laden (wenn Hybrid/Online-Modus)
        if self.mode in ["hybrid", "online"]:
            cached_catalogs = self._load_cached_catalogs()
            catalogs.update(cached_catalogs)

        # 3. Standard-Kataloge
        builtin_catalogs = self._create_builtin_catalogs()
        catalogs.update(builtin_catalogs)

        return catalogs

    def _create_builtin_catalogs(self) -> Dict[str, Dict]:
        """Erstellt eingebaute Entity-Kataloge für häufige Entitäten"""
        return {
            "builtin_organizations": {
                "entities": {
                    "BMW": {
                        "canonical_name": "BMW AG",
                        "aliases": ["BMW", "Bayerische Motoren Werke", "BMW Group"],
                        "type": "ORG",
                        "domain": "wirtschaft",
                        "description": "Deutscher Automobilhersteller",
                        "uri": "http://autograph.local/BMW_AG",
                        "properties": {
                            "industry": "Automotive",
                            "founded": "1916",
                            "headquarters": "München",
                        },
                    },
                    "Siemens": {
                        "canonical_name": "Siemens AG",
                        "aliases": ["Siemens", "Siemens AG"],
                        "type": "ORG",
                        "domain": "wirtschaft",
                        "description": "Deutscher Technologiekonzern",
                        "uri": "http://autograph.local/Siemens_AG",
                        "properties": {
                            "industry": "Technology",
                            "founded": "1847",
                            "headquarters": "München",
                        },
                    },
                }
            },
            "builtin_locations": {
                "entities": {
                    "München": {
                        "canonical_name": "München",
                        "aliases": ["München", "Munich", "Muenchen"],
                        "type": "LOC",
                        "domain": "allgemein",
                        "description": "Hauptstadt von Bayern",
                        "uri": "http://autograph.local/München",
                        "properties": {
                            "country": "Deutschland",
                            "state": "Bayern",
                            "population": "1.5M",
                        },
                    },
                    "Berlin": {
                        "canonical_name": "Berlin",
                        "aliases": ["Berlin"],
                        "type": "LOC",
                        "domain": "allgemein",
                        "description": "Hauptstadt von Deutschland",
                        "uri": "http://autograph.local/Berlin",
                        "properties": {"country": "Deutschland", "capital": "true"},
                    },
                }
            },
        }

    def _load_cached_catalogs(self) -> Dict[str, Dict]:
        """Lädt gecachte Online-Kataloge"""
        cached = {}
        cache_path = Path(self.cache_dir)

        for cache_file in cache_path.glob("*.pkl"):
            try:
                # Cache-Alter prüfen
                cache_age = datetime.now() - datetime.fromtimestamp(
                    cache_file.stat().st_mtime
                )
                if cache_age.days > self.cache_duration_days:
                    self.logger.info(
                        f"[CACHE] Veralteter Cache gelöscht: {cache_file.name}"
                    )
                    cache_file.unlink()
                    continue

                with open(cache_file, "rb") as f:
                    catalog_data = pickle.load(f)
                    catalog_name = f"cached_{cache_file.stem}"
                    cached[catalog_name] = catalog_data
                    self.logger.info(
                        f"[CACHE] Cached Katalog geladen: {cache_file.stem}"
                    )
            except Exception as e:
                self.logger.error(
                    f"[ERROR] Fehler beim Laden des Caches {cache_file}: {e}"
                )

        return cached

    def process(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Führt Entity Linking für alle erkannten Entitäten durch"""
        linked_entities = []
        linking_stats = {
            "total_entities": 0,
            "linked_entities": 0,
            "high_confidence_links": 0,
            "disambiguation_cases": 0,
        }

        for item in data:
            entities = item.get("entities", [])
            domain = item.get("domain", "allgemein")
            context = item.get("content", "")

            for entity in entities:
                linking_stats["total_entities"] += 1

                # Entity Linking durchführen
                linked_entity = self._link_entity(entity, domain, context)

                if linked_entity:
                    linking_stats["linked_entities"] += 1
                    if linked_entity.get("confidence", 0) >= 0.9:
                        linking_stats["high_confidence_links"] += 1
                    if len(linked_entity.get("candidates", [])) > 1:
                        linking_stats["disambiguation_cases"] += 1

                linked_entities.append(linked_entity or entity)

        self.logger.info(
            f"[LINK] Entity Linking abgeschlossen: "
            f"{linking_stats['linked_entities']}/{linking_stats['total_entities']} verknüpft "
            f"({linking_stats['high_confidence_links']} high-confidence)"
        )

        return {
            "entities": linked_entities,
            "metadata": {
                "processor": "EntityLinker",
                "mode": self.mode,
                "stats": linking_stats,
                "catalogs_used": list(self.entity_catalogs.keys()),
            },
        }

    def _link_entity(
        self, entity: Dict[str, Any], domain: str, context: str
    ) -> Optional[Dict[str, Any]]:
        """Verknüpft eine einzelne Entität mit Wissensdatenbanken"""
        entity_text = entity.get("text", "").strip()
        entity_type = entity.get("label", entity.get("type", "ENTITY"))

        if not entity_text:
            return None

        # 1. Kandidaten aus allen Katalogen sammeln
        candidates = self._find_candidates(entity_text, entity_type, domain)

        if not candidates:
            return self._create_unlinked_entity(entity, "no_candidates")

        # 2. Disambiguation durchführen
        best_candidate = self._disambiguate_candidates(
            entity_text, entity_type, candidates, context, domain
        )

        if (
            not best_candidate
            or best_candidate["confidence"] < self.confidence_threshold
        ):
            return self._create_unlinked_entity(entity, "low_confidence")

        # 3. Linked Entity erstellen
        return self._create_linked_entity(entity, best_candidate, candidates)

    def _find_candidates(
        self, entity_text: str, entity_type: str, domain: str
    ) -> List[Dict[str, Any]]:
        """Findet Kandidaten aus allen verfügbaren Katalogen"""
        candidates = []

        for catalog_name, catalog in self.entity_catalogs.items():
            catalog_entities = catalog.get("entities", {})

            for canonical_name, entity_data in catalog_entities.items():
                # Type-Filter (falls spezifiziert)
                if entity_data.get("type") and entity_data["type"] != entity_type:
                    continue

                # Exact Match
                if entity_text.lower() == canonical_name.lower():
                    candidates.append(
                        {
                            "canonical_name": canonical_name,
                            "match_type": "exact",
                            "confidence": 1.0,
                            "catalog": catalog_name,
                            **entity_data,
                        }
                    )
                    continue

                # Alias Match
                aliases = entity_data.get("aliases", [])
                for alias in aliases:
                    if entity_text.lower() == alias.lower():
                        candidates.append(
                            {
                                "canonical_name": canonical_name,
                                "match_type": "alias",
                                "confidence": 0.9,
                                "matched_alias": alias,
                                "catalog": catalog_name,
                                **entity_data,
                            }
                        )
                        continue

                # Fuzzy Match (einfache Substring-Suche)
                if (
                    entity_text.lower() in canonical_name.lower()
                    or canonical_name.lower() in entity_text.lower()
                ):
                    candidates.append(
                        {
                            "canonical_name": canonical_name,
                            "match_type": "fuzzy",
                            "confidence": 0.7,
                            "catalog": catalog_name,
                            **entity_data,
                        }
                    )

        return candidates

    def _disambiguate_candidates(
        self,
        entity_text: str,
        entity_type: str,
        candidates: List[Dict],
        context: str,
        domain: str,
    ) -> Optional[Dict[str, Any]]:
        """Führt Disambiguation bei mehreren Kandidaten durch"""
        if len(candidates) == 1:
            return candidates[0]

        if not candidates:
            return None

        # Scoring für jeden Kandidaten
        scored_candidates = []

        for candidate in candidates:
            score = self._calculate_candidate_score(
                entity_text, entity_type, candidate, context, domain
            )
            candidate["disambiguation_score"] = score
            scored_candidates.append(candidate)

        # Besten Kandidaten wählen
        best_candidate = max(scored_candidates, key=lambda x: x["disambiguation_score"])

        # Ontologie-basierte Validierung (falls verfügbar)
        if self.ontology_manager:
            ontology_score = self._get_ontology_score(best_candidate, domain)
            best_candidate["disambiguation_score"] *= ontology_score

        best_candidate["confidence"] = min(1.0, best_candidate["disambiguation_score"])
        return best_candidate

    def _calculate_candidate_score(
        self,
        entity_text: str,
        entity_type: str,
        candidate: Dict,
        context: str,
        domain: str,
    ) -> float:
        """Berechnet Disambiguation-Score für einen Kandidaten"""
        score = candidate.get("confidence", 0.5)

        # Match-Type Gewichtung
        match_type = candidate.get("match_type", "fuzzy")
        score *= self.disambiguation_weights.get(match_type, 0.5)

        # Domain-Relevanz
        candidate_domain = candidate.get("domain", "allgemein")
        if candidate_domain == domain:
            score *= self.disambiguation_weights["domain_relevance"]
        elif candidate_domain == "allgemein":
            score *= 0.8  # Neutral
        else:
            score *= 0.6  # Penalty für falsche Domäne

        # Context-Similarity (einfache Keyword-Überschneidung)
        context_score = self._calculate_context_similarity(candidate, context)
        score *= 1.0 + context_score * 0.3  # Bonus bis zu 30%

        # Catalog-Priorität
        catalog_priority = self._get_catalog_priority(candidate.get("catalog", ""))
        score *= catalog_priority

        return min(1.0, score)

    def _calculate_context_similarity(self, candidate: Dict, context: str) -> float:
        """Berechnet Kontext-Ähnlichkeit (einfache Implementierung)"""
        if not context:
            return 0.0

        context_lower = context.lower()

        # Eigenschaften des Kandidaten prüfen
        properties = candidate.get("properties", {})
        description = candidate.get("description", "")

        keywords = []
        keywords.extend(description.lower().split())
        for prop_value in properties.values():
            if isinstance(prop_value, str):
                keywords.extend(prop_value.lower().split())

        # Überschneidung zählen
        matches = sum(1 for keyword in keywords if keyword in context_lower)

        if not keywords:
            return 0.0

        return min(1.0, matches / len(keywords))

    def _get_catalog_priority(self, catalog_name: str) -> float:
        """Gibt Priorität für verschiedene Kataloge zurück"""
        if catalog_name.startswith("custom_"):
            return 1.0  # Höchste Priorität für Custom-Kataloge
        elif catalog_name.startswith("cached_"):
            return 0.9  # Cached Online-Daten
        elif catalog_name.startswith("builtin_"):
            return 0.8  # Eingebaute Kataloge
        else:
            return 0.7  # Fallback

    def _get_ontology_score(self, candidate: Dict, domain: str) -> float:
        """Validiert Kandidaten gegen Ontologie (falls verfügbar)"""
        if not self.ontology_manager:
            return 1.0

        try:
            # Prüfe ob Entität in Ontologie existiert
            entity_type = candidate.get("type", "ENTITY")
            canonical_name = candidate.get("canonical_name", "")

            mapping = self.ontology_manager.map_entity(
                canonical_name, entity_type, domain
            )

            if mapping and mapping.get("confidence", 0) > 0.7:
                return self.disambiguation_weights["ontology_mapping"]
            else:
                return 0.9  # Leichte Penalty wenn nicht in Ontologie

        except Exception as e:
            self.logger.debug(f"Ontologie-Validierung fehlgeschlagen: {e}")
            return 1.0  # Neutral bei Fehlern

    def _create_linked_entity(
        self, original_entity: Dict, best_candidate: Dict, all_candidates: List[Dict]
    ) -> Dict[str, Any]:
        """Erstellt verknüpfte Entität mit allen Metadaten"""
        return {
            **original_entity,  # Original-Daten behalten
            "linked": True,
            "canonical_name": best_candidate.get("canonical_name"),
            "uri": best_candidate.get("uri"),
            "description": best_candidate.get("description"),
            "properties": best_candidate.get("properties", {}),
            "confidence": best_candidate.get("confidence"),
            "linking_metadata": {
                "match_type": best_candidate.get("match_type"),
                "catalog": best_candidate.get("catalog"),
                "disambiguation_score": best_candidate.get("disambiguation_score"),
                "candidates_count": len(all_candidates),
                "matched_alias": best_candidate.get("matched_alias"),
            },
        }

    def _create_unlinked_entity(self, entity: Dict, reason: str) -> Dict[str, Any]:
        """Erstellt unverknüpfte Entität mit Grund"""
        return {
            **entity,
            "linked": False,
            "linking_metadata": {
                "unlinked_reason": reason,
                "processor": "EntityLinker",
            },
        }

    def create_custom_catalog_example(self, domain: str, output_path: str) -> None:
        """Erstellt Beispiel-Katalog für eine Domäne"""
        example_catalog = {
            "catalog_info": {
                "domain": domain,
                "created": datetime.now().isoformat(),
                "description": f"Custom Entity-Katalog für {domain}",
                "version": "1.0",
            },
            "entities": {
                "Beispiel_Entität": {
                    "canonical_name": "Beispiel Entität GmbH",
                    "aliases": ["Beispiel", "Beispiel GmbH", "Beispiel Firma"],
                    "type": "ORG",
                    "domain": domain,
                    "description": "Beispiel-Unternehmen für Katalog-Demo",
                    "uri": f"http://autograph.custom/{domain}/beispiel_entitaet",
                    "properties": {
                        "industry": f"{domain.title()}",
                        "founded": "2020",
                        "employees": "100-500",
                    },
                }
            },
        }

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            yaml.dump(example_catalog, f, default_flow_style=False, allow_unicode=True)

        self.logger.info(f"[OK] Beispiel-Katalog erstellt: {output_path}")

    def get_linking_statistics(self) -> Dict[str, Any]:
        """Gibt Entity-Linking Statistiken zurück"""
        return {
            "mode": self.mode,
            "catalogs": {
                name: len(catalog.get("entities", {}))
                for name, catalog in self.entity_catalogs.items()
            },
            "total_entities_in_catalogs": sum(
                len(catalog.get("entities", {}))
                for catalog in self.entity_catalogs.values()
            ),
            "confidence_threshold": self.confidence_threshold,
            "cache_dir": str(self.cache_dir),
            "custom_catalogs_dir": str(self.custom_catalogs_dir),
        }

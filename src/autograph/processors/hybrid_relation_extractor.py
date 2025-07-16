"""
Hybrid Relation Extractor - Kombiniert regel-basierte und ML-basierte Ansätze

Diese Klasse integriert:
- Rule-based RelationExtractor (syntaktische Muster)
- ML-based RelationExtractor (BERT + Transformers)
- Intelligente Ensemble-Methoden
- Performance-optimierte Pipeline
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
import time

from .base import BaseProcessor
from .relation_extractor import RelationExtractor
from .ml_relation_extractor import MLRelationExtractor
from .ml_config import MLRelationConfig
from ..core.cache import cache_async_method


class HybridRelationExtractor(BaseProcessor):
    """
    Hybrid Relation Extractor kombiniert Rule-based und ML-basierte Ansätze

    Features:
    - Parallele Ausführung beider Extraktoren
    - Intelligente Ensemble-Methoden
    - Confidence-basierte Gewichtung
    - Adaptive Threshold-Anpassung
    - Performance-Monitoring
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)

        # Konfiguration
        self.use_ml = self.config.get("use_ml_relations", True)
        self.use_rules = self.config.get("use_rule_relations", True)
        self.ensemble_method = self.config.get("ensemble_method", "weighted_union")
        self.ml_weight = self.config.get("ml_weight", 0.7)
        self.rule_weight = self.config.get("rule_weight", 0.3)
        self.enable_parallel = self.config.get("enable_parallel_extraction", True)

        # ML-Konfiguration
        ml_config = MLRelationConfig()
        if "ml_relation_config" in self.config:
            # Override mit custom config
            for key, value in self.config["ml_relation_config"].items():
                if hasattr(ml_config, key):
                    setattr(ml_config, key, value)

        # Extraktoren initialisieren
        self.rule_extractor = RelationExtractor(config) if self.use_rules else None
        self.ml_extractor = (
            MLRelationExtractor(ml_config.to_dict()) if self.use_ml else None
        )

        # Cache Manager
        self.cache_manager = None

        # Performance Monitoring
        self.performance_stats = {
            "rule_times": [],
            "ml_times": [],
            "ensemble_times": [],
            "total_relations": 0,
            "rule_relations": 0,
            "ml_relations": 0,
        }

        extraction_methods = []
        if self.use_rules:
            extraction_methods.append("rules")
        if self.use_ml:
            extraction_methods.append("ML")

        self.logger.info(
            f"🔄 Hybrid RelationExtractor initialisiert: {', '.join(extraction_methods)}"
        )

    def process(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Synchrone Wrapper für process_async (erforderlich von BaseProcessor)"""
        return asyncio.run(self.process_async(data))

    def set_cache_manager(self, cache_manager):
        """Setzt Cache Manager für alle Extraktoren"""
        self.cache_manager = cache_manager
        if self.rule_extractor:
            self.rule_extractor.cache_manager = cache_manager
        if self.ml_extractor:
            self.ml_extractor.cache_manager = cache_manager

    @cache_async_method(cache_type="hybrid_relations", ttl=3600)
    async def process_async(self, data: Any, domain: str = None) -> Dict[str, Any]:
        """
        Hauptmethode für Hybrid Relation Extraction
        """
        start_time = time.time()
        self.logger.info(f"🔄 Starte Hybrid Relation Extraction (Domain: {domain})")

        # Input validation
        if isinstance(data, str):
            text = data
            entities = []
        elif isinstance(data, dict):
            text = data.get("text", "")
            entities = data.get("entities", [])
        else:
            raise ValueError(f"Unsupported data type: {type(data)}")

        if not text.strip():
            return {
                "relationships": [],
                "metadata": {"method": "hybrid", "error": "empty_text"},
            }

        # Erweiterte Daten für Extraktoren
        extraction_data = {"text": text, "entities": entities}

        # Parallele oder sequenzielle Ausführung
        if self.enable_parallel and self.use_rules and self.use_ml:
            rule_result, ml_result = await self._parallel_extraction(
                extraction_data, domain
            )
        else:
            rule_result = (
                await self._rule_extraction(extraction_data, domain)
                if self.use_rules
                else None
            )
            ml_result = (
                await self._ml_extraction(extraction_data, domain)
                if self.use_ml
                else None
            )

        # Ensemble-Verarbeitung
        ensemble_start = time.time()
        final_relations = self._ensemble_relations(rule_result, ml_result, domain)
        ensemble_time = time.time() - ensemble_start

        # Performance-Statistiken aktualisieren
        self.performance_stats["ensemble_times"].append(ensemble_time)
        self.performance_stats["total_relations"] += len(final_relations)

        total_time = time.time() - start_time

        # Metadata zusammenstellen
        metadata = {
            "method": "hybrid",
            "ensemble_method": self.ensemble_method,
            "extractors_used": self._get_used_extractors(),
            "total_time": total_time,
            "rule_relations": len(rule_result.get("relationships", []))
            if rule_result
            else 0,
            "ml_relations": len(ml_result.get("relationships", [])) if ml_result else 0,
            "final_relations": len(final_relations),
            "ensemble_time": ensemble_time,
            "domain": domain,
        }

        # Extractor-spezifische Metadaten hinzufügen
        if rule_result:
            metadata["rule_metadata"] = rule_result.get("metadata", {})
        if ml_result:
            metadata["ml_metadata"] = ml_result.get("metadata", {})

        self.logger.info(
            f"✅ Hybrid Extraction: {len(final_relations)} Beziehungen in {total_time:.2f}s "
            f"(Rules: {metadata['rule_relations']}, ML: {metadata['ml_relations']})"
        )

        return {"relationships": final_relations, "metadata": metadata}

    async def _parallel_extraction(self, data: Dict, domain: str) -> tuple:
        """Führt Rule-based und ML-basierte Extraktion parallel aus"""
        tasks = []

        if self.rule_extractor:
            tasks.append(self._rule_extraction(data, domain))
        else:
            tasks.append(asyncio.create_task(self._empty_result()))

        if self.ml_extractor:
            tasks.append(self._ml_extraction(data, domain))
        else:
            tasks.append(asyncio.create_task(self._empty_result()))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Fehlerbehandlung
        rule_result = results[0] if not isinstance(results[0], Exception) else None
        ml_result = results[1] if not isinstance(results[1], Exception) else None

        if isinstance(results[0], Exception):
            self.logger.error(f"Rule extraction failed: {results[0]}")
        if isinstance(results[1], Exception):
            self.logger.error(f"ML extraction failed: {results[1]}")

        return rule_result, ml_result

    async def _rule_extraction(self, data: Dict, domain: str) -> Dict:
        """Rule-basierte Extraktion mit Performance-Monitoring"""
        if not self.rule_extractor:
            return {
                "relationships": [],
                "metadata": {"method": "rules", "skipped": True},
            }

        start_time = time.time()
        try:
            result = await self.rule_extractor.process_async(data, domain)
            extraction_time = time.time() - start_time
            self.performance_stats["rule_times"].append(extraction_time)
            self.performance_stats["rule_relations"] += len(
                result.get("relationships", [])
            )
            return result
        except Exception as e:
            self.logger.error(f"Rule extraction error: {e}")
            return {
                "relationships": [],
                "metadata": {"method": "rules", "error": str(e)},
            }

    async def _ml_extraction(self, data: Dict, domain: str) -> Dict:
        """ML-basierte Extraktion mit Performance-Monitoring"""
        if not self.ml_extractor:
            return {"relationships": [], "metadata": {"method": "ml", "skipped": True}}

        start_time = time.time()
        try:
            result = await self.ml_extractor.process_async(data, domain)
            extraction_time = time.time() - start_time
            self.performance_stats["ml_times"].append(extraction_time)
            self.performance_stats["ml_relations"] += len(
                result.get("relationships", [])
            )
            return result
        except Exception as e:
            self.logger.error(f"ML extraction error: {e}")
            return {"relationships": [], "metadata": {"method": "ml", "error": str(e)}}

    async def _empty_result(self) -> Dict:
        """Leeres Ergebnis für deaktivierte Extraktoren"""
        return {"relationships": [], "metadata": {"skipped": True}}

    def _ensemble_relations(
        self, rule_result: Dict, ml_result: Dict, domain: str
    ) -> List[Dict]:
        """Verbesserte Ensemble-Verarbeitung mit Performance-Monitoring"""
        rule_relations = rule_result.get("relationships", []) if rule_result else []
        ml_relations = ml_result.get("relationships", []) if ml_result else []

        self.logger.info(
            f"📊 Ensemble Input: {len(rule_relations)} Rules, {len(ml_relations)} ML"
        )

        # Ensemble-Verarbeitung
        if self.ensemble_method == "union":
            result = self._union_ensemble(rule_relations, ml_relations)
        elif self.ensemble_method == "weighted_union":
            result = self._improved_weighted_union(rule_relations, ml_relations)
        elif self.ensemble_method == "intersection":
            result = self._intersection_ensemble(rule_relations, ml_relations)
        elif self.ensemble_method == "ml_priority":
            result = self._ml_priority_ensemble(rule_relations, ml_relations)
        elif self.ensemble_method == "confidence_threshold":
            result = self._confidence_threshold_ensemble(rule_relations, ml_relations)
        else:
            self.logger.warning(f"Unknown ensemble method: {self.ensemble_method}")
            result = self._improved_weighted_union(rule_relations, ml_relations)

        # Performance-Warnung bei schlechtem Ensemble-Ergebnis
        input_total = len(rule_relations) + len(ml_relations)
        if input_total > 0 and len(result) < max(
            len(rule_relations), len(ml_relations)
        ):
            loss_ratio = (input_total - len(result)) / input_total
            if loss_ratio > 0.5:  # Mehr als 50% Verlust
                self.logger.warning(
                    f"⚠️ Ensemble-Performance-Issue: {loss_ratio:.1%} Relation-Verlust "
                    f"({input_total} → {len(result)}). Methode: {self.ensemble_method}"
                )

        return result

    def _union_ensemble(
        self, rule_relations: List[Dict], ml_relations: List[Dict]
    ) -> List[Dict]:
        """Einfache Union aller Relationen"""
        all_relations = rule_relations + ml_relations
        return self._deduplicate_relations(all_relations)

    def _improved_weighted_union(
        self, rule_relations: List[Dict], ml_relations: List[Dict]
    ) -> List[Dict]:
        """Verbesserte gewichtete Union mit intelligenteren Regeln"""
        # Adaptive Gewichtung basierend auf Anzahl der Relationen
        rule_count = len(rule_relations)
        ml_count = len(ml_relations)

        # Dynamische Gewichtung wenn eine Quelle deutlich mehr Relationen hat
        adaptive_rule_weight = self.rule_weight
        adaptive_ml_weight = self.ml_weight

        if rule_count > 0 and ml_count > 0:
            total_count = rule_count + ml_count
            if rule_count / total_count > 0.8:  # Rules dominieren
                adaptive_ml_weight *= 1.2  # Boost ML
                self.logger.info("🔧 Adaptive Gewichtung: ML-Boost da Rules dominieren")
            elif ml_count / total_count > 0.8:  # ML dominiert
                adaptive_rule_weight *= 1.2  # Boost Rules
                self.logger.info("🔧 Adaptive Gewichtung: Rules-Boost da ML dominiert")

        # Gewichtung anwenden
        for rel in rule_relations:
            original_conf = rel.get("confidence", 0.5)
            rel["confidence"] = original_conf * adaptive_rule_weight
            rel["ensemble_source"] = "rules"
            rel["original_confidence"] = original_conf

        for rel in ml_relations:
            original_conf = rel.get("confidence", 0.5)
            rel["confidence"] = original_conf * adaptive_ml_weight
            rel["ensemble_source"] = "ml"
            rel["original_confidence"] = original_conf

        all_relations = rule_relations + ml_relations

        # Duplikate mit besserer Merge-Logik
        merged = self._intelligent_merge_relations(all_relations)

        # Mindest-Threshold für finale Auswahl
        min_threshold = 0.3  # Weniger restriktiv
        filtered = [r for r in merged if r.get("confidence", 0) >= min_threshold]

        self.logger.info(
            f"🔧 Weighted Union: {len(all_relations)} → {len(merged)} → {len(filtered)} "
            f"(Weights: R={adaptive_rule_weight:.2f}, ML={adaptive_ml_weight:.2f})"
        )

        return filtered

    def _intelligent_merge_relations(self, relations: List[Dict]) -> List[Dict]:
        """Intelligente Duplikat-Behandlung mit Confidence-Boost bei Übereinstimmung"""
        relation_groups = {}

        for rel in relations:
            # Erstelle Schlüssel für Duplikat-Erkennung
            key = (
                rel.get("source", "").lower(),
                rel.get("target", "").lower(),
                rel.get("relationship", "").lower(),
            )

            if key not in relation_groups:
                relation_groups[key] = []
            relation_groups[key].append(rel)

        merged_relations = []

        for key, group in relation_groups.items():
            if len(group) == 1:
                # Keine Duplikate
                merged_relations.append(group[0])
            else:
                # Duplikate gefunden - merge mit Confidence-Boost
                best_rel = max(group, key=lambda x: x.get("confidence", 0))

                # Confidence-Boost bei Übereinstimmung verschiedener Quellen
                sources = set(rel.get("ensemble_source", "unknown") for rel in group)
                if len(sources) > 1:  # Rules + ML stimmen überein
                    boost_factor = 1.3
                    best_rel["confidence"] = min(
                        1.0, best_rel["confidence"] * boost_factor
                    )
                    best_rel["ensemble_agreement"] = True
                    self.logger.debug(
                        f"🤝 Consensus-Boost für: {key[0]} --[{key[2]}]--> {key[1]}"
                    )

                merged_relations.append(best_rel)

        return merged_relations

    def _intersection_ensemble(
        self, rule_relations: List[Dict], ml_relations: List[Dict]
    ) -> List[Dict]:
        """Nur Relationen, die von beiden Extraktoren gefunden wurden"""
        intersection = []

        for rule_rel in rule_relations:
            for ml_rel in ml_relations:
                if self._relations_similar(rule_rel, ml_rel):
                    # Kombinierte Confidence
                    combined_confidence = (
                        rule_rel.get("confidence", 0.5) * self.rule_weight
                        + ml_rel.get("confidence", 0.5) * self.ml_weight
                    )

                    merged_rel = rule_rel.copy()
                    merged_rel["confidence"] = combined_confidence
                    merged_rel["ensemble_source"] = "both"
                    intersection.append(merged_rel)
                    break

        return intersection

    def _ml_priority_ensemble(
        self, rule_relations: List[Dict], ml_relations: List[Dict]
    ) -> List[Dict]:
        """ML-Relationen haben Priorität, Rules füllen Lücken"""
        result = ml_relations.copy()

        for rule_rel in rule_relations:
            if not any(
                self._relations_similar(rule_rel, ml_rel) for ml_rel in ml_relations
            ):
                rule_rel["ensemble_source"] = "rules_supplement"
                result.append(rule_rel)

        return result

    def _confidence_threshold_ensemble(
        self, rule_relations: List[Dict], ml_relations: List[Dict]
    ) -> List[Dict]:
        """Adaptive Confidence-basierte Auswahl"""
        high_confidence_threshold = 0.8
        medium_confidence_threshold = 0.6

        result = []

        # Hohe Confidence: Beide Quellen
        for rel in rule_relations + ml_relations:
            if rel.get("confidence", 0) >= high_confidence_threshold:
                result.append(rel)

        # Mittlere Confidence: Nur wenn von beiden bestätigt
        medium_confidence_rels = [
            rel
            for rel in rule_relations + ml_relations
            if medium_confidence_threshold
            <= rel.get("confidence", 0)
            < high_confidence_threshold
        ]

        for rel in medium_confidence_rels:
            other_source = ml_relations if rel in rule_relations else rule_relations
            if any(
                self._relations_similar(rel, other_rel) for other_rel in other_source
            ):
                result.append(rel)

        return self._deduplicate_relations(result)

    def _relations_similar(
        self, rel1: Dict, rel2: Dict, threshold: float = 0.8
    ) -> bool:
        """Prüft ob zwei Relationen ähnlich sind"""
        # Exact match für Entity-Paare
        if rel1.get("source") == rel2.get("source") and rel1.get("target") == rel2.get(
            "target"
        ):
            return True

        # Reverse match
        if rel1.get("source") == rel2.get("target") and rel1.get("target") == rel2.get(
            "source"
        ):
            return True

        return False

    def _merge_duplicate_relations(self, relations: List[Dict]) -> List[Dict]:
        """Merged Duplikate und behält höchste Confidence"""
        merged = {}

        for rel in relations:
            key = (rel.get("source"), rel.get("target"), rel.get("relationship"))
            reverse_key = (
                rel.get("target"),
                rel.get("source"),
                rel.get("relationship"),
            )

            # Verwende existing key wenn vorhanden
            if key in merged:
                if rel.get("confidence", 0) > merged[key].get("confidence", 0):
                    merged[key] = rel
            elif reverse_key in merged:
                if rel.get("confidence", 0) > merged[reverse_key].get("confidence", 0):
                    merged[reverse_key] = rel
            else:
                merged[key] = rel

        return list(merged.values())

    def _deduplicate_relations(self, relations: List[Dict]) -> List[Dict]:
        """Entfernt exakte Duplikate"""
        seen = set()
        unique = []

        for rel in relations:
            # Erstelle Hash aus relevanten Feldern
            rel_hash = (rel.get("source"), rel.get("target"), rel.get("relationship"))

            if rel_hash not in seen:
                seen.add(rel_hash)
                unique.append(rel)

        return unique

    def _get_used_extractors(self) -> List[str]:
        """Gibt Liste der verwendeten Extraktoren zurück"""
        extractors = []
        if self.use_rules and self.rule_extractor:
            extractors.append("rules")
        if self.use_ml and self.ml_extractor:
            extractors.append("ml")
        return extractors

    def get_performance_stats(self) -> Dict[str, Any]:
        """Gibt Performance-Statistiken zurück"""
        stats = self.performance_stats.copy()

        if stats["rule_times"]:
            stats["avg_rule_time"] = sum(stats["rule_times"]) / len(stats["rule_times"])
        if stats["ml_times"]:
            stats["avg_ml_time"] = sum(stats["ml_times"]) / len(stats["ml_times"])
        if stats["ensemble_times"]:
            stats["avg_ensemble_time"] = sum(stats["ensemble_times"]) / len(
                stats["ensemble_times"]
            )

        return stats

    async def close(self):
        """Cleanup aller Extraktoren"""
        if self.rule_extractor:
            await self.rule_extractor.close() if hasattr(
                self.rule_extractor, "close"
            ) else None

        if self.ml_extractor:
            await self.ml_extractor.close()

        self.logger.info("🔌 Hybrid RelationExtractor geschlossen")

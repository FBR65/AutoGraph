"""
Erweiterte Beziehungsextraktion basierend auf syntaktischen Abhängigkeiten
"""

from typing import List, Dict, Any, Tuple, Optional
import logging
import spacy
import asyncio
from spacy.tokens import Doc, Token

from .base import BaseProcessor
from ..core.cache import cache_async_method


class RelationExtractor(BaseProcessor):
    """Erweiterte Beziehungsextraktion mit syntaktischen Mustern"""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)

        # Konfiguration
        self.model_name = self.config.get("ner_model", "de_core_news_lg")
        self.confidence_threshold = self.config.get(
            "relation_confidence_threshold", 0.6
        )
        self.domain = None  # Wird später gesetzt

        # SpaCy Modell laden
        try:
            self.nlp = spacy.load(self.model_name)
            self.logger.info(
                f"SpaCy Modell für Relation Extraction geladen: {self.model_name}"
            )
        except OSError:
            self.logger.error(f"SpaCy Modell nicht gefunden: {self.model_name}")
            raise

        # Beziehungsmuster definieren
        self.relation_patterns = self._define_relation_patterns()

        # Cache Manager (wird von Pipeline gesetzt)
        self.cache_manager = None

    @cache_async_method(cache_type="relations", ttl=3600)
    async def process_async(self, data: Any, domain: str = None) -> Dict[str, Any]:
        """
        Asynchrone Beziehungsextraktion mit Caching
        """
        self.domain = domain

        if isinstance(data, str):
            # Direkter Text - erst NER durchführen
            entities = await asyncio.get_event_loop().run_in_executor(
                None, self._extract_entities_from_text, data
            )
            text = data
        elif isinstance(data, dict):
            if "entities" in data:
                # Bereits verarbeitete Daten mit Entitäten
                entities = data["entities"]
                text = data.get("text", "")
            elif "text" in data:
                # Nur Text
                text = data["text"]
                entities = await asyncio.get_event_loop().run_in_executor(
                    None, self._extract_entities_from_text, text
                )
            else:
                self.logger.warning(f"Unbekannte Datenstruktur: {data}")
                return {"relationships": [], "entities": []}
        else:
            self.logger.warning(f"Unbekannter Datentyp für Relations: {type(data)}")
            return {"relationships": [], "entities": []}

        # Beziehungsextraktion in Thread Pool
        relationships = await asyncio.get_event_loop().run_in_executor(
            None, self._extract_relationships_from_entities, text, entities
        )

        return {
            "text": text,
            "entities": entities,
            "relationships": relationships,
            "processor": "RelationExtractor",
            "domain": domain,
        }

    def _extract_entities_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extrahiert Entitäten aus Text (falls noch nicht vorhanden)"""
        entities = []
        doc = self.nlp(text)

        for ent in doc.ents:
            entities.append(
                {
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "confidence": 1.0,
                }
            )

        return entities

    def _extract_relationships_from_entities(
        self, text: str, entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extrahiert Beziehungen aus Text und Entitäten"""
        doc = self.nlp(text)
        relationships = []

        # Methode 1: Abhängigkeitsbasierte Extraktion
        dep_relations = self._extract_dependency_based_relations(doc, entities)
        relationships.extend(dep_relations)

        # Methode 2: Musterbasierte Extraktion
        pattern_relations = self._extract_pattern_based_relations(doc, entities)
        relationships.extend(pattern_relations)

        # Methode 3: Satzstruktur-basierte Extraktion
        sentence_relations = self._extract_sentence_structure_relations(doc, entities)
        relationships.extend(sentence_relations)

        # Duplikate entfernen
        unique_relations = self._deduplicate_relations(relationships)

        self.logger.debug(f"Relations: {len(unique_relations)} Beziehungen gefunden")
        return unique_relations

    def _extract_dependency_based_relations(self, doc, entities):
        """Extrahiert Beziehungen basierend auf syntaktischen Abhängigkeiten"""
        return self._extract_dependency_relations(doc, "unknown")

    def _extract_pattern_based_relations(self, doc, entities):
        """Extrahiert Beziehungen basierend auf vordefinierten Mustern"""
        return self._extract_pattern_relations(doc, "unknown")

    def _extract_sentence_structure_relations(self, doc, entities):
        """Extrahiert Beziehungen basierend auf Satzstruktur"""
        return self._extract_sentence_relations(doc, "unknown")

    def _deduplicate_relations(self, relationships):
        """Entfernt doppelte Beziehungen"""
        seen = set()
        unique_relations = []

        for rel in relationships:
            # Erstelle einen eindeutigen Key für die Beziehung
            key = (
                rel.get("subject", "").lower().strip(),
                rel.get("predicate", "").lower().strip(),
                rel.get("object", "").lower().strip(),
            )

            if key not in seen and all(key):  # Nur wenn alle Felder vorhanden
                seen.add(key)
                unique_relations.append(rel)

        return unique_relations

    def _define_relation_patterns(self) -> Dict[str, Dict]:
        """Definiert syntaktische Muster für verschiedene Beziehungstypen"""
        return {
            "leadership": {
                "keywords": [
                    "ceo",
                    "chef",
                    "leiter",
                    "präsident",
                    "direktor",
                    "vorstand",
                    "geschäftsführer",
                ],
                "relation": "ist_Führungskraft_von",
                "confidence": 0.9,
            },
            "employment": {
                "keywords": ["arbeitet", "beschäftigt", "angestellt", "mitarbeiter"],
                "relation": "arbeitet_bei",
                "confidence": 0.7,
            },
            "founding": {
                "keywords": ["gegründet", "gründer", "gründete", "mitbegründer"],
                "relation": "gründete",
                "confidence": 0.9,
            },
            "location": {
                "keywords": ["hauptsitz", "sitz", "standort", "gelegen", "befindet"],
                "relation": "befindet_sich_in",
                "confidence": 0.8,
            },
            "ownership": {
                "keywords": ["besitzt", "gehört", "eigentümer", "besitzer"],
                "relation": "besitzt",
                "confidence": 0.8,
            },
            "partnership": {
                "keywords": ["partner", "zusammenarbeit", "kooperation", "allianz"],
                "relation": "arbeitet_zusammen_mit",
                "confidence": 0.7,
            },
            "competition": {
                "keywords": ["konkurrent", "wettbewerb", "rivale", "konkurriert"],
                "relation": "konkurriert_mit",
                "confidence": 0.7,
            },
            "product": {
                "keywords": ["entwickelt", "produziert", "herstellt", "verkauft"],
                "relation": "produziert",
                "confidence": 0.6,
            },
        }

    def _get_domain_patterns(self, domain: str = None) -> Dict[str, Dict]:
        """Gibt domänen-spezifische Beziehungsmuster zurück"""
        base_patterns = self._define_relation_patterns()

        if not domain:
            return base_patterns

        domain_specific = {}

        if domain.lower() == "medizin":
            domain_specific.update(
                {
                    "diagnose": {
                        "keywords": [
                            "diagnose",
                            "diagnostiziert",
                            "leiden",
                            "erkrankung",
                            "krankheit",
                        ],
                        "relation": "hat_Diagnose",
                        "confidence": 0.8,
                    },
                    "behandlung": {
                        "keywords": [
                            "behandelt",
                            "therapie",
                            "medikament",
                            "verschreibt",
                        ],
                        "relation": "behandelt_mit",
                        "confidence": 0.8,
                    },
                    "symptom": {
                        "keywords": ["symptom", "zeigt", "leidet", "beschwerden"],
                        "relation": "zeigt_Symptom",
                        "confidence": 0.7,
                    },
                }
            )

        elif domain.lower() == "wirtschaft":
            domain_specific.update(
                {
                    "acquisition": {
                        "keywords": ["übernimmt", "akquiriert", "kauft", "erwirbt"],
                        "relation": "übernimmt",
                        "confidence": 0.9,
                    },
                    "investment": {
                        "keywords": ["investiert", "finanziert", "beteiligt"],
                        "relation": "investiert_in",
                        "confidence": 0.8,
                    },
                    "market": {
                        "keywords": ["marktführer", "marktanteil", "dominiert"],
                        "relation": "dominiert_Markt",
                        "confidence": 0.7,
                    },
                }
            )

        elif domain.lower() == "technologie":
            domain_specific.update(
                {
                    "entwicklung": {
                        "keywords": [
                            "entwickelt",
                            "programmiert",
                            "erstellt",
                            "designt",
                        ],
                        "relation": "entwickelt",
                        "confidence": 0.8,
                    },
                    "verwendet": {
                        "keywords": ["nutzt", "verwendet", "basiert", "läuft"],
                        "relation": "nutzt_Technologie",
                        "confidence": 0.7,
                    },
                    "integration": {
                        "keywords": ["integriert", "kompatibel", "unterstützt"],
                        "relation": "ist_kompatibel_mit",
                        "confidence": 0.7,
                    },
                }
            )

        # Kombiniere Basis- und domänen-spezifische Muster
        combined_patterns = {**base_patterns, **domain_specific}
        return combined_patterns

    def set_domain(self, domain: str):
        """Setzt die Domäne und aktualisiert Beziehungsmuster"""
        self.domain = domain
        self.relation_patterns = self._get_domain_patterns(domain)
        self.logger.info(
            f"Domäne gesetzt: {domain} ({len(self.relation_patterns)} Muster aktiv)"
        )

    def process(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Führt erweiterte Beziehungsextraktion durch"""

        entities = []
        relationships = []

        for item in data:
            content = item.get("content", "")
            source = item.get("source", "unknown")

            # NER durchführen
            doc = self.nlp(content)

            # Entitäten extrahieren
            doc_entities = self._extract_entities(doc, source)
            entities.extend(doc_entities)

            # Beziehungen extrahieren
            doc_relations = self._extract_relations(doc, source)
            relationships.extend(doc_relations)

        self.logger.info(
            f"Relation Extraction abgeschlossen: {len(entities)} Entitäten, {len(relationships)} Beziehungen"
        )

        return {
            "entities": entities,
            "relationships": relationships,
            "metadata": {
                "processor": "RelationExtractor",
                "model": self.model_name,
                "confidence_threshold": self.confidence_threshold,
            },
        }

    def _extract_entities(self, doc: Doc, source: str) -> List[Dict[str, Any]]:
        """Extrahiert Entitäten mit Kontext"""
        entities = []

        for ent in doc.ents:
            entity = {
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
                "confidence": getattr(ent, "confidence", 1.0),
                "source": source,
                "context": doc.text[max(0, ent.start_char - 50) : ent.end_char + 50],
            }
            entities.append(entity)

        return entities

    def _extract_relations(self, doc: Doc, source: str) -> List[Dict[str, Any]]:
        """Extrahiert Beziehungen mit verschiedenen Methoden"""
        relations = []

        # 1. Dependency-basierte Extraktion
        relations.extend(self._extract_dependency_relations(doc, source))

        # 2. Pattern-basierte Extraktion
        relations.extend(self._extract_pattern_relations(doc, source))

        # 3. Satzstruktur-basierte Extraktion
        relations.extend(self._extract_sentence_relations(doc, source))

        return relations

    def _extract_dependency_relations(
        self, doc: Doc, source: str
    ) -> List[Dict[str, Any]]:
        """Extrahiert Beziehungen basierend auf syntaktischen Abhängigkeiten"""
        relations = []

        for sent in doc.sents:
            entities_in_sent = [
                (ent.start, ent.end, ent)
                for ent in doc.ents
                if ent.start >= sent.start and ent.end <= sent.end
            ]

            for token in sent:
                # Suche nach Verben, die Beziehungen ausdrücken
                if token.pos_ == "VERB":
                    subjects = [
                        child
                        for child in token.children
                        if child.dep_ in ["sb", "nsubj", "nsubj:pass"]
                    ]
                    objects = [
                        child
                        for child in token.children
                        if child.dep_ in ["oa", "dobj", "pobj"]
                    ]

                    for subj in subjects:
                        for obj in objects:
                            subj_ent = self._find_entity_for_token(
                                subj, entities_in_sent
                            )
                            obj_ent = self._find_entity_for_token(obj, entities_in_sent)

                            if subj_ent and obj_ent and subj_ent != obj_ent:
                                relation = {
                                    "subject": subj_ent.text,
                                    "subject_type": subj_ent.label_,
                                    "predicate": token.lemma_,
                                    "object": obj_ent.text,
                                    "object_type": obj_ent.label_,
                                    "confidence": 0.6,
                                    "source": source,
                                    "sentence": sent.text.strip(),
                                    "method": "dependency",
                                }
                                relations.append(relation)

        return relations

    def _extract_pattern_relations(self, doc: Doc, source: str) -> List[Dict[str, Any]]:
        """Extrahiert Beziehungen basierend auf vordefinierten Mustern"""
        relations = []

        for sent in doc.sents:
            sent_text = sent.text.lower()
            entities_in_sent = [
                ent
                for ent in doc.ents
                if ent.start >= sent.start and ent.end <= sent.end
            ]

            # Prüfe jedes Beziehungsmuster
            for pattern_name, pattern_info in self.relation_patterns.items():
                if any(keyword in sent_text for keyword in pattern_info["keywords"]):
                    # Finde relevante Entitäten für dieses Muster
                    pattern_relations = self._apply_pattern(
                        entities_in_sent, pattern_info, sent, source, pattern_name
                    )
                    relations.extend(pattern_relations)

        return relations

    def _apply_pattern(
        self, entities: List, pattern_info: Dict, sent, source: str, pattern_name: str
    ) -> List[Dict[str, Any]]:
        """Wendet ein spezifisches Muster auf Entitäten an"""
        relations = []

        for i, ent1 in enumerate(entities):
            for ent2 in entities[i + 1 :]:
                relation = self._determine_pattern_relation(
                    ent1, ent2, pattern_info, sent, pattern_name
                )
                if relation:
                    relation.update(
                        {
                            "source": source,
                            "sentence": sent.text.strip(),
                            "method": "pattern",
                        }
                    )
                    relations.append(relation)

        return relations

    def _determine_pattern_relation(
        self, ent1, ent2, pattern_info: Dict, sent, pattern_name: str
    ) -> Optional[Dict[str, Any]]:
        """Bestimmt die spezifische Beziehung zwischen zwei Entitäten für ein Muster"""

        # Leadership Pattern
        if pattern_name == "leadership":
            if ent1.label_ == "PERSON" and ent2.label_ == "ORG":
                return {
                    "subject": ent1.text,
                    "subject_type": ent1.label_,
                    "predicate": pattern_info["relation"],
                    "object": ent2.text,
                    "object_type": ent2.label_,
                    "confidence": pattern_info["confidence"],
                }
            elif ent1.label_ == "ORG" and ent2.label_ == "PERSON":
                return {
                    "subject": ent2.text,
                    "subject_type": ent2.label_,
                    "predicate": pattern_info["relation"],
                    "object": ent1.text,
                    "object_type": ent1.label_,
                    "confidence": pattern_info["confidence"],
                }

        # Location Pattern
        elif pattern_name == "location":
            if ent1.label_ == "ORG" and ent2.label_ in ["LOC", "GPE"]:
                return {
                    "subject": ent1.text,
                    "subject_type": ent1.label_,
                    "predicate": pattern_info["relation"],
                    "object": ent2.text,
                    "object_type": ent2.label_,
                    "confidence": pattern_info["confidence"],
                }
            elif ent1.label_ in ["LOC", "GPE"] and ent2.label_ == "ORG":
                return {
                    "subject": ent2.text,
                    "subject_type": ent2.label_,
                    "predicate": pattern_info["relation"],
                    "object": ent1.text,
                    "object_type": ent1.label_,
                    "confidence": pattern_info["confidence"],
                }

        # Competition Pattern
        elif pattern_name == "competition":
            if ent1.label_ == "ORG" and ent2.label_ == "ORG":
                return {
                    "subject": ent1.text,
                    "subject_type": ent1.label_,
                    "predicate": pattern_info["relation"],
                    "object": ent2.text,
                    "object_type": ent2.label_,
                    "confidence": pattern_info["confidence"],
                }

        # Founding Pattern
        elif pattern_name == "founding":
            if ent1.label_ == "PERSON" and ent2.label_ == "ORG":
                return {
                    "subject": ent1.text,
                    "subject_type": ent1.label_,
                    "predicate": pattern_info["relation"],
                    "object": ent2.text,
                    "object_type": ent2.label_,
                    "confidence": pattern_info["confidence"],
                }
            elif ent1.label_ == "ORG" and ent2.label_ == "PERSON":
                return {
                    "subject": ent2.text,
                    "subject_type": ent2.label_,
                    "predicate": pattern_info["relation"],
                    "object": ent1.text,
                    "object_type": ent1.label_,
                    "confidence": pattern_info["confidence"],
                }

        # Employment Pattern (allgemein)
        elif pattern_name == "employment":
            if ent1.label_ == "PERSON" and ent2.label_ == "ORG":
                return {
                    "subject": ent1.text,
                    "subject_type": ent1.label_,
                    "predicate": pattern_info["relation"],
                    "object": ent2.text,
                    "object_type": ent2.label_,
                    "confidence": pattern_info["confidence"],
                }
            elif ent1.label_ == "ORG" and ent2.label_ == "PERSON":
                return {
                    "subject": ent2.text,
                    "subject_type": ent2.label_,
                    "predicate": pattern_info["relation"],
                    "object": ent1.text,
                    "object_type": ent1.label_,
                    "confidence": pattern_info["confidence"],
                }

        return None

    def _extract_sentence_relations(
        self, doc: Doc, source: str
    ) -> List[Dict[str, Any]]:
        """Extrahiert Beziehungen basierend auf Satzstruktur und Nähe"""
        relations = []

        for sent in doc.sents:
            entities_in_sent = [
                ent
                for ent in doc.ents
                if ent.start >= sent.start and ent.end <= sent.end
            ]

            # Wenn mehrere Entitäten im gleichen Satz sind, erstelle schwache Verbindungen
            for i, ent1 in enumerate(entities_in_sent):
                for ent2 in entities_in_sent[i + 1 :]:
                    if self._entities_are_related(ent1, ent2, sent):
                        relation = {
                            "subject": ent1.text,
                            "subject_type": ent1.label_,
                            "predicate": "erwähnt_mit",
                            "object": ent2.text,
                            "object_type": ent2.label_,
                            "confidence": 0.3,
                            "source": source,
                            "sentence": sent.text.strip(),
                            "method": "cooccurrence",
                        }
                        relations.append(relation)

        return relations

    def _entities_are_related(self, ent1, ent2, sent) -> bool:
        """Prüft ob zwei Entitäten im Kontext verwandt sind"""
        # Einfache Heuristik: Entitäten sind verwandt wenn sie nah beieinander stehen
        distance = abs(ent1.start - ent2.start)
        return distance < 10  # Max 10 Token Abstand

    def _find_entity_for_token(self, token: Token, entities: List[Tuple]) -> Optional:
        """Findet die Entität, die ein bestimmtes Token enthält"""
        for start, end, ent in entities:
            if start <= token.i < end:
                return ent
        return None

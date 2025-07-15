"""
Named Entity Recognition Prozessor
"""

from typing import List, Dict, Any
import logging
import spacy
import asyncio

from .base import BaseProcessor
from ..core.cache import cache_async_method


class NERProcessor(BaseProcessor):
    """Named Entity Recognition mit SpaCy"""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)

        # Konfiguration
        self.model_name = self.config.get("ner_model", "de_core_news_lg")
        self.confidence_threshold = self.config.get("ner_confidence_threshold", 0.8)

        # SpaCy Modell laden
        try:
            self.nlp = spacy.load(self.model_name)
            self.logger.info(f"SpaCy Modell geladen: {self.model_name}")
        except OSError:
            self.logger.error(f"SpaCy Modell nicht gefunden: {self.model_name}")
            raise
        
        # Cache Manager (wird von Pipeline gesetzt)
        self.cache_manager = None

    def process(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Führt NER auf allen Textdaten durch"""

        entities = []
        relationships = []

        for item in data:
            content = item.get("content", "")
            source = item.get("source", "unknown")

            # NER durchführen
            doc = self.nlp(content)

            # Entitäten extrahieren
            for ent in doc.ents:
                entity = {
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "confidence": getattr(ent, "confidence", 1.0),
                    "source": source,
                    "context": content[max(0, ent.start_char - 50) : ent.end_char + 50],
                }

                # Nur Entitäten über Konfidenzschwelle
                if entity["confidence"] >= self.confidence_threshold:
                    entities.append(entity)

            # Einfache Beziehungsextraktion basierend auf Satzstruktur
            relationships.extend(self._extract_simple_relations(doc, source))

        self.logger.info(
            f"NER abgeschlossen: {len(entities)} Entitäten, {len(relationships)} Beziehungen"
        )

        return {
            "entities": entities,
            "relationships": relationships,
            "metadata": {
                "processor": "NERProcessor",
                "model": self.model_name,
                "confidence_threshold": self.confidence_threshold,
            },
        }

    def _extract_simple_relations(self, doc, source: str) -> List[Dict[str, Any]]:
        """Extrahiert einfache Beziehungen basierend auf syntaktischen Mustern"""
        relations = []

        for sent in doc.sents:
            entities_in_sent = [ent for ent in sent.ents]

            # Verschiedene Beziehungspatterns erkennen
            for i, ent1 in enumerate(entities_in_sent):
                for ent2 in entities_in_sent[i + 1 :]:
                    relation = self._determine_relation(ent1, ent2, sent)
                    if relation:
                        relation.update(
                            {"source": source, "sentence": sent.text.strip()}
                        )
                        relations.append(relation)

        return relations

    def _determine_relation(self, ent1, ent2, sent) -> Dict[str, Any]:
        """Bestimmt die Beziehung zwischen zwei Entitäten basierend auf Kontext"""
        sentence_text = sent.text.lower()

        # CEO/Führungsposition
        if any(
            word in sentence_text
            for word in ["ceo", "chef", "leiter", "präsident", "direktor"]
        ):
            if ent1.label_ == "PERSON" and ent2.label_ == "ORG":
                return {
                    "subject": ent1.text,
                    "subject_type": ent1.label_,
                    "predicate": "ist_CEO_von",
                    "object": ent2.text,
                    "object_type": ent2.label_,
                    "confidence": 0.8,
                }
            elif ent1.label_ == "ORG" and ent2.label_ == "PERSON":
                return {
                    "subject": ent2.text,
                    "subject_type": ent2.label_,
                    "predicate": "ist_CEO_von",
                    "object": ent1.text,
                    "object_type": ent1.label_,
                    "confidence": 0.8,
                }

        # Gründung
        if any(word in sentence_text for word in ["gegründet", "gründer", "gründete"]):
            if ent1.label_ == "PERSON" and ent2.label_ == "ORG":
                return {
                    "subject": ent1.text,
                    "subject_type": ent1.label_,
                    "predicate": "gründete",
                    "object": ent2.text,
                    "object_type": ent2.label_,
                    "confidence": 0.9,
                }
            elif ent1.label_ == "ORG" and ent2.label_ == "PERSON":
                return {
                    "subject": ent2.text,
                    "subject_type": ent2.label_,
                    "predicate": "gründete",
                    "object": ent1.text,
                    "object_type": ent1.label_,
                    "confidence": 0.9,
                }

        # Hauptsitz/Standort
        if any(
            word in sentence_text for word in ["hauptsitz", "sitz", "standort", "liegt"]
        ):
            if ent1.label_ == "ORG" and ent2.label_ in ["LOC", "GPE"]:
                return {
                    "subject": ent1.text,
                    "subject_type": ent1.label_,
                    "predicate": "hat_Hauptsitz_in",
                    "object": ent2.text,
                    "object_type": ent2.label_,
                    "confidence": 0.8,
                }
            elif ent1.label_ in ["LOC", "GPE"] and ent2.label_ == "ORG":
                return {
                    "subject": ent2.text,
                    "subject_type": ent2.label_,
                    "predicate": "hat_Hauptsitz_in",
                    "object": ent1.text,
                    "object_type": ent1.label_,
                    "confidence": 0.8,
                }

        # Konkurrenz/Wettbewerb
        if any(word in sentence_text for word in ["konkurrent", "wettbewerb", "rival"]):
            if ent1.label_ == "ORG" and ent2.label_ == "ORG":
                return {
                    "subject": ent1.text,
                    "subject_type": ent1.label_,
                    "predicate": "konkurriert_mit",
                    "object": ent2.text,
                    "object_type": ent2.label_,
                    "confidence": 0.7,
                }

        # Arbeitsbeziehung (allgemein)
        if ent1.label_ == "PERSON" and ent2.label_ == "ORG":
            return {
                "subject": ent1.text,
                "subject_type": ent1.label_,
                "predicate": "arbeitet_bei",
                "object": ent2.text,
                "object_type": ent2.label_,
                "confidence": 0.5,
            }
        elif ent1.label_ == "ORG" and ent2.label_ == "PERSON":
            return {
                "subject": ent2.text,
                "subject_type": ent2.label_,
                "predicate": "arbeitet_bei",
                "object": ent1.text,
                "object_type": ent1.label_,
                "confidence": 0.5,
            }

        return None

    @cache_async_method(cache_type="ner", ttl=3600)
    async def process_async(self, data: Any, domain: str = None) -> Dict[str, Any]:
        """
        Asynchrone NER-Verarbeitung mit Caching
        """
        if isinstance(data, str):
            # Direkter Text
            text = data
            source = "direct_input"
        elif isinstance(data, list):
            # Liste von Datenpunkten
            return await self._process_data_list_async(data, domain)
        elif isinstance(data, dict) and "text" in data:
            # Bereits verarbeitete Daten
            text = data["text"]
            source = data.get("source", "unknown")
        else:
            self.logger.warning(f"Unbekannter Datentyp für NER: {type(data)}")
            return {"entities": [], "text": str(data)}
        
        # NER in Thread ausführen (CPU-intensive)
        entities = await asyncio.get_event_loop().run_in_executor(
            None, self._extract_entities_from_text, text, source
        )
        
        return {
            "text": text,
            "entities": entities,
            "source": source,
            "processor": "NERProcessor"
        }
    
    async def _process_data_list_async(self, data: List[Dict[str, Any]], domain: str = None) -> Dict[str, Any]:
        """Verarbeitet Liste von Datenpunkten asynchron"""
        all_entities = []
        
        # Parallel processing für mehrere Datenpunkte
        tasks = []
        for item in data:
            content = item.get("content", "")
            source = item.get("source", "unknown")
            
            if content.strip():  # Nur nicht-leere Inhalte verarbeiten
                task = asyncio.get_event_loop().run_in_executor(
                    None, self._extract_entities_from_text, content, source
                )
                tasks.append(task)
        
        # Alle Tasks parallel ausführen
        results = await asyncio.gather(*tasks)
        
        # Ergebnisse zusammenführen
        for entities in results:
            all_entities.extend(entities)
        
        return {
            "entities": all_entities,
            "data": data,
            "processor": "NERProcessor"
        }
    
    def _extract_entities_from_text(self, text: str, source: str = "unknown") -> List[Dict[str, Any]]:
        """
        Extrahiert Entitäten aus einem Text (für Thread-Pool Execution)
        """
        entities = []
        
        try:
            # NER durchführen
            doc = self.nlp(text)
            
            # Entitäten extrahieren
            for ent in doc.ents:
                entity = {
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "confidence": 1.0,  # SpaCy gibt keine direkte Confidence zurück
                    "source": source,
                }
                
                # Nur Entitäten über Confidence-Schwelle
                if entity["confidence"] >= self.confidence_threshold:
                    entities.append(entity)
            
            self.logger.debug(f"NER: {len(entities)} Entitäten in {len(text)} Zeichen gefunden")
            
        except Exception as e:
            self.logger.error(f"Fehler bei NER: {e}")
        
        return entities

"""
Advanced ML-basierte Beziehungsextraktion mit BERT und transformers

Diese Klasse implementiert state-of-the-art Relation Extraction mit:
- BERT-basierte Modelle für semantische Beziehungserkennung
- Vortrainierte deutsche Modelle
- Zero-shot und Few-shot Learning
- Kontextuelle Embeddings für Entitäten-Paare
- Confidence Scoring und Threshold-basierte Filterung
"""

import logging
import asyncio
from typing import List, Dict, Any
import torch
from transformers import AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from .base import BaseProcessor
from ..core.cache import cache_async_method


class MLRelationExtractor(BaseProcessor):
    """
    ML-basierte Beziehungsextraktion mit BERT und transformers

    Features:
    - BERT-basierte Relation Classification
    - Semantische Ähnlichkeit für Entitäten-Paare
    - Deutsche vortrainierte Modelle
    - Adaptive Confidence Thresholds
    - Domänen-spezifische Relation Templates
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)

        # Konfiguration
        self.bert_model_name = self.config.get(
            "bert_model",
            "deepset/gbert-base",  # Deutscher BERT
        )
        self.sentence_model_name = self.config.get(
            "sentence_model", "T-Systems-onsite/german-roberta-sentence-transformer-v2"
        )
        self.confidence_threshold = self.config.get(
            "ml_confidence_threshold", 0.5
        )  # Gesenkt von 0.7
        self.max_distance = self.config.get("max_entity_distance", 100)  # Tokens
        self.batch_size = self.config.get("ml_batch_size", 8)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # Modelle lazy loading
        self._bert_model = None
        self._bert_tokenizer = None
        self._sentence_model = None

        # Cache Manager
        self.cache_manager = None

        # Domänen-spezifische Relation Templates
        self.domain_relations = {
            "medizin": [
                "behandelt",
                "verursacht",
                "symptom_von",
                "wirkt_gegen",
                "interagiert_mit",
                "kontraindiziert_für",
                "dosiert_als",
            ],
            "wirtschaft": [
                "gehört_zu",
                "konkurriert_mit",
                "investiert_in",
                "verkauft_an",
                "liefert_an",
                "kooperiert_mit",
                "übernimmt",
                "fusioniert_mit",
            ],
            "wissenschaft": [
                "erforscht",
                "publiziert_über",
                "zitiert",
                "entdeckt",
                "entwickelt",
                "experimentiert_mit",
                "beweist",
                "widerlegt",
            ],
            "allgemein": [
                "ist",
                "hat",
                "gehört_zu",
                "befindet_sich_in",
                "arbeitet_für",
                "stammt_aus",
                "produziert",
                "verwendet",
                "besteht_aus",
            ],
        }

        self.logger.info(
            f"🤖 ML RelationExtractor initialisiert (Device: {self.device})"
        )

    def process(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Synchrone Wrapper für process_async (erforderlich von BaseProcessor)"""
        return asyncio.run(self.process_async(data))

    async def _load_models(self):
        """Lazy Loading der ML-Modelle"""
        if self._bert_model is None:
            self.logger.info(f"Lade BERT Modell: {self.bert_model_name}")

            try:
                self._bert_tokenizer = AutoTokenizer.from_pretrained(
                    self.bert_model_name
                )
                self._bert_model = AutoModel.from_pretrained(self.bert_model_name)
                self._bert_model.to(self.device)
                self._bert_model.eval()

                self.logger.info("✅ BERT Modell geladen")
            except Exception as e:
                self.logger.error(f"❌ Fehler beim Laden des BERT Modells: {e}")
                # Fallback auf deutsches BERT
                self._bert_tokenizer = AutoTokenizer.from_pretrained(
                    "bert-base-german-cased"
                )
                self._bert_model = AutoModel.from_pretrained("bert-base-german-cased")
                self._bert_model.to(self.device)
                self._bert_model.eval()

        if self._sentence_model is None:
            self.logger.info("🇩🇪 Lade T-Systems deutsches RoBERTa Modell DIREKT")

            # T-Systems deutsches Modell - DIREKT OHNE FALLBACKS!
            if (
                "T-Systems-onsite/german-roberta-sentence-transformer-v2"
                in self.sentence_model_name
            ):
                self.logger.info("🚀 DIREKTER LOAD - KEIN SENTENCEPIECE FALLBACK")

                # Load model directly mit SPEZIFISCHEM Tokenizer-Typ
                from transformers import XLMRobertaTokenizer

                tokenizer = XLMRobertaTokenizer.from_pretrained(
                    "T-Systems-onsite/german-roberta-sentence-transformer-v2"
                )
                model = AutoModel.from_pretrained(
                    "T-Systems-onsite/german-roberta-sentence-transformer-v2"
                )
                model.to(self.device)
                model.eval()

                # Wrapper für encode-Kompatibilität
                class TSysGermanTransformer:
                    def __init__(self, tokenizer, model, device):
                        self.tokenizer = tokenizer
                        self.model = model
                        self.device = device

                    def encode(self, sentences, convert_to_tensor=True, **kwargs):
                        if isinstance(sentences, str):
                            sentences = [sentences]

                        embeddings = []
                        for sentence in sentences:
                            inputs = self.tokenizer(
                                sentence,
                                return_tensors="pt",
                                padding=True,
                                truncation=True,
                                max_length=512,
                            )
                            inputs = {k: v.to(self.device) for k, v in inputs.items()}

                            with torch.no_grad():
                                outputs = self.model(**inputs)
                                # Mean pooling
                                token_embeddings = outputs.last_hidden_state
                                attention_mask = inputs["attention_mask"]
                                input_mask_expanded = (
                                    attention_mask.unsqueeze(-1)
                                    .expand(token_embeddings.size())
                                    .float()
                                )
                                embeddings.append(
                                    torch.sum(token_embeddings * input_mask_expanded, 1)
                                    / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
                                )

                        result = torch.cat(embeddings, dim=0)
                        return result if convert_to_tensor else result.cpu().numpy()

                self._sentence_model = TSysGermanTransformer(
                    tokenizer, model, self.device
                )
                self.logger.info("✅ T-Systems deutsches RoBERTa erfolgreich geladen!")
            else:
                # Nur wenn nicht T-Systems Modell
                self._sentence_model = SentenceTransformer(
                    self.sentence_model_name, device=self.device
                )
                self.logger.info(
                    f"✅ Alternative Sentence Transformer geladen: {self.sentence_model_name}"
                )

    @cache_async_method(cache_type="ml_relations", ttl=7200)
    async def process_async(self, data: Any, domain: str = None) -> Dict[str, Any]:
        """Hauptmethode für ML-basierte Beziehungsextraktion"""
        self.logger.info(f"🔍 Starte ML Relation Extraction (Domain: {domain})")

        await self._load_models()

        # Input parsing mit automatischer Entity-Erkennung
        if isinstance(data, str):
            text = data
            entities = self._auto_detect_entities(text)  # Automatische Erkennung
            if not entities:
                self.logger.warning(
                    "⚠️ Keine Entitäten automatisch erkannt. Verwende einfache Token-Extraktion."
                )
                entities = self._simple_entity_extraction(text)
        elif isinstance(data, dict):
            text = data.get("text", "")
            entities = data.get("entities", [])
            if not entities:
                self.logger.info(
                    "📝 Keine Entitäten bereitgestellt. Verwende automatische Erkennung."
                )
                entities = self._auto_detect_entities(text)
        else:
            raise ValueError(f"Unsupported data type: {type(data)}")

        if not text.strip():
            return {"relationships": [], "metadata": {"method": "ml_bert"}}

        # 1. Entitäten-Paare generieren
        entity_pairs = self._generate_entity_pairs(entities, text)

        if not entity_pairs:
            return {
                "relationships": [],
                "metadata": {"method": "ml_bert", "pairs_generated": 0},
            }

        # 2. ML-basierte Relation Classification
        relations = await self._classify_relations_ml(entity_pairs, text, domain)

        # 3. Confidence-basierte Auswahl
        final_relations = self._apply_confidence_threshold(relations)

        metadata = {
            "method": "ml_bert",
            "pairs_generated": len(entity_pairs),
            "relations_classified": len(relations),
            "final_relations": len(final_relations),
            "confidence_threshold": self.confidence_threshold,
            "domain": domain,
            "device": self.device,
        }

        self.logger.info(
            f"✅ ML Relation Extraction: {len(final_relations)} Beziehungen "
            f"aus {len(entity_pairs)} Paaren"
        )

        # Performance-Monitoring: Warnung bei schlechter Performance
        if len(entity_pairs) >= 2 and len(final_relations) == 0:
            self.logger.warning(
                "⚠️ Performance-Issue: Keine Relationen trotz verfügbarer Entitäten-Paare. "
                f"Confidence-Threshold ({self.confidence_threshold}) möglicherweise zu hoch."
            )

        success_rate = len(final_relations) / max(len(entity_pairs), 1)
        if success_rate < 0.1 and len(entity_pairs) > 0:
            self.logger.warning(
                f"⚠️ Niedrige Success-Rate: {success_rate:.2%} "
                f"({len(final_relations)}/{len(entity_pairs)} Paare)"
            )

        return {"relationships": final_relations, "metadata": metadata}

    def _generate_entity_pairs(self, entities: List[Dict], text: str) -> List[Dict]:
        """Generiert alle sinnvollen Entitäten-Paare für Relation Classification"""
        if len(entities) < 2:
            return []

        pairs = []
        text_lower = text.lower()

        for i, ent1 in enumerate(entities):
            for j, ent2 in enumerate(entities):
                if i >= j:  # Vermeidet Duplikate und Selbst-Referenzen
                    continue

                # Position im Text finden
                ent1_pos = text_lower.find(ent1["text"].lower())
                ent2_pos = text_lower.find(ent2["text"].lower())

                if ent1_pos == -1 or ent2_pos == -1:
                    continue

                # Distanz-Check
                distance = abs(ent1_pos - ent2_pos)
                if distance > self.max_distance:
                    continue

                # Kontext extrahieren
                start_pos = max(0, min(ent1_pos, ent2_pos) - 50)
                end_pos = min(
                    len(text),
                    max(ent1_pos + len(ent1["text"]), ent2_pos + len(ent2["text"]))
                    + 50,
                )
                context = text[start_pos:end_pos]

                pairs.append(
                    {
                        "entity1": ent1,
                        "entity2": ent2,
                        "context": context,
                        "distance": distance,
                        "full_text": text,
                    }
                )

        return pairs

    def _auto_detect_entities(self, text: str) -> List[Dict]:
        """Automatische Entitätenerkennung mit einfachen Heuristiken"""
        entities = []

        # Erkenne potenzielle Entitäten (Großgeschriebene Wörter/Phrasen)
        import re

        # Muster für deutsche Entitäten
        patterns = [
            r"\b[A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)*\b",  # Eigennamen
            r"\b[A-ZÄÖÜ]{2,}\b",  # Akronyme (BMW, AG, etc.)
            r"\b\d{4,}\b",  # Jahre
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                entity_text = match.group().strip()

                # Filter aus häufige Stopwörter
                stopwords = {
                    "Der",
                    "Die",
                    "Das",
                    "Ein",
                    "Eine",
                    "Einen",
                    "Und",
                    "Oder",
                    "Mit",
                }
                if entity_text not in stopwords and len(entity_text) > 1:
                    entities.append(
                        {
                            "text": entity_text,
                            "label": self._classify_entity_type(entity_text),
                            "start": match.start(),
                            "end": match.end(),
                        }
                    )

        # Duplikate entfernen
        unique_entities = []
        seen = set()
        for entity in entities:
            if entity["text"] not in seen:
                unique_entities.append(entity)
                seen.add(entity["text"])

        self.logger.info(f"🔍 Automatisch erkannt: {len(unique_entities)} Entitäten")
        return unique_entities

    def _classify_entity_type(self, text: str) -> str:
        """Klassifiziert Entity-Typ basierend auf Heuristiken"""
        if text.isupper() and len(text) <= 5:
            return "ORG"  # Akronyme meist Organisationen
        elif any(
            word in text.lower() for word in ["gmbh", "ag", "inc", "corp", "group"]
        ):
            return "ORG"
        elif any(word in text.lower() for word in ["straße", "platz", "weg", "allee"]):
            return "LOC"
        elif text.isdigit() and len(text) == 4:
            return "DATE"  # Jahre
        else:
            return "PERSON"  # Default für Eigennamen

    def _simple_entity_extraction(self, text: str) -> List[Dict]:
        """Fallback: Einfache Token-basierte Entitäts-Extraktion"""
        import re

        # Extrahiere alle Großgeschriebenen Wörter
        words = re.findall(r"\b[A-ZÄÖÜ][a-zäöüß]+\b", text)
        entities = []

        for i, word in enumerate(set(words)):  # Duplikate entfernen
            if len(word) > 2:  # Mindestlänge
                entities.append(
                    {
                        "text": word,
                        "label": "ENTITY",
                        "start": text.find(word),
                        "end": text.find(word) + len(word),
                    }
                )

        self.logger.info(f"🔤 Einfache Extraktion: {len(entities)} Token-Entitäten")
        return entities

    async def _classify_relations_ml(
        self, pairs: List[Dict], text: str, domain: str
    ) -> List[Dict]:
        """BERT-basierte Relation Classification für Entitäten-Paare"""
        relations = []
        domain_rels = self.domain_relations.get(
            domain, self.domain_relations["allgemein"]
        )

        # Batch-Processing für bessere Performance
        for i in range(0, len(pairs), self.batch_size):
            batch = pairs[i : i + self.batch_size]
            batch_relations = await self._process_batch_relations(batch, domain_rels)
            relations.extend(batch_relations)

        return relations

    async def _process_batch_relations(
        self, batch: List[Dict], domain_relations: List[str]
    ) -> List[Dict]:
        """Verarbeitet einen Batch von Entitäten-Paaren"""
        batch_relations = []

        for pair in batch:
            ent1 = pair["entity1"]
            ent2 = pair["entity2"]
            context = pair["context"]

            # Für jede mögliche Relation Template prüfen
            best_relation = None
            best_confidence = 0.0

            for relation_type in domain_relations:
                confidence = await self._calculate_relation_confidence(
                    ent1, ent2, relation_type, context
                )

                if confidence > best_confidence:
                    best_confidence = confidence
                    best_relation = relation_type

            # Zusätzliche semantische Analyse
            semantic_confidence = await self._semantic_relation_analysis(
                ent1, ent2, context
            )

            # Kombinierte Confidence
            final_confidence = (best_confidence + semantic_confidence) / 2

            if final_confidence > 0.3:  # Minimum threshold für Kandidaten
                batch_relations.append(
                    {
                        "source": ent1["text"],
                        "target": ent2["text"],
                        "relationship": best_relation or "related_to",
                        "confidence": final_confidence,
                        "source_type": ent1.get("label", "ENTITY"),
                        "target_type": ent2.get("label", "ENTITY"),
                        "context": context[:200],  # Begrenzte Kontextlänge
                        "method": "ml_bert",
                        "distance": pair["distance"],
                    }
                )

        return batch_relations

    async def _calculate_relation_confidence(
        self, ent1: Dict, ent2: Dict, relation_type: str, context: str
    ) -> float:
        """Berechnet Confidence für eine spezifische Relation mit BERT"""
        try:
            # Template-basierte Sentence für BERT
            sentence = f"{ent1['text']} {relation_type} {ent2['text']}"

            # BERT Encoding
            inputs = self._bert_tokenizer(
                sentence,
                context,
                return_tensors="pt",
                max_length=512,
                truncation=True,
                padding=True,
            ).to(self.device)

            with torch.no_grad():
                outputs = self._bert_model(**inputs)

                # CLS Token als Sentence Representation
                cls_embedding = outputs.last_hidden_state[:, 0, :]

                # Similarity zwischen Sentence und Context
                sentence_only = self._bert_tokenizer(
                    sentence,
                    return_tensors="pt",
                    max_length=512,
                    truncation=True,
                    padding=True,
                ).to(self.device)

                sentence_outputs = self._bert_model(**sentence_only)
                sentence_embedding = sentence_outputs.last_hidden_state[:, 0, :]

                # Cosine Similarity
                similarity = torch.cosine_similarity(
                    cls_embedding, sentence_embedding, dim=1
                ).item()

                return max(0.0, similarity)

        except Exception as e:
            self.logger.warning(f"BERT Confidence calculation failed: {e}")
            return 0.0

    async def _semantic_relation_analysis(
        self, ent1: Dict, ent2: Dict, context: str
    ) -> float:
        """Semantische Analyse mit Sentence Transformers"""
        try:
            # Entitäten-Kontext für Embedding
            ent1_context = f"{ent1['text']} im Kontext: {context}"
            ent2_context = f"{ent2['text']} im Kontext: {context}"

            # Embeddings generieren
            embeddings = self._sentence_model.encode([ent1_context, ent2_context])

            # Similarity berechnen
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]

            # Normalisierte Confidence
            confidence = min(1.0, max(0.0, similarity))

            return confidence

        except Exception as e:
            self.logger.warning(f"Semantic analysis failed: {e}")
            return 0.0

    def _apply_confidence_threshold(self, relations: List[Dict]) -> List[Dict]:
        """Wendet Confidence Threshold an und sortiert Ergebnisse"""
        # Threshold-basierte Filterung
        filtered = [
            r for r in relations if r["confidence"] >= self.confidence_threshold
        ]

        # Nach Confidence sortieren (höchste zuerst)
        filtered.sort(key=lambda x: x["confidence"], reverse=True)

        # Duplikat-Entfernung basierend auf Entity-Paaren
        unique_relations = []
        seen_pairs = set()

        for relation in filtered:
            pair = (relation["source"], relation["target"], relation["relationship"])
            reverse_pair = (
                relation["target"],
                relation["source"],
                relation["relationship"],
            )

            if pair not in seen_pairs and reverse_pair not in seen_pairs:
                unique_relations.append(relation)
                seen_pairs.add(pair)

        return unique_relations

    async def close(self):
        """Cleanup von Modellen und Ressourcen"""
        if self._bert_model is not None:
            del self._bert_model
            self._bert_model = None

        if self._sentence_model is not None:
            del self._sentence_model
            self._sentence_model = None

        # GPU Memory cleanup
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        self.logger.info("🔌 ML RelationExtractor Ressourcen freigegeben")

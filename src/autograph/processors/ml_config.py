"""
Konfiguration für ML-basierte Relation Extraction
"""

from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class MLRelationConfig:
    """Konfiguration für ML RelationExtractor"""

    # Modell-Konfiguration
    bert_model: str = "deepset/gbert-base"
    sentence_model: str = "T-Systems-onsite/german-roberta-sentence-transformer-v2"

    # Performance-Parameter
    confidence_threshold: float = 0.7
    semantic_threshold: float = 0.5
    max_entity_distance: int = 100
    batch_size: int = 8

    # Cache-Konfiguration
    cache_ttl: int = 7200  # 2 Stunden
    enable_gpu: bool = True

    # Relation Templates
    custom_relations: Dict[str, List[str]] = None

    def __post_init__(self):
        if self.custom_relations is None:
            self.custom_relations = {}

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary für Pipeline-Konfiguration"""
        return {
            "bert_model": self.bert_model,
            "sentence_model": self.sentence_model,
            "ml_confidence_threshold": self.confidence_threshold,
            "semantic_threshold": self.semantic_threshold,
            "max_entity_distance": self.max_entity_distance,
            "ml_batch_size": self.batch_size,
            "cache_ttl": self.cache_ttl,
            "enable_gpu": self.enable_gpu,
            "custom_relations": self.custom_relations,
        }

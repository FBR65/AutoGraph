"""Datenverarbeitungsmodule"""

from .ner import NERProcessor
from .relation_extractor import RelationExtractor
from .ml_relation_extractor import MLRelationExtractor
from .hybrid_relation_extractor import HybridRelationExtractor
from .ml_config import MLRelationConfig
from .base import BaseProcessor


class EntityLinker(BaseProcessor):
    """Placeholder für Entity Linking"""

    def process(self, data):
        return data


__all__ = [
    "NERProcessor",
    "RelationExtractor",
    "MLRelationExtractor",
    "HybridRelationExtractor",
    "MLRelationConfig",
    "EntityLinker",
    "BaseProcessor",
]

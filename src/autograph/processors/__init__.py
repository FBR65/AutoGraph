"""Datenverarbeitungsmodule"""

from .ner import NERProcessor
from .relation_extractor import RelationExtractor
from .base import BaseProcessor


class EntityLinker(BaseProcessor):
    """Placeholder für Entity Linking"""

    def process(self, data):
        return data


__all__ = ["NERProcessor", "RelationExtractor", "EntityLinker", "BaseProcessor"]

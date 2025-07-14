"""
AutoGraph - Automated Knowledge Graph Generation Framework

Ein modulares Framework zur automatisierten Erstellung von Knowledge Graphs
aus verschiedenen Datenquellen mit LLM-unterstützter Pipeline-Optimierung.
"""

__version__ = "0.1.0"
__author__ = "AutoGraph Team"

from .core import AutoGraphPipeline
from .extractors import (
    TextExtractor,
    TableExtractor,
    WebExtractor,
)
from .processors import (
    NERProcessor,
    RelationExtractor,
    EntityLinker,
)
from .storage import Neo4jStorage
from .evaluation import LLMEvaluator

__all__ = [
    "AutoGraphPipeline",
    "TextExtractor",
    "TableExtractor",
    "WebExtractor",
    "NERProcessor",
    "RelationExtractor",
    "EntityLinker",
    "Neo4jStorage",
    "LLMEvaluator",
]

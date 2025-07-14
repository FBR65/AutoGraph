"""
Basis-Abstraktion für Storage-Backends
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..types import PipelineResult


class BaseStorage(ABC):
    """Basisklasse für alle Storage Backends"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    @abstractmethod
    def store(self, result: "PipelineResult") -> bool:
        """
        Speichert Pipeline-Ergebnis

        Args:
            result: Pipeline-Ergebnis mit Entitäten und Beziehungen

        Returns:
            True wenn erfolgreich gespeichert
        """
        pass

    @abstractmethod
    def query(self, query: str) -> List[Dict[str, Any]]:
        """
        Führt Abfrage auf dem gespeicherten Graphen aus

        Args:
            query: Query String (abhängig vom Backend)

        Returns:
            Abfrageergebnisse
        """
        pass

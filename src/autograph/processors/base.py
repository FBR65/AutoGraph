"""
Basis-Abstraktion für Datenverarbeitung
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseProcessor(ABC):
    """Basisklasse für alle Datenverarbeitungsmodule"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    @abstractmethod
    def process(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Verarbeitet die Eingabedaten

        Args:
            data: Liste von Datenpunkten

        Returns:
            Verarbeitete Daten mit Entitäten und Beziehungen
        """
        pass

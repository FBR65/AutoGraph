"""
Basis-Abstraktion für Datenextraktoren
"""

from abc import ABC, abstractmethod
from typing import Any, List, Dict, Union
from pathlib import Path


class BaseExtractor(ABC):
    """Basisklasse für alle Datenextraktoren"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    @abstractmethod
    def extract(self, source: Union[str, Path, List[str]]) -> List[Dict[str, Any]]:
        """
        Extrahiert Rohdaten aus der Quelle

        Args:
            source: Datenquelle (Datei, URL, Liste von Dateien)

        Returns:
            Liste von extrahierten Datenpunkten
        """
        pass

    def validate_source(self, source: Any) -> bool:
        """Validiert ob die Datenquelle unterstützt wird"""
        return True

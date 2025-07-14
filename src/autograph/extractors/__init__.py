"""Datenextraktoren"""

from .text import TextExtractor
from .base import BaseExtractor


# Placeholder für zukünftige Extraktoren
class TableExtractor(BaseExtractor):
    """Placeholder für Tabellen-Extraktor"""

    def extract(self, source):
        return []


class WebExtractor(BaseExtractor):
    """Placeholder für Web-Extraktor"""

    def extract(self, source):
        return []


__all__ = ["TextExtractor", "TableExtractor", "WebExtractor", "BaseExtractor"]

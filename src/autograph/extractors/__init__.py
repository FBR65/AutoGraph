"""Datenextraktoren"""

from .text import TextExtractor
from .base import BaseExtractor
from .table import TableExtractor


# Placeholder für zukünftige Extraktoren
class WebExtractor(BaseExtractor):
    """Placeholder für Web-Extraktor"""

    def extract(self, source):
        return []


__all__ = ["TextExtractor", "TableExtractor", "WebExtractor", "BaseExtractor"]

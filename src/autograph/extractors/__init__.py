"""Datenextraktoren"""

from .text import TextExtractor
from .base import BaseExtractor

# Conditional import für TableExtractor (pandas-abhängig)
try:
    from .table import TableExtractor

    TABLE_EXTRACTOR_AVAILABLE = True
except ImportError:
    # Erstelle eine Dummy-Klasse falls pandas nicht verfügbar ist
    class TableExtractor(BaseExtractor):
        """Fallback TableExtractor ohne pandas-Abhängigkeit"""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def extract(self, source):
            raise ImportError(
                "TableExtractor nicht verfügbar. Installieren Sie pandas: 'uv pip install pandas'"
            )

        def get_supported_formats(self):
            return []

    TABLE_EXTRACTOR_AVAILABLE = False


# Placeholder für zukünftige Extraktoren
class WebExtractor(BaseExtractor):
    """Placeholder für Web-Extraktor"""

    def extract(self, source):
        return []


__all__ = ["TextExtractor", "TableExtractor", "WebExtractor", "BaseExtractor"]

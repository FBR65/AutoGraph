"""
Text-Extraktor für verschiedene Textformate
"""

from typing import List, Dict, Any, Union
from pathlib import Path
import logging

from .base import BaseExtractor


class TextExtractor(BaseExtractor):
    """Extraktor für Text-Dateien (TXT, MD, etc.)"""

    SUPPORTED_EXTENSIONS = {".txt", ".md", ".rst", ".log"}

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)

        # Konfiguration
        self.chunk_size = self.config.get("chunk_size", 1000)
        self.chunk_overlap = self.config.get("chunk_overlap", 200)
        self.enable_chunking = self.config.get("text_chunking", True)

    def extract(self, source: Union[str, Path, List[str]]) -> List[Dict[str, Any]]:
        """Extrahiert Text aus Dateien"""

        if isinstance(source, (str, Path)):
            sources = [Path(source)]
        else:
            sources = [Path(s) for s in source]

        extracted_data = []

        for file_path in sources:
            if not self.validate_source(file_path):
                self.logger.warning(f"Nicht unterstützte Datei: {file_path}")
                continue

            try:
                content = self._read_file(file_path)

                if self.enable_chunking:
                    chunks = self._chunk_text(content)
                    for i, chunk in enumerate(chunks):
                        extracted_data.append(
                            {
                                "content": chunk,
                                "source": str(file_path),
                                "chunk_id": i,
                                "type": "text_chunk",
                                "metadata": {
                                    "file_size": file_path.stat().st_size,
                                    "chunk_size": len(chunk),
                                },
                            }
                        )
                else:
                    extracted_data.append(
                        {
                            "content": content,
                            "source": str(file_path),
                            "type": "text_document",
                            "metadata": {
                                "file_size": file_path.stat().st_size,
                                "content_length": len(content),
                            },
                        }
                    )

                self.logger.info(f"Text extrahiert aus: {file_path}")

            except Exception as e:
                self.logger.error(f"Fehler beim Lesen von {file_path}: {str(e)}")
                continue

        return extracted_data

    def validate_source(self, source: Path) -> bool:
        """Validiert Textdatei"""
        return (
            source.exists()
            and source.is_file()
            and source.suffix.lower() in self.SUPPORTED_EXTENSIONS
        )

    def _read_file(self, file_path: Path) -> str:
        """Liest Textdatei mit verschiedenen Encodings"""
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]

        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue

        raise ValueError(f"Konnte Encoding für {file_path} nicht bestimmen")

    def _chunk_text(self, text: str) -> List[str]:
        """Teilt Text in überlappende Chunks auf"""
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # Versuche an Satzende zu brechen
            if end < len(text):
                sentence_end = text.rfind(".", start, end)
                if sentence_end != -1 and sentence_end > start + self.chunk_size // 2:
                    end = sentence_end + 1

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - self.chunk_overlap

        return chunks

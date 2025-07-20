"""
Table Extractor für CSV, Excel und andere tabellarische Datenformate
"""

from typing import List, Dict, Any, Union, Optional
from pathlib import Path
import logging

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    pd = None
    PANDAS_AVAILABLE = False

from .base import BaseExtractor


class TableExtractor(BaseExtractor):
    """Extrahiert Daten aus tabellarischen Dateien (CSV, Excel, etc.)"""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)

        if not PANDAS_AVAILABLE:
            raise ImportError(
                "pandas ist erforderlich für TableExtractor. Installieren Sie es mit: uv pip install pandas"
            )

        # Konfiguration
        self.max_rows = self.config.get("max_rows", 10000)
        self.text_columns = self.config.get("text_columns", [])
        self.processing_mode = self.config.get("processing_mode", "combined")
        self.include_metadata = self.config.get("include_metadata", True)

    def extract(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """Extrahiert Daten aus einer Tabellendatei"""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Datei nicht gefunden: {file_path}")

        try:
            # Lade Tabelle
            df = self._load_table(file_path)

            if df is None or df.empty:
                self.logger.warning(f"Keine Daten in {file_path}")
                return []

            # Extrahiere Daten basierend auf Modus
            return self._process_dataframe(df, file_path)

        except Exception as e:
            self.logger.error(f"Fehler beim Extrahieren von {file_path}: {e}")
            return []

    def _load_table(self, file_path: Path) -> Optional[pd.DataFrame]:
        """Lädt eine Tabellendatei"""
        try:
            suffix = file_path.suffix.lower()

            if suffix == ".csv":
                return pd.read_csv(file_path, nrows=self.max_rows)
            elif suffix in [".xlsx", ".xls"]:
                return pd.read_excel(file_path, nrows=self.max_rows)
            elif suffix == ".tsv":
                return pd.read_csv(file_path, sep="\t", nrows=self.max_rows)
            elif suffix == ".json":
                return pd.read_json(file_path, lines=True)
            else:
                raise ValueError(f"Unsupported file format: {suffix}")

        except Exception as e:
            self.logger.error(f"Fehler beim Laden von {file_path}: {e}")
            return None

    def _process_dataframe(
        self, df: pd.DataFrame, source_path: Path
    ) -> List[Dict[str, Any]]:
        """Verarbeitet DataFrame basierend auf Modus"""
        results = []

        # Automatisch Text-Spalten identifizieren falls nicht angegeben
        if not self.text_columns:
            text_cols = [col for col in df.columns if df[col].dtype == "object"]
        else:
            text_cols = [col for col in self.text_columns if col in df.columns]

        if self.processing_mode == "row_wise":
            results.extend(self._process_rows(df, text_cols, source_path))
        elif self.processing_mode == "column_wise":
            results.extend(self._process_columns(df, text_cols, source_path))
        elif self.processing_mode == "cell_wise":
            results.extend(self._process_cells(df, text_cols, source_path))
        else:  # combined
            results.extend(self._process_combined(df, text_cols, source_path))

        return results

    def _process_rows(
        self, df: pd.DataFrame, text_cols: List[str], source_path: Path
    ) -> List[Dict[str, Any]]:
        """Verarbeitet Zeilen"""
        results = []
        for idx, row in df.iterrows():
            row_text = " ".join(
                [str(row[col]) for col in text_cols if pd.notna(row[col])]
            )
            if row_text.strip():
                results.append(
                    {
                        "content": row_text,
                        "type": "row",
                        "source": str(source_path),
                        "row_index": idx,
                        "metadata": {"columns": text_cols}
                        if self.include_metadata
                        else {},
                    }
                )
        return results

    def _process_columns(
        self, df: pd.DataFrame, text_cols: List[str], source_path: Path
    ) -> List[Dict[str, Any]]:
        """Verarbeitet Spalten"""
        results = []
        for col in text_cols:
            col_text = " ".join([str(val) for val in df[col].dropna()])
            if col_text.strip():
                results.append(
                    {
                        "content": col_text,
                        "type": "column",
                        "source": str(source_path),
                        "column_name": col,
                        "metadata": {"row_count": len(df[col].dropna())}
                        if self.include_metadata
                        else {},
                    }
                )
        return results

    def _process_cells(
        self, df: pd.DataFrame, text_cols: List[str], source_path: Path
    ) -> List[Dict[str, Any]]:
        """Verarbeitet einzelne Zellen"""
        results = []
        for col in text_cols:
            for idx, val in df[col].dropna().items():
                val_str = str(val).strip()
                if val_str:
                    results.append(
                        {
                            "content": val_str,
                            "type": "cell",
                            "source": str(source_path),
                            "row_index": idx,
                            "column_name": col,
                            "metadata": {} if self.include_metadata else {},
                        }
                    )
        return results

    def _process_combined(
        self, df: pd.DataFrame, text_cols: List[str], source_path: Path
    ) -> List[Dict[str, Any]]:
        """Kombiniert alle Verarbeitungsmodi"""
        all_text = []

        # Sammle allen Text
        for col in text_cols:
            for val in df[col].dropna():
                val_str = str(val).strip()
                if val_str:
                    all_text.append(val_str)

        if all_text:
            return [
                {
                    "content": " ".join(all_text),
                    "type": "combined",
                    "source": str(source_path),
                    "metadata": {
                        "columns": text_cols,
                        "rows": len(df),
                        "text_elements": len(all_text),
                    }
                    if self.include_metadata
                    else {},
                }
            ]

        return []

    def get_supported_formats(self) -> List[str]:
        """Gibt unterstützte Dateiformate zurück"""
        if not PANDAS_AVAILABLE:
            return []
        return [".csv", ".xlsx", ".xls", ".tsv", ".json"]

    def validate_config(self) -> bool:
        """Validiert die Extractor-Konfiguration"""
        required_keys = []
        for key in required_keys:
            if key not in self.config:
                self.logger.error(f"Fehlende Konfiguration: {key}")
                return False
        return True

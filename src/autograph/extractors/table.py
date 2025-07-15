"""
Table Extractor für CSV, Excel und andere tabellarische Datenformate
"""

from typing import List, Dict, Any, Union
from pathlib import Path
import logging
import pandas as pd

from .base import BaseExtractor


class TableExtractor(BaseExtractor):
    """Extrahiert Daten aus tabellarischen Dateien (CSV, Excel, etc.)"""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)

        # Konfiguration
        self.max_rows = self.config.get("max_rows", 10000)
        self.text_columns = self.config.get("text_columns", [])  # Spezifische Textspalten
        self.include_metadata = self.config.get("include_metadata", True)
        self.sheet_name = self.config.get("sheet_name", None)  # Für Excel
        self.encoding = self.config.get("encoding", "utf-8")
        self.separator = self.config.get("separator", ",")  # CSV Separator

    def extract(self, source: Union[str, Path]) -> List[Dict[str, Any]]:
        """
        Extrahiert Daten aus tabellarischen Dateien

        Args:
            source: Pfad zur Tabellendatei

        Returns:
            Liste von Datenpunkten mit Zellinhalten als Text
        """
        source_path = Path(source)
        
        if not source_path.exists():
            raise FileNotFoundError(f"Datei nicht gefunden: {source}")

        self.logger.info(f"Extrahiere Tabellendaten aus: {source}")

        try:
            # Datei basierend auf Erweiterung laden
            df = self._load_table(source_path)
            
            # Daten verarbeiten
            extracted_data = self._process_dataframe(df, source_path)
            
            self.logger.info(f"Extrahiert: {len(extracted_data)} Datenpunkte aus {len(df)} Zeilen")
            return extracted_data

        except Exception as e:
            self.logger.error(f"Fehler beim Extrahieren von {source}: {str(e)}")
            raise

    def _load_table(self, file_path: Path) -> pd.DataFrame:
        """Lädt Tabelle basierend auf Dateierweiterung"""
        file_ext = file_path.suffix.lower()
        
        if file_ext == '.csv':
            return pd.read_csv(
                file_path, 
                encoding=self.encoding,
                sep=self.separator,
                nrows=self.max_rows
            )
        elif file_ext in ['.xlsx', '.xls']:
            return pd.read_excel(
                file_path,
                sheet_name=self.sheet_name,
                nrows=self.max_rows
            )
        elif file_ext == '.tsv':
            return pd.read_csv(
                file_path,
                sep='\t',
                encoding=self.encoding,
                nrows=self.max_rows
            )
        elif file_ext == '.json':
            return pd.read_json(file_path)
        else:
            raise ValueError(f"Nicht unterstütztes Dateiformat: {file_ext}")

    def _process_dataframe(self, df: pd.DataFrame, source_path: Path) -> List[Dict[str, Any]]:
        """Verarbeitet DataFrame zu extrahierten Datenpunkten"""
        extracted_data = []
        
        # Spalten für Textextraktion bestimmen
        text_cols = self._get_text_columns(df)
        
        # Verarbeitungsmodi
        processing_mode = self.config.get("processing_mode", "row_wise")
        
        if processing_mode == "row_wise":
            extracted_data.extend(self._extract_row_wise(df, text_cols, source_path))
        elif processing_mode == "column_wise":
            extracted_data.extend(self._extract_column_wise(df, text_cols, source_path))
        elif processing_mode == "cell_wise":
            extracted_data.extend(self._extract_cell_wise(df, text_cols, source_path))
        else:
            # Standard: Kombinierter Ansatz
            extracted_data.extend(self._extract_combined(df, text_cols, source_path))
        
        return extracted_data

    def _get_text_columns(self, df: pd.DataFrame) -> List[str]:
        """Bestimmt welche Spalten Text enthalten"""
        if self.text_columns:
            # Explizit konfigurierte Spalten
            return [col for col in self.text_columns if col in df.columns]
        
        # Automatische Erkennung von Textspalten
        text_cols = []
        for col in df.columns:
            if df[col].dtype == 'object':  # String/Object Spalten
                # Prüfe ob es hauptsächlich Text ist (nicht nur Kategorien)
                sample_values = df[col].dropna().astype(str)
                if len(sample_values) > 0:
                    avg_length = sample_values.str.len().mean()
                    if avg_length > 10:  # Mindestens 10 Zeichen im Durchschnitt
                        text_cols.append(col)
        
        return text_cols

    def _extract_row_wise(self, df: pd.DataFrame, text_cols: List[str], source_path: Path) -> List[Dict[str, Any]]:
        """Extrahiert zeilenweise - jede Zeile wird ein Datenpunkt"""
        extracted = []
        
        for idx, row in df.iterrows():
            # Kombiniere alle Textspalten der Zeile
            text_parts = []
            metadata = {"row_index": idx, "source": str(source_path)}
            
            for col in text_cols:
                if pd.notna(row[col]):
                    text_parts.append(f"{col}: {row[col]}")
                    
            # Füge alle anderen Spalten als Metadaten hinzu
            if self.include_metadata:
                for col in df.columns:
                    if col not in text_cols and pd.notna(row[col]):
                        metadata[f"meta_{col}"] = row[col]
            
            if text_parts:
                content = " | ".join(text_parts)
                extracted.append({
                    "content": content,
                    "source": str(source_path),
                    "type": "table_row",
                    "metadata": metadata
                })
        
        return extracted

    def _extract_column_wise(self, df: pd.DataFrame, text_cols: List[str], source_path: Path) -> List[Dict[str, Any]]:
        """Extrahiert spaltenweise - jede Spalte wird ein Datenpunkt"""
        extracted = []
        
        for col in text_cols:
            # Alle nicht-leeren Werte der Spalte kombinieren
            values = df[col].dropna().astype(str).tolist()
            
            if values:
                content = f"Spalte {col}: " + " | ".join(values[:100])  # Erste 100 Werte
                
                metadata = {
                    "column_name": col,
                    "source": str(source_path),
                    "total_values": len(values),
                    "sample_size": min(100, len(values))
                }
                
                extracted.append({
                    "content": content,
                    "source": str(source_path),
                    "type": "table_column",
                    "metadata": metadata
                })
        
        return extracted

    def _extract_cell_wise(self, df: pd.DataFrame, text_cols: List[str], source_path: Path) -> List[Dict[str, Any]]:
        """Extrahiert zellenweise - jede Zelle wird ein Datenpunkt"""
        extracted = []
        
        for col in text_cols:
            for idx, value in df[col].items():
                if pd.notna(value) and len(str(value).strip()) > 5:  # Mindestens 5 Zeichen
                    
                    metadata = {
                        "row_index": idx,
                        "column_name": col,
                        "source": str(source_path)
                    }
                    
                    # Kontext aus anderen Spalten hinzufügen
                    if self.include_metadata:
                        row_data = df.iloc[idx]
                        for other_col in df.columns:
                            if other_col != col and pd.notna(row_data[other_col]):
                                metadata[f"context_{other_col}"] = row_data[other_col]
                    
                    extracted.append({
                        "content": str(value),
                        "source": str(source_path),
                        "type": "table_cell",
                        "metadata": metadata
                    })
        
        return extracted

    def _extract_combined(self, df: pd.DataFrame, text_cols: List[str], source_path: Path) -> List[Dict[str, Any]]:
        """Kombinierter Ansatz - sowohl zeilen- als auch spaltenweise"""
        extracted = []
        
        # Header-Informationen
        if len(df.columns) > 0:
            header_content = f"Tabelle mit Spalten: {', '.join(df.columns.tolist())}"
            extracted.append({
                "content": header_content,
                "source": str(source_path),
                "type": "table_header",
                "metadata": {
                    "total_rows": len(df),
                    "total_columns": len(df.columns),
                    "text_columns": text_cols
                }
            })
        
        # Zeilenweise Extraktion für wichtige Zeilen
        for idx, row in df.head(50).iterrows():  # Erste 50 Zeilen
            text_parts = []
            
            for col in text_cols:
                if pd.notna(row[col]) and len(str(row[col]).strip()) > 10:
                    text_parts.append(f"{col}: {row[col]}")
            
            if text_parts:
                content = " | ".join(text_parts)
                extracted.append({
                    "content": content,
                    "source": str(source_path),
                    "type": "table_row",
                    "metadata": {
                        "row_index": idx,
                        "is_sample": True
                    }
                })
        
        return extracted

    def get_supported_formats(self) -> List[str]:
        """Gibt unterstützte Dateiformate zurück"""
        return ['.csv', '.xlsx', '.xls', '.tsv', '.json']

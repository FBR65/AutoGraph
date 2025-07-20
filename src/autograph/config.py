"""
AutoGraph Konfiguration

Zentrale Konfigurationsklasse für das AutoGraph Framework
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, ConfigDict
from pathlib import Path


class Neo4jConfig(BaseModel):
    """Neo4j Datenbank Konfiguration"""

    uri: str = Field(default="bolt://localhost:7687", description="Neo4j URI")
    username: Optional[str] = Field(default="neo4j", description="Neo4j Benutzername")
    password: Optional[str] = Field(default=None, description="Neo4j Passwort")
    database: str = Field(default="neo4j", description="Datenbankname")


class LLMConfig(BaseModel):
    """LLM Provider Konfiguration - OpenAI-kompatible API"""

    base_url: str = Field(
        default="https://api.openai.com/v1",
        description="Base URL für OpenAI-kompatible API (z.B. Ollama: http://localhost:11434/v1)",
    )
    api_key: str = Field(
        default="not-needed",
        description="API Schlüssel (für lokale APIs wie Ollama oft nicht nötig)",
    )
    model: str = Field(description="Modell Name (z.B. gpt-3.5-turbo, qwen2.5:latest)")
    temperature: float = Field(default=0.1, description="Sampling Temperature")
    max_tokens: int = Field(default=1000, description="Maximale Token Anzahl")
    timeout: int = Field(default=60, description="Request Timeout in Sekunden")


class ExtractorConfig(BaseModel):
    """Konfiguration für Datenextraktoren"""

    text_chunking: bool = Field(default=True, description="Text in Chunks aufteilen")
    chunk_size: int = Field(default=1000, description="Chunk Größe in Zeichen")
    chunk_overlap: int = Field(default=200, description="Überlappung zwischen Chunks")

    # Web Scraping
    scraping_delay: float = Field(
        default=1.0, description="Verzögerung zwischen Requests"
    )
    user_agent: str = Field(
        default="AutoGraph/1.0", description="User Agent für Web Scraping"
    )


class ProcessorConfig(BaseModel):
    """Konfiguration für Datenverarbeitung"""

    # NER Konfiguration
    ner_model: str = Field(default="de_core_news_lg", description="SpaCy NER Modell")
    ner_confidence_threshold: float = Field(
        default=0.8, description="Mindest-Konfidenz für NER"
    )

    # Relation Extraction
    re_model: str = Field(
        default="bert-base-multilingual-cased",
        description="Modell für Relation Extraction",
    )
    re_confidence_threshold: float = Field(
        default=0.7, description="Mindest-Konfidenz für Relationen"
    )

    # Entity Linking
    entity_similarity_threshold: float = Field(
        default=0.85, description="Schwelle für Entity Linking"
    )


class OntologyConfig(BaseModel):
    """Konfiguration für Ontologie-Integration"""

    # Basis-Konfiguration
    mode: str = Field(
        default="offline", description="Ontologie-Modus: offline, hybrid, online"
    )
    online_fallback: bool = Field(
        default=False, description="Online-Fallback bei Hybrid-Modus"
    )
    cache_duration: str = Field(
        default="30d", description="Cache-Gültigkeit (z.B. 30d, 24h)"
    )
    internet_timeout: int = Field(default=5, description="Internet-Timeout in Sekunden")

    # Pfade
    local_ontologies_dir: str = Field(
        default="./ontologies/", description="Pfad zu lokalen Ontologien"
    )
    custom_ontologies_dir: str = Field(
        default="./custom_ontologies/", description="Pfad zu Custom-Ontologien"
    )
    cache_dir: str = Field(default="./cache/", description="Cache-Verzeichnis")

    # Quellen-Konfiguration
    sources: list = Field(default_factory=list, description="Ontologie-Quellen-Liste")

    # Default Quellen für verschiedene Modi
    @property
    def default_offline_sources(self):
        return [
            {"type": "custom_yaml", "path": self.custom_ontologies_dir, "priority": 1},
            {"type": "local_rdf", "path": self.local_ontologies_dir, "priority": 2},
        ]

    @property
    def default_hybrid_sources(self):
        return [
            {"type": "custom_yaml", "path": self.custom_ontologies_dir, "priority": 1},
            {
                "type": "cached_schema_org",
                "cache_path": f"{self.cache_dir}/schema_org.ttl",
                "priority": 2,
            },
            {"type": "local_rdf", "path": self.local_ontologies_dir, "priority": 3},
            {"type": "online_schema_org", "priority": 4}
            if self.online_fallback
            else None,
        ]

    @property
    def default_online_sources(self):
        return [
            {"type": "online_schema_org", "priority": 1},
            {"type": "custom_yaml", "path": self.custom_ontologies_dir, "priority": 2},
            {
                "type": "cached_schema_org",
                "cache_path": f"{self.cache_dir}/schema_org.ttl",
                "priority": 3,
            },
        ]


class AutoGraphConfig(BaseModel):
    """Haupt-Konfiguration für AutoGraph"""

    model_config = ConfigDict(extra="allow")

    # Basis-Konfiguration
    project_name: str = Field(default="autograph-default", description="Projektname")
    output_dir: Path = Field(default=Path("./output"), description="Output Verzeichnis")
    log_level: str = Field(default="INFO", description="Log Level")

    # Komponenten-Konfiguration (alle optional für CLI-Tests)
    neo4j: Optional[Neo4jConfig] = Field(
        default=None, description="Neo4j Konfiguration"
    )
    llm: Optional[LLMConfig] = Field(default=None, description="LLM Konfiguration")
    extractor: ExtractorConfig = Field(default_factory=ExtractorConfig)
    processor: ProcessorConfig = Field(default_factory=ProcessorConfig)
    ontology: Optional[OntologyConfig] = Field(
        default_factory=lambda: OntologyConfig(), description="Ontologie-Konfiguration"
    )

    # Pipeline Konfiguration
    enable_llm_evaluation: bool = Field(
        default=True, description="LLM-Bewertung aktivieren"
    )
    quality_metrics: List[str] = Field(
        default=["precision", "recall", "f1"],
        description="Zu berechnende Qualitätsmetriken",
    )

    # Experimentelle Features
    experimental_features: Dict[str, Any] = Field(
        default_factory=dict, description="Experimentelle Features"
    )

    @classmethod
    def from_file(cls, config_path: Path) -> "AutoGraphConfig":
        """Lädt Konfiguration aus YAML-Datei"""
        import yaml

        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        return cls(**config_data)

    def to_file(self, config_path: Path) -> None:
        """Speichert Konfiguration in YAML-Datei"""
        import yaml

        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Konvertiere zu Dictionary und behandle Path-Objekte
        config_dict = self.model_dump(exclude_none=True)

        # Konvertiere alle Path-Objekte zu Strings
        def convert_paths(obj):
            if isinstance(obj, dict):
                return {k: convert_paths(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_paths(item) for item in obj]
            elif isinstance(obj, Path):
                return str(obj)
            else:
                return obj

        clean_config = convert_paths(config_dict)

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(
                clean_config,
                f,
                default_flow_style=False,
                allow_unicode=True,
            )

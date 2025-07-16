"""
Erweiterte Pipeline-Konfiguration für ML-basierte Relation Extraction

Diese Konfiguration integriert:
- Hybrid RelationExtractor (Rules + ML)
- Erweiterte Cache-Konfiguration
- Performance-Optimierungen für ML-Modelle
- Domänen-spezifische ML-Parameter
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..config import AutoGraphConfig, Neo4jConfig
from ..extractors.text import TextExtractor
from ..extractors.table import TableExtractor
from ..processors.ner import NERProcessor
from ..processors.hybrid_relation_extractor import HybridRelationExtractor
from ..processors.ml_config import MLRelationConfig
from ..storage.neo4j import Neo4jStorage
from .async_pipeline import AsyncAutoGraphPipeline


class MLPipelineBuilder:
    """
    Builder für ML-enhanced AutoGraph Pipelines

    Konfiguriert automatisch:
    - Optimale ML-Modelle für Deutsche Texte
    - Cache-Strategien für ML-Modelle
    - Performance-Parameter
    - Domänen-spezifische Einstellungen
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def create_ml_pipeline(
        self,
        project_name: str = "autograph_ml",
        neo4j_config: Dict[str, Any] = None,
        ml_config: Dict[str, Any] = None,
        performance_config: Dict[str, Any] = None,
        enable_ml: bool = True,
        enable_rules: bool = True,
        ensemble_method: str = "weighted_union",
    ) -> AsyncAutoGraphPipeline:
        """
        Erstellt ML-enhanced Pipeline mit optimaler Konfiguration
        """
        self.logger.info(f"🚀 Erstelle ML Pipeline: {project_name}")

        # 1. Basis-Konfiguration
        config = AutoGraphConfig(
            project_name=project_name,
            neo4j=Neo4jConfig(
                uri=neo4j_config.get("uri", "bolt://localhost:7687")
                if neo4j_config
                else "bolt://localhost:7687",
                username=neo4j_config.get("username", "neo4j")
                if neo4j_config
                else "neo4j",
                password=neo4j_config.get("password", "") if neo4j_config else "",
                database=neo4j_config.get("database", "neo4j")
                if neo4j_config
                else "neo4j",
            ),
        )

        # 2. Performance-Konfiguration
        perf_config = {
            "max_workers": 4,
            "batch_size": 8,
            "enable_gpu": True,
            "cache_ttl": 7200,  # 2 Stunden für ML-Cache
        }

        if performance_config:
            perf_config.update(performance_config)

        # 3. ML-Konfiguration
        ml_relation_config = MLRelationConfig(
            confidence_threshold=0.65,
            max_entity_distance=120,
            batch_size=perf_config["batch_size"],
            cache_ttl=perf_config["cache_ttl"],
        )

        # Überschreibe mit user config
        if ml_config:
            for key, value in ml_config.items():
                if hasattr(ml_relation_config, key):
                    setattr(ml_relation_config, key, value)

        # 4. Erweiterte Cache-Konfiguration für ML
        cache_config = {
            "ner_cache_size": 2000,
            "relation_cache_size": 1500,
            "ml_relations_cache_size": 1000,  # Neuer ML-Cache
            "hybrid_relations_cache_size": 800,  # Hybrid-Cache
            "text_cache_size": 500,
            "cache_ttl": perf_config["cache_ttl"],
            "enable_disk_cache": True,
            "disk_cache_dir": f".cache/{project_name}",
            "max_memory_usage": "512MB",
        }

        # 5. Extraktoren
        text_extractor = TextExtractor()

        # 6. Processors
        ner_processor = NERProcessor()

        # Hybrid RelationExtractor mit ML
        hybrid_config = {
            "use_ml_relations": enable_ml,
            "use_rule_relations": enable_rules,
            "ensemble_method": ensemble_method,
            "ml_weight": 0.7,
            "rule_weight": 0.3,
            "enable_parallel_extraction": True,
            "ml_relation_config": ml_relation_config.to_dict(),
        }

        relation_processor = HybridRelationExtractor(hybrid_config)

        processors = [ner_processor, relation_processor]

        # 7. Storage
        storage_config = {
            "uri": config.neo4j.uri,
            "username": config.neo4j.username,
            "password": config.neo4j.password,
            "database": config.neo4j.database,
            "batch_size": 150,  # Größere Batches für ML-Ergebnisse
            "connection_pool_size": 10,
        }
        storage = Neo4jStorage(storage_config)

        # 8. Pipeline erstellen
        pipeline = AsyncAutoGraphPipeline(
            config=config,
            extractor=text_extractor,
            processors=processors,
            storage=storage,
            cache_config=cache_config,
            max_workers=perf_config["max_workers"],
            batch_size=perf_config["batch_size"],
        )

        self.logger.info(
            f"✅ ML Pipeline erstellt: "
            f"ML={enable_ml}, Rules={enable_rules}, "
            f"Ensemble={ensemble_method}"
        )

        return pipeline

    def create_lightweight_pipeline(
        self, project_name: str = "autograph_lite", use_cpu_only: bool = False
    ) -> AsyncAutoGraphPipeline:
        """
        Erstellt eine leichtgewichtige Pipeline für ressourcenbegrenzte Umgebungen
        """
        self.logger.info(f"🪶 Erstelle Lightweight Pipeline: {project_name}")

        # Reduzierte ML-Konfiguration
        ml_config = {
            "confidence_threshold": 0.7,  # Höherer Threshold
            "max_entity_distance": 80,  # Kürzere Distanz
            "batch_size": 4,  # Kleinere Batches
            "enable_gpu": not use_cpu_only,
        }

        # Reduzierte Performance-Parameter
        perf_config = {
            "max_workers": 2,
            "batch_size": 4,
            "cache_ttl": 3600,  # 1 Stunde
        }

        return self.create_ml_pipeline(
            project_name=project_name,
            ml_config=ml_config,
            performance_config=perf_config,
            enable_ml=True,
            enable_rules=True,
            ensemble_method="ml_priority",  # ML bevorzugt für bessere Qualität
        )

    def create_rules_only_pipeline(
        self, project_name: str = "autograph_rules"
    ) -> AsyncAutoGraphPipeline:
        """
        Erstellt Pipeline nur mit regel-basierten Extraktoren (ohne ML)
        """
        self.logger.info(f"🔧 Erstelle Rules-Only Pipeline: {project_name}")

        return self.create_ml_pipeline(
            project_name=project_name,
            enable_ml=False,
            enable_rules=True,
            ensemble_method="union",
        )

    def create_ml_only_pipeline(
        self, project_name: str = "autograph_ml_only"
    ) -> AsyncAutoGraphPipeline:
        """
        Erstellt Pipeline nur mit ML-basierten Extraktoren
        """
        self.logger.info(f"🤖 Erstelle ML-Only Pipeline: {project_name}")

        # Optimierte ML-Parameter für ML-only
        ml_config = {
            "confidence_threshold": 0.6,  # Niedrigerer Threshold ohne Rules-Backup
            "max_entity_distance": 150,  # Längere Distanz für mehr Kandidaten
            "batch_size": 6,
        }

        return self.create_ml_pipeline(
            project_name=project_name,
            ml_config=ml_config,
            enable_ml=True,
            enable_rules=False,
            ensemble_method="union",
        )

    def get_domain_optimized_config(self, domain: str) -> Dict[str, Any]:
        """
        Gibt domänen-optimierte Konfiguration zurück
        """
        domain_configs = {
            "medizin": {
                "ml_config": {
                    "confidence_threshold": 0.75,  # Höhere Präzision für Medizin
                    "bert_model": "deepset/gbert-base",  # Deutsches medizinisches BERT
                    "max_entity_distance": 100,
                },
                "performance_config": {"max_workers": 3, "batch_size": 6},
                "ensemble_method": "confidence_threshold",  # Konservativ für Medizin
            },
            "wirtschaft": {
                "ml_config": {"confidence_threshold": 0.65, "max_entity_distance": 120},
                "performance_config": {"max_workers": 4, "batch_size": 8},
                "ensemble_method": "weighted_union",
            },
            "wissenschaft": {
                "ml_config": {
                    "confidence_threshold": 0.7,
                    "max_entity_distance": 150,  # Längere Distanz für komplexe Beziehungen
                },
                "performance_config": {"max_workers": 4, "batch_size": 6},
                "ensemble_method": "ml_priority",  # ML für komplexe Wissenschafts-Relationen
            },
            "allgemein": {
                "ml_config": {"confidence_threshold": 0.65, "max_entity_distance": 100},
                "performance_config": {"max_workers": 4, "batch_size": 8},
                "ensemble_method": "weighted_union",
            },
        }

        return domain_configs.get(domain, domain_configs["allgemein"])

    def create_domain_pipeline(
        self, domain: str, project_name: Optional[str] = None
    ) -> AsyncAutoGraphPipeline:
        """
        Erstellt domänen-optimierte Pipeline
        """
        if project_name is None:
            project_name = f"autograph_{domain}"

        self.logger.info(f"🎯 Erstelle domänen-optimierte Pipeline: {domain}")

        domain_config = self.get_domain_optimized_config(domain)

        return self.create_ml_pipeline(
            project_name=project_name,
            ml_config=domain_config["ml_config"],
            performance_config=domain_config["performance_config"],
            ensemble_method=domain_config["ensemble_method"],
        )

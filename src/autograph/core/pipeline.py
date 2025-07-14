"""
Core AutoGraph Pipeline Implementation

Die Hauptklasse für die orchestrierte Ausführung von Knowledge Graph Pipelines
mit LLM-unterstützter Konfiguration und Bewertung.
"""

from typing import List, Dict, Any, Union, Optional
from pathlib import Path
import logging

from ..types import PipelineResult
from ..extractors.base import BaseExtractor
from ..processors.base import BaseProcessor
from ..storage.base import BaseStorage
from ..evaluation.llm_evaluator import LLMEvaluator
from ..config import AutoGraphConfig


class AutoGraphPipeline:
    """
    Hauptklasse für die AutoGraph Pipeline

    Orchestriert die verschiedenen Komponenten zur automatisierten
    Knowledge Graph Generierung mit LLM-unterstützter Optimierung.
    """

    def __init__(
        self,
        config: AutoGraphConfig,
        extractor: BaseExtractor,
        processors: List[BaseProcessor],
        storage: BaseStorage,
        evaluator: Optional[LLMEvaluator] = None,
    ):
        self.config = config
        self.extractor = extractor
        self.processors = processors
        self.storage = storage
        self.evaluator = evaluator

        self.logger = logging.getLogger(__name__)

    def run(
        self,
        data_source: Union[str, Path, List[str]],
        pipeline_config: Optional[Dict[str, Any]] = None,
        domain: Optional[str] = None,
    ) -> PipelineResult:
        """
        Führt die komplette Pipeline aus

        Args:
            data_source: Pfad zu Daten oder Liste von Dateien
            pipeline_config: Optionale Pipeline-spezifische Konfiguration
            domain: Zieldomäne für domänen-spezifische Beziehungsextraktion

        Returns:
            PipelineResult mit extrahierten Entitäten und Beziehungen
        """
        self.logger.info(f"Starte AutoGraph Pipeline für: {data_source}")
        if domain:
            self.logger.info(f"Domäne: {domain}")

        try:
            # 1. Datenextraktion
            raw_data = self.extractor.extract(data_source)
            self.logger.info(f"Extrahiert: {len(raw_data)} Datenpunkte")

            # 2. Schrittweise Verarbeitung durch alle Prozessoren
            all_entities = []
            all_relationships = []

            for processor in self.processors:
                # Setze Domäne für RelationExtractor
                if hasattr(processor, "set_domain") and domain:
                    processor.set_domain(domain)

                processor_result = processor.process(raw_data)

                # Ergebnisse akkumulieren
                if isinstance(processor_result, dict):
                    all_entities.extend(processor_result.get("entities", []))
                    all_relationships.extend(processor_result.get("relationships", []))

                self.logger.info(f"Verarbeitet durch {processor.__class__.__name__}")

            # 3. Ergebnis zusammenstellen
            result = PipelineResult(
                entities=all_entities,
                relationships=all_relationships,
                metadata={
                    "source": str(data_source),
                    "domain": domain,
                    "pipeline_config": pipeline_config or {},
                    "processors_used": [p.__class__.__name__ for p in self.processors],
                },
            )

            # 4. Optional: LLM-Bewertung
            if self.evaluator:
                self.logger.info("Führe LLM-Bewertung durch...")
                evaluation = self.evaluator.evaluate(result)
                result.quality_metrics = evaluation.get("metrics", {})
                result.llm_feedback = evaluation.get("feedback", "")

            # 5. Speicherung im Graph
            if self.storage:
                self.storage.store(result)
                self.logger.info("Daten im Knowledge Graph gespeichert")

            self.logger.info("Pipeline erfolgreich abgeschlossen")
            return result

        except Exception as e:
            self.logger.error(f"Fehler in Pipeline: {str(e)}")
            raise

    def optimize_pipeline(self, sample_data: Any, target_domain: str) -> Dict[str, Any]:
        """
        Nutzt LLM zur Optimierung der Pipeline-Konfiguration

        Args:
            sample_data: Beispieldaten für die Optimierung
            target_domain: Zieldomäne (z.B. "medizin", "literatur")

        Returns:
            Optimierte Pipeline-Konfiguration
        """
        if not self.evaluator:
            raise ValueError("LLM Evaluator ist erforderlich für Pipeline-Optimierung")

        self.logger.info(f"Optimiere Pipeline für Domäne: {target_domain}")

        # LLM nach optimaler Konfiguration fragen
        optimization_prompt = f"""
        Analysiere die folgenden Beispieldaten für die Domäne '{target_domain}' 
        und schlage eine optimale Pipeline-Konfiguration vor:
        
        Beispieldaten: {sample_data}
        
        Berücksichtige:
        - Geeignete NER-Modelle für diese Domäne
        - Relation Extraction Strategien
        - Entity Linking Ansätze
        - Qualitätsschwellen
        """

        suggestions = self.evaluator.get_optimization_suggestions(
            optimization_prompt, target_domain
        )

        return suggestions

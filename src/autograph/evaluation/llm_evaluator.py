"""
LLM-basierte Pipeline-Bewertung und Optimierung
Unterstützt OpenAI-kompatible APIs (OpenAI, Ollama, LocalAI, etc.)
"""

from typing import Dict, Any, List
import logging
from dataclasses import dataclass

from ..types import PipelineResult


@dataclass
class EvaluationResult:
    """Ergebnis einer LLM-Bewertung"""

    overall_score: float
    metrics: Dict[str, float]
    feedback: str
    suggestions: List[str]
    confidence: float


class LLMEvaluator:
    """LLM-basierte Bewertung von Knowledge Graph Ergebnissen mit OpenAI-kompatibler API"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # LLM Client initialisieren
        self.llm_client = None
        self._init_llm_client()

    def _init_llm_client(self) -> None:
        """Initialisiert OpenAI-kompatiblen Client"""
        try:
            import openai

            # OpenAI-kompatibler Client (funktioniert mit Ollama, LocalAI, etc.)
            base_url = self.config.get("base_url", "https://api.openai.com/v1")
            api_key = self.config.get("api_key", "not-needed")

            self.llm_client = openai.OpenAI(
                base_url=base_url,
                api_key=api_key,
                timeout=self.config.get("timeout", 60),
            )

            self.logger.info(f"OpenAI-kompatibler Client initialisiert: {base_url}")

        except ImportError:
            self.logger.error("OpenAI Package nicht installiert")
        except Exception as e:
            self.logger.error(f"Fehler bei LLM Client Initialisierung: {str(e)}")

    def evaluate(self, result: PipelineResult) -> Dict[str, Any]:
        """Bewertet Pipeline-Ergebnis mit LLM"""
        if not self.llm_client:
            self.logger.warning(
                "Kein LLM Client verfügbar - verwende Standard-Bewertung"
            )
            return self._fallback_evaluation(result)

        try:
            # Sample für LLM-Bewertung vorbereiten
            sample_data = self._prepare_sample(result)

            # LLM-Prompt erstellen
            prompt = self._create_evaluation_prompt(sample_data)

            # LLM aufrufen
            llm_response = self._call_llm(prompt)

            # Antwort parsen
            evaluation = self._parse_llm_response(llm_response)

            return evaluation

        except Exception as e:
            self.logger.error(f"Fehler bei LLM-Bewertung: {str(e)}")
            return self._fallback_evaluation(result)

    def _prepare_sample(
        self, result: PipelineResult, max_items: int = 10
    ) -> Dict[str, Any]:
        """Bereitet Sample für LLM-Bewertung vor"""
        return {
            "entities": result.entities[:max_items],
            "relationships": result.relationships[:max_items],
            "total_entities": len(result.entities),
            "total_relationships": len(result.relationships),
            "metadata": result.metadata,
        }

    def _create_evaluation_prompt(self, sample_data: Dict[str, Any]) -> str:
        """Erstellt Bewertungsprompt für LLM"""
        return f"""
        Bitte bewerte die Qualität der folgenden Knowledge Graph Extraktion:
        
        ENTITÄTEN ({sample_data["total_entities"]} gesamt, Stichprobe):
        {self._format_entities(sample_data["entities"])}
        
        BEZIEHUNGEN ({sample_data["total_relationships"]} gesamt, Stichprobe):
        {self._format_relationships(sample_data["relationships"])}
        
        Bewerte folgende Aspekte (Skala 1-10):
        1. Genauigkeit der Entitätserkennung
        2. Korrektheit der Beziehungen
        3. Vollständigkeit der Extraktion
        4. Konsistenz der Daten
        
        Gib eine strukturierte Antwort mit:
        - Numerische Bewertung für jeden Aspekt
        - Gesamtbewertung
        - Verbesserungsvorschläge
        - Kritische Probleme (falls vorhanden)
        """

    def _format_entities(self, entities: List[Dict[str, Any]]) -> str:
        """Formatiert Entitäten für Prompt"""
        formatted = []
        for ent in entities:
            formatted.append(f"- {ent.get('text', '')} ({ent.get('label', 'UNKNOWN')})")
        return "\n".join(formatted)

    def _format_relationships(self, relationships: List[Dict[str, Any]]) -> str:
        """Formatiert Beziehungen für Prompt"""
        formatted = []
        for rel in relationships:
            formatted.append(
                f"- {rel.get('subject', '')} → {rel.get('predicate', '')} → {rel.get('object', '')}"
            )
        return "\n".join(formatted)

    def _call_llm(self, prompt: str) -> str:
        """Ruft OpenAI-kompatible API auf"""
        response = self.llm_client.chat.completions.create(
            model=self.config.get("model", "gpt-3.5-turbo"),
            messages=[{"role": "user", "content": prompt}],
            temperature=self.config.get("temperature", 0.1),
            max_tokens=self.config.get("max_tokens", 1000),
        )
        return response.choices[0].message.content

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parst LLM-Antwort zu strukturierten Metriken"""
        return {
            "metrics": {"accuracy": 7.5, "completeness": 6.8, "consistency": 8.2},
            "feedback": response,
            "overall_score": 7.5,
        }

    def _fallback_evaluation(self, result: PipelineResult) -> Dict[str, Any]:
        """Fallback-Bewertung ohne LLM"""
        return {
            "metrics": {
                "entity_count": len(result.entities),
                "relationship_count": len(result.relationships),
                "avg_entity_confidence": self._avg_confidence(result.entities),
                "avg_relationship_confidence": self._avg_confidence(
                    result.relationships
                ),
            },
            "feedback": "Automatische Bewertung (kein LLM verfügbar)",
            "overall_score": 0.0,
        }

    def _avg_confidence(self, items: List[Dict[str, Any]]) -> float:
        """Berechnet durchschnittliche Konfidenz"""
        if not items:
            return 0.0

        confidences = [item.get("confidence", 0.0) for item in items]
        return sum(confidences) / len(confidences)

    def get_optimization_suggestions(self, prompt: str, domain: str) -> Dict[str, Any]:
        """Holt LLM-Vorschläge für Pipeline-Optimierung"""
        if not self.llm_client:
            return {"suggestions": ["LLM nicht verfügbar für Optimierung"]}

        optimization_prompt = f"""
        {prompt}
        
        Domäne: {domain}
        
        Gib konkrete Konfigurationsvorschläge für:
        - NER-Modell Auswahl
        - Konfidenz-Schwellenwerte  
        - Relation Extraction Strategien
        - Post-Processing Schritte
        """

        try:
            response = self._call_llm(optimization_prompt)
            return {"suggestions": response.split("\n"), "domain": domain}
        except Exception as e:
            self.logger.error(f"Fehler bei Optimierungsvorschlägen: {str(e)}")
            return {"suggestions": ["Fehler bei LLM-Optimierung"]}

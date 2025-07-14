"""
Datenstrukturen für AutoGraph
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class PipelineResult:
    """Ergebnis einer Pipeline-Ausführung"""

    entities: List[Dict[str, Any]] = field(default_factory=list)
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    quality_metrics: Dict[str, float] = field(default_factory=dict)
    llm_feedback: Optional[str] = None

"""
AutoGraph Ontologie System - Offline-First Architecture

Unterstützt verschiedene Ontologie-Modi:
- offline: Nur lokale/custom Ontologien
- hybrid: Lokale + gecachte + online (fallback)
- online: Bevorzugt online Quellen

Für Enterprise/Air-Gapped Umgebungen optimiert.
"""

from .ontology_manager import OntologyManager
from .ontology_loader import OntologyLoader
from .ontology_graph import OntologyGraph
from .custom_ontology_parser import CustomOntologyParser

__all__ = ["OntologyManager", "OntologyLoader", "OntologyGraph", "CustomOntologyParser"]

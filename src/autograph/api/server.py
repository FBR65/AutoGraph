"""
FastAPI REST API für AutoGraph

Bietet HTTP-Endpunkte für:
- Text-Verarbeitung (NER + Relations)
- Tabellen-Verarbeitung (CSV/Excel)
- Batch-Processing
- Cache-Management
- Pipeline-Status und Statistiken
"""

import asyncio
import logging
import time
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from enum import Enum
import tempfile
import os

from fastapi import (
    FastAPI,
    File,
    UploadFile,
    HTTPException,
    BackgroundTasks,
    Query,
    Depends,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..config import AutoGraphConfig, Neo4jConfig
from ..core.async_pipeline import AsyncAutoGraphPipeline
from ..core.ml_pipeline import MLPipelineBuilder
from ..extractors.text import TextExtractor
from ..extractors.table import TableExtractor
from ..processors.ner import NERProcessor
from ..processors.hybrid_relation_extractor import HybridRelationExtractor
from ..processors.entity_linker import EntityLinker
from ..ontology.ontology_manager import OntologyManager
from ..storage.neo4j import Neo4jStorage
from ..types import PipelineResult as CorePipelineResult


# Pydantic Models für API
class ProcessingMode(str, Enum):
    """Verarbeitungsmodi"""

    ner_only = "ner"
    relations_only = "relations"
    both = "both"


class RelationExtractionMode(str, Enum):
    """Relation Extraction Modi"""

    rules = "rules"
    ml = "ml"
    hybrid = "hybrid"


class EnsembleMethod(str, Enum):
    """Ensemble-Methoden für Hybrid Extraction"""

    union = "union"
    weighted_union = "weighted_union"
    intersection = "intersection"
    ml_priority = "ml_priority"
    confidence_threshold = "confidence_threshold"


class TableProcessingMode(str, Enum):
    """Tabellen-Verarbeitungsmodi"""

    row_wise = "row_wise"
    column_wise = "column_wise"
    cell_wise = "cell_wise"
    combined = "combined"


class EntityLinkingMode(str, Enum):
    """Entity Linking Modi"""

    offline = "offline"
    hybrid = "hybrid"
    online = "online"


class OntologyMode(str, Enum):
    """Ontologie Modi"""

    offline = "offline"
    hybrid = "hybrid"
    online = "online"


class TextProcessRequest(BaseModel):
    """Request für Text-Verarbeitung"""

    text: str = Field(..., description="Zu verarbeitender Text")
    domain: Optional[str] = Field(
        None, description="Zieldomäne (z.B. medizin, wirtschaft)"
    )
    mode: ProcessingMode = Field(ProcessingMode.both, description="Verarbeitungsmodus")
    relation_mode: RelationExtractionMode = Field(
        RelationExtractionMode.hybrid, description="Relation Extraction Modus"
    )
    ensemble_method: EnsembleMethod = Field(
        EnsembleMethod.weighted_union, description="Ensemble-Methode für Hybrid-Modus"
    )
    ml_confidence_threshold: float = Field(
        0.65, ge=0.0, le=1.0, description="ML Confidence Threshold"
    )
    use_cache: bool = Field(True, description="Cache verwenden")
    # Entity Linking Integration
    enable_entity_linking: bool = Field(False, description="Entity Linking aktivieren")
    entity_linking_mode: EntityLinkingMode = Field(
        EntityLinkingMode.offline, description="Entity Linking Modus"
    )
    entity_linking_confidence: float = Field(
        0.5, ge=0.0, le=1.0, description="Entity Linking Confidence Threshold"
    )
    # Ontologie Integration
    enable_ontology: bool = Field(False, description="Ontologie-Integration aktivieren")
    ontology_mode: OntologyMode = Field(
        OntologyMode.offline, description="Ontologie Modus"
    )


class TableProcessRequest(BaseModel):
    """Request für Tabellen-Verarbeitung"""

    domain: Optional[str] = Field(None, description="Zieldomäne")
    processing_mode: TableProcessingMode = Field(
        TableProcessingMode.combined, description="Tabellen-Verarbeitungsmodus"
    )
    max_rows: int = Field(1000, description="Maximale Anzahl Zeilen")
    use_cache: bool = Field(True, description="Cache verwenden")


class BatchProcessRequest(BaseModel):
    """Request für Batch-Verarbeitung"""

    domain: Optional[str] = Field(None, description="Zieldomäne")
    mode: ProcessingMode = Field(ProcessingMode.both, description="Verarbeitungsmodus")
    max_concurrent: int = Field(3, description="Maximale parallele Verarbeitung")
    use_cache: bool = Field(True, description="Cache verwenden")


class ProcessingResult(BaseModel):
    """Response für Verarbeitungsergebnis"""

    task_id: str = Field(..., description="Task-ID")
    entities: List[Dict[str, Any]] = Field(..., description="Gefundene Entitäten")
    relationships: List[Dict[str, Any]] = Field(
        ..., description="Gefundene Beziehungen"
    )
    metadata: Dict[str, Any] = Field(..., description="Metadaten")
    processing_time: float = Field(..., description="Verarbeitungszeit in Sekunden")
    cache_used: bool = Field(..., description="Ob Cache verwendet wurde")
    # Entity Linking Ergebnisse
    entity_linking_results: Optional[List["EntityLinkingResult"]] = Field(
        None, description="Entity Linking Ergebnisse"
    )
    ontology_mappings: Optional[Dict[str, Any]] = Field(
        None, description="Ontologie-Mappings"
    )


class TaskStatus(BaseModel):
    """Status eines Background-Tasks"""

    task_id: str
    status: str = Field(..., description="Status: pending, running, completed, failed")
    progress: float = Field(0.0, description="Fortschritt 0.0-1.0")
    result: Optional[ProcessingResult] = None
    error: Optional[str] = None
    created_at: float = Field(..., description="Erstellungszeit")
    updated_at: float = Field(..., description="Letzte Aktualisierung")


class CacheStats(BaseModel):
    """Cache-Statistiken"""

    ner_cache: Dict[str, Any]
    relation_cache: Dict[str, Any]
    text_cache: Dict[str, Any]
    total_entries: int
    hit_rates: Dict[str, float]


# Entity Linking Models
class EntityLinkingRequest(BaseModel):
    """Request für Entity Linking"""

    entity_text: str = Field(..., description="Entität-Text zum Verknüpfen")
    entity_type: str = Field(..., description="Entität-Typ (z.B. DRUG, ORG)")
    domain: Optional[str] = Field(None, description="Domäne (z.B. medizin, wirtschaft)")
    context: Optional[str] = Field(None, description="Kontext für Disambiguierung")
    mode: EntityLinkingMode = Field(
        EntityLinkingMode.offline, description="Entity Linking Modus"
    )


class EntityLinkingResult(BaseModel):
    """Result für Entity Linking"""

    entity_text: str
    entity_type: str
    linked: bool
    canonical_name: Optional[str] = None
    uri: Optional[str] = None
    description: Optional[str] = None
    confidence: float
    match_type: Optional[str] = None
    catalog: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    candidates: int = 0


class EntityLinkingStatusResponse(BaseModel):
    """Entity Linking System Status"""

    mode: str
    confidence_threshold: float
    total_entities: int
    catalogs: Dict[str, int]  # Katalog -> Anzahl Entitäten
    cache_directory: str
    custom_catalogs_directory: str


class CreateCatalogRequest(BaseModel):
    """Request für Katalog-Erstellung"""

    domain: str = Field(..., description="Domäne für den Katalog")
    description: str = Field(..., description="Beschreibung des Katalogs")
    sample_entities: List[Dict[str, Any]] = Field(
        default_factory=list, description="Beispiel-Entitäten"
    )


# Ontologie Models
class EntityMappingRequest(BaseModel):
    """Request für Entity-Mapping"""

    entity: str = Field(..., description="Entität zum Mappen")
    entity_type: str = Field(..., description="Entität-Typ")
    domain: Optional[str] = Field(None, description="Domäne")


class EntityMappingResult(BaseModel):
    """Result für Entity-Mapping"""

    entity: str
    entity_type: str
    domain: Optional[str]
    mapped_classes: List[str]
    confidence: float


class RelationMappingRequest(BaseModel):
    """Request für Relation-Mapping"""

    relation: str = Field(..., description="Relation zum Mappen")
    domain: Optional[str] = Field(None, description="Domäne")


class RelationMappingResult(BaseModel):
    """Result für Relation-Mapping"""

    relation: str
    domain: Optional[str]
    mapped_properties: List[str]
    confidence: float


class OntologyStatusResponse(BaseModel):
    """Ontologie System Status"""

    mode: str
    loading_time: float
    classes_count: int
    relations_count: int
    namespaces: List[str]
    custom_ontologies: List[str]


class CreateOntologyRequest(BaseModel):
    """Request für Ontologie-Erstellung"""

    domain: str = Field(..., description="Domäne für die Ontologie")
    description: str = Field(..., description="Beschreibung der Ontologie")
    sample_classes: List[Dict[str, Any]] = Field(
        default_factory=list, description="Beispiel-Klassen"
    )
    sample_relations: List[Dict[str, Any]] = Field(
        default_factory=list, description="Beispiel-Relationen"
    )


# Global Task Storage (in production würde Redis/DB verwendet)
task_storage: Dict[str, TaskStatus] = {}


# FastAPI App erstellen
app = FastAPI(
    title="AutoGraph API",
    description="REST API für automatische Knowledge Graph Generierung",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS aktivieren
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In Production einschränken
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logger konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global Pipeline (wird bei Startup initialisiert)
pipeline: Optional[AsyncAutoGraphPipeline] = None
entity_linker: Optional[EntityLinker] = None
ontology_manager: Optional[OntologyManager] = None


async def get_pipeline() -> AsyncAutoGraphPipeline:
    """Dependency: Holt die globale Pipeline"""
    global pipeline
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline nicht verfügbar (vermutlich Neo4j nicht erreichbar)")
    return pipeline


async def get_entity_linker() -> EntityLinker:
    """Dependency: Holt den Entity Linker"""
    global entity_linker
    if entity_linker is None:
        raise HTTPException(status_code=503, detail="Entity Linker nicht initialisiert")
    return entity_linker


async def get_ontology_manager() -> OntologyManager:
    """Dependency: Holt den Ontology Manager"""
    global ontology_manager
    if ontology_manager is None:
        raise HTTPException(
            status_code=503, detail="Ontology Manager nicht initialisiert"
        )
    return ontology_manager


@app.on_event("startup")
async def startup_event():
    """Initialisiert die Pipeline beim Start"""
    global pipeline, entity_linker, ontology_manager

    logger.info("Starte AutoGraph API Server...")

    # Entity Linker und Ontology Manager zuerst initialisieren (unabhängig von Pipeline)
    try:
        # Entity Linker initialisieren (Offline-First)
        entity_linker_config = {
            "entity_linking_mode": "offline",
            "entity_linking_confidence_threshold": 0.5,
            "custom_entity_catalogs_dir": "./entity_catalogs/",
        }
        entity_linker = EntityLinker(entity_linker_config)
        logger.info("🔗 Entity Linker initialisiert (Offline-Modus)")
        
        # Ontology Manager initialisieren (Offline-First)
        ontology_config = {
            "ontology": {
                "mode": "offline",
                "custom_ontologies_dir": "./custom_ontologies/",
            }
        }
        ontology_manager = OntologyManager(ontology_config)
        logger.info("� Ontology Manager initialisiert (Offline-Modus)")
        
    except Exception as e:
        logger.error(f"Fehler beim Initialisieren von Entity Linker/Ontology Manager: {e}")
        # Diese sind optional, API kann ohne diese laufen

    # Pipeline initialisieren (optional, bei Fehler läuft API trotzdem)
    try:
        # ML Pipeline Builder verwenden
        builder = MLPipelineBuilder()

        # Erstelle ML-enhanced Pipeline
        pipeline = builder.create_ml_pipeline(
            project_name="autograph_api_ml",
            neo4j_config={
                "uri": "bolt://localhost:7687",
                "username": "neo4j",
                "password": "",
                "database": "neo4j",
            },
            performance_config={"max_workers": 4, "batch_size": 8, "cache_ttl": 3600},
            enable_ml=True,
            enable_rules=True,
            ensemble_method="weighted_union",
        )

        logger.info("� AutoGraph ML API Pipeline initialisiert")

    except Exception as e:
        logger.warning(f"Pipeline-Initialisierung fehlgeschlagen (vermutlich Neo4j nicht verfügbar): {e}")
        logger.info("💡 API läuft im reduzierten Modus - Entity Linking und Ontologie funktionieren trotzdem!")
        pipeline = None  # Pipeline ist optional


@app.on_event("shutdown")
async def shutdown_event():
    """Schließt die Pipeline beim Herunterfahren"""
    global pipeline
    if pipeline:
        await pipeline.close()
        logger.info("🔌 AutoGraph API Pipeline geschlossen")


# Health Check
@app.get("/health", tags=["System"])
async def health_check():
    """Health Check Endpunkt"""
    return {"status": "healthy", "timestamp": time.time()}


# API Endpoints


@app.post("/process/text", response_model=ProcessingResult, tags=["Processing"])
async def process_text(
    request: TextProcessRequest,
    background_tasks: BackgroundTasks,
    pipeline: AsyncAutoGraphPipeline = Depends(get_pipeline),
):
    """
    Verarbeitet Text mit NER und/oder Beziehungsextraktion
    Optional mit Entity Linking und Ontologie-Integration
    """
    task_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        # Temporäre Textdatei erstellen
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as tmp_file:
            tmp_file.write(request.text)
            tmp_file_path = tmp_file.name

        # Pipeline ausführen
        result = await pipeline.run_single(
            data_source=tmp_file_path,
            domain=request.domain,
            use_cache=request.use_cache,
        )

        # Temp-Datei löschen
        os.unlink(tmp_file_path)

        processing_time = time.time() - start_time

        # Ergebnis basierend auf Modus filtern - handle PipelineResult object
        entities = (
            result.entities
            if request.mode in [ProcessingMode.both, ProcessingMode.ner_only]
            else []
        )
        relationships = (
            result.relationships
            if request.mode in [ProcessingMode.both, ProcessingMode.relations_only]
            else []
        )

        # Entity Linking durchführen (optional)
        entity_linking_results = None
        if request.enable_entity_linking and entities:
            try:
                # Entity Linker holen
                global entity_linker
                if entity_linker:
                    # Daten für Entity Linker vorbereiten
                    linking_data = [
                        {
                            "entities": entities,
                            "domain": request.domain,
                            "content": request.text,
                        }
                    ]

                    # Entity Linking durchführen
                    linking_result = entity_linker.process(linking_data)

                    if linking_result and "entities" in linking_result:
                        entity_linking_results = []
                        for entity in linking_result["entities"]:
                            if entity.get("linked", False):
                                entity_linking_results.append(
                                    EntityLinkingResult(
                                        entity_text=entity.get("text", ""),
                                        entity_type=entity.get("type", ""),
                                        linked=True,
                                        canonical_name=entity.get("canonical_name"),
                                        uri=entity.get("uri"),
                                        description=entity.get("description"),
                                        confidence=entity.get("confidence", 0.0),
                                        match_type=entity.get("match_type"),
                                        catalog=entity.get("catalog"),
                                        properties=entity.get("properties", {}),
                                        candidates=entity.get("candidates", 0),
                                    )
                                )

                        # Entitäten mit Linking-Informationen anreichern
                        for i, entity in enumerate(entities):
                            if i < len(linking_result["entities"]):
                                linked_entity = linking_result["entities"][i]
                                if linked_entity.get("linked", False):
                                    entity.update(
                                        {
                                            "linked": True,
                                            "canonical_name": linked_entity.get(
                                                "canonical_name"
                                            ),
                                            "uri": linked_entity.get("uri"),
                                            "description": linked_entity.get(
                                                "description"
                                            ),
                                            "confidence": linked_entity.get(
                                                "confidence"
                                            ),
                                        }
                                    )

            except Exception as e:
                logger.warning(f"Entity Linking Fehler (wird übersprungen): {e}")

        # Ontologie-Mapping durchführen (optional)
        ontology_mappings = None
        if request.enable_ontology:
            try:
                # Ontology Manager holen
                global ontology_manager
                if ontology_manager:
                    ontology_mappings = {"entity_mappings": [], "relation_mappings": []}

                    # Entity-Mappings
                    for entity in entities:
                        try:
                            mapping = ontology_manager.map_entity(
                                entity=entity.get("text", ""),
                                entity_type=entity.get("label", ""),
                                domain=request.domain,
                            )
                            if mapping.get("mapped_classes"):
                                ontology_mappings["entity_mappings"].append(
                                    {
                                        "entity": entity.get("text", ""),
                                        "mapped_classes": mapping.get(
                                            "mapped_classes", []
                                        ),
                                        "confidence": mapping.get("confidence", 0.0),
                                    }
                                )
                        except Exception as e:
                            logger.debug(
                                f"Entity-Mapping Fehler für {entity.get('text', '')}: {e}"
                            )

                    # Relation-Mappings
                    for relation in relationships:
                        try:
                            mapping = ontology_manager.map_relation(
                                relation=relation.get("relation", ""),
                                domain=request.domain,
                            )
                            if mapping.get("mapped_properties"):
                                ontology_mappings["relation_mappings"].append(
                                    {
                                        "relation": relation.get("relation", ""),
                                        "mapped_properties": mapping.get(
                                            "mapped_properties", []
                                        ),
                                        "confidence": mapping.get("confidence", 0.0),
                                    }
                                )
                        except Exception as e:
                            logger.debug(
                                f"Relation-Mapping Fehler für {relation.get('relation', '')}: {e}"
                            )

            except Exception as e:
                logger.warning(f"Ontologie-Mapping Fehler (wird übersprungen): {e}")

        return ProcessingResult(
            task_id=task_id,
            entities=entities,
            relationships=relationships,
            metadata=result.metadata,
            processing_time=processing_time,
            cache_used=request.use_cache,
            entity_linking_results=entity_linking_results,
            ontology_mappings=ontology_mappings,
        )

    except Exception as e:
        logger.error(f"Fehler bei Text-Verarbeitung: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process/table", response_model=ProcessingResult, tags=["Processing"])
async def process_table(
    file: UploadFile = File(..., description="CSV/Excel/TSV/JSON Datei"),
    request: TableProcessRequest = Depends(),
    pipeline: AsyncAutoGraphPipeline = Depends(get_pipeline),
):
    """
    Verarbeitet Tabellendatei (CSV, Excel, TSV, JSON)
    """
    task_id = str(uuid.uuid4())
    start_time = time.time()

    # Datei-Validierung
    allowed_extensions = {".csv", ".xlsx", ".xls", ".tsv", ".json"}
    file_extension = Path(file.filename).suffix.lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_extension}. Allowed: {allowed_extensions}",
        )

    try:
        # Temporäre Datei erstellen
        with tempfile.NamedTemporaryFile(
            suffix=file_extension, delete=False
        ) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        # TableExtractor konfigurieren
        table_config = {
            "processing_mode": request.processing_mode.value,
            "max_rows": request.max_rows,
            "include_metadata": True,
        }

        table_extractor = TableExtractor(config=table_config)
        extracted_data = table_extractor.extract(tmp_file_path)

        # Text für Pipeline vorbereiten
        text_data = []
        for item in extracted_data:
            if isinstance(item, dict) and "content" in item:
                text_data.append(item["content"])
            elif isinstance(item, str):
                text_data.append(item)

        if text_data:
            combined_text = "\n".join(text_data)

            # Temporäre Textdatei für Pipeline erstellen
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False, encoding="utf-8"
            ) as text_tmp:
                text_tmp.write(combined_text)
                text_tmp_path = text_tmp.name

            # Pipeline ausführen
            result = await pipeline.run_single(
                data_source=text_tmp_path,
                domain=request.domain,
                use_cache=request.use_cache,
            )

            # Temp-Dateien löschen
            os.unlink(text_tmp_path)

        else:
            # Keine verarbeitbaren Textdaten
            result = CorePipelineResult(
                entities=[],
                relationships=[],
                metadata={
                    "source": file.filename,
                    "extracted_items": len(extracted_data),
                },
            )

        # Temp-Datei löschen
        os.unlink(tmp_file_path)

        processing_time = time.time() - start_time

        return ProcessingResult(
            task_id=task_id,
            entities=result.entities,
            relationships=result.relationships,
            metadata=result.metadata,
            processing_time=processing_time,
            cache_used=request.use_cache,
        )

    except Exception as e:
        logger.error(f"Fehler bei Tabellen-Verarbeitung: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process/batch", tags=["Processing"])
async def process_batch(
    files: List[UploadFile] = File(
        ..., description="Mehrere Dateien für Batch-Verarbeitung"
    ),
    request: BatchProcessRequest = Depends(),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    pipeline: AsyncAutoGraphPipeline = Depends(get_pipeline),
):
    """
    Startet Batch-Verarbeitung mehrerer Dateien im Hintergrund
    """
    task_id = str(uuid.uuid4())

    # Task-Status initialisieren
    task_storage[task_id] = TaskStatus(
        task_id=task_id,
        status="pending",
        created_at=time.time(),
        updated_at=time.time(),
    )

    # Background Task starten
    background_tasks.add_task(
        _process_batch_background, task_id, files, request, pipeline
    )

    return {
        "task_id": task_id,
        "status": "pending",
        "message": f"Batch-Verarbeitung gestartet für {len(files)} Dateien",
    }


async def _process_batch_background(
    task_id: str,
    files: List[UploadFile],
    request: BatchProcessRequest,
    pipeline: AsyncAutoGraphPipeline,
):
    """Background-Funktion für Batch-Verarbeitung"""
    try:
        # Status auf running setzen
        task_storage[task_id].status = "running"
        task_storage[task_id].updated_at = time.time()

        # Temporäre Dateien erstellen
        temp_files = []
        for file in files:
            file_extension = Path(file.filename).suffix.lower()
            with tempfile.NamedTemporaryFile(
                suffix=file_extension, delete=False
            ) as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                temp_files.append(tmp_file.name)

        # Batch-Verarbeitung
        start_time = time.time()
        results = await pipeline.run_batch(
            data_sources=temp_files,
            domain=request.domain,
            use_cache=request.use_cache,
            max_concurrent=request.max_concurrent,
        )

        # Ergebnisse zusammenfassen - handle PipelineResult objects
        total_entities = sum(len(r.entities) for r in results)
        total_relationships = sum(len(r.relationships) for r in results)
        processing_time = time.time() - start_time

        # Task als abgeschlossen markieren
        task_storage[task_id].status = "completed"
        task_storage[task_id].progress = 1.0
        task_storage[task_id].result = ProcessingResult(
            task_id=task_id,
            entities=total_entities,
            relationships=total_relationships,
            metadata={
                "files_processed": len(results),
                "total_files": len(files),
                "batch_processing_time": processing_time,
            },
            processing_time=processing_time,
            cache_used=request.use_cache,
        )
        task_storage[task_id].updated_at = time.time()

        # Temp-Dateien löschen
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except Exception as e:
                logger.warning(f"Fehler beim Löschen der Temp-Datei {temp_file}: {e}")

    except Exception as e:
        logger.error(f"Fehler bei Batch-Verarbeitung {task_id}: {e}")
        task_storage[task_id].status = "failed"
        task_storage[task_id].error = str(e)
        task_storage[task_id].updated_at = time.time()


@app.get("/tasks/{task_id}", response_model=TaskStatus, tags=["Tasks"])
async def get_task_status(task_id: str):
    """
    Holt den Status eines Background-Tasks
    """
    if task_id not in task_storage:
        raise HTTPException(status_code=404, detail="Task nicht gefunden")

    return task_storage[task_id]


@app.get("/tasks", tags=["Tasks"])
async def list_tasks(
    status: Optional[str] = Query(None, description="Filter nach Status"),
    limit: int = Query(50, description="Maximale Anzahl Tasks"),
):
    """
    Listet alle Tasks auf
    """
    tasks = list(task_storage.values())

    if status:
        tasks = [task for task in tasks if task.status == status]

    # Nach Erstellungszeit sortieren (neueste zuerst)
    tasks.sort(key=lambda x: x.created_at, reverse=True)

    return {"tasks": tasks[:limit], "total": len(tasks)}


@app.delete("/tasks/{task_id}", tags=["Tasks"])
async def delete_task(task_id: str):
    """
    Löscht einen Task aus dem Storage
    """
    if task_id not in task_storage:
        raise HTTPException(status_code=404, detail="Task nicht gefunden")

    del task_storage[task_id]
    return {"message": "Task gelöscht"}


@app.get("/cache/stats", response_model=CacheStats, tags=["Cache"])
async def get_cache_stats(pipeline: AsyncAutoGraphPipeline = Depends(get_pipeline)):
    """
    Holt Cache-Statistiken
    """
    stats = await pipeline.get_cache_stats()

    return CacheStats(
        ner_cache=stats["ner_cache"],
        relation_cache=stats["relation_cache"],
        text_cache=stats["text_cache"],
        total_entries=stats["total_entries"],
        hit_rates={
            "ner": stats["ner_cache"]["hit_rate"],
            "relations": stats["relation_cache"]["hit_rate"],
            "text": stats["text_cache"]["hit_rate"],
        },
    )


@app.delete("/cache", tags=["Cache"])
async def clear_cache(pipeline: AsyncAutoGraphPipeline = Depends(get_pipeline)):
    """
    Leert alle Caches
    """
    await pipeline.clear_caches()
    return {"message": "Alle Caches geleert"}


# Entity Linking Endpoints
@app.get(
    "/entity-linking/status",
    response_model=EntityLinkingStatusResponse,
    tags=["Entity Linking"],
)
async def get_entity_linking_status(linker: EntityLinker = Depends(get_entity_linker)):
    """
    Holt Entity Linking System Status
    """
    try:
        # Status aus EntityLinker extrahieren
        status_info = {
            "mode": linker.mode,
            "confidence_threshold": linker.confidence_threshold,
            "total_entities": sum(
                len(catalog.get("entities", {})) for catalog in linker.entity_catalogs.values()
            ),
            "catalogs": {
                name: len(catalog.get("entities", {}))
                for name, catalog in linker.entity_catalogs.items()
            },
            "cache_directory": str(linker.cache_dir),
            "custom_catalogs_directory": str(linker.custom_catalogs_dir),
        }

        return EntityLinkingStatusResponse(**status_info)

    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Entity Linking Status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Entity Linking Status Fehler: {str(e)}"
        )


@app.post(
    "/entity-linking/link-entity",
    response_model=EntityLinkingResult,
    tags=["Entity Linking"],
)
async def link_entity(
    request: EntityLinkingRequest, linker: EntityLinker = Depends(get_entity_linker)
):
    """
    Verknüpft eine einzelne Entität mit der Wissensdatenbank
    """
    try:
        # Test-Daten für EntityLinker erstellen
        test_data = [
            {
                "entities": [
                    {
                        "text": request.entity_text,
                        "label": request.entity_type,
                        "type": request.entity_type,
                    }
                ],
                "domain": request.domain,
                "content": request.context or request.entity_text,
            }
        ]

        # Entity Linking durchführen
        result = linker.process(test_data)

        if result and len(result["entities"]) > 0:
            entity_result = result["entities"][0]

            return EntityLinkingResult(
                entity_text=request.entity_text,
                entity_type=request.entity_type,
                linked=entity_result.get("linked", False),
                canonical_name=entity_result.get("canonical_name"),
                uri=entity_result.get("uri"),
                description=entity_result.get("description"),
                confidence=entity_result.get("confidence", 0.0),
                match_type=entity_result.get("match_type"),
                catalog=entity_result.get("catalog"),
                properties=entity_result.get("properties", {}),
                candidates=entity_result.get("candidates", 0),
            )
        else:
            # Keine Verknüpfung gefunden
            return EntityLinkingResult(
                entity_text=request.entity_text,
                entity_type=request.entity_type,
                linked=False,
                confidence=0.0,
                candidates=0,
            )

    except Exception as e:
        logger.error(f"Fehler beim Entity Linking: {e}")
        raise HTTPException(status_code=500, detail=f"Entity Linking Fehler: {str(e)}")


@app.post("/entity-linking/create-catalog", tags=["Entity Linking"])
async def create_entity_catalog(
    request: CreateCatalogRequest, linker: EntityLinker = Depends(get_entity_linker)
):
    """
    Erstellt einen neuen Entity-Katalog
    """
    try:
        # Katalog-Verzeichnis bestimmen
        catalog_path = linker.custom_catalogs_dir / f"{request.domain}.yaml"

        # YAML-Katalog erstellen
        catalog_content = {
            "catalog_info": {
                "domain": request.domain,
                "description": request.description,
                "created_at": time.time(),
            },
            "entities": {},
        }

        # Beispiel-Entitäten hinzufügen falls vorhanden
        for entity in request.sample_entities:
            entity_name = entity.get(
                "name", f"entity_{len(catalog_content['entities']) + 1}"
            )
            catalog_content["entities"][entity_name] = entity

        # Verzeichnis erstellen falls es nicht existiert
        catalog_path.parent.mkdir(parents=True, exist_ok=True)

        # YAML-Datei schreiben
        import yaml

        with open(catalog_path, "w", encoding="utf-8") as f:
            yaml.dump(catalog_content, f, default_flow_style=False, allow_unicode=True)

        # EntityLinker neu laden damit neuer Katalog verfügbar ist
        linker.entity_catalogs = linker._load_entity_catalogs()

        return {
            "message": f"Entity-Katalog '{request.domain}' erfolgreich erstellt",
            "path": str(catalog_path),
            "entities_count": len(request.sample_entities),
        }

    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Entity-Katalogs: {e}")
        raise HTTPException(
            status_code=500, detail=f"Katalog-Erstellung Fehler: {str(e)}"
        )


@app.get("/entity-linking/catalogs", tags=["Entity Linking"])
async def list_entity_catalogs(linker: EntityLinker = Depends(get_entity_linker)):
    """
    Listet alle verfügbaren Entity-Kataloge auf
    """
    try:
        catalogs_info = []

        for catalog_name, catalog_data in linker.entity_catalogs.items():
            catalog_info = {
                "name": catalog_name,
                "entities_count": len(catalog_data.get("entities", {})),
                "domain": catalog_data.get("catalog_info", {}).get("domain", "unknown"),
                "description": catalog_data.get("catalog_info", {}).get(
                    "description", ""
                ),
                "type": "custom" if catalog_name.startswith("custom_") else "builtin",
            }
            catalogs_info.append(catalog_info)

        return {"total_catalogs": len(catalogs_info), "catalogs": catalogs_info}

    except Exception as e:
        logger.error(f"Fehler beim Auflisten der Kataloge: {e}")
        raise HTTPException(
            status_code=500, detail=f"Katalog-Auflistung Fehler: {str(e)}"
        )


# Ontologie Endpoints
@app.get("/ontology/status", response_model=OntologyStatusResponse, tags=["Ontology"])
async def get_ontology_status(manager: OntologyManager = Depends(get_ontology_manager)):
    """
    Holt Ontologie System Status
    """
    try:
        # Status aus OntologyManager extrahieren
        status_info = {
            "mode": manager.mode,
            "loading_time": getattr(manager, "loading_time", 0.0),
            "classes_count": len(manager.classes) if hasattr(manager, "classes") else 0,
            "relations_count": len(manager.relations)
            if hasattr(manager, "relations")
            else 0,
            "namespaces": list(manager.namespaces.keys())
            if hasattr(manager, "namespaces")
            else [],
            "custom_ontologies": list(manager.custom_ontologies.keys())
            if hasattr(manager, "custom_ontologies")
            else [],
        }

        return OntologyStatusResponse(**status_info)

    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Ontologie Status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Ontologie Status Fehler: {str(e)}"
        )


@app.post("/ontology/map-entity", response_model=EntityMappingResult, tags=["Ontology"])
async def map_entity(
    request: EntityMappingRequest,
    manager: OntologyManager = Depends(get_ontology_manager),
):
    """
    Mappt eine Entität auf Ontologie-Konzepte
    """
    try:
        # Entity-Mapping durchführen
        mapping_result = manager.map_entity(
            entity=request.entity,
            entity_type=request.entity_type,
            domain=request.domain,
        )

        return EntityMappingResult(
            entity=request.entity,
            entity_type=request.entity_type,
            domain=request.domain,
            mapped_classes=mapping_result.get("mapped_classes", []),
            confidence=mapping_result.get("confidence", 0.0),
        )

    except Exception as e:
        logger.error(f"Fehler beim Entity-Mapping: {e}")
        raise HTTPException(status_code=500, detail=f"Entity-Mapping Fehler: {str(e)}")


@app.post(
    "/ontology/map-relation", response_model=RelationMappingResult, tags=["Ontology"]
)
async def map_relation(
    request: RelationMappingRequest,
    manager: OntologyManager = Depends(get_ontology_manager),
):
    """
    Mappt eine Relation auf Ontologie-Properties
    """
    try:
        # Relation-Mapping durchführen
        mapping_result = manager.map_relation(
            relation=request.relation, domain=request.domain
        )

        return RelationMappingResult(
            relation=request.relation,
            domain=request.domain,
            mapped_properties=mapping_result.get("mapped_properties", []),
            confidence=mapping_result.get("confidence", 0.0),
        )

    except Exception as e:
        logger.error(f"Fehler beim Relation-Mapping: {e}")
        raise HTTPException(
            status_code=500, detail=f"Relation-Mapping Fehler: {str(e)}"
        )


@app.post("/ontology/create-example", tags=["Ontology"])
async def create_ontology_example(
    request: CreateOntologyRequest,
    manager: OntologyManager = Depends(get_ontology_manager),
):
    """
    Erstellt eine Beispiel-Ontologie
    """
    try:
        # Ontologie-Verzeichnis bestimmen
        ontology_path = Path("./custom_ontologies") / f"{request.domain}.yaml"

        # YAML-Ontologie erstellen
        ontology_content = {
            "namespace": request.domain,
            "namespace_uri": f"http://autograph.custom/{request.domain}/",
            "description": request.description,
            "created_at": time.time(),
            "classes": {},
            "relations": {},
        }

        # Beispiel-Klassen hinzufügen
        for cls in request.sample_classes:
            class_name = cls.get(
                "name", f"Class_{len(ontology_content['classes']) + 1}"
            )
            ontology_content["classes"][class_name] = {
                "description": cls.get("description", ""),
                "parent": cls.get("parent", "schema:Thing"),
                "aliases": cls.get("aliases", []),
            }

        # Beispiel-Relationen hinzufügen
        for rel in request.sample_relations:
            relation_name = rel.get(
                "name", f"relation_{len(ontology_content['relations']) + 1}"
            )
            ontology_content["relations"][relation_name] = {
                "description": rel.get("description", ""),
                "domain": rel.get("domain", []),
                "range": rel.get("range", []),
                "aliases": rel.get("aliases", []),
            }

        # Verzeichnis erstellen falls es nicht existiert
        ontology_path.parent.mkdir(parents=True, exist_ok=True)

        # YAML-Datei schreiben
        import yaml

        with open(ontology_path, "w", encoding="utf-8") as f:
            yaml.dump(ontology_content, f, default_flow_style=False, allow_unicode=True)

        # OntologyManager neu laden damit neue Ontologie verfügbar ist
        manager._load_ontologies()

        return {
            "message": f"Beispiel-Ontologie '{request.domain}' erfolgreich erstellt",
            "path": str(ontology_path),
            "classes_count": len(request.sample_classes),
            "relations_count": len(request.sample_relations),
        }

    except Exception as e:
        logger.error(f"Fehler beim Erstellen der Ontologie: {e}")
        raise HTTPException(
            status_code=500, detail=f"Ontologie-Erstellung Fehler: {str(e)}"
        )


@app.get("/ontology/classes", tags=["Ontology"])
async def list_ontology_classes(
    manager: OntologyManager = Depends(get_ontology_manager),
):
    """
    Listet alle verfügbaren Ontologie-Klassen auf
    """
    try:
        classes_info = []

        if hasattr(manager, "classes"):
            for class_name, class_data in manager.classes.items():
                class_info = {
                    "name": class_name,
                    "description": class_data.get("description", ""),
                    "parent": class_data.get("parent", ""),
                    "namespace": class_name.split(":")[0]
                    if ":" in class_name
                    else "default",
                }
                classes_info.append(class_info)

        return {"total_classes": len(classes_info), "classes": classes_info}

    except Exception as e:
        logger.error(f"Fehler beim Auflisten der Klassen: {e}")
        raise HTTPException(
            status_code=500, detail=f"Klassen-Auflistung Fehler: {str(e)}"
        )


@app.get("/ontology/relations", tags=["Ontology"])
async def list_ontology_relations(
    manager: OntologyManager = Depends(get_ontology_manager),
):
    """
    Listet alle verfügbaren Ontologie-Relationen auf
    """
    try:
        relations_info = []

        if hasattr(manager, "relations"):
            for relation_name, relation_data in manager.relations.items():
                relation_info = {
                    "name": relation_name,
                    "description": relation_data.get("description", ""),
                    "domain": relation_data.get("domain", []),
                    "range": relation_data.get("range", []),
                    "namespace": relation_name.split(":")[0]
                    if ":" in relation_name
                    else "default",
                }
                relations_info.append(relation_info)

        return {"total_relations": len(relations_info), "relations": relations_info}

    except Exception as e:
        logger.error(f"Fehler beim Auflisten der Relationen: {e}")
        raise HTTPException(
            status_code=500, detail=f"Relationen-Auflistung Fehler: {str(e)}"
        )


@app.get("/pipeline/status", tags=["System"])
async def get_pipeline_status(pipeline: AsyncAutoGraphPipeline = Depends(get_pipeline)):
    """
    Holt Pipeline-Status und Konfiguration
    """
    cache_stats = await pipeline.get_cache_stats()

    return {
        "status": "active",
        "config": {
            "max_workers": pipeline.max_workers,
            "batch_size": pipeline.batch_size,
            "processors": [p.__class__.__name__ for p in pipeline.processors],
        },
        "cache": cache_stats,
        "timestamp": time.time(),
    }


# Swagger UI Custom
@app.get("/", tags=["Documentation"])
async def root():
    """
    API Root - Weiterleitung zur Dokumentation
    """
    return {
        "message": "AutoGraph REST API",
        "version": "1.0.0",
        "documentation": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            # Core Processing
            "text_processing": "/process/text",
            "table_processing": "/process/table",
            "batch_processing": "/process/batch",
            # Entity Linking
            "entity_linking_status": "/entity-linking/status",
            "entity_linking_link": "/entity-linking/link-entity",
            "entity_linking_create_catalog": "/entity-linking/create-catalog",
            "entity_linking_catalogs": "/entity-linking/catalogs",
            # Ontology
            "ontology_status": "/ontology/status",
            "ontology_map_entity": "/ontology/map-entity",
            "ontology_map_relation": "/ontology/map-relation",
            "ontology_create_example": "/ontology/create-example",
            "ontology_classes": "/ontology/classes",
            "ontology_relations": "/ontology/relations",
            # System
            "cache_stats": "/cache/stats",
            "pipeline_status": "/pipeline/status",
        },
        "features": {
            "entity_linking": "Offline-First Entity Linking mit Custom YAML Katalogen",
            "ontology_integration": "Ontologie-Mapping mit Custom YAML Ontologien",
            "ml_relations": "BERT-basierte Relation Extraction für deutsche Texte",
            "air_gapped_support": "Vollständig offline-fähig für Enterprise-Umgebungen",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "autograph.api.server:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info",
    )

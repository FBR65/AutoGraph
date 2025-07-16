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


async def get_pipeline() -> AsyncAutoGraphPipeline:
    """Dependency: Holt die globale Pipeline"""
    global pipeline
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline nicht initialisiert")
    return pipeline


@app.on_event("startup")
async def startup_event():
    """Initialisiert die Pipeline beim Start"""
    global pipeline

    logger.info("Starte AutoGraph API Server...")

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

        logger.info("🤖 AutoGraph ML API Pipeline initialisiert")

    except Exception as e:
        logger.error(f"Fehler beim Initialisieren der Pipeline: {e}")
        raise


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

        return ProcessingResult(
            task_id=task_id,
            entities=entities,
            relationships=relationships,
            metadata=result.metadata,
            processing_time=processing_time,
            cache_used=request.use_cache,
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
            "text_processing": "/process/text",
            "table_processing": "/process/table",
            "batch_processing": "/process/batch",
            "cache_stats": "/cache/stats",
            "pipeline_status": "/pipeline/status",
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

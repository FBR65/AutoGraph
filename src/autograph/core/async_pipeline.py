"""
Asynchrone AutoGraph Pipeline für Performance-optimierte Verarbeitung

Features:
- Parallel Processing von mehreren Dokumenten
- Async NER und Relation Extraction
- Cache-Integration
- Background Tasks
- Streaming für große Dateien
- Connection Pooling
"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, AsyncGenerator
import aiofiles

from ..config import AutoGraphConfig
from ..extractors.base import BaseExtractor
from ..processors.base import BaseProcessor
from ..storage.base import BaseStorage
from ..types import PipelineResult
from .cache import AutoGraphCacheManager


class AsyncAutoGraphPipeline:
    """
    Asynchrone AutoGraph Pipeline mit Performance-Optimierungen
    """

    def __init__(
        self,
        config: AutoGraphConfig,
        extractor: BaseExtractor,
        processors: List[BaseProcessor],
        storage: BaseStorage,
        cache_config: Dict[str, Any] = None,
        max_workers: int = 4,
        batch_size: int = 10,
    ):
        self.config = config
        self.extractor = extractor
        self.processors = processors
        self.storage = storage

        # Performance-Konfiguration
        self.max_workers = max_workers
        self.batch_size = batch_size

        # Thread Pool für CPU-intensive Aufgaben
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # Cache Manager
        self.cache_manager = AutoGraphCacheManager(cache_config or {})

        # Processors mit Cache Manager ausstatten
        for processor in self.processors:
            processor.cache_manager = self.cache_manager

        self.logger = logging.getLogger(__name__)

    async def run_single(
        self,
        data_source: Union[str, Path],
        pipeline_config: Optional[Dict[str, Any]] = None,
        domain: Optional[str] = None,
        use_cache: bool = True,
    ) -> PipelineResult:
        """
        Führt Pipeline für eine einzelne Datenquelle aus
        """
        start_time = time.time()
        source_path = str(data_source)

        self.logger.info(f"Starte Async Pipeline für: {source_path}")

        try:
            # 1. Text-Extraktion (mit Cache)
            extracted_text = None
            if use_cache:
                extracted_text = await self.cache_manager.get_cached_extracted_text(
                    source_path
                )

            if not extracted_text:
                self.logger.debug("Extrahiere Text...")
                # CPU-intensive Extraktion in Thread Pool
                extracted_text = await asyncio.get_event_loop().run_in_executor(
                    self.executor, self.extractor.extract, data_source
                )

                if isinstance(extracted_text, list):
                    # Für TableExtractor - Text aus Datenpunkten extrahieren
                    text_parts = []
                    for item in extracted_text:
                        if isinstance(item, dict) and "content" in item:
                            text_parts.append(item["content"])
                        elif isinstance(item, str):
                            text_parts.append(item)
                    extracted_text = "\n".join(text_parts)

                if use_cache:
                    await self.cache_manager.cache_extracted_text(
                        source_path, extracted_text
                    )
            else:
                self.logger.debug("✅ Text Cache Hit")

            # 2. Parallel Processing der Processors
            all_entities = []
            all_relationships = []

            # Text in Chunks aufteilen für parallele Verarbeitung
            text_chunks = self._split_text_into_chunks(extracted_text)

            # Parallel processing aller Chunks
            chunk_results = await asyncio.gather(
                *[
                    self._process_text_chunk(chunk, domain, use_cache)
                    for chunk in text_chunks
                ]
            )

            # Ergebnisse zusammenführen
            for chunk_entities, chunk_relationships in chunk_results:
                all_entities.extend(chunk_entities)
                all_relationships.extend(chunk_relationships)

            # 3. Duplikate entfernen und Entities konsolidieren
            unique_entities = self._deduplicate_entities(all_entities)
            unique_relationships = self._deduplicate_relationships(all_relationships)

            # 4. Storage (async)
            self.logger.debug("Speichere Ergebnisse...")
            await self._store_results_async(unique_entities, unique_relationships)

            # 5. Ergebnis zusammenstellen
            processing_time = time.time() - start_time
            result = PipelineResult(
                entities=unique_entities,
                relationships=unique_relationships,
                metadata={
                    "source": source_path,
                    "processing_time": processing_time,
                    "chunks_processed": len(text_chunks),
                    "cache_used": use_cache,
                    "domain": domain,
                },
            )

            self.logger.info(
                f"Pipeline abgeschlossen in {processing_time:.2f}s: "
                f"{len(unique_entities)} Entitäten, {len(unique_relationships)} Beziehungen"
            )

            return result

        except Exception as e:
            self.logger.error(f"❌ Pipeline Fehler: {str(e)}")
            raise

    async def run_batch(
        self,
        data_sources: List[Union[str, Path]],
        pipeline_config: Optional[Dict[str, Any]] = None,
        domain: Optional[str] = None,
        use_cache: bool = True,
        max_concurrent: int = 3,
    ) -> List[PipelineResult]:
        """
        Führt Pipeline für mehrere Datenquellen parallel aus
        """
        self.logger.info(
            f"🚀 Starte Batch-Verarbeitung für {len(data_sources)} Quellen"
        )

        # Semaphore für Concurrent-Limiting
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_semaphore(source):
            async with semaphore:
                return await self.run_single(source, pipeline_config, domain, use_cache)

        # Parallel processing aller Quellen
        results = await asyncio.gather(
            *[process_with_semaphore(source) for source in data_sources],
            return_exceptions=True,
        )

        # Fehler vs. erfolgreiche Ergebnisse trennen
        successful_results = []
        failed_sources = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_sources.append((data_sources[i], result))
                self.logger.error(f"❌ Fehler bei {data_sources[i]}: {result}")
            else:
                successful_results.append(result)

        self.logger.info(
            f"✅ Batch-Verarbeitung abgeschlossen: "
            f"{len(successful_results)} erfolgreich, {len(failed_sources)} Fehler"
        )

        return successful_results

    async def run_streaming(
        self,
        data_source: Union[str, Path],
        chunk_size: int = 1024 * 1024,  # 1MB chunks
        domain: Optional[str] = None,
    ) -> AsyncGenerator[PipelineResult, None]:
        """
        Streaming-Verarbeitung für große Dateien
        """
        source_path = Path(data_source)

        if not source_path.exists():
            raise FileNotFoundError(f"Datei nicht gefunden: {source_path}")

        self.logger.info(f"🌊 Starte Streaming-Verarbeitung: {source_path}")

        async with aiofiles.open(source_path, "r", encoding="utf-8") as file:
            chunk_number = 0

            while True:
                # Chunk lesen
                chunk = await file.read(chunk_size)
                if not chunk:
                    break

                chunk_number += 1
                self.logger.debug(
                    f"Verarbeite Chunk {chunk_number} ({len(chunk)} Zeichen)"
                )

                # Chunk verarbeiten
                try:
                    entities, relationships = await self._process_text_chunk(
                        chunk, domain, use_cache=False
                    )

                    # Ergebnis für diesen Chunk yield
                    result = PipelineResult(
                        entities=entities,
                        relationships=relationships,
                        metadata={
                            "source": str(source_path),
                            "chunk_number": chunk_number,
                            "chunk_size": len(chunk),
                            "domain": domain,
                            "streaming": True,
                        },
                    )

                    yield result

                except Exception as e:
                    self.logger.error(f"❌ Fehler in Chunk {chunk_number}: {e}")
                    continue

    async def _process_text_chunk(
        self, text_chunk: str, domain: Optional[str] = None, use_cache: bool = True
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Verarbeitet einen Text-Chunk durch alle Processors
        """
        # Cache-Keys generieren
        ner_cached = None
        relations_cached = None

        if use_cache:
            ner_cached = await self.cache_manager.get_cached_ner_results(text_chunk)
            relations_cached = await self.cache_manager.get_cached_relation_results(
                text_chunk, domain or ""
            )

        entities = []
        relationships = []

        # Processors sequenziell durchlaufen (mit Cache)
        current_data = text_chunk

        for processor in self.processors:
            processor_name = processor.__class__.__name__

            if processor_name == "NERProcessor" and ner_cached:
                self.logger.debug("✅ NER Cache Hit")
                entities = ner_cached
                current_data = {"text": text_chunk, "entities": entities}
            elif processor_name == "RelationExtractor" and relations_cached:
                self.logger.debug("✅ Relations Cache Hit")
                relationships = relations_cached
            else:
                # Processor in Thread Pool ausführen (CPU-intensive)
                if hasattr(processor, "process_async"):
                    # Native async support
                    current_data = await processor.process_async(
                        current_data, domain=domain
                    )
                else:
                    # Sync processor in thread pool
                    current_data = await asyncio.get_event_loop().run_in_executor(
                        self.executor, processor.process, current_data, domain
                    )

                # Cache-Updates
                if processor_name == "NERProcessor" and use_cache:
                    if isinstance(current_data, dict) and "entities" in current_data:
                        await self.cache_manager.cache_ner_results(
                            text_chunk, current_data["entities"]
                        )
                        entities = current_data["entities"]

                elif processor_name == "RelationExtractor" and use_cache:
                    if (
                        isinstance(current_data, dict)
                        and "relationships" in current_data
                    ):
                        await self.cache_manager.cache_relation_results(
                            text_chunk, current_data["relationships"], domain or ""
                        )
                        relationships = current_data["relationships"]

        return entities, relationships

    def _split_text_into_chunks(
        self, text: str, max_chunk_size: int = 5000
    ) -> List[str]:
        """
        Teilt Text in sinnvolle Chunks für parallele Verarbeitung
        """
        if len(text) <= max_chunk_size:
            return [text]

        chunks = []
        sentences = text.split(". ")
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= max_chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _deduplicate_entities(
        self, entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Entfernt doppelte Entitäten basierend auf Text und Label
        """
        seen = set()
        unique_entities = []

        for entity in entities:
            key = (entity.get("text", "").lower(), entity.get("label", ""))
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)

        return unique_entities

    def _deduplicate_relationships(
        self, relationships: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Entfernt doppelte Beziehungen
        """
        seen = set()
        unique_relationships = []

        for rel in relationships:
            key = (
                rel.get("source", "").lower(),
                rel.get("target", "").lower(),
                rel.get("type", ""),
            )
            if key not in seen:
                seen.add(key)
                unique_relationships.append(rel)

        return unique_relationships

    async def _store_results_async(
        self, entities: List[Dict[str, Any]], relationships: List[Dict[str, Any]]
    ) -> None:
        """
        Speichert Ergebnisse asynchron (falls Storage async unterstützt)
        """
        # Daten im erwarteten Format für Storage zusammenstellen
        storage_data = {"entities": entities, "relationships": relationships}

        if hasattr(self.storage, "store_async"):
            await self.storage.store_async(storage_data)
        else:
            # Sync storage in thread pool
            await asyncio.get_event_loop().run_in_executor(
                self.executor, self.storage.store, storage_data
            )

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Cache-Statistiken abrufen
        """
        return await self.cache_manager.get_cache_stats()

    async def clear_caches(self) -> None:
        """
        Alle Caches leeren
        """
        await self.cache_manager.clear_all_caches()

    async def close(self) -> None:
        """
        Pipeline ordnungsgemäß schließen
        """
        self.executor.shutdown(wait=True)
        self.logger.info("🔌 Async Pipeline geschlossen")

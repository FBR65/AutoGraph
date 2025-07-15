"""
Performance Cache Manager für AutoGraph

Implementiert verschiedene Caching-Strategien für bessere Performance:
- LRU Cache für NER-Ergebnisse
- Text-Hash basiertes Caching
- Beziehungs-Cache
- Konfigurierbare Cache-Größen
"""

import hashlib
import json
import logging
import pickle
import time
from functools import lru_cache, wraps
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable
from collections import OrderedDict
import asyncio


class CacheEntry:
    """Cache-Eintrag mit Metadaten"""
    
    def __init__(self, data: Any, ttl: Optional[int] = None):
        self.data = data
        self.created_at = time.time()
        self.ttl = ttl  # Time to live in seconds
        self.hits = 0
        
    def is_expired(self) -> bool:
        """Prüft ob der Cache-Eintrag abgelaufen ist"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl
    
    def touch(self):
        """Markiert Zugriff auf Cache-Eintrag"""
        self.hits += 1


class LRUCache:
    """Thread-safe LRU Cache mit TTL-Unterstützung"""
    
    def __init__(self, max_size: int = 1000, default_ttl: Optional[int] = None):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()
        
    async def get(self, key: str) -> Optional[Any]:
        """Holt Wert aus Cache"""
        async with self._lock:
            if key in self.cache:
                entry = self.cache[key]
                
                if entry.is_expired():
                    del self.cache[key]
                    return None
                
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                entry.touch()
                return entry.data
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Setzt Wert in Cache"""
        async with self._lock:
            # Remove expired entries
            await self._cleanup_expired()
            
            # Remove oldest entries if cache is full
            while len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
            
            # Add new entry
            ttl = ttl or self.default_ttl
            self.cache[key] = CacheEntry(value, ttl)
    
    async def invalidate(self, key: str) -> bool:
        """Entfernt Eintrag aus Cache"""
        async with self._lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    async def clear(self) -> None:
        """Leert kompletten Cache"""
        async with self._lock:
            self.cache.clear()
    
    async def _cleanup_expired(self) -> None:
        """Entfernt abgelaufene Einträge"""
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired()
        ]
        for key in expired_keys:
            del self.cache[key]
    
    async def stats(self) -> Dict[str, Any]:
        """Cache-Statistiken"""
        async with self._lock:
            await self._cleanup_expired()
            total_hits = sum(entry.hits for entry in self.cache.values())
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "total_hits": total_hits,
                "hit_rate": total_hits / max(1, len(self.cache))
            }


class AutoGraphCacheManager:
    """Zentraler Cache Manager für AutoGraph"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Cache-Konfiguration
        self.ner_cache_size = self.config.get("ner_cache_size", 1000)
        self.relation_cache_size = self.config.get("relation_cache_size", 500)
        self.text_cache_size = self.config.get("text_cache_size", 200)
        self.default_ttl = self.config.get("cache_ttl", 3600)  # 1 Stunde
        
        # Cache-Instanzen
        self.ner_cache = LRUCache(self.ner_cache_size, self.default_ttl)
        self.relation_cache = LRUCache(self.relation_cache_size, self.default_ttl)
        self.text_cache = LRUCache(self.text_cache_size, self.default_ttl)
        
        # Datebasiertes Caching (optional)
        self.enable_disk_cache = self.config.get("enable_disk_cache", False)
        self.cache_dir = Path(self.config.get("cache_dir", ".autograph_cache"))
        
        if self.enable_disk_cache:
            self.cache_dir.mkdir(exist_ok=True)
    
    def _generate_cache_key(self, text: str, context: str = "") -> str:
        """Generiert Cache-Schlüssel basierend auf Text-Hash"""
        content = f"{text}:{context}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    async def cache_ner_results(self, text: str, entities: List[Dict[str, Any]], 
                               model_name: str = "") -> None:
        """Cacht NER-Ergebnisse"""
        cache_key = self._generate_cache_key(text, f"ner:{model_name}")
        await self.ner_cache.set(cache_key, entities)
        self.logger.debug(f"NER Ergebnisse gecacht: {cache_key[:8]}...")
    
    async def get_cached_ner_results(self, text: str, 
                                    model_name: str = "") -> Optional[List[Dict[str, Any]]]:
        """Holt gecachte NER-Ergebnisse"""
        cache_key = self._generate_cache_key(text, f"ner:{model_name}")
        result = await self.ner_cache.get(cache_key)
        if result:
            self.logger.debug(f"NER Cache Hit: {cache_key[:8]}...")
        return result
    
    async def cache_relation_results(self, text: str, relationships: List[Dict[str, Any]], 
                                    domain: str = "") -> None:
        """Cacht Beziehungs-Ergebnisse"""
        cache_key = self._generate_cache_key(text, f"relations:{domain}")
        await self.relation_cache.set(cache_key, relationships)
        self.logger.debug(f"Beziehungen gecacht: {cache_key[:8]}...")
    
    async def get_cached_relation_results(self, text: str, 
                                         domain: str = "") -> Optional[List[Dict[str, Any]]]:
        """Holt gecachte Beziehungs-Ergebnisse"""
        cache_key = self._generate_cache_key(text, f"relations:{domain}")
        result = await self.relation_cache.get(cache_key)
        if result:
            self.logger.debug(f"Relations Cache Hit: {cache_key[:8]}...")
        return result
    
    async def cache_extracted_text(self, source_path: str, extracted_text: str) -> None:
        """Cacht extrahierten Text"""
        # Verwende Dateipfad + Modifikationszeit als Cache-Key
        try:
            stat = Path(source_path).stat()
            cache_key = f"text:{source_path}:{stat.st_mtime}"
            await self.text_cache.set(cache_key, extracted_text)
            self.logger.debug(f"Text gecacht: {source_path}")
        except Exception as e:
            self.logger.warning(f"Fehler beim Text-Caching: {e}")
    
    async def get_cached_extracted_text(self, source_path: str) -> Optional[str]:
        """Holt gecachten extrahierten Text"""
        try:
            stat = Path(source_path).stat()
            cache_key = f"text:{source_path}:{stat.st_mtime}"
            result = await self.text_cache.get(cache_key)
            if result:
                self.logger.debug(f"Text Cache Hit: {source_path}")
            return result
        except Exception as e:
            self.logger.warning(f"Fehler beim Text-Cache Zugriff: {e}")
            return None
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Gesamte Cache-Statistiken"""
        ner_stats = await self.ner_cache.stats()
        relation_stats = await self.relation_cache.stats()
        text_stats = await self.text_cache.stats()
        
        return {
            "ner_cache": ner_stats,
            "relation_cache": relation_stats,
            "text_cache": text_stats,
            "total_entries": (
                ner_stats["size"] + 
                relation_stats["size"] + 
                text_stats["size"]
            )
        }
    
    async def clear_all_caches(self) -> None:
        """Leert alle Caches"""
        await self.ner_cache.clear()
        await self.relation_cache.clear()
        await self.text_cache.clear()
        self.logger.info("Alle Caches geleert")
    
    # Disk Cache Methoden (optional)
    def _get_disk_cache_path(self, cache_key: str, cache_type: str) -> Path:
        """Generiert Pfad für Disk-Cache"""
        return self.cache_dir / cache_type / f"{cache_key}.pkl"
    
    async def save_to_disk_cache(self, cache_key: str, data: Any, cache_type: str) -> None:
        """Speichert Daten im Disk-Cache"""
        if not self.enable_disk_cache:
            return
        
        try:
            cache_path = self._get_disk_cache_path(cache_key, cache_type)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
                
            self.logger.debug(f"Disk Cache gespeichert: {cache_path}")
        except Exception as e:
            self.logger.warning(f"Disk Cache Fehler: {e}")
    
    async def load_from_disk_cache(self, cache_key: str, cache_type: str) -> Optional[Any]:
        """Lädt Daten aus Disk-Cache"""
        if not self.enable_disk_cache:
            return None
        
        try:
            cache_path = self._get_disk_cache_path(cache_key, cache_type)
            if cache_path.exists():
                with open(cache_path, 'rb') as f:
                    data = pickle.load(f)
                self.logger.debug(f"Disk Cache geladen: {cache_path}")
                return data
        except Exception as e:
            self.logger.warning(f"Disk Cache Lesefehler: {e}")
        
        return None


def cache_async_method(cache_type: str = "general", ttl: Optional[int] = None):
    """Decorator für Async-Methoden mit automatischem Caching"""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Cache Manager aus self holen
            cache_manager = getattr(self, 'cache_manager', None)
            if not cache_manager:
                return await func(self, *args, **kwargs)
            
            # Cache-Key generieren
            cache_key = hashlib.md5(
                f"{func.__name__}:{str(args)}:{str(kwargs)}".encode()
            ).hexdigest()
            
            # Cache-Zugriff basierend auf Typ
            if cache_type == "ner":
                result = await cache_manager.ner_cache.get(cache_key)
            elif cache_type == "relations":
                result = await cache_manager.relation_cache.get(cache_key)
            else:
                result = await cache_manager.text_cache.get(cache_key)
            
            if result is not None:
                return result
            
            # Funktion ausführen und Ergebnis cachen
            result = await func(self, *args, **kwargs)
            
            if cache_type == "ner":
                await cache_manager.ner_cache.set(cache_key, result, ttl)
            elif cache_type == "relations":
                await cache_manager.relation_cache.set(cache_key, result, ttl)
            else:
                await cache_manager.text_cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator

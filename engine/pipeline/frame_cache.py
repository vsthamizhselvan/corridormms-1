"""CorridorKey 2.0 Desktop — Intelligent Multi-Tier LRU Frame Cache.

Provides bounded, memory-aware caching for decoded video frames, AI alpha mattes,
compositing preview plates, and timeline thumbnails with automatic LRU eviction
and granular edit invalidation.
"""

from __future__ import annotations

import collections
import enum
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


class CacheTier(str, enum.Enum):
    DECODED = "decoded"
    AI_MATTE = "ai_matte"
    COMPOSITE = "composite"
    THUMBNAIL = "thumbnail"


@dataclass
class CacheEntry:
    key: str
    data: np.ndarray
    tier: CacheTier
    size_bytes: int
    created_at: float
    last_accessed: float
    access_count: int = 1
    media_id: Optional[str] = None
    frame_index: Optional[int] = None
    vfx_hash: Optional[str] = None


@dataclass
class CacheStats:
    total_entries: int
    used_memory_mb: float
    max_memory_mb: float
    hits: int
    misses: int
    hit_rate: float
    evictions: int
    tier_counts: Dict[str, int] = field(default_factory=dict)
    tier_memory_mb: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_entries": self.total_entries,
            "used_memory_mb": round(self.used_memory_mb, 2),
            "max_memory_mb": round(self.max_memory_mb, 2),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_pct": round(self.hit_rate * 100, 1),
            "evictions": self.evictions,
            "tier_counts": self.tier_counts,
            "tier_memory_mb": {k: round(v, 2) for k, v in self.tier_memory_mb.items()},
        }


class IntelligentFrameCache:
    """Thread-safe multi-tier LRU cache with strict memory constraints."""

    _instance: Optional["IntelligentFrameCache"] = None
    _lock = threading.RLock()

    @classmethod
    def get_instance(cls, max_memory_mb: int = 1024) -> "IntelligentFrameCache":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(max_memory_mb=max_memory_mb)
            return cls._instance

    def __init__(self, max_memory_mb: int = 1024):
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self._current_memory_bytes = 0

        # OrderedDict maintains insertion/access order for LRU eviction
        self._cache: collections.OrderedDict[str, CacheEntry] = collections.OrderedDict()
        self._lock = threading.RLock()

        # Telemetry
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def set_max_memory(self, max_mb: int) -> None:
        """Dynamically reconfigures the cache memory ceiling and prunes if necessary."""
        with self._lock:
            self.max_memory_bytes = max(64, max_mb) * 1024 * 1024
            self._enforce_limit()

    def _calculate_size(self, data: np.ndarray) -> int:
        if isinstance(data, np.ndarray):
            return data.nbytes
        return sys.getsizeof(data)

    def _enforce_limit(self) -> None:
        """Evicts oldest entries until cache memory fits within max_memory_bytes."""
        while self._current_memory_bytes > self.max_memory_bytes and len(self._cache) > 0:
            # Pop least recently used item (first in OrderedDict)
            _, old_entry = self._cache.popitem(last=False)
            self._current_memory_bytes -= old_entry.size_bytes
            self._evictions += 1

    def _get(self, key: str) -> Optional[np.ndarray]:
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                entry.last_accessed = time.time()
                entry.access_count += 1
                # Move to end (most recently used)
                self._cache.move_to_end(key, last=True)
                self._hits += 1
                return entry.data
            self._misses += 1
            return None

    def _put(
        self,
        key: str,
        data: np.ndarray,
        tier: CacheTier,
        media_id: Optional[str] = None,
        frame_index: Optional[int] = None,
        vfx_hash: Optional[str] = None,
    ) -> None:
        with self._lock:
            size = self._calculate_size(data)
            # If a single item exceeds max memory, do not store
            if size > self.max_memory_bytes:
                return

            now = time.time()
            if key in self._cache:
                old_entry = self._cache.pop(key)
                self._current_memory_bytes -= old_entry.size_bytes

            entry = CacheEntry(
                key=key,
                data=data,
                tier=tier,
                size_bytes=size,
                created_at=now,
                last_accessed=now,
                media_id=media_id,
                frame_index=frame_index,
                vfx_hash=vfx_hash,
            )
            self._cache[key] = entry
            self._current_memory_bytes += size
            self._enforce_limit()

    # -------------------------------------------------------------------------
    # Tier 1: Decoded Video Frames
    # -------------------------------------------------------------------------
    def get_decoded_frame(self, media_id: str, frame_idx: int) -> Optional[np.ndarray]:
        key = f"dec_{media_id}_{frame_idx}"
        return self._get(key)

    def put_decoded_frame(self, media_id: str, frame_idx: int, frame: np.ndarray) -> None:
        key = f"dec_{media_id}_{frame_idx}"
        self._put(key, frame, CacheTier.DECODED, media_id=media_id, frame_index=frame_idx)

    # -------------------------------------------------------------------------
    # Tier 2: AI Neural Alpha Mattes
    # -------------------------------------------------------------------------
    def get_matte(self, media_id: str, frame_idx: int, params_hash: str = "default") -> Optional[np.ndarray]:
        key = f"matte_{media_id}_{frame_idx}_{params_hash}"
        return self._get(key)

    def put_matte(self, media_id: str, frame_idx: int, params_hash: str, matte: np.ndarray) -> None:
        key = f"matte_{media_id}_{frame_idx}_{params_hash}"
        self._put(key, matte, CacheTier.AI_MATTE, media_id=media_id, frame_index=frame_idx)

    # -------------------------------------------------------------------------
    # Tier 3: Composited Previews
    # -------------------------------------------------------------------------
    def get_composite(self, frame_idx: int, vfx_hash: str) -> Optional[np.ndarray]:
        key = f"comp_{frame_idx}_{vfx_hash}"
        return self._get(key)

    def put_composite(self, frame_idx: int, vfx_hash: str, comp: np.ndarray) -> None:
        key = f"comp_{frame_idx}_{vfx_hash}"
        self._put(key, comp, CacheTier.COMPOSITE, frame_index=frame_idx, vfx_hash=vfx_hash)

    # -------------------------------------------------------------------------
    # Tier 4: Thumbnails
    # -------------------------------------------------------------------------
    def get_thumbnail(self, media_id: str, frame_idx: int = 0) -> Optional[np.ndarray]:
        key = f"thumb_{media_id}_{frame_idx}"
        return self._get(key)

    def put_thumbnail(self, media_id: str, frame_idx: int, thumb: np.ndarray) -> None:
        key = f"thumb_{media_id}_{frame_idx}"
        self._put(key, thumb, CacheTier.THUMBNAIL, media_id=media_id, frame_index=frame_idx)

    # -------------------------------------------------------------------------
    # Invalidation Triggers
    # -------------------------------------------------------------------------
    def invalidate_media(self, media_id: str) -> int:
        """Removes all cached decoded frames, mattes, and thumbnails for a specific media item."""
        with self._lock:
            keys_to_remove = [k for k, v in self._cache.items() if v.media_id == media_id]
            for k in keys_to_remove:
                entry = self._cache.pop(k)
                self._current_memory_bytes -= entry.size_bytes
            return len(keys_to_remove)

    def invalidate_vfx(self) -> int:
        """Invalidates all rendered composite preview frames when VFX parameters change."""
        with self._lock:
            keys_to_remove = [k for k, v in self._cache.items() if v.tier == CacheTier.COMPOSITE]
            for k in keys_to_remove:
                entry = self._cache.pop(k)
                self._current_memory_bytes -= entry.size_bytes
            return len(keys_to_remove)

    def clear(self) -> None:
        """Empties all tiers and resets memory counters."""
        with self._lock:
            self._cache.clear()
            self._current_memory_bytes = 0

    def get_stats(self) -> CacheStats:
        """Returns snapshot telemetry metrics for monitoring and performance panels."""
        with self._lock:
            tier_counts: Dict[str, int] = collections.defaultdict(int)
            tier_memory: Dict[str, float] = collections.defaultdict(float)

            for entry in self._cache.values():
                t = entry.tier.value
                tier_counts[t] += 1
                tier_memory[t] += entry.size_bytes / (1024 * 1024)

            total_reqs = self._hits + self._misses
            hit_rate = (self._hits / total_reqs) if total_reqs > 0 else 0.0

            return CacheStats(
                total_entries=len(self._cache),
                used_memory_mb=self._current_memory_bytes / (1024 * 1024),
                max_memory_mb=self.max_memory_bytes / (1024 * 1024),
                hits=self._hits,
                misses=self._misses,
                hit_rate=hit_rate,
                evictions=self._evictions,
                tier_counts=dict(tier_counts),
                tier_memory_mb=dict(tier_memory),
            )

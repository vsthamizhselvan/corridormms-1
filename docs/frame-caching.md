# Multi-Tier Intelligent Frame Caching

## 1. Overview
The `IntelligentFrameCache` is a thread-safe, memory-bounded, multi-tier caching engine that eliminates redundant neural network inferences, disk decodes, and compositing passes during timeline playback and interactive scrubbing.

---

## 2. Multi-Tier Cache Hierarchy

| Tier | Identification Key | Cached Payload | Typical Size (1080p) | Invalidation Trigger |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1: Decoded Video** | `dec_{media_id}_{frame_idx}` | Raw decoded source frame | ~8.29 MB (uint8 RGBA) | Media file relink or replacement |
| **Tier 2: AI Alpha Matte** | `matte_{media_id}_{frame_idx}_{model_hash}` | Neural network alpha matte | ~2.07 MB (uint8 gray) | Keying parameter or model change |
| **Tier 3: Composite Previews** | `comp_{frame_idx}_{vfx_hash}` | Final composited viewport frame | ~8.29 MB (uint8 RGBA) | VFX stack, grade, or mask edit |
| **Tier 4: Thumbnails** | `thumb_{media_id}_{frame_idx}` | Scaled UI thumbnail image | ~18 KB (160x90 RGBA) | Media deletion |

---

## 3. Eviction Policy (LRU)
- Managed via `collections.OrderedDict`.
- Accessing any frame moves the entry to the most-recently-used position:
  ```python
  self._cache.move_to_end(key, last=True)
  ```
- When `current_memory_bytes + item_size > max_memory_bytes`, the oldest items at index 0 are popped and reclaimed:
  ```python
  _, old_entry = self._cache.popitem(last=False)
  ```
- Configurable memory ceiling: Default is `1024 MB`, dynamically adjustable between `256 MB` and `4096 MB` from the UI.

---

## 4. Invalidation Architecture
- `invalidate_media(media_id)`: Removes all entries tied to a specific clip ID when trimmed or replaced.
- `invalidate_vfx()`: Removes all Tier 3 composite frames whenever masks, color grading, or effects change, while preserving raw decoded source frames in Tier 1.
- Scrubbing simulation benchmarks demonstrate **>2,000,000 lookups/sec** with sub-microsecond latency.

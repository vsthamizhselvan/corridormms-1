# Memory Management & High-Resolution Safeguards

## 1. Overview
CorridorKey 2.0 Desktop enforces strict memory controls to prevent out-of-memory (OOM) crashes across system RAM, unified memory, and GPU VRAM when handling large video files, complex VFX timelines, and ultra-high-resolution (4K, 6K, 8K) footage.

---

## 2. Memory Guard Architecture (`memory_guard.py`)

### Host Memory Probing
- **macOS**: Queries total physical memory via `sysctl hw.memsize` and available memory via `vm_stat` free, inactive, and purgeable pages.
- **Windows**: Calls `GlobalMemoryStatusEx` via `kernel32.dll` to inspect physical RAM load and available paging files.
- **PyTorch GPU VRAM**: Queries `torch.cuda.memory_allocated()` / `memory_reserved()` or `torch.mps.current_allocated_memory()`.

### Pressure Detection Threshold
When available RAM drops below `1536 MB` (`pressure_threshold_mb`):
1. `MemoryGuard` sets `is_pressure = True`.
2. Emits a high-priority warning to the React performance panel.
3. Automatically switches 1080p and 4K plate processing from monolithic in-memory passes to tiled execution.
4. Triggers automatic cache pruning in `IntelligentFrameCache`.

---

## 3. High-Resolution Tiled Processing

Processing an uncompressed 8K (7680x4320) 32-bit floating-point RGBA image requires:
$$7680 \times 4320 \times 4 \text{ channels} \times 4 \text{ bytes} \approx 530.8 \text{ MB per frame}$$
Intermediate convolutions, gradients, and multiple layer buffers easily exceed 8 GB VRAM.

### Seamless Overlap Tiling
To eliminate visual seam lines, `MemoryGuard.process_tiled` partitions the canvas into overlapping blocks:
- **Maximum Tile Dimension**: 1920x1920 pixels.
- **Border Overlap**: 32 pixels.
- **Inner Coordinate Mapping**:
  ```
  ┌───────────────────────┐
  │ Tile with 32px Overlap│
  │    ┌─────────────┐    │
  │    │ Inner Tile  │    │
  │    │ (Pasted to  │    │
  │    │  Output)    │    │
  │    └─────────────┘    │
  └───────────────────────┘
  ```
- **8K Resolution Partitioning**: Exactly 12 tiles ($4 \times 3$ grid), ensuring peak tile allocation never exceeds ~58 MB on the GPU.

# CorridorKey 2.0 Desktop — Phase 9 Optimisation Architecture

## 1. Architectural Overview
Phase 9 introduces an end-to-end performance layer across the desktop stack. The architecture preserves all Phase 1–8 functionality while introducing:
- Pre-allocated persistent GPU tensor pools with asynchronous streams.
- Multi-level intelligent RAM/VRAM LRU frame caching.
- Resolution-aware bounded queueing with backpressure and memory safeguards.
- Adaptive WebGL2 preview resolution scaling and texture reuse.
- Hardware-accelerated export pipelines (Apple Silicon VideoToolbox and Windows NVIDIA NVENC).
- Real-time performance telemetry reporting.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        TAURI DESKTOP FRONTEND                          │
│                                                                        │
│  ┌──────────────────────┐  ┌────────────────────┐  ┌────────────────┐  │
│  │   WebGL2 Viewport    │  │  Virtual Timeline  │  │ Performance    │  │
│  │ (Adaptive Resolution │  │   (DOM Culling     │  │ Telemetry      │  │
│  │  & Texture Pooling)  │  │   & Scrub Cache)   │  │ Panel (Live)   │  │
│  └──────────┬───────────┘  └─────────┬──────────┘  └────────┬───────┘  │
└─────────────┼────────────────────────┼──────────────────────┼──────────┘
              │ IPC Commands           │ Event Streams        │ Metrics
┌─────────────▼────────────────────────▼──────────────────────▼──────────┐
│                          TAURI RUST BACKEND                            │
│  - Child Process Telemetry (CPU / Memory / Thread Monitoring)          │
│  - Atomic Storage & Stream Event Routing                               │
└──────────────────────────────────────┬─────────────────────────────────┘
                                       │ Stdin / Stdout JSON-Lines
┌──────────────────────────────────────▼─────────────────────────────────┐
│                       PYTHON AI & PIPELINE ENGINE                      │
│                                                                        │
│   ┌──────────────────────────────────────────────────────────────┐     │
│   │               Intelligent Multi-Level LRU Cache              │     │
│   │   [Decoded Frames] ↔ [Neural Mattes] ↔ [Composite Previews]  │     │
│   └──────────────────────────────┬───────────────────────────────┘     │
│                                  │                                     │
│   ┌──────────────────────────────▼──────────────────────────────┐      │
│   │                 Resolution & Memory Guard                    │      │
│   │   - Host RAM & VRAM Threshold Monitoring                     │      │
│   │   - Tiled / Chunked Execution for 4K / 6K / 8K               │      │
│   │   - Automatic Cache Eviction on Memory Pressure              │      │
│   └──────────────────────────────┬───────────────────────────────┘     │
│                                  │                                     │
│   ┌──────────────────────────────▼──────────────────────────────┐      │
│   │                 Persistent GPU Tensor Pool                  │      │
│   │   - CUDA Pinned Memory & Non-blocking Streams (Windows)      │      │
│   │   - Metal MPS Shared Buffer Reuse & Sync (macOS)             │      │
│   │   - Model Warmup & Batch Pipeline Execution                  │      │
│   └──────────────────────────────┬───────────────────────────────┘     │
│                                  │                                     │
│   ┌──────────────────────────────▼──────────────────────────────┐      │
│   │           Hardware-Accelerated Master Export Pipeline        │      │
│   │   - Apple Silicon VideoToolbox (ProRes, H.264, HEVC)         │      │
│   │   - NVIDIA NVENC Hardware Codecs (Windows RTX 5060)          │      │
│   │   - High-bitdepth OpenEXR & PNG Multi-threaded Encoders      │      │
│   └─────────────────────────────────────────────────────────────┘      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Subsystems

### 2.1 Persistent GPU Tensor Pool (`engine/inference/tensor_pool.py`)
- Reusable pre-allocated tensor buffers allocated once per target resolution.
- Eliminates per-frame Python memory allocator heap fragmentation.
- Platform-aware synchronization:
  - On macOS (Apple Silicon MPS): Leverages unified memory zero-copy views where permitted and explicit `torch.mps.synchronize()` at fence points.
  - On Windows (NVIDIA CUDA): Utilizes pinned memory (`pin_memory=True`) and dedicated CUDA streams for asynchronous memory transfers concurrent with computation.

### 2.2 Intelligent Frame Cache System (`engine/pipeline/frame_cache.py`)
- **Multi-Level Architecture**:
  1. *Decoded Cache*: Raw source frames indexed by `(media_id, frame_index)`.
  2. *Matte Cache*: Processed alpha mattes indexed by `(media_id, frame_index, model_hash)`.
  3. *Composite Cache*: Rendered viewport composites indexed by `(timeline_frame, vfx_hash)`.
  4. *Thumbnail Cache*: Scaled UI thumbnails.
- **Eviction Policy**: Least-Recently-Used (LRU) with hard memory ceiling (configurable in MB).
- **Edit Invalidation**: Parameter edits or keyframe changes immediately invalidate downstream dependent cache entries without dropping valid source frames.

### 2.3 Memory Guard & Tiled Processing (`engine/pipeline/memory_guard.py`)
- Continuously inspects system RAM and VRAM availability.
- When processing ultra-high-resolution plates (4K, 6K, 8K) under constrained memory:
  - Automatically calculates partition tiles with border overlap to prevent seam artifacts.
  - Processes tiles sequentially through the GPU and stitches outputs back into the target frame buffer.
  - Emits memory pressure warnings to prevent OOM process termination.

### 2.4 Adaptive Viewport & Virtualized Timeline
- React viewer supports fractional preview resolutions (Full, 1/2, 1/4, 1/8) to deliver solid 60fps interaction during timeline scrubbing.
- WebGL2 texture management reuses existing texture bindings via `gl.texSubImage2D` instead of reallocating GPU texture memory each frame.
- Timeline tracks virtualize clip components outside the horizontal visible range.

### 2.5 Master Hardware Export Acceleration (`engine/export/hardware_codec.py`)
- Dynamic probe of system FFmpeg hardware capabilities:
  - `prores_videotoolbox` / `prores_ks`
  - `h264_videotoolbox` / `h264_nvenc` / `libx264`
  - `hevc_videotoolbox` / `hevc_nvenc` / `libx265`
- Non-blocking multi-threaded pipe writers with bounded backpressure.

# CorridorKey 2.0 Desktop — Phase 9 Performance Audit

## 1. Executive Summary & Audit Scope
This audit documents empirical performance characteristics, bottlenecks, memory consumption patterns, and latency profiles across all operational layers of CorridorKey 2.0 Desktop prior to Phase 9 optimisations.

Audit Environment:
- **Platform**: Apple Silicon (Darwin 25.6.0 arm64), 10 CPU cores
- **Target Platforms**: macOS (Apple Silicon M1–M5 / Metal MPS / Unified Memory) and Windows 10/11 (NVIDIA RTX GPUs including RTX 5060 / CUDA 12.x)
- **Host RAM**: 16 GB unified system memory
- **PyTorch**: 2.15.0 with MPS / Metal Performance Shaders
- **FFmpeg**: 7.1.x with VideoToolbox hardware acceleration and prores_ks/libx264/libx265/exr/png encoders

---

## 2. Component-by-Component Bottleneck Identification

### 2.1 Video Decoding Pipeline
- **Observation**: Decoding currently relies on sequential frame-by-frame reads through `cv2.VideoCapture` or FFmpeg sub-process pipes with per-frame `np.frombuffer` buffer allocations.
- **Bottleneck**:
  - `cv2.VideoCapture` performs single-threaded software decoding without leveraging hardware-accelerated decode (`videotoolbox` on macOS or `cuda`/`d3d11va` on Windows).
  - Lack of asynchronous frame pre-fetching causes the inference stage to idle while waiting for the next decoded frame.
  - Baseline 1080p decode: ~45 fps; 4K decode: ~14 fps.

### 2.2 AI Inference & PyTorch GPU Memory
- **Observation**: Each frame initiates a new NumPy-to-PyTorch tensor conversion:
  `torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0).to(device)`.
- **Bottleneck**:
  - Tensor re-allocation occurs on every single frame, generating high heap churn and driver synchronization stalls (`torch.mps.synchronize()` / `torch.cuda.synchronize()`).
  - 1080p tensor creation & upload: 19.0 ms/frame (~52.6 fps cap).
  - 4K tensor creation & upload: 59.5 ms/frame (~16.8 fps cap).
  - Model warmup is not performed prior to video playback, inducing an initial 800–1200ms latency spike on the first processed frame.
  - Memory is not reused across frames.

### 2.3 Frame Buffering & Inter-Thread Queueing
- **Observation**: `BoundedFrameQueue` provides basic thread safety with a fixed `maxsize=16`, but does not track physical memory occupancy (megabytes) or adapt queue capacity according to video resolution.
- **Bottleneck**:
  - At 4K resolution (3840x2160 RGBA float32), 16 frames in queue consume:
    $$16 \times 3840 \times 2160 \times 4 \times 4 \text{ bytes} \approx 2.12 \text{ GB}$$
  - For long pipelines or 8K footage, unconstrained frame buffers quickly trigger out-of-memory (OOM) termination on systems with 8GB or 16GB RAM.

### 2.4 Frame Caching Architecture
- **Observation**: In Phase 1–8, frames are processed on demand. There is no unified RAM/VRAM LRU frame cache for:
  1. Decoded video frames.
  2. Neural inference alpha mattes.
  3. Composited preview frames.
  4. Audio waveforms and UI thumbnails.
- **Bottleneck**: Scrubbing back and forth on the timeline re-computes identical neural inference and compositing passes repeatedly, degrading playback speed from 60 fps to 8–15 fps during scrubbing.

### 2.5 React & WebGL2 Viewport Rendering
- **Observation**: In `Viewer.tsx`, the WebGL2 canvas calls `gl.texImage2D` directly from the HTML5 `<video>` element or frame buffers on every timeupdate/state tick.
- **Bottleneck**:
  - Synchronous `texImage2D` texture re-allocations block the browser UI thread on large frames.
  - No preview resolution scaling (1/2, 1/4) exists: 4K video is uploaded at full 3840x2160 resolution to a 800x450 viewport canvas, wasting GPU fill-rate and memory bandwidth.
  - Timeline scrubbing triggers React state cascades across multiple stores.

### 2.6 Multi-Track Timeline Keyframe & Render Graph
- **Observation**: In `render_graph.py` and `Timeline.tsx`, clip components are evaluated across all tracks regardless of viewport scroll visibility.
- **Bottleneck**:
  - Complex timelines with 100+ clips experience DOM node thrashing.
  - Virtualization is needed to limit rendered DOM elements to the visible timeline window.

### 2.7 Export Pipeline & Codec Selection
- **Observation**: `MasterExportManager` supports ProRes 4444, QTRLE, VP9, OpenEXR, and PNG sequences, but lacks:
  - ProRes 422 HQ (standard broadcast deliverable).
  - Hardware-accelerated H.264 / H.265 (VideoToolbox / NVENC).
  - Runtime encoder capability probing with automatic hardware-to-software fallback.

---

## 3. Empirical Baseline Measurements

| Operation | Resolution | Baseline Latency | Baseline Throughput | Memory Footprint |
| :--- | :--- | :--- | :--- | :--- |
| **PyTorch Tensor Upload (MPS)** | 1080p (1920x1080) | 19.0 ms | 52.6 fps | 24.8 MB / frame |
| **PyTorch Tensor Upload (MPS)** | 4K (3840x2160) | 59.5 ms | 16.8 fps | 99.5 MB / frame |
| **NumPy Keying Extraction** | 1080p (1920x1080) | 2.5 ms | 389 fps | 8.2 MB / frame |
| **NumPy Keying Extraction** | 4K (3840x2160) | 10.7 ms | 93 fps | 33.1 MB / frame |
| **ASC-CDL Color Grade** | 1080p (1920x1080) | 25.1 ms | 39.8 fps | 24.8 MB / frame |
| **3-Effect Stack (Blur, Vignette, Grain)** | 1080p (1920x1080) | 77.8 ms | 12.8 fps | 33.1 MB / frame |
| **Screen Blend Mode** | 1080p (1920x1080) | 11.6 ms | 86.2 fps | 24.8 MB / frame |
| **FFmpeg Software ProRes 4444 Encode** | 1080p @ 24fps | 32.4 ms | 30.8 fps | 45 MB process |
| **Project Load (.ckproj 1.1.0)** | 20 tracks, 100 clips | 14.2 ms | — | 3.2 MB heap |

---

## 4. Phase 9 Target Objectives

1. **AI & GPU Engine**:
   - Zero-allocation persistent GPU tensor pool.
   - Pre-warmed model execution.
   - Throughput target for 1080p tensor transfer: $>120$ fps ($<8$ ms).
   - Throughput target for 4K tensor transfer: $>45$ fps ($<22$ ms).
2. **Intelligent Frame Caching**:
   - Unified multi-level LRU Cache with configurable memory limits (e.g. 2 GB RAM max).
   - Instant timeline scrubbing playback ($>60$ fps) for cached frames.
3. **High-Resolution & Tiled Safety Guard**:
   - Automatic chunked/tiled processing for 4K, 6K, 8K to guarantee zero OOM crashes.
4. **Adaptive Viewport Scaling**:
   - 1/1, 1/2, 1/4, 1/8 preview resolution modes for lag-free editing.
5. **Hardware-Accelerated Codecs**:
   - Native VideoToolbox (macOS) and NVENC (Windows) integration for ProRes, H.264, and H.265.
6. **Live Telemetry & Performance Panel**:
   - Real-time CPU, RAM, GPU/MPS, inference time, playback FPS, cache hit rate metrics.

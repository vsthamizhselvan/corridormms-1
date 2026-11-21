# CorridorKey 2.0 Desktop — Cross-Platform Compatibility Matrix

## 1. Hardware & Acceleration Compatibility Matrix

| Platform | Hardware Target | Backend Driver | PyTorch Target | Precision | Native Status | CorridorKey Desktop Support Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Windows 10/11** | **NVIDIA RTX 5060 (Blackwell)** | CUDA 12.8+ / Driver 570+ | `torch>=2.9.1+cu128` | `bfloat16` (Tensor Cores) | **Tier 1 (Official)** | **Full Native Acceleration** (Auto Hann window, full VRAM profiling) |
| **Windows 10/11** | **NVIDIA RTX 40-series (Ada)** | CUDA 12.4+ / Driver 550+ | `torch>=2.4.0+cu124` | `bfloat16` (Tensor Cores) | **Tier 1 (Official)** | **Full Native Acceleration** (80/40 window on 16GB+, 24/12 on 8GB/12GB) |
| **Windows 10/11** | **NVIDIA RTX 30-series (Ampere)**| CUDA 12.1+ / Driver 530+ | `torch>=2.2.0+cu121` | `bfloat16` (Tensor Cores) | **Tier 1 (Official)** | **Full Native Acceleration** (Supported natively by upstream model) |
| **Windows 10/11** | **Intel / AMD CPU** | Host x86_64 AVX2 / AVX-512 | `torch>=2.4.0+cpu` | `float32` / `bfloat16` (AVX) | **Unsupported Upstream** | **Desktop CPU Bridge** (Low VRAM staged processing, chunking) |
| **macOS (Sonoma+)**| **Apple Silicon M3, M4, M5** | Apple Metal / MPS | `torch>=2.4.0` (ARM64) | `float16` / `float32` | **Unsupported Upstream** | **Desktop Apple Silicon Bridge** (MPS accelerated where kernels exist, CPU fallback) |
| **macOS (Sonoma+)**| **Apple Silicon M1, M2** | Apple Metal / MPS | `torch>=2.4.0` (ARM64) | `float16` / `float32` | **Unsupported Upstream** | **Desktop Apple Silicon Bridge** (MPS accelerated with unified memory profiling) |
| **macOS (Sonoma+)**| **Apple Silicon (CPU Mode)** | Host ARM64 NEON | `torch>=2.4.0` (ARM64) | `float32` | **Unsupported Upstream** | **Full CPU Mode Fallback** (Guaranteed operation across all chips) |

---

## 2. Upstream Constraints vs. Desktop Engine Abstraction

The upstream `vendor/CorridorKey2.0` repository was developed primarily as an internal workstation CLI tool targeting NVIDIA CUDA GPUs. When integrating it into a cross-platform desktop application, our desktop engine addresses several architectural bottlenecks:

### Upstream Hardcoded Assumptions:
1. **Device Assumption:**
   - In `infer.py`:
     ```python
     if not torch.cuda.is_available():
         raise RuntimeError("CorridorKey v2 runtime requires a CUDA GPU.")
     model = load_model(paths, device="cuda")
     ```
   - In `corridorkey/runtime.py`:
     ```python
     model.foundations.cuda()
     model.stage1.cuda()
     model.stage2.cuda()
     ```
2. **Precision & Autocast:**
   - In `corridorkey/runtime.py`:
     ```python
     with torch.autocast("cuda", dtype=torch.bfloat16):
     ```
   - `bfloat16` is hardware-native on NVIDIA Ampere (RTX 30-series), Ada (RTX 40-series), and Blackwell (RTX 50-series). On Apple Silicon MPS, PyTorch's `bfloat16` support is partial and varies across macOS versions; `float16` or `float32` must be used.
3. **GPU VRAM Telemetry:**
   - Upstream queries `torch.cuda.mem_get_info()`, which returns free and total VRAM in bytes.
   - On Apple Silicon (MPS) and CPU, `torch.cuda.mem_get_info()` does not exist and throws `AssertionError` or `AttributeError`.
   - Apple Silicon uses unified system memory, measured via macOS `sysctl` or `psutil`.

### Desktop Engine Solution (`engine/backends/`):
- **Zero modification to `vendor/CorridorKey2.0`**: Upstream source code remains clean and unmodified.
- **Hardware-Aware Dispatcher**:
  - `engine/backends/cuda/`: Directly delegates to the upstream CUDA pipeline on Windows RTX GPUs.
  - `engine/backends/apple/`: Adapts execution on Apple Silicon by configuring device pointers, mapping unsupported `bfloat16` operations safely to `float16`/`float32`, providing unified memory telemetry for auto-sizing, and graceful fallback to CPU.
  - `engine/backends/cpu/`: Implements memory-chunked staged execution for machines without compatible discrete GPUs.
- **No False Claims**: The application UI explicitly reports whether CUDA, MPS, or CPU fallback is active.

---

## 3. Video Codec, Format & Color Pipeline Support

| Format / Codec | Extension | Color Representation | Bit Depth | Alpha Channel | Target Pipeline |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ProRes 4444** | `.mov` | Display-coded / Linear straight | 12-bit (`yuva444p12le`) | **Yes (Full 1:1 Alpha)** | Professional VFX Compositing (After Effects, Premiere, Resolve, Nuke) |
| **H.264 Preview** | `.mp4` | Display-coded sRGB / Rec.709 | 10-bit (`yuv444p10le`) | Separate (Alpha preview track) | Rapid desktop review & playback |
| **OpenEXR Sequence**| `.exr` | Unclamped Scene-Linear RGB | 16-bit half / 32-bit float | **Yes (RGBA embedded)** | Studio HDR pipeline, ACES, deep composites |
| **PNG Sequence** | `.png` | Display-coded sRGB | 8-bit / 16-bit RGBA | **Yes (Transparent RGBA)** | Web, game engines, 2D animation |

---

## 4. NVIDIA RTX 5060 (Blackwell) Operational Profile

The **NVIDIA GeForce RTX 5060** (Blackwell architecture, sm_120) provides modern 5th-generation Tensor Cores with high-throughput bfloat16 math:

- **Compute Capability:** `sm_120` (CUDA 12.8+ runtime required).
- **VRAM Configurations:** 8 GB or 16 GB GDDR7.
- **Recommended Memory Profiles on 8 GB RTX 5060:**
  - **1080p (FHD):** Hann Chunk `24`, Hann Stride `12` with `--low_vram` disabled, or automatic selection.
  - **1440p (QHD):** Hann Chunk `8`, Hann Stride `4` with low-VRAM staging.
  - **4K (UHD):** Hann Chunk `4`, Hann Stride `2` with `--low_vram`.
- **Inference Speed:** Estimated 8–18 FPS at 1080p native resolution under bfloat16 acceleration.

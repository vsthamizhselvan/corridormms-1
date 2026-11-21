# CorridorKey 2.0 Desktop — System Architecture Specification

## 1. Executive Summary

**CorridorKey 2.0 Desktop** is a professional, standalone, cross-platform VFX desktop application designed for high-fidelity AI rotoscoping, green-screen/greenless video keying, and matte generation. It embeds and productionizes the breakthrough open-source **CorridorKey 2.0** neural architecture developed by Zachary Harris and Niko Pueringer (Corridor Digital), wrapping it in a native, Adobe-inspired VFX workspace built with **Tauri 2**, **Rust**, **React**, **TypeScript**, and a decoupled **Python AI Engine**.

The application is architected to deliver studio-grade performance:
- Direct hardware acceleration on **NVIDIA RTX GPUs** (including next-generation RTX 5060 Blackwell architectures via CUDA 12.8+ and bfloat16 Tensor Cores).
- Hardware detection and validation for **Apple Silicon (M1–M5)** via Apple Metal / PyTorch MPS and CPU fallbacks.
- Uncompressed and high-bit-depth VFX interchange including **Apple ProRes 4444 with Alpha**, **10-bit YUV444p10le H.264 previews**, and **32-bit/16-bit half OpenEXR HDR image sequences**.

---

## 2. Monorepo Repository Structure

The project is structured as a modular monorepo separating the user interface, native OS bridge, AI engine, vendor dependencies, and shared schemas:

```
corridor-key-2.0/
├── apps/
│   └── desktop/                  # Tauri 2 + React VFX Application
│       ├── src/
│       │   ├── components/       # Reusable UI primitives (shadcn/ui, modals, sliders)
│       │   ├── panels/           # Core VFX workspace panels
│       │   │   ├── MediaBrowser/ # Left panel: footage, assets, bin hierarchy
│       │   │   ├── Preview/      # Centre panel: viewport, zoom, alpha/fg split
│       │   │   ├── Inspector/    # Right panel: keying params, despill, hann window
│       │   │   ├── Timeline/     # Bottom panel: tracks, playhead, frame scrubber
│       │   │   └── StatusBar/    # Bottom strip: GPU/VRAM/CPU meters, active backend
│       │   ├── effects/          # Real-time preview shaders / Canvas matte compositing
│       │   ├── project/          # Project state management & serialization
│       │   ├── settings/         # App preferences, GPU device selector, temp paths
│       │   ├── styles/           # Adobe dark theme tokens & Tailwind config
│       │   ├── App.tsx           # Main dockable workspace layout
│       │   └── main.tsx          # React application entry point
│       └── src-tauri/            # Tauri 2 Rust Core
│           ├── Cargo.toml        # Rust dependencies (tauri, tokio, serde, sysinfo)
│           ├── tauri.conf.json   # Windowing, permissions, bundle configs
│           └── src/
│               ├── main.rs       # Tauri application bootstrap
│               ├── engine_ipc.rs # Subprocess lifecycle & JSON-RPC bridge to Python
│               ├── hardware.rs   # Native OS hardware telemetry (sysinfo / NVML)
│               └── project_io.rs # Project file read/write & SQLite cache
├── engine/                       # Python 3.11 AI Engine
│   ├── api/                      # JSON-RPC / IPC server for Tauri communication
│   │   ├── protocol.py           # Message definitions (commands, events, progress)
│   │   └── server.py             # Stdout/stdin or socket IPC server
│   ├── inference/                # CorridorKey 2.0 orchestration
│   │   ├── runner.py             # Staged inference pipeline controller
│   │   ├── memory_manager.py     # Dynamic Hann window & VRAM allocation
│   │   └── hints.py              # First-frame & hint-video ingest
│   ├── preprocessing/            # Asinh linear transform, gamma, aspect quantum
│   ├── postprocessing/           # Despill suppression, alpha clip, straight linear RGB
│   ├── video/                    # FFmpeg streaming pipes & OpenEXR IO
│   ├── detection/                # Hardware & environment detection
│   │   ├── hardware.py           # Multi-platform GPU/MPS/CUDA/CPU analyzer
│   │   └── validator.py          # Weights and dependency verifier
│   └── backends/                 # Hardware execution targets
│       ├── cuda/                 # NVIDIA CUDA backend (bfloat16, SDPA, VRAM meminfo)
│       ├── apple/                # Apple Silicon MPS backend & compatibility shims
│       └── cpu/                  # Multi-threaded CPU fallback
├── shared/                       # Cross-language contracts
│   ├── schemas/                  # JSON Schemas for engine IPC & project files
│   └── project-format/           # .ckproj specification & sample projects
├── vendor/                       # Upstream Repositories (Untouched)
│   └── CorridorKey2.0/           # Official CorridorKey 2.0 repository
│       ├── LICENSE               # CC BY-NC-SA 4.0 + Corridor Digital Additional Terms
│       ├── README.md             # Upstream documentation
│       ├── infer.py              # Upstream CLI inference entry point
│       ├── run_interactive.py    # Upstream interactive runner
│       ├── requirements.txt      # Upstream dependencies
│       ├── corridorkey/          # Upstream neural network definitions
│       ├── scripts/              # Weight downloaders & smoke test
│       ├── third_party/          # MoGe vendored modules
│       ├── vfms/                 # Foundation model weights directory
│       └── weights/              # CorridorKey checkpoint directory
├── assets/                       # Static media, icons, and VFX presets
├── docs/                         # Engineering and architecture documentation
└── tests/                        # Automated unit, integration, and verification tests
```

---

## 3. CorridorKey 2.0 AI Model Deep Dive

### 3.1 Neural Network Topology

CorridorKey 2.0 is a **transformer-native, two-stage video matting architecture** designed to preserve fine boundary detail (hair, smoke, motion blur) while eliminating background spill and green screen spill without green cloth requirement:

```
Input Video / Image Sequence
           │
           ▼
[Preprocessing: Asinh Signed Color Encoding & Shape Quantum (64px)]
           │
           ├───────────────────────────────┬───────────────────────────────┐
           ▼                               ▼                               ▼
[Frozen C-RADIOv4-SO400M]         [Frozen MoGe-2 ViT-B]          [Frozen DeepMind RVM]
  NVIDIA Visual Features            Microsoft Depth/Geometry        Recurrent Video MAE
  Input: (H/4, W/4), Patch 16       Input: (7H/32, 7W/32)           Input: (H/4, W/4), Patch 16
           │                               │                               │
           └───────────────────────────────┼───────────────────────────────┘
                                           ▼
                      [Feature Token Concatenation at /64 Grid]
                                           │
                                           ▼
                      [Stage 1: Spatiotemporal Context Transformer]
                      - 10 Body blocks at /64 grid (Full Spatiotemporal Attn)
                      - Swin-3D attention at /16 grid
                      - Hann window temporal taper (overlap carry)
                      - Outputs: /16 Baton (d=512) + /2 Auxiliary Alpha & FG
                                           │
                                           ▼
                      [Stage 2: High-Resolution Refinement Transformer]
                      - Streams full-resolution frames
                      - Fuses /16 Baton with raw input RGB
                      - Swin-2D attention + depatchify
                      - Outputs: 1:1 Native Resolution Alpha Matte + FG RGB
                                           │
                                           ▼
[Postprocessing: Despill Suppression, Linear/sRGB Transfer, Output Encoding]
           │
           ├───────────────────────────────┬───────────────────────────────┐
           ▼                               ▼                               ▼
[ProRes 4444 + Alpha]            [x264 10-bit YUV444p]           [OpenEXR RGBA Sequence]
```

### 3.2 Key Model Characteristics

1. **Resolution Independence & Shape Quantum:**
   - Operates directly at native plate resolution (720p, 1080p, 1440p, 4K, 8K).
   - Reflect-pads inputs to multiples of 64 pixels (`shape_quantum = 64`) and crops back precisely upon output.
2. **Temporal Stabilization via Hann Windows:**
   - Overlapping temporal chunks (e.g. 80 frames with 40 frame stride, 24/12, or 8/4) combined using a Hann taper.
   - Stage 1 predictions from overlapping windows are carried forward into subsequent windows to maintain identity coherence.
3. **Foundation Model Guidance:**
   - **C-RADIOv4-SO400M**: High-capacity semantic visual features.
   - **MoGe-2 ViT-B**: Metric depth and surface normal cues, enabling separation based on 3D spatial layout.
   - **RVM (Recurrent Video MAE)**: Chronological temporal state carry.
4. **Color Domain:**
   - Internal processing occurs in an asinh-transformed scene-linear HDR representation, allowing highlights and high dynamic range reflections to be preserved.

---

## 4. Communication & Subprocess Architecture

To maintain complete UI fluidity (60–120 FPS) during heavy neural network inference, the frontend and AI runtime are strictly decoupled:

```
┌────────────────────────────────────────────────────────┐
│             Tauri 2 Frontend (React + TS)              │
│  - Viewport & Matte Canvas                             │
│  - Timeline & Scrubber                                 │
│  - Parameter Inspector                                 │
└───────────────────────────┬────────────────────────────┘
                            │ Tauri IPC (invoke / emit)
                            ▼
┌────────────────────────────────────────────────────────┐
│               Tauri Rust Core (src-tauri)              │
│  - Native windowing & OS file dialogs                  │
│  - Subprocess supervisor (spawns & monitors Python)    │
│  - Non-blocking stdin/stdout JSON-RPC stream           │
│  - System telemetry (CPU, GPU, RAM) via sysinfo/NVML   │
└───────────────────────────┬────────────────────────────┘
                            │ Stdin/Stdout JSON-RPC 2.0
                            ▼
┌────────────────────────────────────────────────────────┐
│            CorridorKey Python Engine (engine/)         │
│  - api/server.py: JSON-RPC message dispatcher          │
│  - detection/hardware.py: Detects CUDA / MPS / CPU     │
│  - inference/runner.py: Orchestrates pipeline          │
│  - Dispatches to vendor/CorridorKey2.0/corridorkey     │
│  - Emits real-time progress events {"type": "progress"}│
└────────────────────────────────────────────────────────┘
```

### 4.1 JSON-RPC Protocol Contract
- **Commands (Tauri -> Engine):**
  - `detect_hardware`: Queries available accelerators, compute capability, VRAM.
  - `validate_assets`: Checks presence and checksums of model weights.
  - `probe_media`: Inspects video file metadata (resolution, frame rate, duration, codec).
  - `start_job`: Starts inference with specified settings (hann_chunk, despill, hint mode).
  - `cancel_job`: Gracefully stops the active inference worker.
- **Events (Engine -> Tauri):**
  - `job_progress`: Frame index, current stage (Foundation / Stage 1 / Stage 2), FPS, ETA.
  - `preview_frame`: Base64 JPEG or shared-memory thumbnail of the latest processed frame.
  - `job_completed`: Final output file paths and elapsed time.
  - `job_failed`: Structured error message, traceback, and remediation suggestions.

---

## 5. UI Workspace & Visual Styling

The interface is inspired by standard VFX applications (Adobe Premiere Pro, Adobe After Effects, DaVinci Resolve) with strict adherence to professional production standards:

1. **Color Palette:**
   - Background Base: `#18181b` (Dark Charcoal / Zinc 900)
   - Panel Surface: `#202024` / `#27272a` (Zinc 800)
   - Border Lines: `#3f3f46` (Subtle 1px border, 0% blur)
   - Accent / Playhead: `#3b82f6` (VFX Blue) / `#10b981` (Success Green)
   - Matte Alpha Display: White (`#ffffff`) foreground, Black (`#000000`) background, or classic 8x8 checkerboard.
2. **Typography & Density:**
   - Font: Inter / SF Pro Display, tabular numbers for timecode and frame counters.
   - Ultra-compact padding (`p-2`, `gap-1.5`, `text-xs`) maximizing plate preview area.
3. **Workspace Panels:**
   - **Top Bar**: Project metadata, menu bar (File, Edit, View, Project, Playback, Export, Settings).
   - **Left Panel (Media Pool)**: Bin navigation, footage drop zone, metadata viewer.
   - **Centre Panel (Viewport)**: High-DPI canvas preview with split modes (Original, Matte, Cutout, Split-screen wiper, Checkerboard).
   - **Right Panel (Inspector)**: Model parameters, Hann window controls, Despill slider, Hint loading, Export codec selector.
   - **Bottom Panel (Timeline & Queue)**: Multi-track timeline, frame playhead, job render queue with real-time status.
   - **Status Bar**: Live hardware metrics (Active device, GPU memory utilized, CPU utilization, Engine status).

# CorridorKey 2.0 Desktop — Final Project Architecture

## 1. System Architecture Diagram

```
+-----------------------------------------------------------------------------------------+
|                                    React 18 / TypeScript UI                             |
|                                                                                         |
|  [ TopMenu ]      [ MediaBrowser ]      [ WebGL2 Viewport ]      [ Timeline / Audio ]   |
|  [ Setup Wizard ] [ Inspector ]         [ Mask & Node VFX ]      [ StatusBar / Diag ]   |
+-----------------------------------------------------------------------------------------+
                                             |
                                  JSON-RPC over Tauri IPC
                                             v
+-----------------------------------------------------------------------------------------+
|                                  Tauri 2 Rust Core Bridge                               |
|                                                                                         |
|  - Process Manager (AiProcessManager)        - Hardware Telemetry (SysInfo)             |
|  - Atomic Project IO (.ckproj)               - Media Probing (FFprobe)                  |
|  - Diagnostics Bundler & Log Rotator         - Window & Menu Event Dispatcher           |
+-----------------------------------------------------------------------------------------+
                                             |
                               Bidirectional Stdin/Stdout Pipe
                                             v
+-----------------------------------------------------------------------------------------+
|                               Python 3.11 Inference Subsystem                           |
|                                                                                         |
|  +---------------------------+  +--------------------------+  +-----------------------+ |
|  | CorridorKey AI Adapter    |  | Video & Frame Pipeline   |  | Multi-Track Timeline  | |
|  | - CorridorKey v2 Weights  |  | - FFmpeg Frame Reader    |  | - Rational Timebase   | |
|  | - NVIDIA C-RADIO Backbone |  | - Bounded Queue Buffer   |  | - SMPTE Timecode      | |
|  | - Microsoft MoGe-2 ViT-B  |  | - Audio 48kHz Resampler  |  | - Keyframe Engine     | |
|  | - DeepMind RVM Temporal   |  | - Codec Exporters        |  | - Render Graph DAG    | |
|  +---------------------------+  +--------------------------+  +-----------------------+ |
|                                                                                         |
|  +---------------------------+  +--------------------------+  +-----------------------+ |
|  | Color & Alpha Science     |  | Advanced VFX Compositor  |  | Memory Guard & Cache  | |
|  | - Straight / Premultiplied|  | - Vector Masks (Bezier)  |  | - Multi-Tier Frame LRU| |
|  | - Despill Average Clamp   |  | - 10-Effect Stack        |  | - 4K/8K Tiled Safety  | |
|  | - Transfer (sRGB/Rec709)  |  | - Layer Blend Modes      |  | - Tensor Pool Recycler| |
|  +---------------------------+  +--------------------------+  +-----------------------+ |
+-----------------------------------------------------------------------------------------+
                                             |
                         Hardware Acceleration Hardware Dispatch
                                             v
      +--------------------------------------+--------------------------------------+
      |                                      |                                      |
      v                                      v                                      v
[ Apple Metal / MPS ]               [ NVIDIA CUDA / NVENC ]                  [ CPU Fallback ]
(Apple Silicon M1–M5)               (Windows 10/11 RTX 2060–5060)            (Multi-Threaded)
```

---

## 2. Directory Layout & Subsystems

* **`apps/desktop/`**: Standalone desktop application.
  - `src/components/`: Modular Adobe-style panels (Viewer, TopMenu, MediaBrowser, Timeline, Inspector, Setup Wizard, Diagnostics).
  - `src/stores/`: Typed Zustand reactive state management.
  - `src-tauri/`: Tauri 2 Rust native bridge, commands, and multi-platform bundle configurations.
* **`engine/`**: Core video and inference engine.
  - `desktop_api/`: Worker protocol, JSON-RPC event loop, model asset management.
  - `inference/`: CorridorKey adapter, GPU tensor pooling, warmup routines.
  - `video/`: Frame extraction, streaming decoders, presentation timestamps.
  - `color/`: Alpha management, despill algorithms, transfer functions.
  - `timeline/`: Edit operations, rational timebases, keyframes, render graph.
  - `vfx/`: Vector masking, layer compositing, node graph evaluation.
  - `export/`: ProRes 4444, VP9, QTRLE, OpenEXR, PNG sequence exporters.
  - `pipeline/`: Intelligent frame caching, memory guard.
  - `packaging/`: Isolated Python runtime manager, model downloader, FFmpeg bundler.
  - `logging/`: Rotating file diagnostics.
* **`vendor/CorridorKey2.0/`**: Upstream CorridorKey v2 reference codebase.
* **`tests/`**: Comprehensive verification suites (`verify_phase2.py` through `verify_phase12.py`).
* **`docs/`**: Complete engineering documentation, guides, and architectural audits.

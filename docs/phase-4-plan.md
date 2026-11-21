# CorridorKey 2.0 Desktop — Phase 4 Implementation Plan
## Professional Video Pipeline & Export Architecture

This document outlines the architectural blueprint, data-plane/control-plane separation, and phased implementation strategy for Phase 4 (Professional Video Pipeline) in CorridorKey 2.0 Desktop.

---

## 1. System Topology & Dual-Plane Architecture

To handle 1080p, 4K, and high-framerate footage reliably without memory exhaustion or UI hitching, the video pipeline is split into a **Control Plane** and a **Data Plane**:

```
 CONTROL PLANE (JSON-lines, Tauri IPC, State Stores)
 ┌───────────────┐     Tauri Commands     ┌───────────────────┐     JSON Lines     ┌──────────────────┐
 │   React UI    │ ─────────────────────> │  Tauri 2 Rust IPC │ ─────────────────> │  Python Worker   │
 │ Export Settings│ <───────────────────── │  Supervisor       │ <───────────────── │  Request Loop    │
 └───────────────┘     Progress Events    └───────────────────┘     Protocol v1    └────────┬─────────┘
                                                                                            │
 DATA PLANE (Raw Frames, Bounded Queues, Subprocess Pipes)                                  │
 ┌───────────────┐        pipe:stdout      ┌───────────────────┐     In-Memory /    ┌───────▼──────────┐
 │ FFmpeg /      │ ─────────────────────> │   Bounded Queue   │ ──── Staging ────> │ CorridorKey AI   │
 │ VideoToolbox  │ (Raw BGR/RGB Pixels    │ (Backpressure     │ (Hann windows,     │ Neural Inference │
 │ Decoder       │  + PTS Timestamps)     │  Cap: 8–16 frames)│  Signed asinh)     │ Model Pipeline   │
 └───────────────┘                        └───────────────────┘                    └───────┬──────────┘
                                                                                            │
 ┌───────────────┐        pipe:stdin       ┌───────────────────┐     Straight/      ┌───────▼──────────┐
 │ FFmpeg / EXR  │ <───────────────────── │   Colour & Alpha  │ <─── Despilled ─── │ Foreground (FG)  │
 │ Professional  │ (Raw BGRA64 / 16-bit   │   Transformation  │     Frames         │ + Alpha Matte    │
 │ Encoders      │  Half-Float Streams)   │   Pipeline        │                    │ (Tensors/Arrays) │
 └───────────────┘                        └───────────────────┘                    └──────────────────┘
```

### 1.1 Control Plane
- **Technology:** JSON-lines over stdin/stdout, Tauri 2 IPC commands, and Zustand frontend stores.
- **Payloads:** Job IDs, export configuration, status checks, frame-level progress metrics (decoding %, inference %, encoding %, overall %, current FPS, ETA), error codes, and cancellation requests.
- **Rule:** Never send binary raw frame buffers through Base64 JSON.

### 1.2 Data Plane
- **Technology:** Standard I/O subprocess pipes (`pipe:0` / `pipe:1`) with raw uncompressed pixel bytes (`bgr24`, `rgb48le`, `bgra64le`, float32/half-float arrays).
- **Backpressure:** Thread-safe bounded queues (`queue.Queue(maxsize=16)`) ensuring that fast decoders do not overrun RAM while inference operates.
- **Timing:** Dedicated `TimestampManager` recording Presentation Timestamps (PTS) for each extracted frame to guarantee frame accuracy and audio sync across variable and constant framerate footage.

---

## 2. Directory Structure & Module Breakdown

```
engine/
├── video/
│   ├── __init__.py
│   ├── probe.py               # Robust FFprobe media analysis (codecs, color metadata, audio, alpha)
│   ├── decoder.py             # FFmpeg hardware & software decoder (VideoToolbox, NVDEC, software)
│   ├── frame_reader.py        # Streaming frame generator yielding (frame_idx, pts, frame_bgr)
│   ├── frame_writer.py        # Streaming frame sink piping to FFmpeg or sequence writers
│   ├── frame_buffer.py        # Thread-safe bounded buffer with explicit backpressure
│   └── timestamp_manager.py   # PTS/DTS tracking, VFR handling, audio synchronization
├── color/
│   ├── __init__.py
│   ├── color_manager.py       # Color pipeline orchestration (Rec.709, sRGB, Linear, Rec.2020)
│   ├── transfer_functions.py  # IEC 61966-2-1, BT.709 curve, asinh HDR, gamma conversions
│   ├── color_metadata.py      # FFmpeg metadata injection (-color_primaries, -color_trc, -colorspace)
│   └── alpha_manager.py       # Straight vs premultiplied alpha, despill, alpha validation
├── export/
│   ├── __init__.py
│   ├── export_manager.py      # Master export orchestrator coordinating encoder selection
│   ├── prores.py              # Apple ProRes 4444 and 4444 XQ (yuva444p10le / ap4h / ap4x)
│   ├── qtrle.py               # QuickTime Animation RLE (argb/rgba)
│   ├── vp9.py                 # VP9 WebM with alpha (yuva420p, -auto-alt-ref 0)
│   ├── openexr.py             # OpenEXR multi-threaded sequence writer (half/float, ZIP compression)
│   ├── png_sequence.py        # PNG sequence writer (8-bit / 16-bit RGBA, %06d.png)
│   └── validation.py          # Post-export file decoding to verify transparency and pixel integrity
└── pipeline/
    ├── __init__.py
    ├── pipeline_manager.py    # Multi-threaded pipeline tying decoder -> queue -> inference -> encoder
    ├── pipeline_state.py      # Structured state tracking (decoding, inference, encoding progress)
    └── pipeline_events.py     # Typed event objects mapped to Protocol v1 JSON
```

---

## 3. Targeted Export Formats & Encoding Specifications

| Format | Container | Codec / Library | Pixel Format | Bit Depth | Alpha Support | Validation Method |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Apple ProRes 4444** | `.mov` | `prores_ks` (profile 4) | `yuva444p10le` | 10-bit / 12-bit | Yes (Lossless A) | Re-decode via FFprobe & OpenCV; test alpha plane variance |
| **Apple ProRes 4444 XQ** | `.mov` | `prores_ks` (profile 5) | `yuva444p10le` | 12-bit | Yes | Re-decode via FFprobe & OpenCV; test alpha plane variance |
| **QuickTime Animation RLE** | `.mov` | `qtrle` | `argb` / `rgba` | 8-bit | Yes | Re-decode via FFmpeg; assert 4 channels present |
| **VP9 / WebM Alpha** | `.webm` | `libvpx-vp9` | `yuva444p` / `yuva420p` | 8-bit | Yes (`-auto-alt-ref 0`) | Re-decode via FFmpeg; verify alpha stream extraction |
| **OpenEXR Sequence** | `.exr` | OpenEXR / ZIP | `RGBA` | 16-bit Half / 32-bit Float | Yes (`A` channel) | Read back with OpenCV (`IMREAD_UNCHANGED`); assert 4 channels |
| **PNG Sequence** | `.png` | PNG | `RGBA` | 8-bit / 16-bit | Yes | Read back with OpenCV; verify transparent background |

---

## 4. Implementation Steps (Sequential Execution)

1. **Step 1:** Complete project inspection & publish implementation plan (`docs/phase-4-plan.md`).
2. **Step 2:** Build `engine/video/probe.py` supporting detailed video, audio, and color analysis.
3. **Step 3 & 4:** Build `engine/video/decoder.py`, `frame_reader.py`, and `timestamp_manager.py` with hardware acceleration discovery (VideoToolbox on macOS, NVDEC on Windows, software fallback).
4. **Step 5:** Implement bounded frame queues with backpressure in `engine/video/frame_buffer.py`.
5. **Step 6 & 7:** Integrate with CorridorKey inference adapter and implement `engine/color/alpha_manager.py` (straight/premultiplied alpha, despill, validation).
6. **Step 8–11:** Build professional export modules (`prores.py`, `qtrle.py`, `vp9.py`, `openexr.py`, `png_sequence.py`, `validation.py`).
7. **Step 12:** Build dedicated color management subsystem (`engine/color/color_manager.py`, `transfer_functions.py`, `color_metadata.py`).
8. **Step 13:** Implement audio stream passthrough and preservation in `engine/video/frame_writer.py` and `export_manager.py`.
9. **Step 14:** Connect pipeline to Tauri IPC and build Adobe-style React export panel and progress monitors.
10. **Step 15:** Comprehensive test suite (`tests/test_video_pipeline.py`, `tests/verify_phase4.py`) and documentation suite.

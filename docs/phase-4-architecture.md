# CorridorKey 2.0 Desktop — Phase 4 Video Pipeline Architecture

This document specifies the technical design, data/control plane separation, thread topology, and stream protocols powering the Phase 4 Video Pipeline in CorridorKey 2.0 Desktop.

---

## 1. Pipeline Topology & Separation of Concerns

High-resolution video processing (1080p, 4K, high framerate) requires strict architectural decoupling between message passing and binary pixel transport:

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

### 1.1 The Control Plane
- **Channel:** Standard input and output lines parsed as typed Protocol v1 JSON envelopes.
- **Responsibilities:**
  - Job initialization (`start_job` payload containing resolution, format, color space, alpha mode).
  - High-frequency event streaming (`job_progress` with decoding %, inference %, encoding %, FPS, and ETA).
  - Clean cancellation signaling and error trapping.
- **Rule:** Never serialize binary pixel buffers into Base64 JSON.

### 1.2 The Data Plane
- **Channel:** Standard OS anonymous pipes connected between FFmpeg subprocesses and in-memory NumPy buffers.
- **Responsibilities:**
  - Streaming uncompressed raw video frames (`bgr24`, `bgr48le`, `bgra64le`, planar `gbrapf32le`).
  - Maintaining presentation timestamps (PTS) to guarantee 100% audio-video synchronization.
  - Applying bounded queue backpressure (`queue.Queue(maxsize=16)`) to limit active RAM usage to < 500 MB regardless of video duration.

---

## 2. Multi-Threaded Pipeline Architecture

The execution of a render job is orchestrated by [engine/pipeline/pipeline_manager.py](file:///Volumes/VST%20SSD/corridor%20key%202.0/engine/pipeline/pipeline_manager.py) across three concurrent worker threads:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Thread 1: Decoder Thread                        │
│  - Reads source video using FFmpeg streaming decoder                   │
│  - Hardware acceleration: VideoToolbox (macOS) / NVDEC (Windows)       │
│  - Extracts frames & assigns exact Presentation Timestamps (PTS)       │
│  - Pushes DecodedFrame into raw_queue (Bounded: 16 frames)             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Backpressure Blocking
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   Thread 2: Neural Inference Thread                    │
│  - Pops uncompressed frames from raw_queue                             │
│  - Preprocesses color: Input SDR -> Scene-Linear -> Signed asinh       │
│  - CorridorKey 2.0 Stage 1 & Stage 2 Transformer execution             │
│  - Computes sub-pixel alpha matte and despilled foreground             │
│  - Pushes (FG, Alpha) pair into processed_queue (Bounded: 16 frames)   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Backpressure Blocking
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        Thread 3: Encoder Thread                        │
│  - Pops (FG, Alpha) from processed_queue                               │
│  - Assembles 4-channel RGBA in Straight or Premultiplied mode          │
│  - Applies target color space transform (Rec.709 / sRGB / ACEScg)      │
│  - Streams frames to encoder (ProRes 4444, QTRLE, VP9, OpenEXR, PNG)   │
│  - Tracks smoothed FPS, ETA, and broadcasts pipeline telemetry         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     Post-Export Validation Gate                        │
│  - Closes encoder and flushes file descriptors                         │
│  - Re-decodes exported media to rigorously verify alpha channel presence│
│  - Calculates opaque vs transparent pixel distributions                │
│  - Emits final completion event with validation report                 │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Memory & Backpressure Management

Without bounded buffering, decoding a 4K 60fps clip at uncompressed 16-bit depth would consume over 1 GB of RAM per second:
1. `BoundedFrameQueue`: Enforces a hard ceiling of 16 frames between the decoder and neural model, and 16 frames between the model and encoder.
2. RAM Footprint: At 1080p RGBA 16-bit, each frame is ~16 MB. 32 buffered frames consume a maximum of ~512 MB RAM.
3. Garbage Collection: Arrays are contiguous NumPy buffers reused or immediately released upon pipe write.

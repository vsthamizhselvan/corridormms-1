# CorridorKey 2.0 Desktop — AI Engine Integration Guide

This document describes the design, implementation, and operational details of the AI Engine integration connecting the CorridorKey 2.0 desktop frontend (Tauri 2 + React) with the Python AI inference engine.

---

## 1. Architectural Overview

CorridorKey 2.0 Desktop operates as a dual-process architecture:
1. **Desktop Host (Rust + WebKit/WebView):**
   - Renders the Adobe-style dark VFX user interface.
   - Manages window state, project files (`.ckproj`), timeline scrubbing, and viewer compositing.
   - Implements a resilient process supervisor in Rust using Tokio async channels.
2. **AI Inference Subprocess (Python 3.11):**
   - Executes PyTorch neural network inference with the CorridorKey 2.0 model.
   - Interfaces directly with GPU hardware (CUDA on Windows, Apple Silicon Metal/MPS on macOS, or CPU fallback).
   - Manages video frame streaming, input staging, despill, alpha estimation, and output encoding.

```
┌────────────────────────────────────────────────────────┐
│             React Desktop UI (Apps/Desktop)            │
│  - Stores: aiJobStore, aiEngineStore, projectStore     │
│  - Components: ProcessingPanel, ModelStatus, Queue     │
└───────────────────────────┬────────────────────────────┘
                            │ Tauri IPC (invoke) & Events (listen)
                            ▼
┌────────────────────────────────────────────────────────┐
│               Tauri 2 Rust Core Bridge                 │
│  - src/ai_engine/process.rs: EngineSupervisor          │
│  - src/ai_engine/commands.rs: Tauri Invocations        │
│  - src/ai_engine/protocol.rs: Serde De/Serialization   │
│  - src/ai_engine/events.rs: Event Bus                  │
└───────────────────────────┬────────────────────────────┘
                            │ stdin / stdout (JSON-lines, Protocol v1)
                            │ stderr (Diagnostic & Engine Logs)
                            ▼
┌────────────────────────────────────────────────────────┐
│            Python AI Engine Worker (engine/)           │
│  - desktop_api/worker.py: Request loop                 │
│  - desktop_api/hardware.py: Hardware Detection         │
│  - desktop_api/model_manager.py: Checkpoint Manager    │
│  - jobs/job_manager.py: Threaded Task Execution        │
│  - inference/corridor_key_adapter.py: Model Bridge     │
└────────────────────────────────────────────────────────┘
```

---

## 2. Process Supervisor & Lifecycle

The lifecycle of the Python engine is supervised by `EngineSupervisor` located at [apps/desktop/src-tauri/src/ai_engine/process.rs](file:///Volumes/VST%20SSD/corridor%20key%202.0/apps/desktop/src-tauri/src/ai_engine/process.rs).

### 2.1 Initialization
When the desktop application launches:
1. The supervisor locates the Python executable:
   - Priority 1: Virtual environment at `<workspace>/.venv/bin/python` (macOS/Linux) or `<workspace>/.venv/Scripts/python.exe` (Windows).
   - Priority 2: System Python (`python3` or `python`).
2. The subprocess is spawned with:
   - Command: `<python> -m engine.desktop_api.main`
   - Working Directory: Project root.
   - Piped `stdin`, piped `stdout`, and piped `stderr`.
3. Background async tasks are spawned to monitor:
   - `stdout` reader: Parses line-delimited JSON messages conforming to `Protocol v1`.
   - `stderr` reader: Captures and logs Python diagnostic messages without polluting the JSON data channel.

### 2.2 Health Checks & Heartbeats
- The supervisor sends a `ping` command periodically or upon user interaction.
- The Python worker immediately responds with `{"type": "pong", "payload": {"timestamp": <float>}}`.
- If the subprocess terminates unexpectedly, the supervisor updates the UI status to `disconnected` and can automatically respawn the worker.

### 2.3 Clean Shutdown
Upon application exit:
1. The supervisor sends `{"type": "shutdown", "payload": {}}` over stdin.
2. The Python worker sets its stop event, aborts running background jobs safely, flushes open file writers, and exits with code 0.
3. If the process does not terminate within 3 seconds, a kill signal is issued.

---

## 3. Communication Protocol (Protocol v1)

All communication between Rust and Python occurs over `stdin` and `stdout` using newline-delimited JSON.

### 3.1 Request-Response Correlation
Every command issued by Rust contains a unique `id` (UUIDv4) and a `type` string. The Python worker returns a matching response carrying the same `id`.

**Rust -> Python:**
```json
{
  "id": "c1f7b82e-9d2a-4a5c-bb12-9c3f71ef82a1",
  "type": "detect_hardware",
  "payload": {}
}
```

**Python -> Rust:**
```json
{
  "id": "c1f7b82e-9d2a-4a5c-bb12-9c3f71ef82a1",
  "type": "hardware_detected",
  "success": true,
  "payload": {
    "os_name": "Darwin",
    "backend": "mps",
    "device_name": "Apple M-Series (MPS)",
    "cuda_available": false,
    "mps_available": true,
    "recommended_backend": "mps",
    "total_memory_mb": 16384,
    "is_rtx_5060": false
  }
}
```

### 3.2 Asynchronous Event Streaming
During long-running jobs (such as video keying), the Python engine emits unprompted events containing `"event"` instead of `"type"`:

```json
{
  "event": "job_progress",
  "payload": {
    "job_id": "job-8f2e9",
    "status": "processing",
    "progress": 0.45,
    "current_frame": 45,
    "total_frames": 100,
    "fps": 28.4,
    "eta_seconds": 1.93,
    "message": "Keying frame 45/100"
  }
}
```

---

## 4. Model Management & Lifecycle

Neural model loading and weights caching are handled by `ModelManager` located at [engine/desktop_api/model_manager.py](file:///Volumes/VST%20SSD/corridor%20key%202.0/engine/desktop_api/model_manager.py).

### 4.1 Asset Integrity Validation
Before loading, the engine verifies the presence and integrity of all required CorridorKey 2.0 checkpoints:
- Primary Checkpoint: `vendor/CorridorKey2.0/weights/corridorkey_v2.safetensors`
- Foundation Statistics: `vendor/CorridorKey2.0/weights/foundation_stats.safetensors`
- Visual Foundation Models:
  - Robust Video Matting (RVM): `vendor/CorridorKey2.0/vfms/rvm/pretrain_rvm_small16_256_204031069.npz`
  - MoGe-2 Geometry: `vendor/CorridorKey2.0/vfms/moge/model.pt`
  - C-RADIOv4 Vision Backbone: `vendor/CorridorKey2.0/vfms/cradio/C-RADIOv4-SO400M`

### 4.2 In-Memory Caching
- **Avoid Repeated Loading:** The ~5GB neural network is loaded once and held in GPU VRAM (or Unified Memory under MPS).
- **Subsequent Jobs:** Consecutive inference runs reuse the already-initialized model pipeline, eliminating redundant 5–15 second disk read and graph construction times.
- **Graceful Fallback:** If weights have not been downloaded yet, the engine reports `missing_weights` and falls back to a deterministic color-guided keying and despill pipeline for continuous development and UI verification.

---

## 5. Job Execution & Cancellation

Jobs are managed by `JobManager` at [engine/jobs/job_manager.py](file:///Volumes/VST%20SSD/corridor%20key%202.0/engine/jobs/job_manager.py).

### 5.1 Job Flow
1. **Creation:** The user triggers "Start AI Processing" in `ProcessingPanel.tsx`.
2. **Submission:** React calls `startAiJob(...)` Tauri command, which forwards `start_job` to the Python worker.
3. **Execution:** The job executes in a dedicated Python daemon thread.
4. **Streaming:** Progress updates (`job_progress`) are emitted every frame or batch of frames.
5. **Completion:** When finished, `job_completed` is emitted with output paths (`alpha_path`, `foreground_path`).
6. **Preview:** The React UI updates the timeline and viewer preview with the generated matte and despilled foreground.

### 5.2 Safe Cancellation
- The user can click "Cancel" at any time.
- The supervisor sends `cancel_job` with the target `job_id`.
- The Python adapter checks `job.is_cancelled()` at every frame boundary.
- Upon cancellation, partially written video files are flushed and closed, temporary memory buffers are freed, and `job_cancelled` is returned.
- Unsupported pause/resume operations are explicitly avoided in compliance with the architecture specification.

---

## 6. Verification and Testing

Automated verification of the integration layer is executed via:
```bash
.venv/bin/python3 tests/test_engine_service.py
```
This tests:
1. Protocol serialization and deserialization.
2. Hardware detection across platforms.
3. Model manager asset validation.
4. End-to-end synthetic video generation, inference processing, and progress reporting.
5. Job cancellation mid-flight.
6. Subprocess worker communication loop.

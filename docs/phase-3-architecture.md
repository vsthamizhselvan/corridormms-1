# CorridorKey 2.0 Desktop — Phase 3 AI Engine Integration Architecture

## 1. System Topology & Process Boundaries

The Phase 3 integration establishes a resilient, asynchronous processing bridge between the native desktop application and the CorridorKey 2.0 neural inference runtime:

```
┌────────────────────────────────────────────────────────┐
│             React Desktop UI (Apps/Desktop)            │
│  - ProcessingPanel & Progress Indicators               │
│  - HardwareInfo & ModelStatus Cards                    │
│  - RenderQueue & History Views                         │
└───────────────────────────┬────────────────────────────┘
                            │ Zustand Actions (aiJobStore, aiEngineStore)
                            ▼
┌────────────────────────────────────────────────────────┐
│               Tauri 2 Rust Core Bridge                 │
│  - src/ai_engine/process.rs: Subprocess Supervisor     │
│  - src/ai_engine/commands.rs: Typed Tauri IPC Commands │
│  - Asynchronous event dispatcher & oneshot channels    │
└───────────────────────────┬────────────────────────────┘
                            │ Versioned JSON-lines over stdin/stdout
                            │ (Diagnostics strictly on stderr)
                            ▼
┌────────────────────────────────────────────────────────┐
│            Python AI Engine Worker (engine/)           │
│  - desktop_api/worker.py: Request loop & command router│
│  - desktop_api/hardware.py: CUDA / MPS / CPU detection │
│  - desktop_api/model_manager.py: Model cache & assets  │
│  - jobs/job_manager.py: Cancellation & thread pool     │
│  - inference/corridor_key_adapter.py: Pipeline runner  │
└───────────────────────────┬────────────────────────────┘
                            │ Direct In-Memory Invocation
                            ▼
┌────────────────────────────────────────────────────────┐
│             Vendor CorridorKey 2.0 Runtime             │
│  - vendor/CorridorKey2.0/corridorkey/runtime.py        │
│  - Frozen Foundations (C-RADIOv4, MoGe-2, RVM)         │
│  - Stage 1 Spatiotemporal Context Transformer          │
│  - Stage 2 Native Resolution Refinement Transformer    │
│  - FFmpeg / OpenCV Video Streaming Encoders            │
└────────────────────────────────────────────────────────┘
```

---

## 2. Key Architecture Principles

1. **Non-Blocking UI Thread:**
   - Inference tasks run in a detached background thread within the Python worker subprocess.
   - The Tauri Rust core communicates asynchronously using Tokio channels (`tokio::sync::oneshot`), ensuring zero hitching or UI lag in the React viewport.
2. **Strict Protocol Separation:**
   - Standard output is reserved 100% for machine-parseable JSON lines conforming to Protocol v1.
   - All diagnostic logs, progress banners, PyTorch memory traces, and warnings are streamed to standard error, captured by the Rust logger.
3. **Model Caching & Memory Reuse:**
   - The 5GB neural model checkpoint is cached in GPU/MPS memory via `ModelManager` across multiple consecutive render jobs, avoiding the multi-second overhead of re-reading weights from disk for each plate.
4. **Safe Cancellation & Resource Cleanup:**
   - Jobs can be cancelled at any frame boundary. Video writer handles, temporary memmaps, and memory allocations are cleaned up safely.
5. **Hardware Isolation:**
   - Dedicated detection routines accurately profile NVIDIA RTX GPUs (such as RTX 5060 Blackwell) and Apple Silicon Metal (M1–M5), reporting actual supported acceleration rather than silently claiming unsupported features.

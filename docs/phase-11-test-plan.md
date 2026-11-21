# CorridorKey 2.0 Desktop — Phase 11 Master Test Plan

## 1. Scope & Execution Strategy

The Phase 11 Test Plan encompasses 11 comprehensive testing domains executed via automated Python verification harnesses, regression suites, stress scripts, and frontend build validations.

---

## 2. Testing Matrices & Domains

### Domain 1: Full Regression Suite (Phases 1–10)
* Execute and log tests for:
  - Phase 2: Desktop application foundation (`tests/verify_phase2.py`)
  - Phase 3: AI engine integration & IPC (`tests/verify_phase3.py`)
  - Phase 4: Video pipeline & hardware codecs (`tests/verify_phase4.py`)
  - Phase 5: Interactive viewer & WebGL compositing (`tests/verify_phase5.py`)
  - Phase 6: Multi-track timeline & timebase (`tests/verify_phase6.py`)
  - Phase 7: Project serialization, autosave & atomic recovery (`tests/verify_phase7.py`)
  - Phase 8: Advanced VFX compositing, masking, effects & nodes (`tests/verify_phase8.py`)
  - Phase 9: Performance engineering & memory guard (`tests/verify_phase9.py`)
  - Phase 10: Production packaging, runtime & licensing (`tests/verify_phase10.py`)

### Domain 2: AI Engine Deep Validation
* GPU/MPS execution and float16 inference stability.
* CPU fallback verification.
* Frame-by-frame alpha consistency over multi-frame sequences.
* Job cancellation latency and memory cleanup.
* Corruption detection when model weights are truncated or missing.

### Domain 3: Video Pipeline Resilience
* Container coverage: MP4, MOV, WebM, MKV, AVI, ProRes, PNG sequences.
* Variable Frame Rate (VFR) handling and PTS preservation.
* Audio stream extraction, 48 kHz resampling, and audio/video sync.
* Corrupted file handling: Graceful error recovery without crashing.

### Domain 4: Alpha & Colour Fidelity Validation
* Straight alpha vs premultiplied alpha verification.
* Edge transition fidelity (fine hair, motion blur, transparency ramps).
* Spill suppression and de-spill algorithm efficacy.
* Transfer functions: Linear, Rec.709, sRGB, Rec.2020.
* Verification that alpha channel is never erroneously gamma-corrected.

### Domain 5: VFX Compositing & Node Engine
* Mask geometry: Rect, Ellipse, Polygon, Bezier curves.
* Effect stack operations: Blur, Sharpen, Glow, Shadow, Grain, Vignette, Color Grade.
* Blend modes: Normal, Add, Multiply, Screen, Overlay.
* Node Graph validation: Cycle detection, topological sort, dynamic execution.

### Domain 6: Timeline & Playback
* Frame-accurate scrubbing and multi-track composite rendering.
* Clip trimming, split, snap, and ripple delete.
* Undo/redo stack integrity across 50 consecutive operations.

### Domain 7: Project Serialization & Disaster Recovery
* Project save (`.ckproj`), atomic temp writes, schema validation (`v1.1.0`).
* Autosave snapshot generation and crash recovery simulation.
* Missing media relocation and relinking heuristics.

### Domain 8: Performance & Stress Testing
* High-resolution testing: 1080p, 1440p, 4K UHD, and 8K tiled execution.
* Timeline stress: 100+ simulated clips.
* Memory pressure and LRU eviction validation.

### Domain 9: Cross-Platform Validation
* macOS: Native Apple Silicon (arm64) execution, Metal MPS acceleration, DMG installer config.
* Windows: x64 architecture configuration, NSIS installer specs, CUDA backend path checks.

### Domain 10: Security & Packaging Audit
* Subprocess command sanitation (no shell injection in FFmpeg or Python worker).
* License verification (`LICENSE`, `THIRD_PARTY_LICENSES.md`, `NOTICE.md`).
* Model download checksum verification.

### Domain 11: Release Candidate Sign-Off
* Packaging targets inspection.
* Version consistency across `package.json`, `Cargo.toml`, and `tauri.conf.json`.
* Final defect resolution check and sign-off recommendation.

# CorridorKey 2.0 Desktop — Phase 11 QA & Release Audit

## 1. Executive Summary

CorridorKey 2.0 Desktop has progressed through Phases 1–10, establishing a cross-platform desktop application using Tauri 2, React, TypeScript, Rust, Python 3.11, PyTorch, and FFmpeg.

Phase 11 initiates the rigorous Quality Assurance, Regression Testing, Cross-Platform Release Validation, and Release Candidate sign-off process. The objective is to identify defects, validate end-to-end user workflows, measure performance, stress-test high-resolution pipelines, and remediate release-blocking issues.

---

## 2. Test Coverage & Module Risk Assessment

| Subsystem | Source Path | Test Coverage Status | Risk Level | Key Vulnerabilities / Failure Modes |
| :--- | :--- | :--- | :--- | :--- |
| **Python Worker & IPC** | `engine/desktop_api/` | High (`test_engine_service.py`, `verify_phase3.py`) | **Medium** | Stdin/stdout pipe deadlocks, unhandled JSON-RPC parse exceptions on crash. |
| **AI Inference & Tensor Pool**| `engine/inference/` | High (`verify_inference.py`, `verify_phase9.py`) | **High** | GPU VRAM spikes on large batch sizes, MPS float16 precision quirks, fallback recovery. |
| **Video Decoding & Streaming**| `engine/video/` | High (`test_video_pipeline.py`, `verify_phase4.py`) | **High** | Variable frame rate (VFR) drift, missing PTS timestamps, corrupted container headers. |
| **Alpha & Colour Engine** | `engine/color/` | Medium | **Critical** | Premultiplication mismatch, gamma-corrected matte banding, green spill bleeding. |
| **VFX Compositing & Nodes** | `engine/vfx/` | High (`test_vfx_compositing.py`, `verify_phase8.py`) | **Medium** | Circular node graph cycles, non-contiguous mask point coordinates. |
| **Multi-Track Timeline** | `engine/timeline/` | High (`test_timeline_engine.py`, `verify_phase6.py`) | **Medium** | Ripple delete boundary rounding, audio desync on non-standard sample rates. |
| **Project Serialization** | `engine/project/` | High (`test_project_serialization.py`, `verify_phase7.py`)| **Low** | Malformed JSON schema version parsing, relative file path breakage during migration. |
| **Hardware Codec Exporters** | `engine/export/` | High (`verify_phase4.py`, `verify_phase9.py`) | **Medium** | ProRes 4444 16-bit alpha preservation, missing external FFmpeg binaries. |
| **Packaging & First-Run** | `engine/packaging/` | High (`verify_phase10.py`) | **Low** | Write permissions in restricted user application data directories. |
| **React UI & WebGL Viewport** | `apps/desktop/src/` | High (Vite compilation, state unit coverage) | **Low** | React re-render churn during high-FPS timeline scrubbing. |

---

## 3. Known Defects & Edge Cases

1. **VFR (Variable Frame Rate) Drift:** Video containers with non-constant frame rates can exhibit timestamp drift if frame counts are strictly deduced from duration multiplied by nominal FPS.
2. **Audio Multiplexing Edge Case:** Audio tracks encoded with non-standard sample rates (e.g. 22.05 kHz or 96 kHz) can cause FFmpeg to fail muxing into ProRes containers unless resampled to 48 kHz.
3. **Alpha Matte Premultiplication Drift:** Applying colour grading nodes before un-premultiplying alpha causes dark halos around fine hair and motion-blurred edges.
4. **Platform Availability Constraints:** Host machine runs Darwin arm64 (macOS Apple Silicon). Windows x64 testing must be verified via architecture validation, CI build matrices, and mock simulation without fabricating physical runtimes.

---

## 4. Release Blockers Definition (P0 / P1)

* **P0 — Critical (Release Blocker):**
  - Application crash or hung process during standard inference or playback.
  - Silent project file corruption or loss of user work during autosave.
  - Security vulnerabilities (unrestricted file execution, command injection via filename).
* **P1 — High (Release Blocker):**
  - Failure to export ProRes 4444 or VP9 with functional alpha channel.
  - Severe audio desynchronization (>2 frames over 10 seconds).
  - Failure of the First-Run Setup Wizard to discover Python or FFmpeg when installed.

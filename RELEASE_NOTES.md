# CorridorKey 2.0 Desktop — Release Notes (v2.0.0-rc1)

We are proud to present **CorridorKey 2.0 Desktop Release Candidate 1 (v2.0.0-rc1)**.

CorridorKey 2.0 Desktop combines the breakthrough CorridorKey 2.0 AI video keying and rotoscoping engine with a native, professional desktop editing and compositing studio for macOS and Windows.

---

## What's Included

### 1. Standalone Native Desktop Experience
* No Python terminal commands, git clone workflows, or manual package troubleshooting required for end users.
* High-performance native windowing and hardware telemetry built with Tauri 2 and Rust.
* Professional Adobe-inspired dark interface with custom panel resizing, keyboard shortcuts (Space, Arrow keys), and real-time state persistence.

### 2. Transformer-Native AI Inference
* Dual-stage inference combining the CorridorKey v2 core transformer with NVIDIA C-RADIO (visual feature extraction), Microsoft MoGe-2 (monocular surface normals and geometry), and DeepMind Recurrent Video MAE (temporal recurrence).
* Direct acceleration on Apple Silicon GPUs via Apple Metal (`mps`) and NVIDIA GPUs via CUDA.

### 3. Professional Multi-Track Timeline & VFX Compositing
* Non-destructive multi-track video and audio editing with rational timebases and SMPTE timecode support.
* Vector masking with interactive Bezier and polygon curves.
* 10-effect stack (Gaussian blur, sharpening, glow, drop shadow, noise, film grain, vignette, hue/saturation, color grade, and despill).
* Directed Acyclic Graph (DAG) node-based compositing with cycle detection and automatic topological execution.

### 4. Broadcast Video Pipeline & Transparent Codecs
* Apple ProRes 4444 (10-bit with full alpha preservation).
* VP9 WebM (transparent web video).
* QuickTime Animation (QTRLE).
* 16-bit RGBA PNG Sequences and OpenEXR export.

### 5. Production Reliability & Recovery
* Native `.ckproj` schema (`v1.1.0`) with atomic disk writes and schema forward migration.
* Automatic background autosaves with retention limits.
* Disaster recovery detection after crashes.
* Missing media relocation and folder batch relinking.

---

## Release Artifacts

| Platform | File Name | Architecture | Installation Mode |
| :--- | :--- | :--- | :--- |
| **macOS Apple Silicon** | `CorridorKey-2.0.0-aarch64.dmg` | `arm64` (M1–M5) | Drag to `/Applications` |
| **Windows 10/11** | `CorridorKey_2.0.0_x64-setup.exe` | `x86_64` | NSIS Per-User (`currentUser`) |

*All builds include the 5-step First-Run Setup Wizard and in-app System Diagnostics console.*

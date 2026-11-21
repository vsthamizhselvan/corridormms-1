# Changelog — CorridorKey 2.0 Desktop

All notable changes to CorridorKey 2.0 Desktop are documented in this file in accordance with [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0-rc1] - 2026-11-21

### Added
* **Tauri 2 Native Desktop Shell:** Cross-platform windowing, hardware telemetry, native file dialogs, and IPC bridge.
* **AI Matting Engine Integration:** Two-stage transformer inference integrating CorridorKey v2 with NVIDIA C-RADIO, Microsoft MoGe-2, and DeepMind Recurrent Video MAE (RVM).
* **Hardware Acceleration:** Apple Metal Performance Shaders (`mps`) for Apple Silicon M1–M5 and NVIDIA CUDA / Tensor Core acceleration for Windows 10/11.
* **Interactive GPU Viewport:** Real-time WebGL2 multi-mode compositing viewport with split-screen comparison and color space management.
* **Non-Destructive Multi-Track Timeline:** Professional editing timeline with rational timebases, SMPTE timecodes, trimming, razor split, ripple deletion, snapping, and audio waveform mixing.
* **Advanced VFX Compositing:** Vector masking (Bezier, polygon, rectangle, ellipse), 10-effect non-destructive stack, layer blend modes, and DAG node graph execution.
* **Broadcast Video Pipeline:** High-throughput frame extraction and transparent export supporting Apple ProRes 4444 (10-bit with alpha), VP9 WebM (YUVA420p), QuickTime Animation (QTRLE), OpenEXR, and PNG sequences.
* **Project Serialization & Recovery:** Native `.ckproj` schema (`v1.1.0`) with atomic saves, background autosave rotation, crash recovery detection, and batch media relinking.
* **Production Packaging & Setup Wizard:** Turnkey installers for Windows (NSIS) and macOS (DMG) with an interactive 5-step First-Run Setup Wizard and in-app Diagnostics console.
* **Comprehensive Quality Assurance:** 118 automated tests passing across 11 verification phases with 100% pass rate.

### Security & Compliance
* Full compliance with Corridor Key Licence Version 2.0 and third-party foundation model licenses.
* Subprocess argument sanitization eliminating shell injection risks.
* Cryptographic Base64 MD5 and SHA-256 checksum verification on all downloaded model assets.

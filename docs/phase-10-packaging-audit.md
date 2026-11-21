# CorridorKey 2.0 Desktop — Phase 10 Packaging Audit

## 1. Executive Summary

CorridorKey 2.0 Desktop has completed Phases 1 through 9, creating an end-to-end AI VFX keying and compositing system powered by Tauri 2, React, TypeScript, Rust, Python, PyTorch, and FFmpeg.

Phase 10 evaluates and establishes the complete packaging, distribution, and runtime bootstrapping architecture required to deliver CorridorKey 2.0 Desktop as an easy-to-install, standalone application for **Windows 10/11 (x64 with NVIDIA RTX acceleration)** and **macOS (Apple Silicon M1–M5 with Apple Metal/MPS acceleration)** without requiring users to install Python, Node.js, Rust, or manual AI libraries.

---

## 2. Component-by-Component Packaging Audit

### 2.1 Tauri 2 Configuration & Bundle Targets
* **Current State:**
  * `tauri.conf.json` defines version `2.0.0`, identifier `com.corridorkey.desktop`, window settings, and basic bundle targets.
  * Application icons exist in `apps/desktop/src-tauri/icons/` (`32x32.png`, `128x128.png`, `icon.icns`, `icon.ico`, `icon.png`).
* **Required Packaging Enhancements:**
  * **Windows:** Configure NSIS (`.exe` installer) with desktop shortcuts, Start Menu entry, custom install directory (`%LocalAppData%/Programs/CorridorKey 2.0` or `Program Files`), uninstaller, and file association for `.ckproj` (CorridorKey Project).
  * **macOS:** Configure `.app` and `.dmg` bundling with Retina window layout, Application folder symlink, hardened runtime entitlements, and bundle metadata.
  * Register file association for `.ckproj` with MIME `application/x-corridorkey-project`.

### 2.2 Python AI Engine & PyTorch Runtime
* **Current State:**
  * Development operates via a local Python 3.11 virtualenv (`.venv`).
  * PyTorch 2.15.0 with Metal MPS is active on macOS; CUDA is targeted for Windows.
  * Worker protocol communicates over bidirectional JSON-RPC stdin/stdout (`engine/desktop_api/main.py`).
* **Packaging Challenge:**
  * End users do not have Python 3.11 or PyTorch installed.
  * Bundling a 3GB PyTorch wheel inside the installer payload causes bloated installers and installation timeouts.
* **Packaging Solution:**
  * Support a dual-strategy **Managed Python Runtime**:
    1. **Portable Embedded Python Runtime**: Standalone distribution layout using python-build-standalone (`cpython-*-portable`).
    2. **Managed Virtualenv Bootstrapper**: Automated discovery of existing local Python 3.10-3.12 or zero-config download of isolated embedded Python environment with pre-verified wheels.
  * Clear isolation: Runtime is kept strictly inside application data (`~/Library/Application Support/CorridorKey/python_runtime` on macOS, `%LocalAppData%/CorridorKey/python_runtime` on Windows). System Python is never polluted.

### 2.3 AI Model Weights & Licensing Constraints
* **Current State:**
  * The original CorridorKey 2.0 project uses:
    * `nikopueringer/CorridorKey2.0`: `corridorkey_v2.safetensors`, `foundation_stats.safetensors`
    * `nvidia/C-RADIOv4-SO400M`: NVIDIA Open Model License
    * `Ruicheng/moge-2-vitb-normal`: MoGe-2 ViT-B (Microsoft MIT)
    * `Google DeepMind representations4d`: RVM small (CC-BY 4.0)
* **Licensing Constraint:**
  * The CorridorKey Licence Version 2.0 specifically stipulates:
    * Commercial redistribution of model weights bundled for sale is strictly forbidden.
    * Foundation models must not be redistributed directly in third-party packages; they must be fetched from original publishers under their respective licenses.
* **Packaging Solution:**
  * Model weights must **not** be baked directly into the initial ~150MB installer binary.
  * Implement an in-app **First-Run Model Downloader & Verification System**:
    * Authenticated fetch from official Hugging Face & Google Cloud storage sources.
    * SHA256 / MD5 integrity checking with resume capability on interrupted connections.
    * Corruption detection and repair.

### 2.4 FFmpeg & FFprobe Integration
* **Current State:**
  * Engine invokes system `ffmpeg` and `ffprobe` for frame extraction, probe metadata, and multi-format export.
  * Hardware acceleration supports `videotoolbox` (macOS), `cuda` / `nvenc` (Windows), and `cpu` fallback.
* **Packaging Solution:**
  * Detect system FFmpeg if present and compatible (version >= 5.0 with ProRes, VP9, NVENC/VideoToolbox).
  * Provide managed staging of statically-linked FFmpeg/FFprobe binaries in the application resource directory (`resources/bin/ffmpeg`).

### 2.5 First-Run Experience & User Guidance
* **Current State:**
  * Application boots directly to the editing workspace. If Python or models are missing, inference fails or requires manual shell execution.
* **Packaging Solution:**
  * Interactive **First-Run Setup Wizard**:
    1. System compatibility validation (OS, CPU cores, RAM, GPU/Metal/CUDA).
    2. Managed Python runtime status check & bootstrap.
    3. AI Model download & checksum verification.
    4. FFmpeg codec validation test.
    5. Ready screen with option to load sample project or create a new project.

### 2.6 Logging, Diagnostics & Telemetry
* **Packaging Solution:**
  * Production logging subsystem writing rotated logs to standard user data directories.
  * Dedicated **System Diagnostics & Logs Modal** in the desktop UI:
    * Copy diagnostic report to clipboard.
    * Export complete diagnostic bundle (`.json` / `.log`) for support.
    * Clear caches and inspect memory pressure.

---

## 3. Packaging Compatibility Matrix

| Platform | Installer Format | Architecture | Acceleration Backend | Model Storage Path |
| :--- | :--- | :--- | :--- | :--- |
| **Windows 10/11** | NSIS (`.exe`) & MSI | x86_64 | NVIDIA CUDA / NVENC / CPU | `%LocalAppData%\CorridorKey\models` |
| **macOS 12+** | DMG & `.app` Bundle | Apple Silicon (arm64) | Apple Metal (MPS) / VideoToolbox | `~/Library/Application Support/CorridorKey/models` |

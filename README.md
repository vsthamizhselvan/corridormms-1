# CorridorKey 2.0 Desktop

<div align="center">

![CorridorKey 2.0 Desktop Logo](apps/desktop/src-tauri/icons/128x128@2x.png)

**Professional Standalone AI Video Keying, Rotoscoping & Multi-Track VFX Compositing Desktop Application**

[![License](https://img.shields.io/badge/License-CorridorKey_v2.0-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-macOS_Apple_Silicon_%7C_Windows_10%2F11-brightgreen.svg)](#system-requirements)
[![Version](https://img.shields.io/badge/Release-v2.0.0--rc1-orange.svg)](CHANGELOG.md)
[![Backend](https://img.shields.io/badge/Acceleration-Metal_MPS_%7C_NVIDIA_CUDA-purple.svg)](#hardware-acceleration)

</div>

---

## 1. Overview

**CorridorKey 2.0 Desktop** is a native, standalone, cross-platform VFX desktop application integrating the open-source **CorridorKey 2.0** AI matting architecture into a modern Adobe-inspired visual studio.

Built with **Tauri 2**, **React 18**, **TypeScript**, **Rust**, **Python 3.11**, **PyTorch**, and **FFmpeg**, CorridorKey 2.0 Desktop gives filmmakers, 3D artists, and visual effects professionals high-throughput green-screen extraction, sub-pixel alpha matte refinement, non-destructive multi-track timeline editing, and broadcast-grade transparent video export—without requiring manual terminal setup or cloud subscription paywalls.

> **Upstream Attribution:** Built upon the CorridorKey 2.0 AI video keying system developed by Niko Pueringer and the Corridor Digital team. See [NOTICE.md](NOTICE.md) and [LICENSE](LICENSE).

---

## 2. Key Features

* **AI Foreground & Alpha Extraction:** Transformer-native two-stage matting combining CorridorKey v2 with NVIDIA C-RADIO, Microsoft MoGe-2, and DeepMind Recurrent Video MAE (RVM).
* **Hardware Acceleration:** Native Apple Metal Performance Shaders (`mps`) on Apple Silicon (M1–M5) and NVIDIA CUDA / Tensor Core acceleration on Windows 10/11.
* **GPU-Accelerated Interactive Viewport:** Real-time WebGL2 rendering pipeline with split-screen comparison (Original, Processed Foreground, Alpha Matte, Background Plate, Final Composite).
* **Multi-Track Timeline Editing:** Professional non-destructive timeline with rational broadcast timebases, SMPTE timecodes, clip trimming, razor split, ripple deletion, magnetic snapping, and audio waveform mixing.
* **Advanced VFX Compositing & Node Engine:** Vector masking (Bezier, polygon, rectangle, ellipse), 10-effect stack (blur, sharpen, glow, grain, shadow, vignette), layer blend modes, and DAG node graph execution.
* **Broadcast-Grade Export Pipeline:** High-throughput transparent video rendering supporting Apple ProRes 4444 (10-bit with alpha), VP9 WebM (YUVA420p), QuickTime Animation (QTRLE), OpenEXR, and 16-bit PNG sequences.
* **Robust Project Persistence:** Native `.ckproj` schema (`v1.1.0`) with atomic saves, background autosave with retention pruning, crash recovery detection, and batch media relinking.
* **Managed Isolated Runtime:** Self-contained Python virtual environment operating inside user application data, leaving host Python environments completely untouched.

---

## 3. System Requirements

| Specification | macOS (Apple Silicon) | Windows 10/11 (x64) |
| :--- | :--- | :--- |
| **Operating System** | macOS 12.0 (Monterey) through 15.0+ (Sequoia) | Windows 10 (64-bit 20H2+) or Windows 11 |
| **Processor** | Apple Silicon M1, M2, M3, M4, or M5 | Intel Core i7 / AMD Ryzen 7 (8+ cores) |
| **Memory (RAM)** | 16 GB Unified Memory (32 GB for 4K) | 16 GB RAM minimum (32 GB recommended) |
| **Graphics (GPU)** | Apple Metal GPU (Unified Memory) | NVIDIA RTX 2060+ (RTX 3060/4070/5060, 8GB+ VRAM) |
| **Disk Storage** | 10 GB free APFS SSD space | 10 GB free NTFS SSD space |
| **Acceleration** | Apple Metal Performance Shaders (`mps`) | NVIDIA CUDA 12+ / Tensor Cores |

---

## 4. Installation & First-Run Setup

### macOS Installation
1. Download `CorridorKey-2.0.0-aarch64.dmg` from the private releases.
2. Open the Disk Image and drag `CorridorKey 2.0.app` to `/Applications`.
3. Launch CorridorKey from Launchpad or Applications.
4. On first launch, the **Initial Setup Wizard** automatically validates your hardware, initializes the isolated Python runtime, checks model weights, and verifies FFmpeg codecs.

### Windows 10/11 Installation
1. Download `CorridorKey_2.0.0_x64-setup.exe`.
2. Run the installer (installs per-user to `%LocalAppData%\Programs\CorridorKey 2.0` without requiring Administrator privileges).
3. Launch CorridorKey from the Start Menu or Desktop shortcut.
4. Follow the Initial Setup Wizard.

*For detailed platform guides, see [docs/macos-installation.md](docs/macos-installation.md) and [docs/windows-installation.md](docs/windows-installation.md).*

---

## 5. Development & Build from Source

### Prerequisites
* **Node.js:** v20.x or higher & npm
* **Rust:** Stable toolchain (`rustup target add aarch64-apple-darwin` or `x86_64-pc-windows-msvc`)
* **Python:** 3.11.x with PyTorch
* **FFmpeg:** v5.0+ installed and on system PATH

### Building
```bash
# 1. Clone repository
git clone https://github.com/CorridorKey/CorridorKey-2.0-Desktop.git
cd CorridorKey-2.0-Desktop

# 2. Setup Python Virtual Environment
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r vendor/CorridorKey2.0/requirements.txt

# 3. Install Frontend Dependencies & Build
cd apps/desktop
npm install
npm run build
cd ../..

# 4. Run Desktop Application in Development
cd apps/desktop
npm run tauri dev

# 5. Run Full Verification Suite
python tests/verify_phase11.py
```

---

## 6. Project Architecture & Documentation Index

* [Architecture Overview](docs/phase-10-architecture.md)
* [QA & Validation Final Report](docs/phase-11-final-report.md)
* [Managed Python Runtime Packaging](docs/python-engine-packaging.md)
* [AI Model Management & Integrity](docs/model-management.md)
* [FFmpeg Codec Engine & Acceleration](docs/ffmpeg-packaging.md)
* [Open-Source Licensing & Compliance](docs/open-source-compliance.md)
* [Release Candidate Details](docs/phase-11-release-candidate.md)

---

## 7. Open-Source Licensing & Commercial Terms

CorridorKey 2.0 Desktop is licensed under the **Corridor Key Licence Version 2.0** (based on CC BY-NC-SA 4.0 with additional licensor terms):
* **Your Content is Yours:** All output videos, images, and visual effects you render with this tool belong 100% to you for commercial and personal use.
* **No Closed Repackaging or Resale:** You may not repackage, redistribute, or sell this software, code, or model weights as a commercial product.
* **Derivatives Freely Accessible:** Any public derivative work incorporating this software must be made freely accessible to the public.
* **Large Organizations ($20M+ Revenue):** Commercial entities exceeding US $20,000,000 gross annual revenue must purchase seat licenses from [corridorkey.com](https://corridorkey.com).

See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md) for full legal text and third-party notices.

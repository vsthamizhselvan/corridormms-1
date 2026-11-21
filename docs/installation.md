# CorridorKey 2.0 Desktop — Installation & Setup Guide

This guide details the complete, step-by-step installation instructions for building, running, and developing **CorridorKey 2.0 Desktop** across Windows (NVIDIA RTX GPUs including RTX 5060) and macOS (Apple Silicon M1–M5).

---

## 1. System Requirements

### Windows (Target: NVIDIA RTX GPU Workstations)
- **Operating System:** Windows 10 (Build 19044+) or Windows 11 (64-bit).
- **GPU:** NVIDIA GeForce RTX 30-series, 40-series, or 50-series (e.g. **RTX 5060 8GB/16GB**).
- **VRAM:**
  - Minimum: 4 GB VRAM (720p / 1080p in low-VRAM mode).
  - Recommended: 8 GB+ VRAM (1080p / 1440p standard inference).
  - Production 4K: 12 GB+ VRAM.
- **NVIDIA Driver:** Version 570.xx or newer (supporting CUDA 12.8+).
- **Disk Space:** 30 GB free SSD storage (5 GB model weights + scratch cache).

### macOS (Target: Apple Silicon Workstations)
- **Operating System:** macOS Sonoma (14.0+) or macOS Sequoia (15.0+).
- **Chip:** Apple Silicon M1, M2, M3, M4, or M5 (Standard, Pro, Max, or Ultra).
- **Unified Memory:**
  - Minimum: 16 GB unified memory.
  - Recommended: 32 GB or 64 GB+ for 4K video processing.
- **Acceleration:** Apple Metal Performance Shaders (MPS) / Multi-threaded CPU fallback.

---

## 2. Windows 10/11 Setup (RTX 5060 / CUDA 12.8)

### Step 2.1: Install Prerequisites
1. **Git:** Download and install [Git for Windows](https://git-scm.com/download/win).
2. **Python 3.11:**
   - Download Python 3.11.9 from [python.org](https://www.python.org/downloads/release/python-3119/).
   - **Crucial:** Check "Add python.exe to PATH" during installation.
3. **FFmpeg:**
   - Install via winget:
     ```powershell
     winget install Gyan.FFmpeg
     ```
   - Verify `ffmpeg -version` works in PowerShell.
4. **Node.js (LTS):**
   - Download and install Node.js 20+ from [nodejs.org](https://nodejs.org/).
5. **Rust & Tauri 2 Prerequisites:**
   - Install Microsoft C++ Build Tools (via Visual Studio Installer with "Desktop development with C++").
   - Install `rustup` from [rustup.rs](https://rustup.rs/).
   - Restart your terminal and check:
     ```powershell
     rustc --version
     cargo --version
     ```

### Step 2.2: Setup Python AI Environment with CUDA 12.8
The NVIDIA RTX 5060 is based on the Blackwell architecture (sm_120) and requires CUDA 12.8+ capable PyTorch wheels.

Open PowerShell in the project directory:
```powershell
# 1. Create a dedicated virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Upgrade pip and build tools
python -m pip install --upgrade pip setuptools wheel

# 3. Install PyTorch with CUDA 12.8 support
# CorridorKey 2.0 is validated with torch 2.9+ / cu128:
pip install torch==2.9.1 torchvision==0.24.1 --index-url https://download.pytorch.org/whl/cu128

# 4. Install CorridorKey 2.0 core dependencies
pip install -r vendor/CorridorKey2.0/requirements.txt

# 5. Verify CUDA acceleration and GPU detection
python -c "import torch; print('CUDA Available:', torch.cuda.is_available()); print('Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None'); print('Capability:', torch.cuda.get_device_capability(0) if torch.cuda.is_available() else 'None')"
```

### Step 2.3: Download Neural Network Weights
Download CorridorKey 2.0 weights and foundation models (~5 GB total):
```powershell
python vendor/CorridorKey2.0/scripts/download_weights.py
```
This automatically populates:
- `vendor/CorridorKey2.0/weights/corridorkey_v2.safetensors`
- `vendor/CorridorKey2.0/weights/foundation_stats.safetensors`
- `vendor/CorridorKey2.0/vfms/cradio/C-RADIOv4-SO400M/` (NVIDIA)
- `vendor/CorridorKey2.0/vfms/moge/model.pt` (Microsoft)
- `vendor/CorridorKey2.0/vfms/rvm/pretrain_rvm_small16_256_204031069.npz` (Google DeepMind)

---

## 3. macOS Setup (Apple Silicon M1–M5)

### Step 3.1: Install Prerequisites
1. **Homebrew:** If not already installed:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
2. **System Dependencies:**
   ```bash
   brew install python@3.11 ffmpeg node
   ```
3. **Rust Toolchain:**
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   source "$HOME/.cargo/env"
   ```

### Step 3.2: Setup Python AI Environment for macOS
```bash
# 1. Create virtual environment with Python 3.11
python3.11 -m venv .venv
source .venv/bin/activate

# 2. Upgrade pip
pip install --upgrade pip setuptools wheel

# 3. Install PyTorch with Apple Silicon MPS support
pip install torch torchvision

# 4. Install dependencies (handle git requirement for utils3d)
pip install -r vendor/CorridorKey2.0/requirements.txt

# 5. Verify Apple Metal MPS detection
python -c "import torch; print('MPS Available:', torch.backends.mps.is_available()); print('MPS Built:', torch.backends.mps.is_built())"
```

### Step 3.3: Download Neural Network Weights
```bash
python vendor/CorridorKey2.0/scripts/download_weights.py
```

---

## 4. Model Verification & Smoke Test

To verify that model weights, PyTorch runtime, and foundational dependencies are intact:

```bash
# Test runtime checkpoint integrity
python vendor/CorridorKey2.0/scripts/smoke_test_runtime.py

# Test engine hardware detection
python engine/detection/hardware.py
```

---

## 5. Desktop Application Development Workflow

### Step 5.1: Install Desktop Frontend Dependencies
```bash
cd apps/desktop
npm install
```

### Step 5.2: Launch in Development Mode
```bash
# Runs React dev server + Tauri 2 native desktop window
npm run tauri dev
```

### Step 5.3: Production Build
```bash
# Compiles React frontend and builds native installer (.exe on Windows, .dmg on macOS)
npm run tauri build
```

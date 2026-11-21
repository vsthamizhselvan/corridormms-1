# CorridorKey 2.0 Desktop — Phase 10 Architecture: Production Packaging & Distribution

## 1. High-Level Architecture Overview

CorridorKey 2.0 Desktop's distribution architecture is engineered to separate the lightweight native desktop application shell (~80–120 MB) from heavyweight machine learning runtimes (~2.5 GB) and multi-gigabyte foundation model weights (~4.5 GB), ensuring fast downloads, reliable updates, and compliance with upstream licensing.

```
+----------------------------------------------------------------------------------+
|                             Tauri 2 Desktop Application Shell                    |
|                                                                                  |
|  [ React 18 / TypeScript VFX UI ]  <--->  [ Tauri Rust IPC / Process Manager ]   |
|         |                                              |                         |
|         v                                              v                         |
|   First-Run Setup Wizard                 System Diagnostics & Log Rotator        |
+----------------------------------------------------------------------------------+
          |                                              |
          v                                              v
+-----------------------------+               +------------------------------------+
| Managed Python Runtime      |               | Managed FFmpeg Subsystem           |
|  * Embedded / Bootstrapped  |               |  * System PATH or Bundled Static   |
|  * PyTorch (MPS / CUDA)     |               |  * Codec capability check          |
|  * Zero system pollution    |               |  * ProRes 4444, VP9, H.264/265     |
+-----------------------------+               +------------------------------------+
          |
          v
+----------------------------------------------------------------------------------+
| AI Model Management & Integrity Verifier                                         |
|  * Official Hugging Face / GCS endpoints (CorridorKey v2, C-RADIO, MoGe-2, RVM)  |
|  * Chunked streaming download with SHA-256 / MD5 validation                      |
|  * Corruption detection, auto-repair, and local storage orchestration            |
+----------------------------------------------------------------------------------+
```

---

## 2. Directory & Path Specification

### 2.1 macOS Layout
* **Application Bundle:** `/Applications/CorridorKey 2.0.app`
* **Executable:** `/Applications/CorridorKey 2.0.app/Contents/MacOS/corridorkey-desktop`
* **Embedded Resources:** `/Applications/CorridorKey 2.0.app/Contents/Resources/`
* **User Application Support:** `~/Library/Application Support/CorridorKey/`
  * `python_runtime/`: Isolated Python 3.11 virtual environment or embedded framework.
  * `models/`: Weights (`weights/`, `vfms/`).
  * `logs/`: Application, engine, and FFmpeg logs (`corridorkey.log`, `engine.log`).
  * `autosave/`: Automatic snapshot storage (`.ckproj.bak`).
  * `cache/`: Timeline playback frame cache and scratch buffers.

### 2.2 Windows 10/11 Layout
* **Installation Root:** `%LocalAppData%\Programs\CorridorKey 2.0\` (per-user) or `C:\Program Files\CorridorKey 2.0\` (per-machine)
* **Executable:** `corridorkey-desktop.exe`
* **User AppData:** `%LocalAppData%\CorridorKey\`
  * `python_runtime\`: Managed Python environment with CUDA-enabled PyTorch.
  * `models\`: Pinned model weights.
  * `logs\`: Production logs with automatic rotation.
  * `autosave\`: Project autosave recovery snapshots.
  * `cache\`: Decoded frame disk cache.

---

## 3. Managed Python Runtime Lifecycle

1. **Detection Phase:**
   Upon launch, the Rust backend invokes `detect_python_runtime()`.
   It checks:
   - Configured custom Python path in user settings.
   - Isolated managed environment in user application data.
   - Bundled embedded python directory in app resources.
   - Compatible system Python 3.10–3.12 with PyTorch installed.
2. **Bootstrap Phase (if missing):**
   - The First-Run Setup Wizard prompts the user.
   - The runtime bootstrapper initializes the virtual environment and installs required pinned packages without needing system sudo or admin rights.
3. **Execution Phase:**
   - The Rust `AiProcessManager` spawns the Python worker (`engine/desktop_api/main.py`) using the verified interpreter binary.
   - Health check ping/pong confirms bidirectional communication over IPC.

---

## 4. Model Weights Download & Verification Flow

1. **Catalog Specification:**
   Model metadata is strictly defined in `engine/packaging/model_downloader.py`:
   - `corridorkey_v2`: Hugging Face `nikopueringer/CorridorKey2.0/corridorkey_v2.safetensors`
   - `foundation_stats`: Hugging Face `nikopueringer/CorridorKey2.0/foundation_stats.safetensors`
   - `cradio`: Hugging Face `nvidia/C-RADIOv4-SO400M` (commit `c0457f5`)
   - `moge`: Hugging Face `Ruicheng/moge-2-vitb-normal` (commit `ca5f0e0`, `model.pt`)
   - `rvm`: GCS `pretrain_rvm_small16_256_204031069.npz` (MD5 `ZJb6kj8+tasiJbVeplXu7Q==`)
2. **Download Execution:**
   - Atomic `.part` temporary files prevent partial corrupt downloads from masquerading as complete models.
   - SHA-256 and MD5 verification verifies byte-for-byte integrity before renaming into active directories.

---

## 5. Security & Isolation Principles

- **No Arbitrary Code Execution:** The Python worker only executes pre-audited engine commands received over structured JSON-RPC.
- **Sandboxed File Access:** All media and project reads/writes are restricted to valid project paths and designated cache directories.
- **Hardened Runtime on macOS:** Signed with macOS hardened runtime and entitlements for Apple Silicon Neural Engine / Metal access.
- **Zero Registry Bloat on Windows:** All user configurations are self-contained in standard `%LocalAppData%\CorridorKey`. Clean uninstallation deletes all associated runtime assets upon request.

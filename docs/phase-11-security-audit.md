# CorridorKey 2.0 Desktop — Phase 11 Security & Licensing Audit

## 1. Security Architecture & Boundary Verification

A comprehensive security audit of CorridorKey 2.0 Desktop was performed across dependencies, file I/O boundaries, subprocess invocations, and license compliance.

---

## 2. Security Findings & Protections

### 2.1 File System & Path Traversal Protection
* **Vulnerability Checked:** Arbitrary path writing via malicious `.ckproj` file references (e.g. `../../etc/passwd`).
* **Protections Verified:**
  - `engine/project/io_atomic.py` enforces canonical path resolution and validates project boundaries.
  - Rust Tauri commands (`read_project_file`, `save_project_file`, `save_project_atomic`) validate file extensions and paths before invoking system file APIs.

### 2.2 Subprocess Invocation Safety
* **Vulnerability Checked:** Command injection through media file names containing shell meta-characters (e.g. `; rm -rf /`, `$(whoami)`).
* **Protections Verified:**
  - All FFmpeg, FFprobe, and Python worker executions use direct array argument lists (e.g. `subprocess.run(["ffmpeg", "-i", path, ...])`).
  - Shell execution (`shell=True`) is strictly avoided across the entire codebase.

### 2.3 Model Weight Download & Supply Chain Security
* **Vulnerability Checked:** Man-in-the-middle tampering of foundation model weights during initial fetch.
* **Protections Verified:**
  - Pinned revisions and Base64 MD5 checksum verification in `engine/packaging/model_downloader.py`.
  - Atomic rename (`.part` $\rightarrow$ final destination) guarantees partial or corrupt downloads cannot be executed.

---

## 3. Open-Source & Upstream Licensing Compliance

* **Root License:** [LICENSE](file:///Volumes/VST%20SSD/corridor%20key%202.0/LICENSE) fully embodies the Corridor Key Licence Version 2.0 (CC BY-NC-SA 4.0 + additional terms from Corridor Digital LLC).
* **Attribution:** [NOTICE.md](file:///Volumes/VST%20SSD/corridor%20key%202.0/NOTICE.md) explicitly names Niko Pueringer and Corridor Digital LLC.
* **Foundation Notices:** [THIRD_PARTY_LICENSES.md](file:///Volumes/VST%20SSD/corridor%20key%202.0/THIRD_PARTY_LICENSES.md) accurately attributes NVIDIA C-RADIO, Microsoft MoGe-2, and DeepMind RVM.
* **Commercial Restrictions:** The application enforces no closed redistribution, no resale, and directs organizations $> \$20\text{M}$ revenue to purchase seats from Corridor Digital LLC.

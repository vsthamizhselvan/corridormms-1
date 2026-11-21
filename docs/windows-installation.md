# CorridorKey 2.0 Desktop — Windows Installation & Packaging Guide

## 1. System Requirements

* **Operating System:** Windows 10 (64-bit, version 20H2 or later) or Windows 11.
* **Processor:** Intel Core i7 / AMD Ryzen 7 (8+ physical cores recommended).
* **RAM:** 16 GB minimum (32 GB recommended for 4K video keying).
* **GPU:** NVIDIA GeForce RTX 2060 or newer (RTX 3060, 4070, 5060 recommended; 8 GB+ VRAM).
* **Disk Space:** 10 GB free SSD storage (for application, model cache, and frame buffer).

---

## 2. Installation Architecture

CorridorKey 2.0 Desktop for Windows is distributed as a standalone **NSIS installer (`.exe`)** and **MSI package**:

* **Per-User Installation (Default):**
  - Installs to `%LocalAppData%\Programs\CorridorKey 2.0\`.
  - Requires no Windows Administrator / UAC privileges.
* **Per-Machine Installation (Optional):**
  - Installs to `C:\Program Files\CorridorKey 2.0\`.
* **Shortcuts & File Associations:**
  - Creates Start Menu shortcut and optional Desktop icon.
  - Automatically associates `.ckproj` (CorridorKey Project) files with the application.
* **Uninstallation:**
  - Includes a clean uninstaller registered in Windows Settings > Apps & Features.
  - Prompts whether to keep or remove user models and cached render files.

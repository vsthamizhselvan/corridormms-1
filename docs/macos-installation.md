# CorridorKey 2.0 Desktop — macOS Installation & Packaging Guide

## 1. System Requirements

* **Operating System:** macOS Monterey (12.0), Ventura (13.0), Sonoma (14.0), or Sequoia (15.0+).
* **Architecture:** Apple Silicon (M1, M2, M3, M4, M5 series).
* **RAM:** 16 GB Unified Memory minimum (24 GB+ recommended for multi-stream 4K workflows).
* **Disk Space:** 10 GB free APFS storage.

---

## 2. Installation Process

CorridorKey 2.0 Desktop for macOS is distributed as a notarized Apple Silicon Disk Image (`.dmg`):

1. **Mounting:** Double-click `CorridorKey-2.0.0-aarch64.dmg`.
2. **Installation:** Drag the `CorridorKey 2.0.app` bundle into the `/Applications` folder alias.
3. **First Launch:**
   - Launch `CorridorKey 2.0` from Launchpad or Spotlight.
   - The application starts with native Apple Metal MPS hardware acceleration enabled out-of-the-box.
4. **Clean Removal:**
   - Drag `CorridorKey 2.0.app` from `/Applications` to Trash.
   - Optionally remove user preferences: `rm -rf ~/Library/Application\ Support/CorridorKey`.

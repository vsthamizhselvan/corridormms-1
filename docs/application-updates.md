# CorridorKey 2.0 Desktop — Versioning & Application Updates

## 1. Versioning Specification

CorridorKey 2.0 Desktop follows strict Semantic Versioning (`MAJOR.MINOR.PATCH`):
* **Desktop Application:** Current version **`2.0.0`** (defined in `package.json`, `Cargo.toml`, and `tauri.conf.json`).
* **Project Schema Version:** Current version **`1.1.0`** (`.ckproj` specification).
* **AI Engine Worker Protocol:** Version **`2.0`**.

---

## 2. Update Strategy & Verification

* **Tauri Native Updater Support:**
  - Configurable in `tauri.conf.json` with public ECDSA key signatures (`tauri-updater`).
  - Supports automatic update check on application startup.
* **Non-Destructive Migrations:**
  - Project files (`.ckproj`) retain schema versioning with automatic forward migrations (`engine/project/serializer.py`).
  - Model weights stored in user application data are preserved across application updates without requiring re-download.

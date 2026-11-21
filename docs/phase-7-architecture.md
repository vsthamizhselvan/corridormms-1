# Phase 7 Architecture — Project Serialization, Autosave & Recovery

## 1. System Overview

CorridorKey 2.0 Desktop Phase 7 implements a resilient, cross-platform persistence and recovery system for complete VFX and video editing projects. The architecture ensures atomic operations, non-blocking background autosaves, asset path portability, and crash resilience.

```
+-------------------------------------------------------------------------+
|                        React Desktop UI                                 |
|  - File Menu (New, Open, Save, Save As, Backup, Close)                  |
|  - Missing Media Dialog (Relink Single Asset / Batch Relink Folder)     |
|  - Recovery Modal (Restore Latest Autosave / Inspect Snapshots)         |
+------------------------------------+------------------------------------+
                                     |
               Zustand Project & Media Stores (Atomic State)
                                     |
+------------------------------------v------------------------------------+
|                       Tauri 2 Native Core (Rust)                        |
|  - save_project_atomic (fsync + atomic replace)                         |
|  - list_project_autosaves (scan .ck_autosaves/)                         |
|  - create_project_backup (timestamped snapshots in .ck_backups/)        |
|  - check_project_recovery (mtime comparison)                            |
+------------------------------------+------------------------------------+
                                     |
+------------------------------------v------------------------------------+
|                  Python Engine Services (`engine/project/`)             |
|                                                                         |
|  +--------------------+  +--------------------+  +--------------------+ |
|  | Schema & Migration |  | Serializer         |  | Atomic IO          | |
|  | - v1.0.0 Spec      |  | - Validation       |  | - fsync            | |
|  | - 0.9.0 -> 1.0.0   |  | - Security Filters |  | - os.replace       | |
|  +--------------------+  +--------------------+  +--------------------+ |
|                                                                         |
|  +--------------------+  +--------------------+                         |
|  | Media Manager      |  | Autosave Manager   |                         |
|  | - Relative Paths   |  | - Timer & Dirty    |                         |
|  | - Batch Relinking  |  | - Snapshot Pruning |                         |
|  +--------------------+  +--------------------+                         |
+-------------------------------------------------------------------------+
```

---

## 2. Atomic Writing Strategy

To eliminate project file truncation or corruption caused by operating system crashes, application termination, or unexpected drive disconnection:
1. Serialized project data is written to a hidden temporary file adjacent to the destination: `.<basename>.tmp.<uuid>`.
2. All memory buffers are flushed to disk followed by an `os.fsync()` / `file.sync_all()` system call.
3. The temporary file replaces the target project file using an atomic rename primitive (`os.replace` on POSIX and modern Windows NTFS).
4. If an error occurs at any point before the rename completes, the temporary file is unlinked, leaving the original saved project file completely untouched.

---

## 3. Dual-Path Portability Architecture

To ensure projects remain portable across drives, network mounts, and operating systems:
- **Relative Path:** Normalized relative to the `.ckproj` project file directory. Takes primary precedence when opening a project on a different machine or volume.
- **Absolute Path:** Full system path stored as a fallback.
- **Missing Asset Detection:** If neither relative nor absolute paths resolve on disk, the asset is tagged as `MISSING` and surfaced in the Missing Media Dialog for user-guided relinking.

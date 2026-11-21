# Autosave, Backup & Crash Recovery System — CorridorKey 2.0 Desktop

## 1. Autosave Architecture

CorridorKey 2.0 Desktop incorporates a background, non-blocking autosave subsystem:
- **Default Interval:** 3 minutes (configurable from 1 to 10 minutes in user preferences).
- **Dirty State Guard:** Autosave only triggers when `isDirty == true`, preventing redundant disk writes.
- **Dedicated Directory:** Autosave snapshots are preserved in a hidden folder adjacent to the project: `<project_dir>/.ck_autosaves/`.
- **Snapshot Naming:** `<project_name>_autosave_YYYYMMDD_HHMMSS_<microseconds>.ckproj`.
- **Retention Policy:** Automatically prunes snapshots older than the configured limit (default: 5 snapshots).

---

## 2. Manual Backup Snapshots

At any time, users can generate a dedicated timestamped backup via **File -> Backup Snapshot**:
- Backups are stored in `<project_dir>/.ck_backups/`.
- File naming: `<project_name>_backup_YYYYMMDD_HHMMSS_<microseconds>.ckproj`.
- Backups are permanent and are never automatically pruned.

---

## 3. Crash Recovery Detection

When a project file is opened:
1. `check_project_recovery` queries the project directory for `.ck_autosaves/`.
2. The latest autosave modification time ($T_{\text{auto}}$) is compared against the saved project modification time ($T_{\text{saved}}$).
3. If $T_{\text{auto}} > T_{\text{saved}} + 2\text{s}$, the **Recovery Modal** is displayed:
   - **Recover Latest Autosave Snapshot:** Restores the latest unsaved work into memory while keeping the original file intact until the user manually saves.
   - **Open Last Saved Project File:** Ignores the autosave snapshot and opens the last explicit user save.
   - **Inspect Snapshots:** Lists all available historical autosaves with timestamps and file sizes.

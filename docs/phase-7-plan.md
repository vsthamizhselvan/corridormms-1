# CorridorKey 2.0 Desktop — Phase 7 Implementation Plan
## Project Serialization, Autosave & Crash Recovery

**Phase:** Phase 7  
**Date:** November 2026  
**Status:** In Progress  

---

## 1. Architectural Inspection & Existing State

The CorridorKey 2.0 Desktop architecture spans:
1. **Frontend State (React + Zustand):**
   - `projectStore`: Project metadata (name, resolution, frame rate, color space, modified timestamp, file path, isDirty).
   - `timelineStore`: Tracks, clips, durations, undo/redo history, snapping, active tools.
   - `mediaStore`: Imported media list, asset IDs, paths, codecs, durations.
   - `inspectorStore`: Keying settings, matte adjustment parameters, 2D transform parameters.
   - `workspaceStore`: Panel widths, heights, and panel visibility.
   - `playbackStore`: Current playhead frame, total frames, framerate, loop mode.
2. **Backend Processing (Python `engine/`):**
   - `engine/timeline/`: `TimelineSequence`, `TrackItem`, `ClipItem`, `PropertyTrack`, `Keyframe`, `Timebase`.
   - `engine/color/`: Transfer functions and color management.
   - `engine/export/`: Professional export profiles (ProRes, DNxHR/QTRLE, VP9, OpenEXR, PNG).
3. **Desktop Native Layer (Tauri 2 + Rust):**
   - `commands.rs`: `read_project_file`, `save_project_file`, `probe_media_file`, `check_file_exists`.

---

## 2. Native Project Format Specification (`.ckproj`)

The native CorridorKey project format is a standardized JSON format with extension `.ckproj`.

```json
{
  "format": "corridorkey-project",
  "schema_version": "1.0.0",
  "generator": "CorridorKey 2.0 Desktop",
  "project": {
    "project_id": "proj-uuid-1234",
    "name": "VFX Shot 01",
    "width": 1920,
    "height": 1080,
    "frame_rate": 24.0,
    "timebase": { "numerator": 24, "denominator": 1 },
    "color_space": "Rec.709",
    "created_at": "2026-11-20T21:00:00Z",
    "modified_at": "2026-11-20T22:00:00Z"
  },
  "media_pool": [
    {
      "asset_id": "asset-uuid-5678",
      "name": "foreground_greenscreen.mov",
      "relative_path": "media/foreground_greenscreen.mov",
      "absolute_path": "/Volumes/VST SSD/projects/media/foreground_greenscreen.mov",
      "width": 1920,
      "height": 1080,
      "frame_rate": 24.0,
      "duration_frames": 240,
      "duration_seconds": 10.0,
      "codec": "PRORES",
      "file_size_bytes": 104857600
    }
  ],
  "timeline": {
    "duration_frames": 240,
    "current_frame": 0,
    "tracks": [
      {
        "track_id": "v1",
        "type": "video",
        "name": "Video 1",
        "visible": true,
        "locked": false,
        "muted": false,
        "solo": false,
        "order_index": 0,
        "clips": [
          {
            "clip_id": "clip-uuid-9999",
            "media_id": "asset-uuid-5678",
            "track_id": "v1",
            "name": "Action Take 1",
            "source_in": 0,
            "source_out": 240,
            "timeline_start": 0,
            "timeline_end": 240,
            "speed": 1.0,
            "volume": 1.0,
            "is_muted": false,
            "color_tag": "#0d9488",
            "properties": {
              "posX": { "name": "posX", "default_value": 0.0, "keyframes": [] },
              "posY": { "name": "posY", "default_value": 0.0, "keyframes": [] },
              "scale": { "name": "scale", "default_value": 100.0, "keyframes": [] },
              "rotation": { "name": "rotation", "default_value": 0.0, "keyframes": [] },
              "opacity": { "name": "opacity", "default_value": 100.0, "keyframes": [] }
            }
          }
        ]
      }
    ]
  },
  "settings": {
    "keying": {
      "hann_chunk": 96,
      "hann_stride": 48,
      "low_vram": false,
      "despill_strength": 0.7,
      "hint_mode": "first_frame",
      "hint_quality": 3
    },
    "matte": {
      "contrast": 1.0,
      "edge_refinement": 0.0,
      "invert": false,
      "alpha_threshold": 0.0
    },
    "viewer": {
      "display_mode": "composite",
      "background_type": "checkerboard",
      "background_color": "#000000",
      "gradient_color_a": "#1e293b",
      "gradient_color_b": "#0f172a",
      "compare_mode": "off",
      "wipe_position": 0.5,
      "alpha_mode": "premultiplied",
      "exposure": 0.0,
      "saturation": 1.0
    },
    "export": {
      "format": "prores4444",
      "resolution": "source",
      "color_space": "Rec.709",
      "include_alpha": true
    }
  },
  "workspace": {
    "left_panel_width": 300,
    "right_panel_width": 340,
    "bottom_panel_height": 260,
    "show_media_browser": true,
    "show_inspector": true,
    "show_timeline": true,
    "zoom_ratio": 1.5
  }
}
```

---

## 3. Atomic File Writes & Security

1. **Atomic Writing Pipeline:**
   - Write serialized payload to a temporary file in the same directory: `<filepath>.tmp.<pid>`.
   - Flush buffers and fsync to guarantee storage persistence.
   - Atomically replace target file using `std::fs::rename` (Rust) or `os.replace` (Python).
   - Never write directly to a valid project file in place, preventing truncation on crash or power failure.
2. **Security & Untrusted Input Handling:**
   - Path traversal prevention: Resolve relative media paths strictly within project boundary or approved media directories. Reject any `..` escaping root.
   - Input sanitization: Validate field types, ranges, schema versions, and bounds before ingestion.
   - Never use `eval()`, `pickle`, or dangerous execution primitives.

---

## 4. Media Path Management & Relinking

1. **Portability Algorithm:**
   - On save: compute `os.path.relpath(media_abs_path, project_dir)` and store both `relative_path` and `absolute_path`.
   - On load:
     1. Test if `relative_path` exists relative to current project directory.
     2. If not, test if `absolute_path` exists.
     3. If neither exists, flag asset as **MISSING**.
2. **Relinking Interface:**
   - Detect missing media upon project load.
   - Present **Missing Media Dialog** showing missing filenames and previous locations.
   - Relink individual media or scan a folder to batch-relink all matching filenames.
   - Allow user to "Skip" missing assets without failing project load.

---

## 5. Autosave & Crash Recovery

1. **Autosave Engine:**
   - Background interval (default 3 minutes, configurable 1-10 minutes).
   - Only triggers if `isDirty == true`.
   - Saves to `<project_dir>/.ck_autosaves/<project_name>_autosave_<timestamp>.ckproj`.
   - Snapshot retention: Keeps last $N$ snapshots (default 5), auto-purges older ones.
2. **Crash Recovery Manifest:**
   - Session lock manifest: `<appDataDir>/session_lock.json` containing active project path, session ID, and last heartbeat timestamp.
   - Clean shutdown removes session lock.
   - If application launches and session lock exists (abnormal shutdown) or an autosave exists with timestamp > saved project file:
     - Prompt **Crash Recovery Dialog**:
       - *Option 1: Recover Latest Autosave Snapshot*
       - *Option 2: Open Last Manually Saved Project*
       - *Option 3: View Recovery Snapshots History*

---

## 6. Implementation Stages

- **Step 1:** Define Python project engine (`engine/project/`) with full serialization, deserialization, validation, atomic saving, and schema migration.
- **Step 2:** Define Rust native atomic commands (`save_project_atomic`, `list_autosaves`, `verify_media_paths`).
- **Step 3:** Implement Media Relinking subsystem (`engine/project/media_manager.py`).
- **Step 4:** Implement Autosave & Recovery subsystem (`engine/project/autosave_manager.py`).
- **Step 5:** Implement React Autosave hook & Crash Recovery Dialog (`RecoveryModal.tsx`, `MissingMediaModal.tsx`).
- **Step 6:** Wire File menu actions in `TopMenu.tsx` (New, Open, Save, Save As, Backup, Close).
- **Step 7:** Create automated unit and regression test suite (`tests/test_project_serialization.py`).
- **Step 8:** Run master Phase 7 verification (`tests/verify_phase7.py`).
- **Step 9:** Complete documentation deliverables.

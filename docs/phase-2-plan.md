# CorridorKey 2.0 Desktop — Phase 2 Implementation Plan
## Desktop Foundation | Tauri 2 + React + TypeScript

**Phase:** Phase 2: Desktop Foundation  
**Status:** In Progress  
**Author:** CorridorKey 2.0 Desktop Architecture Team  

---

## 1. Project Inspection & Existing State

### 1.1 Existing Workspace Components
- **Vendor Code:** `vendor/CorridorKey2.0/` is cloned and intact with full licensing (`LICENSE`), third-party notices (`THIRD_PARTY_NOTICES.md`), model inference (`infer.py`), and foundation model downloaders (`scripts/download_weights.py`).
- **AI Engine Detection:** `engine/detection/hardware.py` provides cross-platform detection of NVIDIA CUDA (including RTX 5060 Blackwell detection), Apple Silicon Metal (MPS), CPU, and FFmpeg versioning.
- **Verification Suite:** `tests/verify_inference.py` validates repository assets, dependencies, and environment status.
- **Documentation:** `docs/architecture.md`, `docs/installation.md`, `docs/compatibility-matrix.md`, and `docs/cross-platform-compatibility-report.md`.

### 1.2 Target Deliverables for Phase 2
1. **Tauri 2 Rust Application Core** (`apps/desktop/src-tauri`):
   - Secure Rust commands for project file serialization (.ckproj), media inspection via FFmpeg, file dialog integration, and hardware status retrieval.
   - Configured capabilities and permissions conforming to Tauri 2 security boundaries.
2. **React + TypeScript + Vite Desktop Frontend** (`apps/desktop`):
   - Professional Adobe-inspired VFX design tokens (charcoal #18181b, border #27272a, subtle blue accent #3b82f6).
   - Resizable workspace layout (Media Browser on left, Central Viewport in center, Inspector on right, Timeline on bottom, Menu bar on top, Status bar on bottom).
   - Real video playback engine with frame scrubbing, timecode, zoom controls, and checkerboard transparency.
   - Modular Zustand state management (`projectStore`, `mediaStore`, `playbackStore`, `inspectorStore`, `timelineStore`, `workspaceStore`).
   - Project format specification and automated JSON serialization tests.

---

## 2. Design System Tokens & Aesthetics

Adhering strictly to professional VFX software conventions (Adobe Premiere Pro, After Effects, DaVinci Resolve):

| Token Category | Value / Hex | Usage |
| :--- | :--- | :--- |
| **Workspace Background** | `#121214` | Window background and app shell |
| **Panel Surface** | `#1a1a1e` | Main panel backgrounds |
| **Panel Header / Subpanel** | `#222226` | Tab bars, inspector sub-sections, menu bar |
| **Subtle Border** | `#2e2e34` | 1px clean separation lines |
| **Active Border / Focus** | `#3b82f6` | Playhead, focused panel highlight |
| **Text Primary** | `#f4f4f5` | High-contrast labels, timecodes, headers |
| **Text Secondary** | `#a1a1aa` | Dimensions, frame rates, unselected tabs |
| **Text Muted** | `#71717a` | Disabled controls, secondary metadata |
| **Accent Primary** | `#2563eb` | Primary buttons, playhead scrubber, active toggles |
| **VFX Track Accent** | `#0d9488` | Video track clip background (Teal 600) |
| **Audio Track Accent** | `#0284c7` | Audio track clip background (Sky 600) |

---

## 3. Modular Architecture Breakdown

### 3.1 Top Menu Bar (`TopMenu.tsx`)
- Native menu triggers with keyboard shortcuts:
  - `File`: New Project (`Ctrl+N` / `Cmd+N`), Open Project (`Ctrl+O` / `Cmd+O`), Save (`Ctrl+S` / `Cmd+S`), Save As, Import Media (`Ctrl+I` / `Cmd+I`), Exit.
  - `Edit`: Undo, Redo, Preferences.
  - `View`: Reset Workspace, Toggle Panels.
  - `Project`: Project Settings, Project Info.
  - `Playback`: Play/Pause (`Space`), Next Frame (`Right`), Prev Frame (`Left`).
  - `Export`: Export Settings, Render Queue.
  - `Help`: About CorridorKey, Documentation.
- Truly disabled UI states for features deferred to subsequent phases.

### 3.2 Media Browser (`MediaBrowser.tsx`)
- Tabbed interface: **Project Media** & **Explorer**.
- Drag & Drop media zone + Native File Picker button.
- Rich media metadata table: Name, Extension, Resolution (WxH), Framerate, Duration, Codec, File Size.
- Filter and search bar.
- Clip selection bound to `mediaStore`.

### 3.3 Central Viewport (`Viewer.tsx`)
- Real `<video>` and `<canvas>` playback integration.
- Display Modes:
  - **Original Video**: Live native playback.
  - **Foreground / Cutout**: Composited with despill.
  - **Alpha Matte**: High-contrast black & white matte view.
  - **Checkerboard**: VFX transparency checkerboard grid (8x8px).
- View controls: Fit, 50%, 100%, 200% Zoom, Pan offset.
- Timecode display (HH:MM:SS:FF) and current frame counter.
- Playhead transport controls (Play, Pause, Step Backward, Step Forward, Loop).

### 3.4 Inspector Panel (`Inspector.tsx`)
- Tabs: **Media Info**, **AI Keying**, **Matte Controls**, **Transform**.
- **Media Info**: Live codec, frame count, color space, audio channels.
- **AI Keying**: Backend status indicator (CUDA / MPS / CPU), Model load status, Hann Window parameters, Low-VRAM mode toggle, Despill strength.
- **Matte Controls**: Contrast, Edge Refinement, Invert Matte, Alpha Threshold.
- Disabled indicators for controls requiring the Phase 3 inference engine.

### 3.5 Timeline Foundation (`Timeline.tsx`)
- Time ruler with adaptive frame markings.
- Interactive playhead scrubber synced with Viewer.
- Video Track (V1) & Audio Track (A1) headers:
  - Track Lock, Mute, Visibility toggle.
  - Drag-to-position clips, clip trimming handles, clip selection.
- Zoom slider and frame navigation.

### 3.6 Status Bar (`StatusBar.tsx`)
- Real-time hardware telemetry:
  - CPU usage & thread count.
  - Active Acceleration Backend (e.g. `CUDA (RTX 5060)` or `Metal MPS (Apple M5)` or `CPU`).
  - GPU Memory / RAM consumption.
  - Engine state indicator (Ready / Idle).

---

## 4. Project File Format (.ckproj)

Versioned, portable JSON specification:
```json
{
  "format": "corridorkey-project",
  "version": 1,
  "generator": "CorridorKey 2.0 Desktop",
  "project": {
    "name": "VFX_Shot_01",
    "width": 1920,
    "height": 1080,
    "frameRate": 24.0,
    "colorSpace": "sRGB",
    "createdAt": "2026-11-20T18:50:00Z",
    "modifiedAt": "2026-11-20T18:50:00Z"
  },
  "media": [
    {
      "id": "med_01",
      "name": "greenscreen_plate.mp4",
      "path": "/footage/greenscreen_plate.mp4",
      "relativePath": "./footage/greenscreen_plate.mp4",
      "width": 1920,
      "height": 1080,
      "frameRate": 24.0,
      "durationFrames": 240,
      "codec": "h264"
    }
  ],
  "timeline": {
    "durationFrames": 240,
    "currentFrame": 0,
    "tracks": [
      {
        "id": "track_v1",
        "type": "video",
        "name": "Video 1",
        "visible": true,
        "locked": false,
        "clips": [
          {
            "id": "clip_01",
            "mediaId": "med_01",
            "startFrame": 0,
            "endFrame": 240,
            "sourceIn": 0,
            "sourceOut": 240
          }
        ]
      }
    ]
  },
  "keyingSettings": {
    "hannChunk": 24,
    "hannStride": 12,
    "lowVram": false,
    "despillStrength": 0.5
  },
  "workspace": {
    "leftPanelWidth": 320,
    "rightPanelWidth": 360,
    "bottomPanelHeight": 260
  }
}
```

---

## 5. Execution Steps

1. **Step 1:** Architectural review & Phase 2 plan documentation (Done).
2. **Step 2:** Scaffold React + Vite + Tailwind CSS + Lucide + Zustand in `apps/desktop`.
3. **Step 3:** Implement Design Tokens & Top Menu Bar with active keyboard shortcuts.
4. **Step 4:** Implement Media Browser with Drag & Drop and native metadata probing.
5. **Step 5:** Implement Central Viewer with real video playback, split view, and transparency checkerboard.
6. **Step 6:** Implement Inspector panels with tabs for Media, Keying, Matte, and Transform.
7. **Step 7:** Implement Bottom Timeline with tracks, playhead scrubbing, and clip blocks.
8. **Step 8:** Implement Project Creation, Opening, Saving (.ckproj), and persistence with native dialogs.
9. **Step 9:** Implement Status Bar with live hardware status.
10. **Step 10:** Implement Tauri 2 Rust commands, capabilities, and compile/test verification.

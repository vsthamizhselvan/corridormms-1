# Timeline Editing Guide — CorridorKey 2.0 Desktop

## 1. Professional Editing Workflow

CorridorKey 2.0 Desktop provides an editing workflow tailored for VFX artists, matting operators, and compositors.

### Key Tools & Modes

| Tool | Shortcut | Icon | Description |
| :--- | :--- | :--- | :--- |
| **Selection Tool** | `V` | Pointer | Select clips, drag to reposition, drag edge handles to trim. |
| **Razor / Split Tool** | `C` | Scissors | Click anywhere on a clip to split into two non-destructive parts. |
| **Split at Playhead** | `Cmd+K` / `Ctrl+K` | — | Splits the selected clip or clip under playhead at current frame. |
| **Magnetic Snapping** | `S` | Magnet | Snaps playhead and clips to frame 0, cut points, and playhead. |
| **Ripple Delete** | `Shift+Del` | Trash | Deletes clip and automatically pulls subsequent clips left to close the gap. |
| **Duplicate Clip** | `Cmd+D` / `Ctrl+D` | Copy | Clones selected clip and places it adjacent to original. |
| **Undo** | `Cmd+Z` / `Ctrl+Z` | Rotate Left | Reverts previous timeline operation. |
| **Redo** | `Cmd+Shift+Z` | Rotate Right | Restores previously undone operation. |

---

## 2. Trimming Operations

- **Trim In:** Drag the left edge of any clip (`cursor-ew-resize`). The timeline start advances while proportionally advancing the source In-point. Duration decreases accordingly.
- **Trim Out:** Drag the right edge of any clip. The timeline end contracts while adjusting the source Out-point. Duration decreases accordingly.
- **Snapping Guides:** While dragging or trimming with snapping enabled, a bright cyan vertical guide appears when the cursor is within 6 frames of a cut point or the playhead.

---

## 3. Multi-Track Bus Management

- **Add Tracks:** Click `+V` to add a new video track above existing video tracks, or `+A` to add an audio track below.
- **Mute (`M`):** Temporarily mutes the track output.
- **Solo (`S`):** Isolates the track, muting all non-soloed tracks.
- **Lock (`L`):** Protects the track against edits, cuts, and moves.
- **Visibility (`V`):** Hides video track layers from the GPU compositor viewport and export pipeline.

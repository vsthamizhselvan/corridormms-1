# CorridorKey 2.0 Desktop — Phase 6 Implementation Plan
## Multi-Track Timeline Editing & Compositing System

This document specifies the architectural blueprint, data model, timebase math, clip editing operations, render graph evaluation, and testing strategy for Phase 6 (Multi-Track Timeline Editing).

---

## 1. System Topology & Dual-Layer Architecture

The timeline system operates as a non-destructive, frame-accurate editing core where media files are referenced rather than modified:

```
┌────────────────────────────────────────────────────────┐
│             React Timeline UI (Timeline.tsx)           │
│  - Time Ruler with Dynamic Timecode Markings           │
│  - Multi-Track Lanes (V3, V2, V1, A1, A2)              │
│  - Interactive Clip Draggable Handles & Trim Bounds    │
│  - Playhead Scrubber, Snap Indicators, Audio Waveforms │
└───────────────────────────┬────────────────────────────┘
                            │ Zustand Actions (useTimelineStore, usePlaybackStore)
                            ▼
┌────────────────────────────────────────────────────────┐
│          Command Pattern History (Undo / Redo)         │
│  - MoveCommand, TrimCommand, SplitCommand              │
│  - RippleDeleteCommand, AddTrackCommand, KeyframeCmd   │
└───────────────────────────┬────────────────────────────┘
                            │ Timeline State Synchronization
                            ▼
┌────────────────────────────────────────────────────────┐
│          Timeline Evaluation Core (engine/timeline/)   │
│  - timebase.py: Rational frame ticks (num/den)         │
│  - timeline_model.py: Sequence, Track, Clip, Keyframes │
│  - edit_operations.py: Non-destructive trim, split,    │
│    move, snap, ripple delete calculations             │
│  - keyframe_engine.py: Linear, Hold, Bezier evaluation │
│  - render_graph.py: Multi-layer timeline compositor    │
└───────────────────────────┬────────────────────────────┘
                            │ Active Media & Layer Stack at Frame F
                            ▼
┌────────────────────────────────────────────────────────┐
│             GPU WebGL2 Compositor (Phase 5)            │
│  - Renders Active Video Track Layers in Real-Time      │
│  - Applies Animated Transform Matrix (Pos, Scale, Op)  │
│  - 60 FPS Smooth Playhead Tracking & Scrubbing         │
└────────────────────────────────────────────────────────┘
```

---

## 2. Integer Frame Timebase & Rational Representation

To eliminate floating-point precision drift across long sequences:
- All timeline positions, durations, in/out marks, and keyframe times are represented strictly as **integer frame ticks** ($0, 1, 2, \dots$).
- The sequence framerate is represented as a **rational fraction** ($\frac{\text{numerator}}{\text{denominator}}$):
  - $24.0\text{ fps} \to 24 / 1$
  - $23.976\text{ fps} \to 24000 / 1001$
  - $29.97\text{ fps} \to 30000 / 1001$
  - $30.0\text{ fps} \to 30 / 1$
  - $60.0\text{ fps} \to 60 / 1$
- SMPTE Timecode Conversion: Formats integer frame ticks into exact `HH:MM:SS:FF` or drop-frame `HH:MM:SS;FF`.

---

## 3. Non-Destructive Clip Geometry

Every clip on the timeline references underlying source media without altering source files:
- **`source_in` (int):** Start frame within the source media file.
- **`source_out` (int):** End frame within the source media file.
- **`timeline_start` (int):** Placement position on the timeline ruler.
- **`timeline_end` (int):** $\text{timeline\_start} + (\text{source\_out} - \text{source\_in})$.
- **`duration` (int):** $\text{source\_out} - \text{source\_in}$.
- Source Mapping: At timeline frame $F$ where $\text{timeline\_start} \le F < \text{timeline\_end}$, the source frame is:
  $$\text{SourceFrame} = \text{source\_in} + (F - \text{timeline\_start}) \times \text{speed}$$

---

## 4. Editing Operations & Snapping

- **Move:** Repositions clip across timeline tracks and start frames.
- **Trim In:** Adjusts `source_in` and `timeline_start` while clamping within media boundaries $[0, \text{source\_out} - 1]$.
- **Trim Out:** Adjusts `source_out` and `timeline_end` while clamping within $[\text{source\_in} + 1, \text{media\_duration}]$.
- **Split at Playhead (Razor Tool):** Divides clip into two adjacent clips at playhead frame $P$, preserving continuous media playback.
- **Ripple Delete:** Removes target clip and shifts all subsequent clips on the track to the left by the deleted clip's duration, eliminating gaps.
- **Magnetic Snapping:** Detects alignment within a configurable threshold ($\pm 5$ frames) against:
  - Playhead position
  - Other clip start and end boundaries
  - In/Out markers

---

## 5. Keyframe Animation Engine

Supports animating transform properties over time:
- Properties: `posX`, `posY`, `scale`, `rotation`, `opacity`.
- Interpolation modes:
  - **Hold:** Value stays constant until next keyframe.
  - **Linear:** Constant velocity interpolation between keyframe points.
  - **Bezier / Ease:** Smooth cubic spline curve ($S$-curve) with customizable ease-in/ease-out tension.

---

## 6. Implementation Sequence

1. `engine/timeline/timebase.py`: Rational timebase and SMPTE timecode conversions.
2. `engine/timeline/timeline_model.py`: Data models for Sequences, Tracks, Clips, and Keyframes.
3. `engine/timeline/edit_operations.py`: Move, Trim, Split, Ripple Delete, and Snapping math.
4. `engine/timeline/keyframe_engine.py`: Linear, Hold, and Bezier keyframe evaluation.
5. `engine/timeline/render_graph.py`: Multi-track timeline evaluation at frame $F$.
6. `engine/timeline/undo_manager.py`: Command-based undo/redo history.
7. `apps/desktop/src/project/timelineStore.ts`: Full reactive state store with undo/redo and editing commands.
8. `apps/desktop/src/panels/Timeline/Timeline.tsx`: Complete Adobe-style multi-track UI with trimming handles, razor tool, track controls, waveforms, and visual snap indicators.
9. Verification and acceptance tests (`tests/test_timeline_engine.py`, `tests/verify_phase6.py`).

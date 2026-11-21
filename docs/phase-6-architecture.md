# Phase 6 Architecture — Non-Destructive Multi-Track Timeline System

## 1. System Overview

CorridorKey 2.0 Desktop Phase 6 implements a professional non-destructive multi-track video and audio timeline system inspired by Adobe Premiere Pro and DaVinci Resolve. The architecture cleanly decouples timeline geometry, source media boundaries, keyframe parameter evaluation, and multi-track compositing order.

```
+-------------------------------------------------------------------+
|                        React Timeline UI                          |
|  - Tracks & Clips Display     - In/Out Trimming Handles           |
|  - Magnetic Snapping Guides   - Razor Tool & Ripple Delete        |
|  - Multi-track Solo/Mute/Lock - Audio Waveform Envelope Visualizer|
+---------------------------------+---------------------------------+
                                  |
                   Zustand Timeline Store (History Stack)
                                  |
+---------------------------------v---------------------------------+
|                   Non-Destructive Timeline Engine                 |
|                                                                   |
|  +--------------------+  +--------------------+  +--------------+ |
|  | Rational Timebase  |  | Keyframe Engine    |  | Audio Engine | |
|  | - Integer Ticks    |  | - Hold, Linear     |  | - Mute/Solo  | |
|  | - SMPTE Timecode   |  | - Cubic Bezier     |  | - Waveforms  | |
|  +--------------------+  +--------------------+  +--------------+ |
|                                                                   |
|  +--------------------+  +--------------------+  +--------------+ |
|  | Edit Operations    |  | Undo/Redo Manager  |  | Render Graph | |
|  | - Trim / Split     |  | - Snapshot Stack   |  | - V1->Vn Plan| |
|  | - Ripple Delete    |  | - Max 50 States    |  | - Layer Sync | |
|  +--------------------+  +--------------------+  +--------------+ |
+---------------------------------+---------------------------------+
                                  |
                   WebGL2 GPU Compositor / Viewport
```

---

## 2. Rational Timebase and Integer Frame Ticks

Editing precision requires complete elimination of floating-point seconds as the primary temporal coordinate. `Timebase` models framerates as rational fractions `numerator / denominator`:

- **24.0 fps:** `Timebase(24, 1)`
- **23.976 fps:** `Timebase(24000, 1001)`
- **25.0 fps:** `Timebase(25, 1)`
- **29.97 fps:** `Timebase(30000, 1001)`
- **30.0 fps:** `Timebase(30, 1)`
- **59.94 fps:** `Timebase(60000, 1001)`
- **60.0 fps:** `Timebase(60, 1)`

### Frame Conversion Equations

$$\text{seconds} = \frac{\text{frame} \times \text{denominator}}{\text{numerator}}$$

$$\text{frame} = \left\lfloor \frac{\text{seconds} \times \text{numerator}}{\text{denominator}} + 0.5 \right\rfloor$$

---

## 3. Clip Geometry & Non-Destructive Principles

Each clip retains independent coordinates:
- **Timeline Space:** `[timeline_start, timeline_end)` in global integer sequence frame ticks.
- **Source Media Space:** `[source_in, source_out)` in raw video frames.

When a clip is placed on the timeline at frame $F$, the evaluated source frame is:
$$\text{source\_frame} = \text{source\_in} + \left\lfloor (F - \text{timeline\_start}) \times \text{speed} \right\rceil$$

Trimming or moving a clip never modifies original source media on disk.

---

## 4. Track Hierarchy & Routing

- **Video Tracks:** Evaluated in bottom-to-top order ($V_1 \to V_2 \to \dots \to V_n$). Top layers composite over lower layers with independent opacity and 2D affine transforms.
- **Audio Tracks:** Bus-summed with track solo and mute routing:
  - If any track is soloed, only soloed non-muted tracks produce sound.
  - Otherwise, all non-muted tracks produce sound.

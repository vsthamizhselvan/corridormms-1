# CorridorKey 2.0 Desktop — Phase 5 Implementation Plan
## Interactive Viewer & GPU Compositing Engine

This document outlines the architecture, WebGL2 rendering pipeline, shader specifications, viewport interaction model, and testing strategy for Phase 5 (Interactive Viewer & Compositing).

---

## 1. System Topology & WebGL2 Rendering Architecture

To deliver 60 FPS real-time feedback with sub-frame responsiveness during scrubbing, panning, and zooming, the viewer utilizes a dedicated WebGL2 rendering engine:

```
┌────────────────────────────────────────────────────────┐
│             React Desktop UI (Viewer.tsx)              │
│  - Viewport Controls: Fit, 25%, 50%, 100%, 200%, Pan   │
│  - Transport: Play/Pause, Step ±1f, Timecode (SMPTE)   │
│  - Compare Controls: Wipe, Side-by-Side, Difference    │
│  - Background Selector: Checkerboard, Solid, Gradient  │
└───────────────────────────┬────────────────────────────┘
                            │ Reactive State (viewerStore, inspectorStore)
                            ▼
┌────────────────────────────────────────────────────────┐
│            WebGL2 Compositor (compositor.ts)           │
│  - Texture Uploads: Video Plate Texture (UNIT 0)       │
│  - Background Texture: Image / Video Texture (UNIT 1)  │
│  - GLSL Shaders: Vertex & Multi-Pass Fragment Shader   │
│  - Procedural Generators: Anti-aliased Checkerboard    │
│  - Matrix Transforms: Pan & Zoom UV projection         │
└───────────────────────────┬────────────────────────────┘
                            │ GLSL ES 3.0 Fragment Pipeline
                            ▼
┌────────────────────────────────────────────────────────┐
│               GLSL ES 3.0 Fragment Shader              │
│  1. Sampling: Source RGB & Background (Tex Units 0, 1) │
│  2. Matte Extraction: High-fidelity Green/Blue Key     │
│  3. Alpha Shaping: Threshold, Contrast, Inversion      │
│  4. Despill: Green/Blue suppression with balance       │
│  5. Composite: Straight vs. Premultiplied math         │
│  6. Comparison: Interactive Wipe & Side-by-Side        │
└────────────────────────────────────────────────────────┘
```

---

## 2. GLSL Shading Pipeline & Features

The GPU fragment shader executes the following operations in a single draw pass:
1. **Procedural Checkerboard:** Computed dynamically in screen-space coordinates to remain sharp and anti-aliased regardless of magnification.
2. **Interactive Alpha Extraction:** Fast GPU keying metric $A = \text{clamp}(1.0 - (G - \max(R, B)) \times 2.5, 0.0, 1.0)$.
3. **Matte Grading:** Controllable contrast pivot, alpha threshold/pedestal, and inversion.
4. **Foreground Despill:** Real-time suppression of reflected green/blue bounce on hair and edges.
5. **Background Compositing:** Blending foreground over:
   - Checkerboard pattern
   - Solid customizable color (RGB)
   - 2-stop linear gradient
   - Secondary background texture (custom image plate or video)
6. **Comparison Modes:**
   - **Single View:** Original plate, Despilled foreground, Alpha matte (Grayscale), or Final composite.
   - **Split Wipe:** Draggable divider line with anti-aliased border showing original on left and composite/alpha on right.
   - **Side-by-Side:** Horizontal dual-screen comparison.
   - **Difference:** Visualizes pixel delta between source plate and composite.

---

## 3. Viewport Navigation: Pan & Zoom

- **Pan:** Middle-mouse drag, Space + Left drag, or right-click drag.
- **Zoom:** Mouse-wheel centered at cursor coordinates, plus discrete presets:
  - Fit to Viewer (resets transform to fit container bounds)
  - Fit Width / Fit Height
  - 25%, 50%, 100%, 200%
- **Timecode & Transport:** SMPTE `HH:MM:SS:FF`, frame counter `0000/0240f`, playback loop, frame stepping (`←` / `→`).

---

## 4. Inspector Integration

The Inspector panel is augmented with real-time controls wired to the viewer compositor:
- **Matte Controls:** Contrast, Alpha Threshold, Invert Matte, Edge Soften.
- **Keying Controls:** Despill Strength, Key Color mode.
- **Background Controls:** Mode (Checkerboard, Solid, Gradient, Image), Color picker, Gradient stops.
- **Composite Controls:** Straight vs Premultiplied alpha mode, Exposure adjustment, Foreground saturation.

---

## 5. Implementation Milestones

1. **Step 1:** Create `viewerStore.ts` managing view modes, background types, zoom/pan transforms, and wipe positions.
2. **Step 2:** Build WebGL2 shader and compositor engine in `apps/desktop/src/components/viewer/webgl/`.
3. **Step 3:** Build interactive viewer component with canvas, pan/zoom gesture listeners, and wipe split handle.
4. **Step 4:** Integrate Background and Composite controls into `Inspector.tsx`.
5. **Step 5:** Automated test suite (`tests/verify_phase5.py`) validating shader math, store state, and acceptance criteria.

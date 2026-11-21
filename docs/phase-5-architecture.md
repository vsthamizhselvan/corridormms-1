# CorridorKey 2.0 Desktop — Phase 5 Interactive Viewer Architecture

This document details the GPU-accelerated rendering pipeline, GLSL ES 3.0 shader system, texture caching, and viewport pan/zoom controls implemented in CorridorKey 2.0 Desktop.

---

## 1. System Topology & WebGL2 Rendering Pipeline

To guarantee 60 FPS real-time feedback during timeline playback, video scrubbing, and parameter adjustment without blocking the JavaScript main thread:

```
┌────────────────────────────────────────────────────────┐
│             React Desktop UI (Viewer.tsx)              │
│  - Pan & Zoom Gesture Listeners                        │
│  - Interactive Wipe Split Dragging                     │
│  - Transport: TC (SMPTE), Play/Pause, Step ±1f         │
└───────────────────────────┬────────────────────────────┘
                            │ Zustand Stores (viewerStore, inspectorStore)
                            ▼
┌────────────────────────────────────────────────────────┐
│            WebGL2 Compositor (compositor.ts)           │
│  - Texture Unit 0: Source Video Frame (HTMLVideoElement)│
│  - Texture Unit 1: Background Plate (Image/Video)      │
│  - Full-Screen Quad Geometry (VAO / VBO)               │
│  - Cached GLSL ES 3.0 Uniform Locations                │
└───────────────────────────┬────────────────────────────┘
                            │ GPU Draw Call (gl.drawArrays)
                            ▼
┌────────────────────────────────────────────────────────┐
│               GLSL ES 3.0 Fragment Shader              │
│  - Sub-pixel Matte Extraction & Alpha Thresholding     │
│  - Green/Blue Spill Suppression                        │
│  - Exposure Grading (-3 to +3 EV) & Saturation Scaling │
│  - Straight vs. Premultiplied Alpha Compositing        │
│  - Procedural Screen-Space Anti-Aliased Checkerboard   │
│  - Draggable Split Wipe & Side-by-Side Comparison      │
└────────────────────────────────────────────────────────┘
```

---

## 2. GLSL ES 3.0 Shading Pipeline

The fragment shader [engine/webgl/shaders.ts](file:///Volumes/VST%20SSD/corridor%20key%202.0/apps/desktop/src/components/viewer/webgl/shaders.ts) executes in a single GPU pass:

### 2.1 Real-Time Keying Metric
$$A = \text{clamp}\left(1.0 - \max(0.0, G - \max(R, B)) \times 2.5, 0.0, 1.0\right)$$
- Followed by alpha pedestal thresholding:
  $$A_{\text{thresh}} = \text{clamp}\left(\frac{A - \text{threshold}}{1.0 - \text{threshold} + \epsilon}, 0.0, 1.0\right)$$
- And contrast shaping:
  $$A_{\text{contrast}} = \text{clamp}\left((A_{\text{thresh}} - 0.5) \times \text{contrast} + 0.5, 0.0, 1.0\right)$$

### 2.2 Despill Suppression
$$G_{\text{despilled}} = G - \max(0.0, G - \max(R, B)) \times \text{strength}$$
$$R_{\text{balanced}} = R + \text{spill} \times 0.5 \times \text{strength}$$
$$B_{\text{balanced}} = B + \text{spill} \times 0.5 \times \text{strength}$$

### 2.3 Alpha Composite Mathematics
- **Straight (Unassociated) Mode:**
  $$\text{Composite} = \text{FG}_{\text{despilled}} \times A + \text{BG} \times (1.0 - A)$$
- **Premultiplied (Associated) Mode:**
  $$\text{Composite} = (\text{FG}_{\text{despilled}} \times A) + \text{BG} \times (1.0 - A)$$

---

## 3. Viewport Interaction: Pan, Zoom & Wipe

- **Pan:** Middle-mouse drag, Space + Left drag, or right-click drag adjusts `(panX, panY)` in screen space.
- **Zoom:** Mouse-wheel zoom scales around the viewport center. Presets include:
  - **Fit to Viewer:** Fits the full video resolution within the container bounds.
  - **25%, 50%, 100%, 200%:** Fixed pixel magnification levels.
- **Split Wipe:** Draggable divider line with anti-aliased border. Tracks mouse drag horizontally across the video frame, displaying original camera plate on the left and composite/alpha on the right.

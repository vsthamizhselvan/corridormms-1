# Phase 8 Audit — Advanced VFX Compositing System

**Project:** CorridorKey 2.0 Desktop  
**Date:** November 2026  
**Status:** Audit Complete — Phase 8 Implementation Initialized  

---

## 1. Existing System Architecture Overview

CorridorKey 2.0 Desktop consists of a tightly integrated, cross-platform architecture:
1. **AI Inference Subsystem (`engine/inference/`, `vendor/CorridorKey2.0/`):**
   - Official PyTorch CorridorKey model with C-RADIOv4, MoGe-2, and RVM backends.
   - Dual-process supervisor (`apps/desktop/src-tauri/src/ai_engine/`) communicating over Protocol v1 JSON-lines stdin/stdout.
   - Hardware detection supporting NVIDIA CUDA (RTX GPUs), Apple Silicon MPS (M1-M5), and CPU fallback.
2. **Video & Export Pipeline (`engine/video/`, `engine/color/`, `engine/export/`):**
   - FFmpeg decoding and frame extraction.
   - Professional alpha-preserving encoders: Apple ProRes 4444/XQ, QuickTime Animation (RLE), VP9 Alpha, 16-bit half-float OpenEXR sequences, and 16-bit PNG sequences.
   - Colour-space conversion matrices (Rec.709, sRGB, Linear, ACEScg, Rec.2020).
3. **Interactive GPU Viewer & Compositing (`apps/desktop/src/components/viewer/webgl/`):**
   - WebGL2 hardware-accelerated pipeline (`shaders.ts`, `compositor.ts`).
   - Real-time despill suppression, matte contrast/thresholding, straight vs premultiplied alpha composite, and wipe/split comparisons.
4. **Non-Destructive Multi-Track Timeline (`engine/timeline/`, `apps/desktop/src/project/timelineStore.ts`):**
   - Integer frame tick timebase (`Timebase(num, den)`), SMPTE timecode formatting.
   - Tracks, clips, trimming, razor split, ripple deletion, magnetic snapping.
   - `PropertyTrack` keyframe animation engine supporting Hold, Linear, and Cubic Bezier easing.
   - Multi-layer render graph compositing hierarchy ($V_1 \to V_n$).
5. **Project Persistence, Autosave & Recovery (`engine/project/`, `apps/desktop/src/project/projectStore.ts`):**
   - Native `.ckproj` schema v1.0.0 with atomic file writes (`fsync` + rename).
   - Media path portability (relative + absolute fallback), missing media detection, and folder batch relinking.
   - Background non-blocking autosave with snapshot rotation and crash recovery dialogs.

---

## 2. Reusable Modules for Phase 8

| Module | Location | Reusability in Phase 8 |
| :--- | :--- | :--- |
| **Keyframe Engine** | `engine/timeline/keyframe_engine.py` | Animating mask vertices, feather, opacity, effect parameters, and color grading controls. |
| **Timeline Render Graph** | `engine/timeline/render_graph.py` | Multi-layer execution order, layer transforms, and composite hierarchy. |
| **Color Management** | `engine/color/` | Gamma curves, ACEScg / Rec.709 conversions, and channel transformations. |
| **WebGL2 Shaders** | `apps/desktop/src/components/viewer/webgl/shaders.ts` | Adding real-time multi-pass shaders for masks, blur, color grading, and blend modes. |
| **Atomic Project Serializer** | `engine/project/serializer.py` | Serializing mask arrays, effect stacks, blend modes, and node graph definitions. |
| **Undo / Redo Manager** | `engine/timeline/undo_manager.py` | Snapshot management for mask operations, effect additions, and node graph edits. |

---

## 3. Missing Features to Implement in Phase 8

1. **Masking & Rotoscoping Subsystem (`engine/vfx/masking.py`, `apps/desktop/src/components/viewer/webgl/`):**
   - Rectangle, Ellipse, Freehand, Bezier, and Polygon mask geometry.
   - Add, Subtract, Invert, Feathering, Expansion/Contraction, Opacity, and Keyframed coordinates.
   - Interactive SVG/Canvas/WebGL mask editing overlays in the desktop viewer.
2. **Advanced Alpha Matte Refinement (`engine/vfx/matte_refine.py`, WebGL shaders):**
   - Real-time choke & expand (morphological erosion/dilation), edge softness, alpha blur, edge decontamination, and foreground detail restoration.
3. **Comprehensive Colour Correction & Grading (`engine/vfx/color_grade.py`, WebGL shaders):**
   - Primary: Exposure, Contrast, Brightness, Highlights, Shadows, Whites, Blacks, Temperature, Tint, Saturation, Vibrance, Lift, Gamma, Gain.
   - Secondary: RGB channel curves and before/after split evaluation.
4. **Non-Destructive Effect Stack (`engine/vfx/effects/`, `apps/desktop/src/stores/effectStore.ts`):**
   - 10 real implementations: Gaussian Blur, Sharpen, Glow, Drop Shadow, Gaussian Noise, Film Grain, Vignette, Hue/Saturation, Colour Correction, Chroma Spill Suppression.
   - Add, remove, duplicate, reorder, enable/disable, copy/paste, and presets.
5. **Layer-Based Compositing Extensions (`engine/vfx/layer_compositor.py`):**
   - Blend modes: Normal, Multiply, Screen, Add, Overlay, Difference.
   - Straight vs Premultiplied alpha composite handling across multi-layer video tracks.
6. **Node-Based Compositing Foundation (`engine/vfx/nodes/`, `apps/desktop/src/components/nodes/`):**
   - Directed acyclic graph (DAG) engine with cycle detection and topological execution ordering.
   - 10 core node types: Media Input, AI Foreground, Alpha Matte, Mask, Blur, Colour Correction, Transform, Background, Merge, Media Output.
   - Interactive React node graph editor with connectable input/output ports.
7. **Project Serialization v1.1.0 Integration:**
   - Extend `.ckproj` schema to persist masks, effect stacks, blend modes, and node graph definitions with backward compatibility for v1.0.0 projects.

---

## 4. Implementation Strategy & Milestones

- **Stage 1:** Audit & Architecture documentation (`docs/phase-8-audit.md`, `docs/phase-8-architecture.md`).
- **Stage 2:** Python VFX Compositing Engine (`engine/vfx/`):
  - `masking.py`: Vector mask rasterization, Bezier curve evaluation, expansion/choke, feather blur, add/subtract operations.
  - `matte_refine.py`: Morphological operations, edge decontamination, despill, soft feathering, thresholding.
  - `color_grade.py`: Lift/Gamma/Gain, Temperature/Tint, Exposure, Highlights/Shadows, Saturation/Vibrance.
  - `effects/`: 10 modular effect classes with serialization and parameter validation.
  - `layer_compositor.py`: Blend mode math (Normal, Multiply, Screen, Add, Overlay, Difference), alpha premultiplication.
  - `nodes/`: Graph DAG, port connections, cycle detection, topological evaluator, and 10 core nodes.
- **Stage 3:** WebGL2 Shader Pipeline Enhancements:
  - Add GLSL ES 3.0 multi-pass shaders for mask clipping, color grading, blur/sharpen/glow/grain/vignette effects, and blend modes in `shaders.ts` and `compositor.ts`.
- **Stage 4:** React Desktop UI Extensions:
  - Mask editing tools in viewer and Inspector tab (`MasksPanel.tsx`).
  - Matte refinement controls in Inspector (`MatteRefinePanel.tsx`).
  - Colour grading panel (`ColorGradePanel.tsx`) with sliders and wheels.
  - Effects stack panel (`EffectStackPanel.tsx`) with drag-and-drop reordering.
  - Node editor canvas (`NodeEditor.tsx`) with draggable nodes, wire connections, and inspector.
- **Stage 5:** Project Serialization (`.ckproj` v1.1.0 migration):
  - Update `engine/project/schema.py` and `serializer.py` to persist all Phase 8 data structures.
- **Stage 6:** Verification & Testing:
  - Unit tests in `tests/test_vfx_compositing.py`.
  - Master Phase 8 verification script `tests/verify_phase8.py`.
  - Regression testing across Phases 1–7.

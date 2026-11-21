# CorridorKey 2.0 Desktop — Transparency and Alpha Management

This document defines the mathematical foundations, compositing conventions, edge despill algorithms, and validation checks implemented in CorridorKey 2.0 Desktop.

---

## 1. Straight Alpha vs. Premultiplied Alpha

CorridorKey 2.0 Desktop provides explicit user control between **Straight Alpha** and **Premultiplied Alpha** via [engine/color/alpha_manager.py](file:///Volumes/VST%20SSD/corridor%20key%202.0/engine/color/alpha_manager.py).

### 1.1 Straight Alpha (Unassociated)
- **Definition:** RGB color channels store their original, unattenuated physical chromaticity, independent of the alpha value:
  $$\text{Pixel} = [R, G, B, A]$$
- **Usage:** Ideal for color grading, keying adjustments, and editing systems (such as Final Cut Pro and Avid Media Composer) that expect unassociated color.

### 1.2 Premultiplied Alpha (Associated)
- **Definition:** RGB color channels are multiplied by the linear alpha matte value:
  $$\text{Pixel} = [R \times A, G \times A, B \times A, A]$$
- **Usage:** Standard in high-end VFX compositing packages (Nuke, Flame, Houdini, After Effects, DaVinci Resolve).
- **Benefit:** When composited over a background using $C = \text{FG} + \text{BG} \times (1 - A)$, premultiplication eliminates dark fringing around soft edges, motion blur, and fine hair strands.

### 1.3 Un-premultiplication (Color Recovery)
To recover straight color from premultiplied footage without numerical instability near zero:
$$\text{FG}_{\text{straight}} = \frac{\text{FG}_{\text{premul}}}{\max(A, 0.0) + \epsilon} \quad (\epsilon = 10^{-6})$$

---

## 2. Edge Despill Algorithms

Green screen and blue screen plates suffer from chromatic reflection (spill) where colored light reflects onto the subject's skin, clothing, and hair:

```
┌────────────────────────────────────────────────────────┐
│               Average Despill Algorithm                │
│                                                        │
│  spill = max(G - 0.5 * (R + B), 0.0)                   │
│                                                        │
│  R_clean = R + spill * (0.5 * strength)                │
│  G_clean = G - spill * strength                        │
│  B_clean = B + spill * (0.5 * strength)                │
└────────────────────────────────────────────────────────┘
```
- **Controlled Suppression:** The user can adjust `despill_strength` from 0% (no suppression) to 100% (full suppression).
- **Magenta Balance:** Subtracting green spill while restoring half of the energy to red and blue neutralizes green fringes without darkening the subject's edges.

---

## 3. Strict Alpha Rules

1. **NO Gamma Transformation of Alpha:**
   - Alpha represents physical area coverage (opacity).
   - Transfer functions (sRGB, Rec.709, PQ, HLG) MUST ONLY be applied to RGB channels.
   - Applying gamma to alpha distorts edge feathering, making soft edges harsh or transparent edges artificially opaque.
2. **NO Double Premultiplication:**
   - The pipeline tracks the alpha mode explicitly in `ExportJobConfig`.
   - Frames are never premultiplied twice.
3. **Clamping & Precision:**
   - Alpha values are strictly bounded in $[0.0, 1.0]$.
   - Negative values from sinc/Lanczos ringing are clamped to $0.0$ before encoding.

---

## 4. Post-Export Alpha Validation

To prevent silent pipeline failures, [engine/export/validation.py](file:///Volumes/VST%20SSD/corridor%20key%202.0/engine/export/validation.py) re-decodes every exported file or image sequence and computes:
- `has_alpha_channel`: Asserts 4 valid channels ($R, G, B, A$).
- `transparent_percent`: Percentage of pixels where $A < 0.01$ (background).
- `opaque_percent`: Percentage of pixels where $A > 0.99$ (subject).
- `semi_transparent_percent`: Percentage of pixels where $0.01 \le A \le 0.99$ (hair, motion blur).
- **Validation Gate:** A file is marked valid only if both transparent and opaque regions are present, preventing solid black or white dummy alphas.

# CorridorKey 2.0 Desktop — Precision Colour Management

This document defines the colour science principles, transfer functions, matrix transforms, and container metadata tags implemented in CorridorKey 2.0 Desktop.

---

## 1. Colour Space Matrix & Characteristics

| Colour Space | Primaries | Transfer Characteristic (TRC) | White Point | Primary Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Rec.709** | ITU-R BT.709 | ITU-R BT.709-6 OETF ($L < 0.018$ linear, $0.45$ power) | D65 | Broadcast Television, Standard Video |
| **sRGB** | ITU-R BT.709 | IEC 61966-2-1 ($L \le 0.0031308$ linear, $1/2.4$ power) | D65 | Computer Displays, Web Browsers, UI |
| **Scene-Linear** | ITU-R BT.709 | Identity ($1.0$ Linear Light) | D65 | Neural AI Model, VFX Compositing |
| **Rec.2020** | ITU-R BT.2020 | ITU-R BT.2020-10 OETF | D65 | Ultra HD, Wide Color Gamut (WCG) |
| **ACEScg (AP1)**| ACES AP1 | Linear Light | D60 | High-End Film & Visual Effects Standard |

> [!IMPORTANT]
> **Rec.709 and sRGB are NOT interchangeable.**
> While they share the exact same chromaticity primaries, their transfer functions differ significantly:
> - Rec.709 uses a linear segment up to $0.018$ and an exponent of $0.45$ (effective gamma ~1.95).
> - sRGB uses a linear segment up to $0.0031308$ and an exponent of $1/2.4$ with an offset of $0.055$ (effective gamma ~2.2).
> Confusing the two causes noticeable midtone lifting or crushing (the "gamma 2.2 vs 2.4 shift").

---

## 2. Transfer Functions Implementation

Mathematical transforms are implemented in [engine/color/transfer_functions.py](file:///Volumes/VST%20SSD/corridor%20key%202.0/engine/color/transfer_functions.py):

### 2.1 Scene-Linear to sRGB (IEC 61966-2-1)
$$\text{sRGB}(x) = \begin{cases} 12.92 \times x & \text{if } x \le 0.0031308 \\ 1.055 \times x^{1/2.4} - 0.055 & \text{if } x > 0.0031308 \end{cases}$$

### 2.2 Scene-Linear to Rec.709 (ITU-R BT.709-6)
$$\text{Rec.709}(x) = \begin{cases} 4.5 \times x & \text{if } x < 0.018 \\ 1.099 \times x^{0.45} - 0.099 & \text{if } x \ge 0.018 \end{cases}$$

### 2.3 CorridorKey Neural Asinh HDR Compression
CorridorKey 2.0 uses signed hyperbolic arcsine encoding to compress high-dynamic-range scene-linear values into a compact, zero-symmetric range without clipping specular highlights:
$$y = \frac{\operatorname{asinh}(x / k)}{\operatorname{asinh}(\text{ref} / k)} \quad (k = 0.008, \text{ref} = 16.0)$$
- **Reversibility:** Unlike log or Reinhard tonemapping, signed asinh is strictly invertible across all finite real numbers without gradient divergence at zero.

---

## 3. ACEScg & Wide-Gamut Matrix Transforms

For ACEScg workflows, the linear conversion between Rec.709 primaries and ACES AP1 primaries uses 3x3 chromatic adaptation matrices:

$$\begin{bmatrix} R_{\text{aces}} \\ G_{\text{aces}} \\ B_{\text{aces}} \end{bmatrix} = \begin{bmatrix} 0.613097 & 0.339523 & 0.047379 \\ 0.070194 & 0.916354 & 0.013452 \\ 0.020616 & 0.109570 & 0.869814 \end{bmatrix} \begin{bmatrix} R_{709} \\ G_{709} \\ B_{709} \end{bmatrix}$$

---

## 4. Container Tagging & QuickTime `colr` Atom

When exporting ProRes or QuickTime files, FFmpeg is instructed to write explicit NCLX/colr container metadata via [engine/color/color_metadata.py](file:///Volumes/VST%20SSD/corridor%20key%202.0/engine/color/color_metadata.py):
- `-color_primaries bt709`
- `-color_trc bt709` (or `iec61966-2-1` for sRGB)
- `-colorspace bt709`
- `-color_range tv` (limited 16–235) or `pc` (full 0–255)
- `-movflags +write_colr` (writes the QuickTime `colr` atom, preventing QuickTime Player, macOS Safari, and DaVinci Resolve from guessing or defaulting to incorrect gamma curves).

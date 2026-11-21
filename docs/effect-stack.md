# Non-Destructive Effect Stack Subsystem

## Overview
The Non-Destructive Effect Stack provides a flexible, layerable, and reorderable effects engine. Every effect operates on 32-bit floating-point or 8-bit RGBA image buffers, supports parameter keyframing, bypass toggling, and clean duplication.

## 10 Production Effects Specification

| Effect Name | Type ID | Parameters | Description |
| :--- | :--- | :--- | :--- |
| **Gaussian Blur** | `gaussian_blur` | `radius` (float) | Separable 2D Gaussian convolution kernel for soft defocus. |
| **Sharpen** | `sharpen` | `amount` (float), `radius` (float) | Unsharp masking filter enhancing edge high-frequency detail. |
| **Glow** | `glow` | `threshold` (float), `intensity` (float), `radius` (float) | Optical blooming filter over high-luminance pixels. |
| **Drop Shadow** | `drop_shadow` | `offset_x` (float), `offset_y` (float), `blur` (float), `opacity` (float), `color` (hex) | Alpha-derived directional shadow composited behind the layer. |
| **Gaussian Noise** | `gaussian_noise` | `amount` (float), `monochrome` (bool) | Additive Gaussian normal distribution sensor noise. |
| **Film Grain** | `film_grain` | `intensity` (float), `grain_size` (float) | Organic 35mm film silver halide grain emulation. |
| **Vignette** | `vignette` | `amount` (float), `feather` (float), `roundness` (float) | Optical lens peripheral luminance falloff. |
| **Hue / Saturation** | `hue_saturation` | `hue_shift` (degrees), `saturation` (float), `lightness` (float) | HSV colour space transformations. |
| **Color Correction** | `color_correction` | `brightness` (float), `contrast` (float), `gamma` (float) | Fast primary grade correction stage. |
| **Chroma Spill Suppression** | `chroma_spill_suppression` | `color` (green/blue), `strength` (float) | Edge despill algorithm for green or blue screen footage. |

## Stack Processing Architecture
1. **Pipeline Execution**: The effect stack iterates from bottom to top or top to bottom in designated stack order.
2. **Bypass / Mute**: Any effect can be toggled without discarding its parameters.
3. **Reordering**: Effects can be shifted up or down, instantly recomputing the final composite.
4. **Duplication**: Complete parameter snapshots can be duplicated to create multi-pass effects (e.g. multi-radius glow).

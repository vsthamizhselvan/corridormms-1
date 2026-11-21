# Alpha Matte Refinement Subsystem

## Overview
Alpha Matte Refinement bridges raw AI neural network segmentation output from CorridorKey 2.0 with professional feature film quality edge standards. It addresses boundary softness, green/blue chroma fringing, haloing, and optical edge contamination.

## Matte Operations Pipeline
The refinement pipeline executes the following stages in strict order:

```
Raw AI Alpha Matte
        │
        ▼
[Contrast & Brightness Adjustment]
        │
        ▼
[Alpha Threshold Pedestal Cut]
        │
        ▼
[Morphological Choke / Expansion]
        │
        ▼
[Edge Softness & Gaussian Feather]
        │
        ▼
[Chroma Despill Suppression]
        │
        ▼
[Edge Color Decontamination]
        │
        ▼
Refined Premultiplied RGBA Plate
```

### Mathematical Formulations

#### 1. Contrast and Brightness
Density is remapped around a midpoint of 0.5:
$$\alpha' = \text{clamp}((\alpha - 0.5) \cdot \text{contrast} + 0.5 + \text{brightness}, 0.0, 1.0)$$

#### 2. Threshold Pedestal Cut
Suppresses low-level neural network haze:
$$\alpha'' = \begin{cases} 
0.0, & \alpha' < \theta \\
\frac{\alpha' - \theta}{1.0 - \theta}, & \alpha' \ge \theta 
\end{cases}$$

#### 3. Morphological Choke / Expand
- **Choke** (Erosion, $\text{choke} < 0$): Pulls the matte boundary inwards to hide green edge halos.
- **Expand** (Dilation, $\text{choke} > 0$): Expands fine hair strands and semi-transparent details.

#### 4. Chroma Despill Algorithms
- **Green Screen Despill**:
  $$G' = \min\left(G, \frac{R + B}{2} + (1.0 - \text{spill\_strength}) \cdot \max\left(0, G - \frac{R + B}{2}\right)\right)$$
- **Blue Screen Despill**:
  $$B' = \min\left(B, \frac{R + G}{2} + (1.0 - \text{spill\_strength}) \cdot \max\left(0, B - \frac{R + G}{2}\right)\right)$$

#### 5. Edge Decontamination
Calculates the spill excess and restores the neutral foreground luminance across semi-transparent edge pixels ($\alpha < 1.0$):
$$C_{\text{decon}} = C - k \cdot (1.0 - \alpha) \cdot \Delta_{\text{spill}}$$

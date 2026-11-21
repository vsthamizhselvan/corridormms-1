# Colour Correction and Grading Subsystem

## Overview
CorridorKey 2.0 Desktop incorporates a professional non-destructive primary and secondary colour grading pipeline adhering to the ASC-CDL (American Society of Cinematographers Color Decision List) specification and feature-film grading standards.

## Grading Operations

### 1. Exposure (EV)
Exposure scaling is performed in linear radiometric space:
$$C_{\text{linear}} = C_{\text{in}} \cdot 2^{\text{EV}}$$
- $+1.0\text{ EV}$ precisely doubles scene luminance.
- $-1.0\text{ EV}$ precisely halves scene luminance.

### 2. ASC-CDL Lift / Gamma / Gain
Operates on the tonal ranges:
$$C_{\text{cdl}} = \left(\max(0.0, C \cdot \text{gain} + \text{lift})\right)^{\frac{1}{\text{gamma}}}$$
- **Lift**: Shifts black pedestal / shadows without crushing highlights.
- **Gamma**: Adjusts midtones smoothly without shifting absolute 0.0 or 1.0 points.
- **Gain**: Scales overall highlights and peak luminance.

### 3. Highlights and Shadows Tone Control
Non-linear soft-knee adjustments target shadow details and highlight clipping:
$$S(C) = C + \text{shadows} \cdot (1 - C)^2 \cdot 0.5$$
$$H(C) = C + \text{highlights} \cdot C^2 \cdot 0.5$$

### 4. White Balance (Temperature and Tint)
Simulates Planckian chromaticity shifts:
- **Temperature**: Shifts between warm amber (boosts Red, decreases Blue) and cool azure (boosts Blue, decreases Red).
- **Tint**: Shifts along the orthogonal green-magenta chromaticity axis.

### 5. Saturation and Vibrance
- **Saturation**: Scales chromatic distance from luminance $Y = 0.2126 R + 0.7152 G + 0.0722 B$.
- **Vibrance**: Applies an adaptive non-linear chroma boost that prioritizes desaturated pixels while preserving skin tones and saturated colors from clipping.

### 6. Per-Channel RGB Multipliers
Fine-tune color balance by directly scaling R, G, and B components independently.

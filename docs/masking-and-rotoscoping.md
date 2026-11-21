# Masking and Rotoscoping Subsystem

## Overview
The Vector Masking and Rotoscoping engine in CorridorKey 2.0 Desktop provides non-destructive, resolution-independent vector shapes for isolating subjects, cutting garbage mattes, and refining AI keying boundaries.

## Architecture
Masks are evaluated non-destructively as normalized coordinate paths $[0.0, 1.0]$ and rasterized to match the target plate resolution.

### Supported Mask Types
1. **Rectangle**: Defined by top-left and bottom-right corner vertices.
2. **Ellipse**: Defined by center coordinates and semi-major/semi-minor radii axes.
3. **Polygon**: Multi-point closed vector polygon defined by an arbitrary sequence of points.
4. **Bezier**: Cubic Bezier curves with independent tangent in/out handle controls:
   $$B(t) = (1-t)^3 P_0 + 3(1-t)^2 t P_1 + 3(1-t) t^2 P_2 + t^3 P_3, \quad t \in [0, 1]$$
5. **Freehand**: High-density polygon sampled from direct pen or cursor input.

### Mask Parameter Controls
- **Mode**: `Add` (union) or `Subtract` (cutout subtraction).
- **Inverted**: Inverts mask polarity ($M_{inv} = 1.0 - M$).
- **Feather**: Gaussian blur standard deviation $\sigma = \frac{\text{feather}}{3}$ producing a smooth edge roll-off.
- **Expansion / Choke**: Morphological dilation or erosion in pixel space:
  - Expansion $> 0$: `cv2.dilate` with circular structuring element.
  - Choke $< 0$: `cv2.erode` with circular structuring element.
- **Opacity**: Global scalar multiplier $[0.0, 1.0]$ scaling the mask density.
- **Spatial Transforms**: PosX, PosY offset and uniform Scale.

## Boolean Combination
Multiple masks in the stack are composited sequentially:
$$M_{k} = \begin{cases}
\min(1.0, M_{k-1} + M_{\text{curr}}), & \text{mode} = \text{Add} \\
\max(0.0, M_{k-1} - M_{\text{curr}}), & \text{mode} = \text{Subtract}
\end{cases}$$

## GPU Real-Time Shader Integration
In the WebGL2 GPU viewport, masks are uploaded as vector uniforms and clipped directly in the fragment shader (`shaders.ts`), allowing zero-latency preview during timeline playback and interactive scrubbing.

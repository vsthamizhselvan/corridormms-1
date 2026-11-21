# Layer-Based Compositing Subsystem

## Overview
CorridorKey 2.0 Desktop supports multi-layer 2D compositing with professional blending modes, affine coordinate transformations, and alpha management.

## Layer Types
- **Video Layer**: Dynamic video frame decoded via FFmpeg pipeline.
- **Image Layer**: Static graphic, matte painting, or still plate.
- **Solid Layer**: Generative solid colour background canvas.
- **AI Foreground**: Processed alpha key plate extracted by the CorridorKey neural network.

## Blend Modes Math

Given base pixel $B$ and foreground pixel $F$ normalized in $[0.0, 1.0]$:

1. **Normal**:
   $$R = F \cdot \alpha_F + B \cdot (1 - \alpha_F)$$
2. **Multiply**:
   $$R = B \times F$$
3. **Screen**:
   $$R = 1 - (1 - B) \times (1 - F)$$
4. **Add (Linear Dodge)**:
   $$R = \min(1.0, B + F)$$
5. **Overlay**:
   $$R = \begin{cases}
   2 \times B \times F, & B < 0.5 \\
   1 - 2 \times (1 - B) \times (1 - F), & B \ge 0.5
   \end{cases}$$
6. **Difference**:
   $$R = |B - F|$$

## Spatial Affine Transformations
Each layer has an affine transformation model:
$$\begin{bmatrix} x' \\ y' \\ 1 \end{bmatrix} = \mathbf{T}(x_0, y_0) \cdot \mathbf{R}(\theta) \cdot \mathbf{S}(s_x, s_y) \cdot \mathbf{T}(-a_x, -a_y) \cdot \begin{bmatrix} x \\ y \\ 1 \end{bmatrix}$$
- **Translation**: PosX, PosY offset in target pixel space.
- **Rotation**: Angle $\theta$ in degrees around the anchor point.
- **Scale**: Independent ScaleX and ScaleY factors.
- **Anchor Point**: Normalized $(a_x, a_y)$ origin of rotation and scaling.

## Straight vs Premultiplied Alpha
The compositing engine natively supports:
- **Straight Alpha**: RGB color values are independent of the alpha channel.
- **Premultiplied Alpha**: RGB color values are pre-scaled by alpha ($C_{\text{premult}} = C \cdot \alpha$), preventing dark fringing when filtering and blending.

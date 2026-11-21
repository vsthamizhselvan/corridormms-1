# Keyframe Animation Engine — CorridorKey 2.0 Desktop

## 1. Parameter Animation Architecture

Every clip instance manages independent `PropertyTrack` objects for spatial and optical transformations:
- `posX`: Pixel horizontal offset (default 0.0)
- `posY`: Pixel vertical offset (default 0.0)
- `scale`: Size percentage (default 100.0%)
- `rotation`: Angle in degrees (default 0.0°)
- `opacity`: Transparency percentage (0.0% to 100.0%, default 100.0%)

---

## 2. Interpolation Modes

`KeyframeInterpolation` supports three industry-standard curve types:

### 1. Hold
Maintains the keyframe's value constantly until the next keyframe tick is reached. Ideal for discrete cuts, visibility toggles, and step changes.

### 2. Linear
Interpolates values along a direct straight line between adjacent keyframe times:
$$V(t) = V_1 + (V_2 - V_1) \times \frac{t - t_1}{t_2 - t_1}$$

### 3. Cubic Bezier Easing
Computes smooth acceleration and deceleration using standard cubic Bezier equations parameterized by tangents $(p_1, p_2)$:
$$B(u) = (1-u)^3 p_0 + 3(1-u)^2 u\, p_1 + 3(1-u) u^2\, p_2 + u^3 p_3 \quad \text{for } u \in [0, 1]$$

---

## 3. Boundary Clamping & Binary Search

Evaluation uses binary search ($O(\log K)$) across sorted keyframe frame ticks. Frames before the first keyframe hold the first keyframe's value; frames beyond the final keyframe hold the final keyframe's value.

# Phase 8 Architecture — Advanced VFX Compositing System

## 1. Non-Destructive Compositing Pipeline

The CorridorKey 2.0 Desktop VFX compositing pipeline processes each layer through a deterministic, modular transformation chain:

```
+-------------------------------------------------------------------------+
|                              Media Source                               |
|        (RGB Video Frame / Image Plate / Color Generator Plate)          |
+------------------------------------+------------------------------------+
                                     |
+------------------------------------v------------------------------------+
|                      AI Foreground Extraction                           |
|        (CorridorKey C-RADIOv4 / MoGe-2 / RVM Inference Engine)          |
+------------------------------------+------------------------------------+
                                     |
+------------------------------------v------------------------------------+
|                       Alpha Matte Refinement                            |
| (Choke/Expand, Edge Blur, Softness, Edge Decontamination, Despill)      |
+------------------------------------+------------------------------------+
                                     |
+------------------------------------v------------------------------------+
|                        Masks and Rotoscoping                            |
|   (Rectangle, Ellipse, Freehand, Bezier, Polygon - Add/Subtract/Feather)|
+------------------------------------+------------------------------------+
                                     |
+------------------------------------v------------------------------------+
|                      Colour Correction & Grading                        |
|  (Lift/Gamma/Gain, Temp/Tint, Exposure, Highlights/Shadows, Sat/Vib)    |
+------------------------------------+------------------------------------+
                                     |
+------------------------------------v------------------------------------+
|                         Effects Processing Stack                        |
| (Blur, Sharpen, Glow, Drop Shadow, Noise, Grain, Vignette, Spill, etc.) |
+------------------------------------+------------------------------------+
                                     |
+------------------------------------v------------------------------------+
|                        Layer-Based Compositing                          |
|   (Normal, Multiply, Screen, Add, Overlay, Difference Blend Modes)      |
+------------------------------------+------------------------------------+
                                     |
+------------------------------------v------------------------------------+
|                            Final Composite                              |
|           (WebGL2 Real-time GPU Viewport / Master File Export)          |
+-------------------------------------------------------------------------+
```

---

## 2. Mathematical Formulations

### 2.1 Alpha Matte Refinement

1. **Morphological Choke / Expand:**
   Given a matte $M(x, y) \in [0, 1]$ and structuring element $B_r$ of radius $r$:
   $$\text{Expand}(M) = M \oplus B_r = \max_{(dx, dy) \in B_r} M(x + dx, y + dy)$$
   $$\text{Choke}(M) = M \ominus B_r = \min_{(dx, dy) \in B_r} M(x + dx, y + dy)$$
2. **Edge Feathering:**
   Feathering applies a normalized Gaussian kernel $G_\sigma$:
   $$M_{\text{feather}} = M * G_\sigma \quad \text{where } \sigma = \frac{\text{feather\_pixels}}{2.57}$$
3. **Contrast & Pedestal / Threshold:**
   $$M_{\text{thresh}} = \text{clamp}\left( \frac{M - t_{\text{low}}}{t_{\text{high}} - t_{\text{low}}}, 0, 1 \right)$$
   $$M_{\text{contrast}} = \text{clamp}\left( 0.5 + (M_{\text{thresh}} - 0.5) \times \gamma_{\text{contrast}}, 0, 1 \right)$$

---

### 2.2 Colour Correction (Lift / Gamma / Gain & Film Curves)

Let $C_{\text{in}} \in [0, 1]$ be a normalized color channel:
1. **Lift, Gamma, Gain (ASC-CDL derivative):**
   $$C_1 = \text{Lift} \times (1 - C_{\text{in}}) + \text{Gain} \times C_{\text{in}}$$
   $$C_2 = \max(C_1, 0.0)^{\frac{1}{\text{Gamma}}}$$
2. **Exposure Adjustment:**
   $$C_3 = C_2 \times 2^{\text{exposure\_ev}}$$
3. **Temperature & Tint (White Balance Matrix):**
   Shifts chromaticity along the Planckian blackbody locus (Temperature) and magenta/green axis (Tint):
   $$\Delta R = 0.4 \times T_{\text{temp}} - 0.1 \times T_{\text{tint}}, \quad \Delta B = -0.4 \times T_{\text{temp}} - 0.1 \times T_{\text{tint}}, \quad \Delta G = 0.2 \times T_{\text{tint}}$$

---

### 2.3 Blend Modes & Alpha Compositing

For foreground layer $F$ with alpha $\alpha_F$ over background layer $B$ with alpha $\alpha_B$:

| Blend Mode | Equation $f(B, F)$ |
| :--- | :--- |
| **Normal** | $F$ |
| **Multiply** | $B \times F$ |
| **Screen** | $1 - (1 - B) \times (1 - F)$ |
| **Add** | $\min(1.0, B + F)$ |
| **Overlay** | $\begin{cases} 2 \times B \times F & \text{if } B < 0.5 \\ 1 - 2 \times (1 - B) \times (1 - F) & \text{otherwise} \end{cases}$ |
| **Difference** | $|B - F|$ |

**Final Composite (Over Operator with straight or premultiplied alpha):**
$$\alpha_{\text{out}} = \alpha_F + \alpha_B \times (1 - \alpha_F)$$
$$C_{\text{out}} = \frac{f(B, F) \times \alpha_F + B \times \alpha_B \times (1 - \alpha_F)}{\alpha_{\text{out}}}$$

---

## 3. Node-Based Execution Graph (DAG)

The node compositing engine represents processing as a Directed Acyclic Graph $G = (V, E)$:
1. **Nodes ($V$):** Computational units with defined input and output sockets.
2. **Edges ($E$):** Data connections routing image buffers, alphas, or vectors.
3. **Topological Sort:** Resolves dependency ordering:
   $$\text{Order} = \text{TopologicalSort}(G)$$
4. **Cycle Detection:** Tarjan's or Kahn's algorithm verifies that the graph contains zero feedback loops before execution.

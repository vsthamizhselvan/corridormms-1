# CorridorKey 2.0 Desktop — Viewer Compositing & Comparison Tools

This document specifies the background compositing modes, comparison tools, and grading controls implemented in CorridorKey 2.0 Desktop.

---

## 1. Transparency Background Modes

The viewer allows VFX artists to evaluate matte quality against multiple background environments:

| Mode | Visual Environment | Purpose |
| :--- | :--- | :--- |
| **Checkerboard** | Procedural screen-space dual-gray tiles ($16\text{px}$–$32\text{px}$) | Standard VFX transparency inspection without scaling blur. |
| **Solid Black** | Pure RGB $(0, 0, 0)$ | Inspects edge fringing, white halos, and semi-transparent hair strands. |
| **Solid White** | Pure RGB $(1, 1, 1)$ | Inspects dark fringes, spill suppression artifacts, and shadow detail. |
| **Custom Color** | User-selected RGB hex color | Matches specific production background plates or green/blue screen references. |
| **Linear Gradient** | Two-stop customizable gradient ($45^\circ$ diagonal) | Simulates dynamic lighting and sky-to-ground falloff. |
| **Texture Plate** | Imported image or video background | Full contextual composite verification. |

---

## 2. Real-Time Comparison Tools

To facilitate critical A/B inspection before final export:

### 2.1 Interactive Split Wipe (A/B)
- Displays original camera plate on the left and processed composite on the right.
- Features a draggable blue divider line with a centered anchor badge ($↔$).
- Artists can drag the divider freely from $0\%$ to $100\%$ across the plate to inspect fine edge transitions.

### 2.2 Side-by-Side (2-Up)
- Splits the viewport into two synchronized horizontal frames.
- Left half displays the full source plate; right half displays the full composite.

### 2.3 Difference Matte
- Computes pixel absolute delta:
  $$\Delta = 3.0 \times \left| \text{RGB}_{\text{original}} - \text{RGB}_{\text{composite}} \right|$$
- Amplified $3\times$ to highlight subtle edge artifacts, despill color shifts, and compression discrepancies.

---

## 3. Real-Time Color Grading & Matte Controls

- **Matte Contrast:** Pivot around $0.5$ midtone to tighten semi-transparent areas.
- **Alpha Pedestal / Threshold:** Suppresses faint background noise ($0.0 \dots 0.9$).
- **Invert Matte:** Inverts alpha channel for background extraction.
- **Exposure:** $-3.0\text{ EV}$ to $+3.0\text{ EV}$ logarithmic gain for shadow and highlight checking.
- **Saturation:** $0\%$ (Grayscale) to $200\%$ to inspect chromatic edge halos.

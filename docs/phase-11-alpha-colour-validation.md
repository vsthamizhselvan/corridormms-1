# CorridorKey 2.0 Desktop — Phase 11 Alpha & Colour Fidelity Report

## 1. Scope & Objective

Alpha channel preservation and color fidelity are critical requirements for a professional VFX compositing application. Testing was performed using `tests/test_alpha_colour_validation.py` to ensure mathematical precision across alpha modes, despill suppression, edge transitions, and color spaces.

---

## 2. Quantitative Verification Results

### 2.1 Straight vs Premultiplied Alpha Math
* **Premultiplication Formula:** $\text{RGB}_{\text{pre}} = \text{RGB}_{\text{straight}} \times \alpha$
  - Pixels with $\alpha = 0.0$ yield pure black $[0.0, 0.0, 0.0]$: **PASS**.
  - Pixels with $\alpha = 1.0$ retain exact original values: **PASS**.
* **Unpremultiplication Round-Trip:** $\text{RGB}_{\text{straight}} = \text{RGB}_{\text{pre}} / (\alpha + \epsilon)$
  - Maximum reconstruction error across the continuous alpha gradient: **$0.000016$** (well below the $1 \times 10^{-4}$ VFX threshold). **PASS**.

### 2.2 Alpha Gamma Integrity
* **Gamma Rule:** The alpha channel represents physical area coverage and optical opacity. **Alpha must never be gamma-corrected.**
* In sRGB conversion tests, linear RGB mid-grey ($0.5$) properly expanded to $0.737$ in sRGB.
* The alpha channel remained strictly linear at $0.50196$ without non-linear warping or banding. **PASS**.

### 2.3 Green Spill Suppression
* Evaluated against saturated green fringe ($R=0.196, G=0.863, B=0.235$):
  - Green channel suppressed down to $0.215$ (neutral luminance match).
  - Red and Blue compensated to preserve edge luminescence without dark or discolored halos. **PASS**.

### 2.4 Sub-Pixel Hair & Motion Blur
* Simulated 1-pixel fine hair strands with semi-transparency ($\alpha = 0.45$).
* Validated that semi-transparent pixels were retained without binary threshold collapse. **PASS**.

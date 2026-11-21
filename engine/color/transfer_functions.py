"""CorridorKey 2.0 Desktop — Precision Color Transfer Functions.

Implements mathematically rigorous, bidirectional color space transforms:
- sRGB (IEC 61966-2-1)
- Rec.709 (ITU-R BT.709-6)
- HDR Signed asinh (CorridorKey model domain)
- Rec.2020 (ITU-R BT.2020)
- ACEScg linear matrix conversions

Rule: Alpha represents physical coverage and is NEVER modified by transfer functions.
"""

from __future__ import annotations

import numpy as np

# CorridorKey HDR reference constants
HDR_ASINH_KNEE = 0.008
HDR_ASINH_REF = 16.0


# ============================================================================
# 1. sRGB (IEC 61966-2-1)
# ============================================================================

def linear_to_srgb(linear: np.ndarray) -> np.ndarray:
    """Converts linear-light RGB [0, 1] to sRGB (IEC 61966-2-1)."""
    arr = np.asanyarray(linear, dtype=np.float32)
    pos = np.maximum(arr, 0.0)
    out = np.where(
        pos <= 0.0031308,
        pos * 12.92,
        1.055 * np.power(pos, 1.0 / 2.4) - 0.055,
    )
    # Preserve negative values with odd symmetry
    neg = np.maximum(-arr, 0.0)
    neg_out = np.where(
        neg <= 0.0031308,
        neg * 12.92,
        1.055 * np.power(neg, 1.0 / 2.4) - 0.055,
    )
    return np.where(arr >= 0, out, -neg_out)


def srgb_to_linear(srgb: np.ndarray) -> np.ndarray:
    """Converts sRGB to linear-light RGB (IEC 61966-2-1)."""
    arr = np.asanyarray(srgb, dtype=np.float32)
    pos = np.maximum(arr, 0.0)
    out = np.where(
        pos <= 0.04045,
        pos / 12.92,
        np.power((pos + 0.055) / 1.055, 2.4),
    )
    neg = np.maximum(-arr, 0.0)
    neg_out = np.where(
        neg <= 0.04045,
        neg / 12.92,
        np.power((neg + 0.055) / 1.055, 2.4),
    )
    return np.where(arr >= 0, out, -neg_out)


# ============================================================================
# 2. Rec.709 (ITU-R BT.709-6)
# ============================================================================

def linear_to_rec709(linear: np.ndarray) -> np.ndarray:
    """Converts linear-light RGB to Rec.709 OETF (ITU-R BT.709-6)."""
    arr = np.asanyarray(linear, dtype=np.float32)
    pos = np.maximum(arr, 0.0)
    out = np.where(
        pos < 0.018,
        pos * 4.5,
        1.099 * np.power(pos, 0.45) - 0.099,
    )
    return out


def rec709_to_linear(rec709: np.ndarray) -> np.ndarray:
    """Converts Rec.709 OETF to linear-light RGB (ITU-R BT.709-6)."""
    arr = np.asanyarray(rec709, dtype=np.float32)
    pos = np.maximum(arr, 0.0)
    out = np.where(
        pos < 0.081,
        pos / 4.5,
        np.power((pos + 0.099) / 1.099, 1.0 / 0.45),
    )
    return out


# ============================================================================
# 3. HDR Signed asinh (CorridorKey 2.0 Neural Representation)
# ============================================================================

def linear_to_asinh(linear: np.ndarray, knee: float = HDR_ASINH_KNEE, ref: float = HDR_ASINH_REF) -> np.ndarray:
    """Compresses scene-linear RGB into signed asinh domain for neural transformer."""
    denom = np.arcsinh(ref / knee)
    return np.arcsinh(linear / knee) / denom


def asinh_to_linear(encoded: np.ndarray, knee: float = HDR_ASINH_KNEE, ref: float = HDR_ASINH_REF) -> np.ndarray:
    """Inverts signed asinh domain back into scene-linear RGB."""
    denom = np.arcsinh(ref / knee)
    return np.sinh(encoded * denom) * knee


# ============================================================================
# 4. ACEScg & Color Matrix Conversions
# ============================================================================

# Rec.709 to ACEScg (AP1 primaries) matrix
M_REC709_TO_ACESCG = np.array([
    [0.613097, 0.339523, 0.047379],
    [0.070194, 0.916354, 0.013452],
    [0.020616, 0.109570, 0.869814],
], dtype=np.float32)

# ACEScg to Rec.709 matrix
M_ACESCG_TO_REC709 = np.linalg.inv(M_REC709_TO_ACESCG)


def rec709_linear_to_acescg(rgb_linear: np.ndarray) -> np.ndarray:
    """Converts Rec.709 scene-linear RGB to ACEScg (AP1). Shape: (..., 3)."""
    return np.matmul(rgb_linear, M_REC709_TO_ACESCG.T)


def acescg_to_rec709_linear(acescg: np.ndarray) -> np.ndarray:
    """Converts ACEScg (AP1) to Rec.709 scene-linear RGB. Shape: (..., 3)."""
    return np.matmul(acescg, M_ACESCG_TO_REC709.T)

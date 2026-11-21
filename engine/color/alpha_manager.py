"""CorridorKey 2.0 Desktop — Transparency and Alpha Channel Management.

Handles:
- Straight vs. Premultiplied alpha conversions
- Edge despill (green/blue spill suppression)
- Dynamic range clamping and NaN prevention
- Statistical validation of alpha matte integrity
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Tuple

import numpy as np


class AlphaMode(str, Enum):
    STRAIGHT = "straight"
    PREMULTIPLIED = "premultiplied"


@dataclass
class AlphaValidationResult:
    has_alpha: bool
    is_valid: bool
    min_value: float
    max_value: float
    mean_value: float
    transparent_percent: float
    opaque_percent: float
    semi_transparent_percent: float
    details: str


def premultiply_alpha(rgb: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    """Multiplies RGB channels by alpha matte. Shapes: rgb (..., 3), alpha (..., 1) or (...)."""
    a = np.clip(alpha, 0.0, 1.0)
    if a.ndim == rgb.ndim - 1:
        a = a[..., None]
    return rgb * a


def unpremultiply_alpha(rgb: np.ndarray, alpha: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    """Recovers straight RGB by dividing by alpha."""
    a = np.maximum(alpha, 0.0)
    if a.ndim == rgb.ndim - 1:
        a = a[..., None]
    return rgb / (a + eps)


def despill_green(rgb: np.ndarray, strength: float = 0.5) -> np.ndarray:
    """Suppresses green spill on transparent fringes using average despill algorithm."""
    if strength <= 0.0:
        return rgb
    r = rgb[..., 0]
    g = rgb[..., 1]
    b = rgb[..., 2]
    spill = np.maximum(g - (r + b) * 0.5, 0.0)

    despilled_r = r + spill * (0.5 * strength)
    despilled_g = g - spill * strength
    despilled_b = b + spill * (0.5 * strength)

    return np.stack([despilled_r, despilled_g, despilled_b], axis=-1)


def assemble_rgba(
    rgb: np.ndarray,
    alpha: np.ndarray,
    alpha_mode: AlphaMode = AlphaMode.STRAIGHT,
    despill_strength: float = 0.0,
) -> np.ndarray:
    """Assembles a 4-channel RGBA frame from separate RGB and Alpha components."""
    clean_rgb = despill_green(rgb, strength=despill_strength) if despill_strength > 0 else rgb
    clean_a = np.clip(alpha, 0.0, 1.0)
    if clean_a.ndim == 2:
        clean_a = clean_a[..., None]

    if alpha_mode == AlphaMode.PREMULTIPLIED:
        clean_rgb = premultiply_alpha(clean_rgb, clean_a)

    return np.concatenate([clean_rgb, clean_a], axis=-1)


def validate_alpha_matte(alpha: np.ndarray) -> AlphaValidationResult:
    """Inspects an alpha matte array and checks for transparency distribution."""
    a = np.asarray(alpha, dtype=np.float32)
    if a.max() > 1.01:
        a = a / 255.0  # normalize if uint8

    min_val = float(a.min())
    max_val = float(a.max())
    mean_val = float(a.mean())

    total_pixels = a.size
    transparent_count = int(np.sum(a < 0.01))
    opaque_count = int(np.sum(a > 0.99))
    semi_count = total_pixels - transparent_count - opaque_count

    trans_pct = (transparent_count / total_pixels) * 100.0
    opaque_pct = (opaque_count / total_pixels) * 100.0
    semi_pct = (semi_count / total_pixels) * 100.0

    # A valid key typically has some transparent background and some opaque foreground
    is_valid = (trans_pct > 0.5) and (opaque_pct > 0.5)

    details = (
        f"Alpha matte analysis: {opaque_pct:.1f}% opaque, "
        f"{trans_pct:.1f}% transparent, {semi_pct:.1f}% soft edge pixels. "
        f"Range: [{min_val:.3f}, {max_val:.3f}]."
    )

    return AlphaValidationResult(
        has_alpha=True,
        is_valid=is_valid,
        min_value=min_val,
        max_value=max_val,
        mean_value=mean_val,
        transparent_percent=trans_pct,
        opaque_percent=opaque_pct,
        semi_transparent_percent=semi_pct,
        details=details,
    )

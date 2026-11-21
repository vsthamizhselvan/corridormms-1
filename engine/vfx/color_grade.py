"""CorridorKey 2.0 Desktop — Professional Colour Correction & Grading Subsystem.

Provides non-destructive color processing: ASC-CDL Lift/Gamma/Gain, Exposure EV,
Highlights/Shadows tone mapping, White Balance (Temperature/Tint), and Saturation/Vibrance.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

import numpy as np


@dataclass
class ColorGradeSettings:
    # Primary exposure & tones
    exposure: float = 0.0  # EV (-3.0 to +3.0)
    contrast: float = 1.0  # 0.2 to 2.5
    brightness: float = 0.0  # -0.5 to 0.5
    highlights: float = 0.0  # -1.0 to 1.0
    shadows: float = 0.0  # -1.0 to 1.0
    whites: float = 0.0  # -1.0 to 1.0
    blacks: float = 0.0  # -1.0 to 1.0

    # Color balance & temperature
    temperature: float = 0.0  # -1.0 (cool/blue) to +1.0 (warm/orange)
    tint: float = 0.0  # -1.0 (green) to +1.0 (magenta)
    saturation: float = 1.0  # 0.0 to 2.5
    vibrance: float = 0.0  # -1.0 to 1.0

    # Lift / Gamma / Gain (ASC-CDL standard)
    lift: float = 0.0  # Shadows offset (-0.5 to 0.5)
    gamma: float = 1.0  # Midtones power (0.2 to 3.0)
    gain: float = 1.0  # Highlights multiplier (0.0 to 3.0)

    # RGB Channel multiplier
    channel_r: float = 1.0
    channel_g: float = 1.0
    channel_b: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ColorGradeSettings":
        return cls(
            exposure=float(d.get("exposure", 0.0)),
            contrast=float(d.get("contrast", 1.0)),
            brightness=float(d.get("brightness", 0.0)),
            highlights=float(d.get("highlights", 0.0)),
            shadows=float(d.get("shadows", 0.0)),
            whites=float(d.get("whites", 0.0)),
            blacks=float(d.get("blacks", 0.0)),
            temperature=float(d.get("temperature", 0.0)),
            tint=float(d.get("tint", 0.0)),
            saturation=float(d.get("saturation", 1.0)),
            vibrance=float(d.get("vibrance", 0.0)),
            lift=float(d.get("lift", 0.0)),
            gamma=float(d.get("gamma", 1.0)),
            gain=float(d.get("gain", 1.0)),
            channel_r=float(d.get("channel_r", 1.0)),
            channel_g=float(d.get("channel_g", 1.0)),
            channel_b=float(d.get("channel_b", 1.0)),
        )


def apply_color_grade(image: np.ndarray, settings: Optional[ColorGradeSettings] = None) -> np.ndarray:
    """Applies non-destructive colour correction and grading to an RGB or RGBA float image.

    Args:
        image: Float32 image in [0.0, 1.0], shape (H, W, 3) or (H, W, 4).
        settings: ColorGradeSettings instance.

    Returns:
        Graded float32 image in [0.0, 1.0].
    """
    if settings is None:
        settings = ColorGradeSettings()

    img = image.astype(np.float32).copy()
    has_alpha = img.shape[2] == 4
    rgb = img[:, :, :3]
    alpha = img[:, :, 3] if has_alpha else None

    # 1. Lift, Gamma, Gain (ASC-CDL)
    if abs(settings.lift) > 0.001 or abs(settings.gain - 1.0) > 0.001:
        # Lift * (1 - x) + Gain * x
        rgb = settings.lift * (1.0 - rgb) + settings.gain * rgb
        rgb = np.clip(rgb, 0.0, 1.0)

    if abs(settings.gamma - 1.0) > 0.001:
        # Avoid division by zero
        inv_gamma = 1.0 / max(0.01, settings.gamma)
        rgb = np.power(np.maximum(rgb, 0.0), inv_gamma)

    # 2. Exposure Scaling (EV stops)
    if abs(settings.exposure) > 0.001:
        ev_scale = math.pow(2.0, settings.exposure)
        rgb = rgb * ev_scale

    # 3. Brightness & Contrast
    if abs(settings.brightness) > 0.001:
        rgb = rgb + settings.brightness

    if abs(settings.contrast - 1.0) > 0.001:
        rgb = (rgb - 0.5) * settings.contrast + 0.5

    # 4. Tones: Highlights, Shadows, Whites, Blacks
    if abs(settings.highlights) > 0.001 or abs(settings.shadows) > 0.001:
        luma = 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]
        # Smooth tone weighting
        shadow_weight = np.clip((0.5 - luma) * 2.0, 0.0, 1.0)[:, :, np.newaxis]
        highlight_weight = np.clip((luma - 0.5) * 2.0, 0.0, 1.0)[:, :, np.newaxis]
        rgb += shadow_weight * (settings.shadows * 0.2) + highlight_weight * (settings.highlights * 0.2)

    if abs(settings.blacks) > 0.001 or abs(settings.whites) > 0.001:
        rgb = rgb * (1.0 + settings.whites * 0.2) + (settings.blacks * 0.1)

    # 5. Temperature & Tint
    if abs(settings.temperature) > 0.001 or abs(settings.tint) > 0.001:
        # Warm adds red, removes blue. Tint adds magenta (red+blue), removes green.
        delta_r = 0.3 * settings.temperature + 0.2 * settings.tint
        delta_g = -0.3 * settings.tint
        delta_b = -0.3 * settings.temperature + 0.2 * settings.tint
        rgb[:, :, 0] += delta_r
        rgb[:, :, 1] += delta_g
        rgb[:, :, 2] += delta_b

    # 6. RGB Channel Multipliers
    if abs(settings.channel_r - 1.0) > 0.001:
        rgb[:, :, 0] *= settings.channel_r
    if abs(settings.channel_g - 1.0) > 0.001:
        rgb[:, :, 1] *= settings.channel_g
    if abs(settings.channel_b - 1.0) > 0.001:
        rgb[:, :, 2] *= settings.channel_b

    # 7. Saturation & Vibrance
    rgb = np.clip(rgb, 0.0, 1.0)
    luma = 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]
    luma_3d = np.repeat(luma[:, :, np.newaxis], 3, axis=2)

    # Standard Saturation
    if abs(settings.saturation - 1.0) > 0.001:
        rgb = luma_3d + (rgb - luma_3d) * settings.saturation

    # Vibrance: boost less-saturated colors more than already saturated ones
    if abs(settings.vibrance) > 0.001:
        max_ch = np.max(rgb, axis=2)
        min_ch = np.min(rgb, axis=2)
        current_sat = np.clip(max_ch - min_ch, 0.0, 1.0)[:, :, np.newaxis]
        vibrance_factor = 1.0 + settings.vibrance * (1.0 - current_sat)
        rgb = luma_3d + (rgb - luma_3d) * vibrance_factor

    rgb = np.clip(rgb, 0.0, 1.0)

    if has_alpha and alpha is not None:
        return np.dstack([rgb, alpha])
    return rgb

"""CorridorKey 2.0 Desktop — Color Management Pipeline.

Coordinates color space conversions between camera footage, CorridorKey AI neural inference
(signed asinh scene-linear), and final export color spaces (Rec.709, sRGB, ACEScg, Linear HDR).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, Optional, Tuple

import numpy as np

from engine.color.color_metadata import ColorTagConfig, get_color_tags
from engine.color.transfer_functions import (
    acescg_to_rec709_linear,
    asinh_to_linear,
    linear_to_asinh,
    linear_to_rec709,
    linear_to_srgb,
    rec709_linear_to_acescg,
    rec709_to_linear,
    srgb_to_linear,
)


@dataclass
class ColorConversionReport:
    source_space: str
    target_space: str
    transforms_applied: list[str]
    linear_compositing_used: bool
    ffmpeg_color_tags: ColorTagConfig

    def to_dict(self) -> Dict:
        return {
            "source_space": self.source_space,
            "target_space": self.target_space,
            "transforms_applied": self.transforms_applied,
            "linear_compositing_used": self.linear_compositing_used,
            "tags": asdict(self.ffmpeg_color_tags),
        }


class ColorManager:
    """Manages color transforms across ingest, inference, and export."""

    def __init__(self, source_space: str = "rec709", target_space: str = "rec709"):
        self.source_space = source_space.lower()
        self.target_space = target_space.lower()

    def input_to_linear(self, rgb: np.ndarray) -> np.ndarray:
        """Converts incoming SDR RGB [0, 1] into scene-linear RGB."""
        arr = np.clip(rgb, 0.0, 1.0).astype(np.float32)
        if "srgb" in self.source_space:
            return srgb_to_linear(arr)
        elif "rec709" in self.source_space or "bt709" in self.source_space:
            return rec709_to_linear(arr)
        elif "acescg" in self.source_space:
            return acescg_to_rec709_linear(arr)
        # Fallback to standard sRGB/Rec709 conversion
        return srgb_to_linear(arr)

    def linear_to_model_asinh(self, linear_rgb: np.ndarray) -> np.ndarray:
        """Encodes scene-linear RGB into signed asinh domain for CorridorKey 2.0."""
        return linear_to_asinh(linear_rgb)

    def model_asinh_to_linear(self, model_rgb: np.ndarray) -> np.ndarray:
        """Decodes CorridorKey 2.0 output from signed asinh back into scene-linear."""
        return asinh_to_linear(model_rgb)

    def linear_to_target(self, linear_rgb: np.ndarray) -> np.ndarray:
        """Converts scene-linear RGB into target export color space."""
        if "linear" in self.target_space or "exr" in self.target_space:
            return linear_rgb
        elif "srgb" in self.target_space:
            return np.clip(linear_to_srgb(linear_rgb), 0.0, 1.0)
        elif "rec709" in self.target_space or "bt709" in self.target_space:
            return np.clip(linear_to_rec709(linear_rgb), 0.0, 1.0)
        elif "acescg" in self.target_space:
            return rec709_linear_to_acescg(linear_rgb)
        return np.clip(linear_to_rec709(linear_rgb), 0.0, 1.0)

    def get_conversion_report(self) -> ColorConversionReport:
        tags = get_color_tags(self.target_space)
        transforms = [
            f"Input ({self.source_space}) -> Scene-linear RGB",
            "Scene-linear RGB -> Neural asinh representation",
            "Neural asinh representation -> Scene-linear RGB",
            f"Scene-linear RGB -> Target ({self.target_space})",
        ]
        return ColorConversionReport(
            source_space=self.source_space,
            target_space=self.target_space,
            transforms_applied=transforms,
            linear_compositing_used=True,
            ffmpeg_color_tags=tags,
        )

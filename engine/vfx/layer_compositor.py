"""CorridorKey 2.0 Desktop — Non-Destructive Layer-Based Compositing Engine.

Provides multi-layer compositing, affine layer transforms (Position, Scale, Rotation, Anchor),
opacity blending, and standard blend modes (Normal, Multiply, Screen, Add, Overlay, Difference)
with straight and premultiplied alpha precision.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np


class BlendMode(str, Enum):
    NORMAL = "normal"
    MULTIPLY = "multiply"
    SCREEN = "screen"
    ADD = "add"
    OVERLAY = "overlay"
    DIFFERENCE = "difference"


@dataclass
class LayerItem:
    layer_id: str
    name: str
    layer_type: str = "video"  # "video" | "image" | "solid" | "ai_foreground"
    visible: bool = True
    locked: bool = False
    opacity: float = 1.0  # 0.0 to 1.0
    blend_mode: BlendMode = BlendMode.NORMAL
    pos_x: float = 0.0  # Pixels offset
    pos_y: float = 0.0  # Pixels offset
    scale_x: float = 1.0
    scale_y: float = 1.0
    rotation: float = 0.0  # Degrees
    anchor_x: float = 0.5  # 0.0 to 1.0 normalized
    anchor_y: float = 0.5
    solid_color: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # RGB for solid layers

    def to_dict(self) -> Dict[str, Any]:
        return {
            "layer_id": self.layer_id,
            "name": self.name,
            "layer_type": self.layer_type,
            "visible": self.visible,
            "locked": self.locked,
            "opacity": self.opacity,
            "blend_mode": self.blend_mode.value,
            "pos_x": self.pos_x,
            "pos_y": self.pos_y,
            "scale_x": self.scale_x,
            "scale_y": self.scale_y,
            "rotation": self.rotation,
            "anchor_x": self.anchor_x,
            "anchor_y": self.anchor_y,
            "solid_color": list(self.solid_color),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LayerItem":
        return cls(
            layer_id=d["layer_id"],
            name=d.get("name", "Layer"),
            layer_type=d.get("layer_type", "video"),
            visible=bool(d.get("visible", True)),
            locked=bool(d.get("locked", False)),
            opacity=float(d.get("opacity", 1.0)),
            blend_mode=BlendMode(d.get("blend_mode", "normal")),
            pos_x=float(d.get("pos_x", 0.0)),
            pos_y=float(d.get("pos_y", 0.0)),
            scale_x=float(d.get("scale_x", 1.0)),
            scale_y=float(d.get("scale_y", 1.0)),
            rotation=float(d.get("rotation", 0.0)),
            anchor_x=float(d.get("anchor_x", 0.5)),
            anchor_y=float(d.get("anchor_y", 0.5)),
            solid_color=tuple(d.get("solid_color", (0.0, 0.0, 0.0))),
        )


def apply_blend_mode(base_rgb: np.ndarray, blend_rgb: np.ndarray, mode: BlendMode) -> np.ndarray:
    """Applies blend mode math between base (background) and blend (foreground) RGB in [0.0, 1.0]."""
    if mode == BlendMode.NORMAL:
        return blend_rgb

    elif mode == BlendMode.MULTIPLY:
        return base_rgb * blend_rgb

    elif mode == BlendMode.SCREEN:
        return 1.0 - (1.0 - base_rgb) * (1.0 - blend_rgb)

    elif mode == BlendMode.ADD:
        return np.clip(base_rgb + blend_rgb, 0.0, 1.0)

    elif mode == BlendMode.OVERLAY:
        # Standard Overlay formula: if base < 0.5: 2 * base * blend else 1 - 2*(1-base)*(1-blend)
        low = 2.0 * base_rgb * blend_rgb
        high = 1.0 - 2.0 * (1.0 - base_rgb) * (1.0 - blend_rgb)
        return np.where(base_rgb < 0.5, low, high)

    elif mode == BlendMode.DIFFERENCE:
        return np.abs(base_rgb - blend_rgb)

    return blend_rgb


def transform_layer_image(
    image: np.ndarray,
    target_width: int,
    target_height: int,
    layer: LayerItem,
) -> np.ndarray:
    """Applies affine transforms (Position, Scale, Rotation, Anchor) to a layer."""
    h_src, w_src = image.shape[:2]
    # Anchor point in source coordinates
    ax = layer.anchor_x * w_src
    ay = layer.anchor_y * h_src

    # Target placement center
    target_cx = target_width * 0.5 + layer.pos_x
    target_cy = target_height * 0.5 + layer.pos_y

    # Compute 2D Affine Transformation Matrix
    # 1. Translate anchor to origin
    # 2. Scale & Rotate
    # 3. Translate to target center
    cos_r = math.cos(math.radians(layer.rotation))
    sin_r = math.sin(math.radians(layer.rotation))

    sx = layer.scale_x
    sy = layer.scale_y

    # Affine matrix 2x3
    m00 = cos_r * sx
    m01 = -sin_r * sy
    m02 = target_cx - (m00 * ax + m01 * ay)

    m10 = sin_r * sx
    m11 = cos_r * sy
    m12 = target_cy - (m10 * ax + m11 * ay)

    m = np.array([[m00, m01, m02], [m10, m11, m12]], dtype=np.float32)

    transformed = cv2.warpAffine(
        image,
        m,
        (target_width, target_height),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0, 0) if image.shape[2] == 4 else (0, 0, 0),
    )
    return transformed


def composite_two_layers(
    bg_rgba: np.ndarray,
    fg_rgba: np.ndarray,
    blend_mode: BlendMode = BlendMode.NORMAL,
    fg_opacity: float = 1.0,
) -> np.ndarray:
    """Composites foreground RGBA over background RGBA with blend mode and opacity."""
    fg_a = fg_rgba[:, :, 3:4] * fg_opacity
    bg_a = bg_rgba[:, :, 3:4]

    fg_rgb = fg_rgba[:, :, :3]
    bg_rgb = bg_rgba[:, :, :3]

    # Evaluate blend mode
    blended_rgb = apply_blend_mode(bg_rgb, fg_rgb, blend_mode)

    # Porter-Duff 'Over' operator
    out_a = fg_a + bg_a * (1.0 - fg_a)

    # Safe division avoiding zeros
    safe_out_a = np.maximum(out_a, 1e-6)
    out_rgb = (blended_rgb * fg_a + bg_rgb * bg_a * (1.0 - fg_a)) / safe_out_a
    out_rgb = np.where(out_a > 1e-5, out_rgb, 0.0)

    return np.concatenate([np.clip(out_rgb, 0.0, 1.0), np.clip(out_a, 0.0, 1.0)], axis=2)


def composite_layer_stack(
    layers: List[Tuple[LayerItem, np.ndarray]],
    width: int,
    height: int,
) -> np.ndarray:
    """Composites an ordered list of (LayerItem, raw_rgba_image) from bottom to top."""
    composite = np.zeros((height, width, 4), dtype=np.float32)

    for layer, raw_img in layers:
        if not layer.visible or layer.opacity <= 0.001:
            continue

        # If image does not have alpha, append 1.0 alpha
        if raw_img.shape[2] == 3:
            raw_img = np.dstack([raw_img, np.ones((raw_img.shape[0], raw_img.shape[1], 1), dtype=np.float32)])

        # Apply layer affine transforms
        transformed_fg = transform_layer_image(raw_img, width, height, layer)

        # Composite layer over current accumulation
        composite = composite_two_layers(
            bg_rgba=composite,
            fg_rgba=transformed_fg,
            blend_mode=layer.blend_mode,
            fg_opacity=layer.opacity,
        )

    return composite

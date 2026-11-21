"""CorridorKey 2.0 Desktop — Vector Masking and Rotoscoping Engine.

Provides non-destructive vector masks (Rectangle, Ellipse, Freehand, Bezier, Polygon),
feathering, expansion/contraction, inversion, and Add/Subtract blending modes.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np


class MaskType(str, Enum):
    RECTANGLE = "rectangle"
    ELLIPSE = "ellipse"
    FREEHAND = "freehand"
    BEZIER = "bezier"
    POLYGON = "polygon"


class MaskMode(str, Enum):
    ADD = "add"
    SUBTRACT = "subtract"


@dataclass
class MaskPoint:
    x: float  # Normalized 0.0 to 1.0 (or pixel space)
    y: float
    handle_in: Tuple[float, float] = (0.0, 0.0)
    handle_out: Tuple[float, float] = (0.0, 0.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "x": self.x,
            "y": self.y,
            "handle_in": list(self.handle_in),
            "handle_out": list(self.handle_out),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "MaskPoint":
        return cls(
            x=float(d["x"]),
            y=float(d["y"]),
            handle_in=tuple(d.get("handle_in", (0.0, 0.0))),
            handle_out=tuple(d.get("handle_out", (0.0, 0.0))),
        )


@dataclass
class MaskItem:
    mask_id: str
    name: str
    mask_type: MaskType = MaskType.RECTANGLE
    mode: MaskMode = MaskMode.ADD
    inverted: bool = False
    feather: float = 0.0  # Pixels
    expansion: float = 0.0  # Pixels (-50 to +50)
    opacity: float = 1.0  # 0.0 to 1.0
    visible: bool = True
    pos_x: float = 0.0  # Pixels offset
    pos_y: float = 0.0
    scale: float = 1.0
    points: List[MaskPoint] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mask_id": self.mask_id,
            "name": self.name,
            "mask_type": self.mask_type.value,
            "mode": self.mode.value,
            "inverted": self.inverted,
            "feather": self.feather,
            "expansion": self.expansion,
            "opacity": self.opacity,
            "visible": self.visible,
            "pos_x": self.pos_x,
            "pos_y": self.pos_y,
            "scale": self.scale,
            "points": [p.to_dict() for p in self.points],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "MaskItem":
        return cls(
            mask_id=d["mask_id"],
            name=d.get("name", "Mask"),
            mask_type=MaskType(d.get("mask_type", "rectangle")),
            mode=MaskMode(d.get("mode", "add")),
            inverted=bool(d.get("inverted", False)),
            feather=float(d.get("feather", 0.0)),
            expansion=float(d.get("expansion", 0.0)),
            opacity=float(d.get("opacity", 1.0)),
            visible=bool(d.get("visible", True)),
            pos_x=float(d.get("pos_x", 0.0)),
            pos_y=float(d.get("pos_y", 0.0)),
            scale=float(d.get("scale", 1.0)),
            points=[MaskPoint.from_dict(p) for p in d.get("points", [])],
        )


def _eval_cubic_bezier_2d(p0: Tuple[float, float], p1: Tuple[float, float], p2: Tuple[float, float], p3: Tuple[float, float], num_steps: int = 10) -> List[Tuple[float, float]]:
    """Evaluates 2D cubic Bezier curve points between p0 and p3."""
    curve = []
    for step in range(num_steps + 1):
        t = step / num_steps
        u = 1.0 - t
        x = (u**3 * p0[0]) + (3 * u**2 * t * p1[0]) + (3 * u * t**2 * p2[0]) + (t**3 * p3[0])
        y = (u**3 * p0[1]) + (3 * u**2 * t * p1[1]) + (3 * u * t**2 * p2[1]) + (t**3 * p3[1])
        curve.append((x, y))
    return curve


def rasterize_mask(mask: MaskItem, width: int, height: int) -> np.ndarray:
    """Rasterizes a single mask into a float32 [0.0, 1.0] alpha matte."""
    if not mask.visible:
        return np.zeros((height, width), dtype=np.float32)

    canvas = np.zeros((height, width), dtype=np.uint8)

    cx = width / 2.0 + mask.pos_x
    cy = height / 2.0 + mask.pos_y

    if mask.mask_type == MaskType.RECTANGLE:
        # Default rect or custom bounding points
        if len(mask.points) >= 2:
            p1, p2 = mask.points[0], mask.points[1]
            x1, y1 = int(p1.x * width + mask.pos_x), int(p1.y * height + mask.pos_y)
            x2, y2 = int(p2.x * width + mask.pos_x), int(p2.y * height + mask.pos_y)
        else:
            w = int(width * 0.5 * mask.scale)
            h = int(height * 0.5 * mask.scale)
            x1, y1 = int(cx - w / 2), int(cy - h / 2)
            x2, y2 = int(cx + w / 2), int(cy + h / 2)
        cv2.rectangle(canvas, (min(x1, x2), min(y1, y2)), (max(x1, x2), max(y1, y2)), 255, -1)

    elif mask.mask_type == MaskType.ELLIPSE:
        if len(mask.points) >= 2:
            p1, p2 = mask.points[0], mask.points[1]
            axes = (int(abs(p2.x - p1.x) * width / 2 * mask.scale), int(abs(p2.y - p1.y) * height / 2 * mask.scale))
            center = (int((p1.x + p2.x) * width / 2 + mask.pos_x), int((p1.y + p2.y) * height / 2 + mask.pos_y))
        else:
            axes = (int(width * 0.25 * mask.scale), int(height * 0.25 * mask.scale))
            center = (int(cx), int(cy))
        axes = (max(1, axes[0]), max(1, axes[1]))
        cv2.ellipse(canvas, center, axes, 0, 0, 360, 255, -1)

    elif mask.mask_type in (MaskType.POLYGON, MaskType.FREEHAND):
        if len(mask.points) >= 3:
            pts = []
            for p in mask.points:
                px = int(p.x * width * mask.scale + mask.pos_x)
                py = int(p.y * height * mask.scale + mask.pos_y)
                pts.append([px, py])
            pts_arr = np.array([pts], dtype=np.int32)
            cv2.fillPoly(canvas, pts_arr, 255)

    elif mask.mask_type == MaskType.BEZIER:
        if len(mask.points) >= 3:
            # Interpolate smooth Bezier points between control points
            dense_pts = []
            n = len(mask.points)
            for i in range(n):
                p_curr = mask.points[i]
                p_next = mask.points[(i + 1) % n]

                p0 = (p_curr.x * width * mask.scale + mask.pos_x, p_curr.y * height * mask.scale + mask.pos_y)
                p1 = (p0[0] + p_curr.handle_out[0] * width, p0[1] + p_curr.handle_out[1] * height)
                p3 = (p_next.x * width * mask.scale + mask.pos_x, p_next.y * height * mask.scale + mask.pos_y)
                p2 = (p3[0] + p_next.handle_in[0] * width, p3[1] + p_next.handle_in[1] * height)

                segment = _eval_cubic_bezier_2d(p0, p1, p2, p3, num_steps=8)
                for pt in segment[:-1]:
                    dense_pts.append([int(pt[0]), int(pt[1])])
            pts_arr = np.array([dense_pts], dtype=np.int32)
            cv2.fillPoly(canvas, pts_arr, 255)

    # 1. Mask Expansion / Contraction (Choke / Dilation)
    if abs(mask.expansion) >= 1.0:
        kernel_size = int(round(abs(mask.expansion))) * 2 + 1
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        if mask.expansion > 0:
            canvas = cv2.dilate(canvas, kernel)
        else:
            canvas = cv2.erode(canvas, kernel)

    # Convert to float32
    matte = canvas.astype(np.float32) / 255.0

    # 2. Feathering (Gaussian Blur)
    if mask.feather > 0.5:
        # Kernel size must be odd
        ksize = int(round(mask.feather * 2.5)) * 2 + 1
        sigma = mask.feather / 2.0
        matte = cv2.GaussianBlur(matte, (ksize, ksize), sigmaX=sigma, sigmaY=sigma)

    # 3. Inversion
    if mask.inverted:
        matte = 1.0 - matte

    # 4. Opacity
    if mask.opacity < 0.999:
        matte = matte * mask.opacity

    return np.clip(matte, 0.0, 1.0)


def combine_masks(masks: List[MaskItem], width: int, height: int) -> np.ndarray:
    """Combines a stack of masks respecting Add/Subtract modes and opacities."""
    active_masks = [m for m in masks if m.visible]
    if not active_masks:
        return np.ones((height, width), dtype=np.float32)

    result = np.zeros((height, width), dtype=np.float32)

    for mask in active_masks:
        raster = rasterize_mask(mask, width, height)
        if mask.mode == MaskMode.ADD:
            result = np.maximum(result, raster)
        elif mask.mode == MaskMode.SUBTRACT:
            result = np.clip(result - raster, 0.0, 1.0)

    return np.clip(result, 0.0, 1.0)

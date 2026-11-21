"""CorridorKey 2.0 Desktop — Keyframe Animation & Interpolation Engine.

Supports animated parameters (Position X/Y, Scale, Rotation, Opacity)
with Hold, Linear, and Smooth Cubic Bezier easing curves.
"""

from __future__ import annotations

import bisect
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class KeyframeInterpolation(str, Enum):
    HOLD = "hold"
    LINEAR = "linear"
    BEZIER = "bezier"


@dataclass
class Keyframe:
    frame: int
    value: float
    interpolation: KeyframeInterpolation = KeyframeInterpolation.LINEAR
    # Normalized bezier control handles (dx, dy) relative to keyframe point
    in_handle: Tuple[float, float] = (-0.33, 0.0)
    out_handle: Tuple[float, float] = (0.33, 0.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frame": self.frame,
            "value": self.value,
            "interpolation": self.interpolation.value,
            "in_handle": list(self.in_handle),
            "out_handle": list(self.out_handle),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Keyframe":
        return cls(
            frame=int(d["frame"]),
            value=float(d["value"]),
            interpolation=KeyframeInterpolation(d.get("interpolation", "linear")),
            in_handle=tuple(d.get("in_handle", (-0.33, 0.0))),
            out_handle=tuple(d.get("out_handle", (0.33, 0.0))),
        )


def _eval_cubic_bezier_1d(t: float, p0: float, p1: float, p2: float, p3: float) -> float:
    """Evaluates 1D cubic Bezier curve at parameter t in [0, 1]."""
    u = 1.0 - t
    return (u**3 * p0) + (3.0 * u**2 * t * p1) + (3.0 * u * t**2 * p2) + (t**3 * p3)


class PropertyTrack:
    """Animates a single scalar property across integer frame ticks."""

    def __init__(self, name: str, default_value: float = 0.0):
        self.name = name
        self.default_value = default_value
        self.keyframes: List[Keyframe] = []

    def add_keyframe(
        self,
        frame: int,
        value: float,
        interpolation: KeyframeInterpolation = KeyframeInterpolation.LINEAR,
    ) -> Keyframe:
        """Adds or updates a keyframe at the specified frame."""
        for i, k in enumerate(self.keyframes):
            if k.frame == frame:
                self.keyframes[i] = Keyframe(frame, value, interpolation)
                return self.keyframes[i]

        kf = Keyframe(frame, value, interpolation)
        self.keyframes.append(kf)
        self.keyframes.sort(key=lambda k: k.frame)
        return kf

    def remove_keyframe(self, frame: int) -> bool:
        for i, k in enumerate(self.keyframes):
            if k.frame == frame:
                self.keyframes.pop(i)
                return True
        return False

    def evaluate(self, frame: int) -> float:
        """Evaluates animated value at integer frame tick."""
        if not self.keyframes:
            return self.default_value

        # Boundary clamps
        if frame <= self.keyframes[0].frame:
            return self.keyframes[0].value
        if frame >= self.keyframes[-1].frame:
            return self.keyframes[-1].value

        # Find keyframe span [k1, k2]
        idx = bisect.bisect_right([k.frame for k in self.keyframes], frame)
        k1 = self.keyframes[idx - 1]
        k2 = self.keyframes[idx]

        if k1.interpolation == KeyframeInterpolation.HOLD:
            return k1.value

        span_frames = max(1, k2.frame - k1.frame)
        t = (frame - k1.frame) / span_frames

        if k1.interpolation == KeyframeInterpolation.LINEAR:
            return k1.value + (k2.value - k1.value) * t

        elif k1.interpolation == KeyframeInterpolation.BEZIER:
            # S-curve ease-in/ease-out
            p0 = k1.value
            p1 = k1.value + (k2.value - k1.value) * 0.2
            p2 = k2.value - (k2.value - k1.value) * 0.2
            p3 = k2.value
            return _eval_cubic_bezier_1d(t, p0, p1, p2, p3)

        return k1.value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "default_value": self.default_value,
            "keyframes": [k.to_dict() for k in self.keyframes],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PropertyTrack":
        pt = cls(name=d["name"], default_value=float(d.get("default_value", 0.0)))
        for k in d.get("keyframes", []):
            pt.keyframes.append(Keyframe.from_dict(k))
        pt.keyframes.sort(key=lambda x: x.frame)
        return pt

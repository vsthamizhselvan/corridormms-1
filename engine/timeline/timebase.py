"""CorridorKey 2.0 Desktop — Rational Timebase & SMPTE Timecode Engine.

Provides exact rational representation of video framerates and integer frame tick math,
preventing timing drift across long-form VFX sequences.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Timebase:
    numerator: int
    denominator: int = 1

    @property
    def fps(self) -> float:
        return self.numerator / self.denominator

    def frame_to_seconds(self, frame: int) -> float:
        """Converts integer frame tick to physical seconds."""
        return (frame * self.denominator) / self.numerator

    def seconds_to_frame(self, seconds: float) -> int:
        """Converts physical seconds to nearest integer frame tick."""
        return int(round((seconds * self.numerator) / self.denominator))

    def frame_to_timecode(self, frame: int, drop_frame: bool = False) -> str:
        """Formats integer frame tick into SMPTE timecode (HH:MM:SS:FF)."""
        fps_nominal = int(round(self.fps))

        total_seconds = frame // fps_nominal
        ff = frame % fps_nominal
        ss = total_seconds % 60
        mm = (total_seconds // 60) % 60
        hh = total_seconds // 3600

        sep = ";" if drop_frame else ":"
        return f"{hh:02d}:{mm:02d}:{ss:02d}{sep}{ff:02d}"

    def timecode_to_frame(self, tc: str) -> int:
        """Parses SMPTE timecode string into exact integer frame tick."""
        clean = tc.strip().replace(";", ":")
        parts = [int(p) for p in clean.split(":")]
        if len(parts) != 4:
            raise ValueError(f"Invalid SMPTE timecode format: '{tc}'")

        hh, mm, ss, ff = parts
        fps_nominal = int(round(self.fps))
        return ((hh * 3600 + mm * 60 + ss) * fps_nominal) + ff


# Standard Industry Presets
TIMEBASE_24 = Timebase(24, 1)          # Film & Standard VFX (24.0 fps)
TIMEBASE_23_976 = Timebase(24000, 1001) # NTSC Film (23.976 fps)
TIMEBASE_25 = Timebase(25, 1)          # PAL Broadcast (25.0 fps)
TIMEBASE_29_97 = Timebase(30000, 1001)  # NTSC Video (29.97 fps)
TIMEBASE_30 = Timebase(30, 1)          # Standard Video (30.0 fps)
TIMEBASE_50 = Timebase(50, 1)          # High-Framerate PAL (50.0 fps)
TIMEBASE_59_94 = Timebase(60000, 1001) # High-Framerate NTSC (59.94 fps)
TIMEBASE_60 = Timebase(60, 1)          # High-Framerate 60p (60.0 fps)


def get_timebase_from_fps(fps: float) -> Timebase:
    """Matches a floating-point framerate to its closest standard rational timebase."""
    if abs(fps - 23.976) < 0.05 or abs(fps - 23.98) < 0.05:
        return TIMEBASE_23_976
    elif abs(fps - 29.97) < 0.05:
        return TIMEBASE_29_97
    elif abs(fps - 59.94) < 0.05:
        return TIMEBASE_59_94
    elif abs(fps - 25.0) < 0.05:
        return TIMEBASE_25
    elif abs(fps - 30.0) < 0.05:
        return TIMEBASE_30
    elif abs(fps - 60.0) < 0.05:
        return TIMEBASE_60
    elif abs(fps - 50.0) < 0.05:
        return TIMEBASE_50
    return TIMEBASE_24

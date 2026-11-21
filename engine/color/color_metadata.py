"""CorridorKey 2.0 Desktop — FFmpeg Color Metadata & Tagging.

Provides mappings between standard VFX color spaces and FFmpeg command-line parameters
to ensure QuickTime, DaVinci Resolve, Adobe Premiere, and Final Cut Pro correctly
read container color tags without gamma distortion or shifts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ColorTagConfig:
    name: str
    primaries: str
    transfer: str
    matrix: str
    range_str: str = "pc"  # 'pc' (full 0-255) | 'tv' (video 16-235)

    def to_ffmpeg_args(self) -> List[str]:
        args = [
            "-color_primaries", self.primaries,
            "-color_trc", self.transfer,
            "-colorspace", self.matrix,
            "-color_range", self.range_str,
        ]
        return args


COLOR_PROFILES = {
    "rec709": ColorTagConfig(
        name="Rec.709",
        primaries="bt709",
        transfer="bt709",
        matrix="bt709",
        range_str="tv",
    ),
    "srgb": ColorTagConfig(
        name="sRGB",
        primaries="bt709",
        transfer="iec61966-2-1",
        matrix="bt709",
        range_str="pc",
    ),
    "linear": ColorTagConfig(
        name="Linear",
        primaries="bt709",
        transfer="linear",
        matrix="bt709",
        range_str="pc",
    ),
    "rec2020": ColorTagConfig(
        name="Rec.2020",
        primaries="bt2020",
        transfer="bt2020-10",
        matrix="bt2020nc",
        range_str="tv",
    ),
    "pq": ColorTagConfig(
        name="HDR10 (PQ)",
        primaries="bt2020",
        transfer="smpte2084",
        matrix="bt2020nc",
        range_str="tv",
    ),
    "hlg": ColorTagConfig(
        name="HLG",
        primaries="bt2020",
        transfer="arib-std-b67",
        matrix="bt2020nc",
        range_str="tv",
    ),
}


def get_color_tags(profile_name: str = "rec709") -> ColorTagConfig:
    key = profile_name.lower().replace(".", "").replace("-", "")
    for k, v in COLOR_PROFILES.items():
        if k in key:
            return v
    return COLOR_PROFILES["rec709"]

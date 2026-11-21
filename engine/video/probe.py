"""CorridorKey 2.0 Desktop — Professional Video Probing & Media Analysis.

Uses ffprobe and filesystem inspection to extract detailed stream metadata,
color science metadata, audio tracks, alpha transparency indicators, and
frame rate characteristics across containers and image sequences.
"""

from __future__ import annotations

import glob
import json
import os
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class AudioStreamInfo:
    codec: str
    sample_rate: int
    channels: int
    channel_layout: Optional[str] = None
    bitrate: Optional[int] = None
    duration_seconds: Optional[float] = None


@dataclass
class ColorMetadata:
    color_primaries: Optional[str] = None  # e.g., 'bt709', 'bt2020'
    color_trc: Optional[str] = None  # e.g., 'bt709', 'iec61966-2-1', 'smpte2084'
    colorspace: Optional[str] = None  # matrix coefficients e.g. 'bt709'
    color_range: Optional[str] = None  # 'tv' (limited) or 'pc' (full)
    chroma_location: Optional[str] = None

    def is_rec709(self) -> bool:
        return self.color_primaries == "bt709" or self.colorspace == "bt709"

    def is_srgb(self) -> bool:
        return self.color_trc in ("iec61966-2-1", "srgb")

    def is_hdr(self) -> bool:
        return self.color_trc in ("smpte2084", "arib-std-b67") or self.color_primaries == "bt2020"


@dataclass
class MediaProbeReport:
    file_path: str
    is_sequence: bool
    container_format: str
    width: int
    height: int
    fps: float
    avg_fps: float
    time_base: str
    duration_seconds: float
    frame_count: Optional[int]
    video_codec: str
    pixel_format: str
    bit_depth: int
    has_alpha: bool
    is_vfr: bool
    color: ColorMetadata
    audio_streams: List[AudioStreamInfo] = field(default_factory=list)
    raw_streams: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["color"] = asdict(self.color)
        d["audio_streams"] = [asdict(a) for a in self.audio_streams]
        return d


def _parse_fraction(frac_str: Optional[str]) -> Optional[float]:
    if not frac_str or frac_str in ("0/0", "N/A"):
        return None
    try:
        if "/" in frac_str:
            num, den = frac_str.split("/", 1)
            den_f = float(den)
            return float(num) / den_f if den_f != 0 else None
        return float(frac_str)
    except (ValueError, ZeroDivisionError):
        return None


def _infer_bit_depth_from_pix_fmt(pix_fmt: str) -> int:
    fmt = pix_fmt.lower()
    if any(k in fmt for k in ("16le", "16be", "64le", "64be", "rgb48", "bgr48", "gray16")):
        return 16
    if any(k in fmt for k in ("12le", "12be", "p12")):
        return 12
    if any(k in fmt for k in ("10le", "10be", "p10")):
        return 10
    if any(k in fmt for k in ("32f", "exr", "float")):
        return 32
    return 8


def _detect_alpha_in_pix_fmt(pix_fmt: str, codec: str) -> bool:
    fmt = pix_fmt.lower()
    alpha_indicators = ("yuva", "rgba", "bgra", "argb", "abgr", "ya8", "ya16", "gbrpa")
    if any(k in fmt for k in alpha_indicators):
        return True
    if codec.lower() in ("png", "qtrle", "apng") and "a" in fmt:
        return True
    return False


def probe_image_sequence(folder_or_pattern: str | Path) -> MediaProbeReport:
    """Probes an image sequence directory or glob pattern."""
    p = Path(folder_or_pattern)
    if p.is_dir():
        candidates = []
        for ext in ("*.exr", "*.png", "*.jpg", "*.jpeg", "*.tiff", "*.tif", "*.dpx"):
            candidates.extend(sorted(glob.glob(os.path.join(str(p), ext))))
            candidates.extend(sorted(glob.glob(os.path.join(str(p), ext.upper()))))
        files = sorted(candidates)
    else:
        files = sorted(glob.glob(str(p)))

    if not files:
        raise FileNotFoundError(f"No image sequence files found for path: {folder_or_pattern}")

    first_file = files[0]
    first_report = probe_media_file(first_file)

    # Sequence properties
    ext = Path(first_file).suffix.lower()
    is_exr = ext == ".exr"
    bit_depth = 32 if is_exr else (16 if ext in (".tiff", ".tif") else first_report.bit_depth)

    return MediaProbeReport(
        file_path=str(folder_or_pattern),
        is_sequence=True,
        container_format=f"image_sequence ({ext.lstrip('.')})",
        width=first_report.width,
        height=first_report.height,
        fps=24.0,  # Default VFX playback framerate for image sequences
        avg_fps=24.0,
        time_base="1/24",
        duration_seconds=len(files) / 24.0,
        frame_count=len(files),
        video_codec=ext.lstrip("."),
        pixel_format=first_report.pixel_format,
        bit_depth=bit_depth,
        has_alpha=first_report.has_alpha or is_exr,
        is_vfr=False,
        color=first_report.color,
        audio_streams=[],
        warnings=["Framerate for image sequence assumed to be 24.0 fps; adjust in project settings."],
    )


def probe_media_file(file_path: str | Path, ffprobe_bin: str = "ffprobe") -> MediaProbeReport:
    """Invokes ffprobe to inspect a video or image file in JSON mode."""
    path = str(file_path)

    # Check for image sequence pattern or folder
    if os.path.isdir(path) or "%" in path or "*" in path:
        return probe_image_sequence(path)

    if not os.path.isfile(path):
        raise FileNotFoundError(f"Media file not found: {path}")

    if not shutil.which(ffprobe_bin):
        raise FileNotFoundError(f"ffprobe binary not found at '{ffprobe_bin}'.")

    cmd = [
        ffprobe_bin,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        path,
    ]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ffprobe execution failed on {path}: {e.stderr}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse ffprobe JSON output for {path}: {e}")

    format_data = data.get("format", {})
    streams = data.get("streams", [])

    video_stream: Optional[Dict[str, Any]] = None
    audio_streams: List[AudioStreamInfo] = []

    for s in streams:
        c_type = s.get("codec_type")
        if c_type == "video" and video_stream is None:
            video_stream = s
        elif c_type == "audio":
            sr = int(s.get("sample_rate", 48000))
            channels = int(s.get("channels", 2))
            audio_streams.append(
                AudioStreamInfo(
                    codec=s.get("codec_name", "unknown"),
                    sample_rate=sr,
                    channels=channels,
                    channel_layout=s.get("channel_layout"),
                    bitrate=int(s.get("bit_rate")) if s.get("bit_rate") else None,
                    duration_seconds=_parse_fraction(s.get("duration")),
                )
            )

    if not video_stream:
        raise ValueError(f"No video stream found in {path}")

    # Geometry & Codec
    width = int(video_stream.get("width", 0))
    height = int(video_stream.get("height", 0))
    codec_name = video_stream.get("codec_name", "unknown")
    pix_fmt = video_stream.get("pix_fmt", "unknown")
    time_base = video_stream.get("time_base", "1/1000")

    # Framerates
    r_fps = _parse_fraction(video_stream.get("r_frame_rate")) or 24.0
    avg_fps = _parse_fraction(video_stream.get("avg_frame_rate")) or r_fps
    is_vfr = abs(r_fps - avg_fps) > 0.05 if r_fps and avg_fps else False

    # Duration & Frame Count
    dur_str = video_stream.get("duration") or format_data.get("duration")
    duration = float(dur_str) if dur_str and dur_str != "N/A" else 0.0

    nb_frames_str = video_stream.get("nb_frames")
    frame_count: Optional[int] = None
    if nb_frames_str and nb_frames_str != "N/A":
        try:
            frame_count = int(nb_frames_str)
        except ValueError:
            pass

    if frame_count is None and duration > 0 and avg_fps > 0:
        frame_count = int(round(duration * avg_fps))

    # Bit Depth & Alpha
    bit_depth = _infer_bit_depth_from_pix_fmt(pix_fmt)
    has_alpha = _detect_alpha_in_pix_fmt(pix_fmt, codec_name)

    # Color Science
    color = ColorMetadata(
        color_primaries=video_stream.get("color_primaries"),
        color_trc=video_stream.get("color_transfer") or video_stream.get("color_trc"),
        colorspace=video_stream.get("color_space") or video_stream.get("colorspace"),
        color_range=video_stream.get("color_range"),
        chroma_location=video_stream.get("chroma_location"),
    )

    warnings = []
    if is_vfr:
        warnings.append(
            f"Variable frame rate detected (r_fps={r_fps:.2f}, avg_fps={avg_fps:.2f}). "
            "Pipeline will preserve PTS timestamps."
        )
    if bit_depth > 8:
        warnings.append(f"High dynamic range / deep color detected ({bit_depth}-bit).")

    return MediaProbeReport(
        file_path=path,
        is_sequence=False,
        container_format=format_data.get("format_name", "unknown"),
        width=width,
        height=height,
        fps=r_fps,
        avg_fps=avg_fps,
        time_base=time_base,
        duration_seconds=duration,
        frame_count=frame_count,
        video_codec=codec_name,
        pixel_format=pix_fmt,
        bit_depth=bit_depth,
        has_alpha=has_alpha,
        is_vfr=is_vfr,
        color=color,
        audio_streams=audio_streams,
        raw_streams=streams,
        warnings=warnings,
    )

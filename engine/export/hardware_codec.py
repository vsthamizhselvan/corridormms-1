"""CorridorKey 2.0 Desktop — Hardware-Accelerated Video Codec Prober & Selector.

Validates available encoders at runtime and selects optimal hardware-accelerated
encoders for Apple Silicon (VideoToolbox), NVIDIA RTX (NVENC), and CPU fallbacks.
"""

from __future__ import annotations

import functools
import platform
import shutil
import subprocess
from typing import Dict, List, Optional, Tuple


@functools.lru_cache(maxsize=1)
def get_available_encoders(ffmpeg_bin: str = "ffmpeg") -> List[str]:
    """Queries FFmpeg for the list of compiled and supported encoders."""
    if not shutil.which(ffmpeg_bin):
        return []
    try:
        proc = subprocess.run(
            [ffmpeg_bin, "-hide_banner", "-encoders"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        encoders = []
        for line in proc.stdout.splitlines():
            line_s = line.strip()
            if line_s.startswith("V") or line_s.startswith("A"):
                parts = line_s.split()
                if len(parts) >= 2:
                    encoders.append(parts[1])
        return encoders
    except Exception:
        return []


def select_optimal_encoder(
    target_codec: str,
    requires_alpha: bool = False,
    prefer_hardware: bool = True,
    ffmpeg_bin: str = "ffmpeg",
) -> Tuple[str, str]:
    """Selects the best available encoder and pixel format for the requested format.

    Returns:
        (encoder_name, pixel_format)
    """
    avail = get_available_encoders(ffmpeg_bin)
    plat = platform.system()
    tc = target_codec.lower().replace("-", "_")

    # 1. ProRes 4444 / 4444 XQ (Requires Alpha)
    if tc in ("prores_4444", "prores_4444_xq", "prores4444", "prores_xq"):
        # For 10/12-bit ProRes with alpha, prores_ks is the gold standard for alpha compatibility
        return ("prores_ks", "yuva444p10le")

    # 2. ProRes 422 HQ (Broadcast standard, no alpha)
    if tc in ("prores_422_hq", "prores_422", "prores422hq", "prores"):
        if prefer_hardware and plat == "Darwin" and "prores_videotoolbox" in avail:
            return ("prores_videotoolbox", "p010le")
        return ("prores_ks", "yuv422p10le")

    # 3. H.264 / AVC
    if tc in ("h264", "avc", "mp4"):
        if prefer_hardware:
            if plat == "Darwin" and "h264_videotoolbox" in avail:
                return ("h264_videotoolbox", "yuv420p")
            if plat == "Windows" and "h264_nvenc" in avail:
                return ("h264_nvenc", "yuv420p")
        if "libx264" in avail:
            return ("libx264", "yuv420p")
        return ("h264", "yuv420p")

    # 4. H.265 / HEVC
    if tc in ("h265", "hevc"):
        if prefer_hardware:
            if plat == "Darwin" and "hevc_videotoolbox" in avail:
                # VideoToolbox HEVC supports alpha on macOS with yuva420p
                pix = "yuva420p" if requires_alpha else "yuv420p"
                return ("hevc_videotoolbox", pix)
            if plat == "Windows" and "hevc_nvenc" in avail:
                return ("hevc_nvenc", "yuv420p")
        if "libx265" in avail:
            return ("libx265", "yuv420p")
        return ("hevc", "yuv420p")

    # 5. VP9
    if tc in ("vp9", "webm"):
        if "libvpx_vp9" in avail:
            return ("libvpx_vp9", "yuva420p" if requires_alpha else "yuv420p")
        return ("vp9", "yuva420p" if requires_alpha else "yuv420p")

    # Default fallback
    return ("libx264", "yuv420p")

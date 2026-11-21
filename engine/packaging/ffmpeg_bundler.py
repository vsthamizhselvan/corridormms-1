"""CorridorKey 2.0 Desktop — FFmpeg / FFprobe Packaging & Codec Capability Subsystem.

Detects, bundles, and validates FFmpeg binaries and codec capabilities
including hardware acceleration (VideoToolbox on macOS, NVENC on Windows).
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class CodecCapabilityReport:
    ffmpeg_available: bool
    ffprobe_available: bool
    ffmpeg_path: str
    ffprobe_path: str
    version_string: str
    supports_prores_4444: bool
    supports_vp9_alpha: bool
    supports_qtrle: bool
    supports_png_sequence: bool
    hardware_accelerator: str  # "videotoolbox", "nvenc", "none"
    is_production_ready: bool
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FFmpegManager:
    """Manages locating, validating, and testing FFmpeg & FFprobe."""

    def __init__(self, bundled_bin_dir: Optional[Path] = None):
        self.bundled_bin_dir = bundled_bin_dir

    def locate_binaries(self) -> Tuple[Optional[str], Optional[str]]:
        """Finds FFmpeg and FFprobe from bundled resources or system PATH."""
        ffmpeg_name = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"
        ffprobe_name = "ffprobe.exe" if platform.system() == "Windows" else "ffprobe"

        # 1. Bundled bin dir check
        if self.bundled_bin_dir and self.bundled_bin_dir.is_dir():
            b_ffmpeg = self.bundled_bin_dir / ffmpeg_name
            b_ffprobe = self.bundled_bin_dir / ffprobe_name
            if b_ffmpeg.is_file() and b_ffprobe.is_file():
                return str(b_ffmpeg), str(b_ffprobe)

        # 2. System PATH check
        sys_ffmpeg = shutil.which("ffmpeg")
        sys_ffprobe = shutil.which("ffprobe")

        return sys_ffmpeg, sys_ffprobe

    def probe_capabilities(self) -> CodecCapabilityReport:
        """Executes diagnostic checks on ffmpeg/ffprobe and validates VFX codecs."""
        ffmpeg_bin, ffprobe_bin = self.locate_binaries()

        if not ffmpeg_bin:
            return CodecCapabilityReport(
                ffmpeg_available=False,
                ffprobe_available=bool(ffprobe_bin),
                ffmpeg_path="",
                ffprobe_path=ffprobe_bin or "",
                version_string="",
                supports_prores_4444=False,
                supports_vp9_alpha=False,
                supports_qtrle=False,
                supports_png_sequence=False,
                hardware_accelerator="none",
                is_production_ready=False,
                error_message="FFmpeg executable not found in bundle or system PATH.",
            )

        # Check version
        try:
            v_res = subprocess.run([ffmpeg_bin, "-version"], capture_output=True, text=True, timeout=5)
            version_line = v_res.stdout.splitlines()[0] if v_res.returncode == 0 and v_res.stdout else "unknown"
        except Exception as e:
            version_line = f"error: {e}"

        # Check encoders
        try:
            enc_res = subprocess.run([ffmpeg_bin, "-encoders"], capture_output=True, text=True, timeout=5)
            encoders_out = enc_res.stdout.lower() if enc_res.returncode == 0 else ""
        except Exception:
            encoders_out = ""

        supports_prores = "prores_ks" in encoders_out or "prores" in encoders_out
        supports_vp9 = "libvpx-vp9" in encoders_out or "vp9" in encoders_out
        supports_qtrle = "qtrle" in encoders_out
        supports_png = "png" in encoders_out

        # Hardware acceleration
        hw_accel = "none"
        if platform.system() == "Darwin":
            if "h264_videotoolbox" in encoders_out or "hevc_videotoolbox" in encoders_out:
                hw_accel = "videotoolbox"
        elif platform.system() == "Windows":
            if "h264_nvenc" in encoders_out or "hevc_nvenc" in encoders_out:
                hw_accel = "nvenc"

        is_ready = bool(ffmpeg_bin and ffprobe_bin and supports_png and supports_prores)

        return CodecCapabilityReport(
            ffmpeg_available=True,
            ffprobe_available=bool(ffprobe_bin),
            ffmpeg_path=ffmpeg_bin,
            ffprobe_path=ffprobe_bin or "",
            version_string=version_line,
            supports_prores_4444=supports_prores,
            supports_vp9_alpha=supports_vp9,
            supports_qtrle=supports_qtrle,
            supports_png_sequence=supports_png,
            hardware_accelerator=hw_accel,
            is_production_ready=is_ready,
            error_message=None if is_ready else "Some core video encoders are missing.",
        )

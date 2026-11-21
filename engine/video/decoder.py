"""CorridorKey 2.0 Desktop — High-Performance FFmpeg Video Decoder.

Provides streaming hardware and software decoding with support for VideoToolbox
(Apple Silicon), NVDEC (Windows NVIDIA), and multi-threaded CPU decoding.
Streams raw pixel buffers to standard output without loading full clips into RAM.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from engine.video.probe import MediaProbeReport, probe_media_file


@dataclass
class DecoderConfig:
    ffmpeg_bin: str = "ffmpeg"
    pix_fmt: str = "bgr24"  # 'bgr24' (8-bit) | 'bgr48le' (16-bit) | 'rgb24'
    target_width: Optional[int] = None
    target_height: Optional[int] = None
    fps: Optional[float] = None
    start_frame: int = 0
    num_frames: Optional[int] = None
    hwaccel: str = "auto"  # 'auto' | 'videotoolbox' | 'cuda' | 'cpu'
    threads: int = 4


def detect_decoder_hwaccel(ffmpeg_bin: str = "ffmpeg") -> str:
    """Detects available hardware acceleration on current OS."""
    os_name = platform.system()

    if not shutil.which(ffmpeg_bin):
        return "cpu"

    try:
        res = subprocess.run([ffmpeg_bin, "-hwaccels"], capture_output=True, text=True)
        accels = res.stdout.lower()

        if os_name == "Darwin" and "videotoolbox" in accels:
            return "videotoolbox"
        elif os_name == "Windows" and ("cuda" in accels or "nvdec" in accels):
            return "cuda"
    except Exception:
        pass

    return "cpu"


class FFmpegDecoder:
    """Spawns an FFmpeg decoding process streaming raw uncompressed pixel bytes."""

    def __init__(self, media_path: str | Path, config: Optional[DecoderConfig] = None):
        self.media_path = str(media_path)
        self.config = config or DecoderConfig()
        self.probe_report: MediaProbeReport = probe_media_file(self.media_path)

        # Resolve output dimensions
        self.width = self.config.target_width or self.probe_report.width
        self.height = self.config.target_height or self.probe_report.height
        self.fps = self.config.fps or self.probe_report.fps

        # Resolve pixel format and frame byte stride
        self.pix_fmt = self.config.pix_fmt
        if self.pix_fmt in ("bgr24", "rgb24"):
            self.bytes_per_pixel = 3
            self.dtype_str = "uint8"
        elif self.pix_fmt in ("bgr48le", "rgb48le"):
            self.bytes_per_pixel = 6
            self.dtype_str = "uint16"
        elif self.pix_fmt in ("bgra", "rgba"):
            self.bytes_per_pixel = 4
            self.dtype_str = "uint8"
        elif self.pix_fmt == "bgra64le":
            self.bytes_per_pixel = 8
            self.dtype_str = "uint16"
        else:
            self.bytes_per_pixel = 3
            self.dtype_str = "uint8"

        self.frame_bytes = self.width * self.height * self.bytes_per_pixel
        self.proc: Optional[subprocess.Popen] = None
        self._hwaccel_used = "cpu"

    def start(self) -> subprocess.Popen:
        """Launches the FFmpeg decoding subprocess."""
        if shutil.which(self.config.ffmpeg_bin) is None:
            raise FileNotFoundError(f"FFmpeg binary not found at '{self.config.ffmpeg_bin}'")

        hw = self.config.hwaccel
        if hw == "auto":
            hw = detect_decoder_hwaccel(self.config.ffmpeg_bin)
        self._hwaccel_used = hw

        cmd = [self.config.ffmpeg_bin, "-y", "-hide_banner", "-loglevel", "error"]

        # Hardware acceleration args
        if hw == "videotoolbox":
            cmd.extend(["-hwaccel", "videotoolbox"])
        elif hw in ("cuda", "nvdec"):
            cmd.extend(["-hwaccel", "cuda"])

        # Input specification
        if self.probe_report.is_sequence:
            cmd.extend(["-framerate", f"{self.fps:.4f}", "-i", self.media_path])
        else:
            if self.config.start_frame > 0 and self.fps > 0:
                start_sec = self.config.start_frame / self.fps
                cmd.extend(["-ss", f"{start_sec:.4f}"])
            cmd.extend(["-i", self.media_path])

        if self.config.num_frames is not None and self.config.num_frames > 0:
            cmd.extend(["-vframes", str(self.config.num_frames)])

        # Video filters (scaling if target differs from source)
        vf_filters = []
        if (self.width != self.probe_report.width) or (self.height != self.probe_report.height):
            vf_filters.append(f"scale={self.width}:{self.height}:flags=lanczos")

        if vf_filters:
            cmd.extend(["-vf", ",".join(vf_filters)])

        # Output format: rawvideo on stdout pipe
        cmd.extend([
            "-f", "rawvideo",
            "-pix_fmt", self.pix_fmt,
            "-an",  # Skip audio in frame video pipeline
            "-threads", str(max(1, self.config.threads)),
            "pipe:1",
        ])

        try:
            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=self.frame_bytes * 4,
            )
            return self.proc
        except Exception as e:
            raise RuntimeError(f"Failed to start FFmpeg decoder: {e}")

    @property
    def hwaccel_used(self) -> str:
        return self._hwaccel_used

    def close(self):
        """Terminates the decoder process safely."""
        if self.proc is not None:
            if self.proc.stdout:
                try:
                    self.proc.stdout.close()
                except Exception:
                    pass
            if self.proc.stderr:
                try:
                    self.proc.stderr.close()
                except Exception:
                    pass
            if self.proc.poll() is None:
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
            self.proc = None

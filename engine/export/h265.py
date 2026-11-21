"""CorridorKey 2.0 Desktop — H.265 / HEVC Video Export.

Provides high-efficiency H.265/HEVC video encoding with hardware acceleration
via VideoToolbox (Apple Silicon) or NVENC (NVIDIA RTX) and high-quality libx265 CPU fallback.
Supports alpha channel transparency where container and encoder support it.
"""

from __future__ import annotations

import os
import queue
import shutil
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

from engine.color.color_metadata import get_color_tags
from engine.export.hardware_codec import select_optimal_encoder


@dataclass
class H265Config:
    ffmpeg_bin: str = "ffmpeg"
    bitrate: str = "15M"
    crf: int = 20
    color_profile: str = "rec709"
    prefer_hardware: bool = True
    preserve_alpha: bool = True
    audio_source: Optional[str] = None


class H265Exporter:
    """Streams video frames to FFmpeg H.265/HEVC encoder."""

    def __init__(
        self,
        output_path: str | Path,
        width: int,
        height: int,
        fps: float,
        config: Optional[H265Config] = None,
    ):
        self.output_path = str(output_path)
        self.width = width
        self.height = height
        self.fps = fps
        self.config = config or H265Config()

        self.proc: Optional[subprocess.Popen] = None
        self._q: queue.Queue = queue.Queue(maxsize=8)
        self._err: Optional[Exception] = None
        self._thread: Optional[threading.Thread] = None
        self._frames_written = 0
        self._init_encoder()

    def _init_encoder(self):
        if not shutil.which(self.config.ffmpeg_bin):
            raise FileNotFoundError(f"FFmpeg binary not found at '{self.config.ffmpeg_bin}'")

        Path(self.output_path).parent.mkdir(parents=True, exist_ok=True)
        encoder, pix_fmt = select_optimal_encoder(
            "h265",
            requires_alpha=self.config.preserve_alpha,
            prefer_hardware=self.config.prefer_hardware,
            ffmpeg_bin=self.config.ffmpeg_bin,
        )

        color_tags = get_color_tags(self.config.color_profile)

        cmd = [
            self.config.ffmpeg_bin,
            "-y",
            "-hide_banner",
            "-loglevel", "error",
            "-f", "rawvideo",
            "-pix_fmt", "rgba",
            "-s:v", f"{self.width}x{self.height}",
            "-r", f"{self.fps:.6f}",
            "-i", "pipe:0",
        ]

        has_audio = False
        if self.config.audio_source and os.path.isfile(self.config.audio_source):
            cmd.extend(["-i", self.config.audio_source])
            has_audio = True

        cmd.extend(["-c:v", encoder, "-pix_fmt", pix_fmt])

        if encoder == "libx265":
            cmd.extend(["-crf", str(self.config.crf), "-preset", "medium"])
        elif "videotoolbox" in encoder:
            cmd.extend(["-b:v", self.config.bitrate])
            if self.config.preserve_alpha:
                cmd.extend(["-tag:v", "hvc1"])
        elif "nvenc" in encoder:
            cmd.extend(["-b:v", self.config.bitrate, "-preset", "p5"])

        cmd.extend(color_tags.to_ffmpeg_args())
        cmd.extend(["-movflags", "+faststart"])

        if has_audio:
            cmd.extend(["-map", "0:v:0", "-map", "1:a:0?", "-c:a", "aac", "-b:a", "320k", "-shortest"])
        else:
            cmd.extend(["-an"])

        cmd.append(self.output_path)

        try:
            self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            self._thread = threading.Thread(target=self._worker, daemon=True)
            self._thread.start()
        except Exception as e:
            raise RuntimeError(f"Failed to start H.265 exporter ({encoder}): {e}")

    def _worker(self):
        try:
            while True:
                item = self._q.get()
                if item is None:
                    self._q.task_done()
                    break
                if self.proc and self.proc.stdin:
                    self.proc.stdin.write(item)
                self._q.task_done()
        except Exception as e:
            self._err = e

    def write_frame_rgba(self, rgba: np.ndarray):
        """Buffers RGBA 8-bit frame for streaming into encoder pipe."""
        if self._err:
            raise self._err
        if rgba.dtype != np.uint8:
            rgba = np.clip(rgba * 255.0, 0.0, 255.0).astype(np.uint8)
        self._q.put(rgba.tobytes())
        self._frames_written += 1

    def write_rgba(self, rgba: np.ndarray):
        self.write_frame_rgba(rgba)

    def close(self):
        """Finalizes encoding and waits for encoder process completion."""
        self._q.put(None)
        if self._thread:
            self._thread.join(timeout=30.0)
        if self.proc:
            if self.proc.stdin:
                try:
                    self.proc.stdin.close()
                except Exception:
                    pass
            self.proc.wait(timeout=30.0)
            if self.proc.returncode != 0:
                raise RuntimeError(f"H.265 export failed with code {self.proc.returncode}")

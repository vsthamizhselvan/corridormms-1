"""CorridorKey 2.0 Desktop — Apple ProRes 4444 Video Export.

Encodes high-quality 10-bit/12-bit master video with full alpha channel support
using FFmpeg prores_ks (profile 4 for 4444, profile 5 for 4444 XQ) and yuva444p10le.
"""

from __future__ import annotations

import os
import queue
import shutil
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

from engine.color.color_metadata import get_color_tags


@dataclass
class ProResConfig:
    ffmpeg_bin: str = "ffmpeg"
    profile: int = 4  # 4 = ProRes 4444, 5 = ProRes 4444 XQ
    color_profile: str = "rec709"
    threads: int = 4
    audio_source: Optional[str] = None  # path to source file for audio muxing


class ProResExporter:
    """Streams 4-channel RGBA frames to FFmpeg ProRes 4444 encoder."""

    def __init__(self, output_path: str | Path, width: int, height: int, fps: float, config: Optional[ProResConfig] = None):
        self.output_path = str(output_path)
        self.width = width
        self.height = height
        self.fps = fps
        self.config = config or ProResConfig()

        self.proc: Optional[subprocess.Popen] = None
        self._q: queue.Queue = queue.Queue(maxsize=4)
        self._err: Optional[Exception] = None
        self._thread: Optional[threading.Thread] = None
        self._frames_written = 0
        self._init_encoder()

    def _init_encoder(self):
        if not shutil.which(self.config.ffmpeg_bin):
            raise FileNotFoundError(f"FFmpeg binary not found at '{self.config.ffmpeg_bin}'")

        Path(self.output_path).parent.mkdir(parents=True, exist_ok=True)
        color_tags = get_color_tags(self.config.color_profile)

        # Video stream input from stdin: raw 64-bit BGRA (16-bit per channel)
        cmd = [
            self.config.ffmpeg_bin,
            "-y",
            "-hide_banner",
            "-loglevel", "error",
            "-f", "rawvideo",
            "-pix_fmt", "bgra64le",
            "-s:v", f"{self.width}x{self.height}",
            "-r", f"{self.fps:.6f}",
            "-i", "pipe:0",
        ]

        # Audio stream muxing if provided
        has_audio = False
        if self.config.audio_source and os.path.isfile(self.config.audio_source):
            cmd.extend(["-i", self.config.audio_source])
            has_audio = True

        # Video encoding parameters
        cmd.extend([
            "-c:v", "prores_ks",
            "-profile:v", str(self.config.profile),
            "-pix_fmt", "yuva444p10le",
            "-threads", str(max(1, self.config.threads)),
        ])

        # Color metadata
        cmd.extend(color_tags.to_ffmpeg_args())
        cmd.extend(["-movflags", "+write_colr"])

        # Audio mapping
        if has_audio:
            cmd.extend(["-map", "0:v:0", "-map", "1:a:0?", "-c:a", "copy", "-shortest"])
        else:
            cmd.extend(["-an"])

        cmd.append(self.output_path)

        try:
            self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            self._thread = threading.Thread(target=self._worker, daemon=True)
            self._thread.start()
        except Exception as e:
            raise RuntimeError(f"Failed to start ProRes exporter: {e}")

    def _worker(self):
        try:
            while True:
                item = self._q.get()
                if item is None:
                    self._q.task_done()
                    return
                if self.proc and self.proc.stdin:
                    self.proc.stdin.write(item.tobytes())
                self._q.task_done()
        except Exception as e:
            self._err = e

    def write_frame_rgba(self, rgba: np.ndarray):
        """Accepts RGBA frame (float32 [0, 1] or uint8 [0, 255] or uint16). Converted to uint16 BGRA."""
        if self._err is not None:
            raise self._err

        arr = np.ascontiguousarray(rgba)
        if arr.dtype == np.float32:
            arr = np.clip(arr * 65535.0, 0.0, 65535.0).astype(np.uint16)
        elif arr.dtype == np.uint8:
            arr = (arr.astype(np.uint16) * 257)  # 8-bit to 16-bit mapping

        # Ensure BGRA order for bgra64le input
        r, g, b, a = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]
        bgra = np.stack([b, g, r, a], axis=-1)

        self._q.put(bgra)
        self._frames_written += 1

    def close(self):
        self._q.put(None)
        if self._thread:
            self._thread.join()
        if self.proc:
            if self.proc.stdin:
                try:
                    self.proc.stdin.close()
                except Exception:
                    pass
            rc = self.proc.wait()
            if rc != 0 and self._err is None:
                self._err = RuntimeError(f"ProRes FFmpeg exporter exited with error code {rc}")
            self.proc = None
        if self._err is not None:
            raise self._err

    @property
    def frames_written(self) -> int:
        return self._frames_written

"""CorridorKey 2.0 Desktop — VP9 / WebM Transparent Video Export.

Encodes WebM video with verified alpha transparency using FFmpeg libvpx-vp9
with yuva420p and auto-alt-ref disabled.
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


@dataclass
class Vp9Config:
    ffmpeg_bin: str = "ffmpeg"
    crf: int = 20
    deadline: str = "good"  # 'good' | 'best' | 'realtime'
    threads: int = 4
    audio_source: Optional[str] = None


class Vp9Exporter:
    """Streams 4-channel RGBA frames to FFmpeg libvpx-vp9 encoder with alpha."""

    def __init__(self, output_path: str | Path, width: int, height: int, fps: float, config: Optional[Vp9Config] = None):
        self.output_path = str(output_path)
        self.width = width
        self.height = height
        self.fps = fps
        self.config = config or Vp9Config()

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

        cmd = [
            self.config.ffmpeg_bin,
            "-y",
            "-hide_banner",
            "-loglevel", "error",
            "-f", "rawvideo",
            "-pix_fmt", "bgra",
            "-s:v", f"{self.width}x{self.height}",
            "-r", f"{self.fps:.6f}",
            "-i", "pipe:0",
        ]

        has_audio = False
        if self.config.audio_source and os.path.isfile(self.config.audio_source):
            cmd.extend(["-i", self.config.audio_source])
            has_audio = True

        cmd.extend([
            "-c:v", "libvpx-vp9",
            "-pix_fmt", "yuva420p",
            "-auto-alt-ref", "0",  # MANDATORY for VP9 alpha channel preservation
            "-b:v", "0",
            "-crf", str(self.config.crf),
            "-deadline", self.config.deadline,
            "-threads", str(max(1, self.config.threads)),
        ])

        if has_audio:
            cmd.extend(["-map", "0:v:0", "-map", "1:a:0?", "-c:a", "libopus", "-b:a", "128k", "-shortest"])
        else:
            cmd.extend(["-an"])

        cmd.append(self.output_path)

        try:
            self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            self._thread = threading.Thread(target=self._worker, daemon=True)
            self._thread.start()
        except Exception as e:
            raise RuntimeError(f"Failed to start VP9 exporter: {e}")

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
        if self._err is not None:
            raise self._err

        arr = np.ascontiguousarray(rgba)
        if arr.dtype == np.float32:
            arr = np.clip(arr * 255.0, 0.0, 255.0).astype(np.uint8)
        elif arr.dtype == np.uint16:
            arr = (arr // 257).astype(np.uint8)

        # Reorder to BGRA
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
                self._err = RuntimeError(f"VP9 FFmpeg exporter exited with error code {rc}")
            self.proc = None
        if self._err is not None:
            raise self._err

    @property
    def frames_written(self) -> int:
        return self._frames_written

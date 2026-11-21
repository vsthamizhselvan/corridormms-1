"""CorridorKey 2.0 Desktop — OpenEXR Sequence Export.

Writes multi-channel scene-referred HDR frames as an OpenEXR image sequence
with full 16-bit half-float or 32-bit float accuracy and lossless ZIP compression
using FFmpeg's high-performance native EXR encoder.
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
class ExrConfig:
    ffmpeg_bin: str = "ffmpeg"
    dtype: str = "half"  # 'half' (float16) | 'float' (float32)
    compression: str = "zip1"  # 'none' | 'rle' | 'zip1' | 'zip16'
    frame_prefix: str = "frame"
    start_index: int = 1


class OpenExrExporter:
    """Asynchronously writes RGBA frames to an OpenEXR image sequence using FFmpeg."""

    def __init__(self, output_dir: str | Path, width: int, height: int, fps: float, config: Optional[ExrConfig] = None):
        self.output_dir = str(output_dir)
        self.width = width
        self.height = height
        self.fps = fps
        self.config = config or ExrConfig()

        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

        self._q: queue.Queue = queue.Queue(maxsize=8)
        self._err: Optional[Exception] = None
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
        self._frames_written = 0

    def _worker(self):
        try:
            while True:
                item = self._q.get()
                if item is None:
                    self._q.task_done()
                    return

                idx, planar_bytes = item
                filename = f"{self.config.frame_prefix}_{idx:06d}.exr"
                out_path = os.path.join(self.output_dir, filename)

                cmd = [
                    self.config.ffmpeg_bin,
                    "-y",
                    "-hide_banner",
                    "-loglevel", "error",
                    "-f", "rawvideo",
                    "-pix_fmt", "gbrapf32le",
                    "-s:v", f"{self.width}x{self.height}",
                    "-i", "pipe:0",
                    "-c:v", "exr",
                    "-format", "half" if self.config.dtype == "half" else "float",
                    "-compression", self.config.compression,
                    out_path,
                ]

                proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
                _, stderr = proc.communicate(input=planar_bytes)
                if proc.returncode != 0:
                    raise RuntimeError(f"FFmpeg EXR export failed: {stderr.decode()}")

                self._q.task_done()
        except Exception as e:
            self._err = e

    def write_frame_rgba(self, rgba: np.ndarray):
        """Accepts float32 or uint8 RGBA frame. Converts to planar GBRAPF32LE byte stream."""
        if self._err is not None:
            raise self._err

        arr = np.ascontiguousarray(rgba, dtype=np.float32)
        if arr.max() > 1.05:
            arr = arr / 255.0

        r = arr[..., 0]
        g = arr[..., 1]
        b = arr[..., 2]
        a = arr[..., 3]

        # In FFmpeg, gbrapf32le is planar G, B, R, A (each float32)
        planar = np.ascontiguousarray(np.stack([g, b, r, a], axis=0), dtype=np.float32).tobytes()

        idx = self.config.start_index + self._frames_written
        self._q.put((idx, planar))
        self._frames_written += 1

    def close(self):
        self._q.put(None)
        self._thread.join()
        if self._err is not None:
            raise self._err

    @property
    def frames_written(self) -> int:
        return self._frames_written

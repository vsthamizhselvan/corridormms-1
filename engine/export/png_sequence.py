"""CorridorKey 2.0 Desktop — PNG Sequence Export.

Writes transparent 8-bit or 16-bit RGBA image sequences with lossless compression.
"""

from __future__ import annotations

import os
import queue
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np


@dataclass
class PngConfig:
    bit_depth: int = 8  # 8 or 16
    compression: int = 4  # 0 to 9
    frame_prefix: str = "frame"
    start_index: int = 1


class PngSequenceExporter:
    """Asynchronously writes RGBA frames to a PNG image sequence."""

    def __init__(self, output_dir: str | Path, width: int, height: int, fps: float, config: Optional[PngConfig] = None):
        self.output_dir = str(output_dir)
        self.width = width
        self.height = height
        self.fps = fps
        self.config = config or PngConfig()

        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        self.imwrite_params = [cv2.IMWRITE_PNG_COMPRESSION, self.config.compression]

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

                idx, bgra_arr = item
                filename = f"{self.config.frame_prefix}_{idx:06d}.png"
                out_path = os.path.join(self.output_dir, filename)

                ok = cv2.imwrite(out_path, bgra_arr, self.imwrite_params)
                if not ok:
                    raise RuntimeError(f"Failed to write PNG frame: {out_path}")

                self._q.task_done()
        except Exception as e:
            self._err = e

    def write_frame_rgba(self, rgba: np.ndarray):
        if self._err is not None:
            raise self._err

        arr = np.ascontiguousarray(rgba)
        if self.config.bit_depth == 16:
            if arr.dtype == np.float32:
                arr = np.clip(arr * 65535.0, 0.0, 65535.0).astype(np.uint16)
            elif arr.dtype == np.uint8:
                arr = (arr.astype(np.uint16) * 257)
        else:
            if arr.dtype == np.float32:
                arr = np.clip(arr * 255.0, 0.0, 255.0).astype(np.uint8)
            elif arr.dtype == np.uint16:
                arr = (arr // 257).astype(np.uint8)

        # Convert RGBA to BGRA
        r, g, b, a = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]
        bgra = np.stack([b, g, r, a], axis=-1)

        idx = self.config.start_index + self._frames_written
        self._q.put((idx, bgra))
        self._frames_written += 1

    def close(self):
        self._q.put(None)
        self._thread.join()
        if self._err is not None:
            raise self._err

    @property
    def frames_written(self) -> int:
        return self._frames_written

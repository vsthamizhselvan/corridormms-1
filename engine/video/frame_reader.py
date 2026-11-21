"""CorridorKey 2.0 Desktop — Streaming Frame Reader.

Reads raw binary pixel buffers from an FFmpegDecoder instance, reconstructs
contiguous NumPy frame arrays, and yields frames with their exact presentation timestamps.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Iterator, Optional, Tuple

import numpy as np

from engine.video.decoder import DecoderConfig, FFmpegDecoder
from engine.video.timestamp_manager import TimestampManager


@dataclass
class DecodedFrame:
    index: int
    pts_time: float
    image: np.ndarray  # H x W x C (uint8 or uint16)
    width: int
    height: int
    channels: int
    pix_fmt: str


class FrameReader:
    """Iterates over decoded video frames from FFmpegDecoder."""

    def __init__(self, media_path: str | Path, config: Optional[DecoderConfig] = None):
        self.decoder = FFmpegDecoder(media_path, config)
        self.timing_mgr = TimestampManager.from_ffprobe(media_path)
        self._proc = None

    def __iter__(self) -> Iterator[DecodedFrame]:
        proc = self.decoder.start()
        self._proc = proc
        stdout = proc.stdout
        if stdout is None:
            raise RuntimeError("Decoder stdout pipe is not available")

        frame_bytes = self.decoder.frame_bytes
        h, w = self.decoder.height, self.decoder.width
        c = self.decoder.bytes_per_pixel // (2 if self.decoder.dtype_str == "uint16" else 1)
        dtype = np.uint16 if self.decoder.dtype_str == "uint16" else np.uint8

        frame_idx = 0
        try:
            while True:
                # Read exactly one frame from the pipe
                raw_data = stdout.read(frame_bytes)
                if not raw_data or len(raw_data) < frame_bytes:
                    break

                # Convert raw buffer directly into contiguous NumPy frame
                arr = np.frombuffer(raw_data, dtype=dtype).reshape((h, w, c))
                pts = self.timing_mgr.get_timestamp(frame_idx)

                yield DecodedFrame(
                    index=frame_idx,
                    pts_time=pts,
                    image=arr,
                    width=w,
                    height=h,
                    channels=c,
                    pix_fmt=self.decoder.pix_fmt,
                )
                frame_idx += 1

        finally:
            self.close()

    def close(self):
        self.decoder.close()

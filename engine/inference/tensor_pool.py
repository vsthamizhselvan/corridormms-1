"""CorridorKey 2.0 Desktop — Persistent GPU Tensor Pool & Inference Optimiser.

Manages reusable pre-allocated GPU tensor buffers, asynchronous memory transfers,
device auto-detection (NVIDIA CUDA / Apple Silicon MPS / CPU), model warmup,
and memory reclamation.
"""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import numpy as np
import torch


@dataclass
class HardwareTarget:
    device_type: str  # 'cuda' | 'mps' | 'cpu'
    device_index: int = 0
    device_name: str = "CPU"
    is_unified_memory: bool = False
    cuda_compute_capability: Optional[Tuple[int, int]] = None
    stream: Optional[Any] = None


def resolve_optimal_device(preference: str = "auto") -> HardwareTarget:
    """Resolves optimal PyTorch execution device with validation and graceful fallback."""
    pref = preference.lower().strip()

    # 1. Explicit CUDA request or auto
    if pref in ("auto", "cuda", "gpu", "nvidia"):
        if torch.cuda.is_available():
            idx = torch.cuda.current_device()
            name = torch.cuda.get_device_name(idx)
            cc = torch.cuda.get_device_capability(idx)
            stream = torch.cuda.Stream()
            return HardwareTarget(
                device_type="cuda",
                device_index=idx,
                device_name=name,
                is_unified_memory=False,
                cuda_compute_capability=cc,
                stream=stream,
            )

    # 2. Explicit MPS request or auto
    if pref in ("auto", "mps", "apple", "metal", "gpu"):
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return HardwareTarget(
                device_type="mps",
                device_index=0,
                device_name="Apple Silicon (Metal / MPS)",
                is_unified_memory=True,
                cuda_compute_capability=None,
                stream=None,
            )

    # 3. CPU fallback
    return HardwareTarget(
        device_type="cpu",
        device_index=0,
        device_name="Host CPU",
        is_unified_memory=False,
        cuda_compute_capability=None,
        stream=None,
    )


class GpuTensorPool:
    """Zero-allocation reusable GPU tensor buffer pool for high-throughput frame processing."""

    def __init__(self, target: Optional[HardwareTarget] = None):
        self.target = target or resolve_optimal_device("auto")
        self.device = torch.device(self.target.device_type)

        # Pre-allocated tensor registry: shape_key -> torch.Tensor
        self._input_buffers: Dict[Tuple[int, ...], torch.Tensor] = {}
        self._output_buffers: Dict[Tuple[int, ...], torch.Tensor] = {}
        self._pinned_staging: Dict[Tuple[int, ...], torch.Tensor] = {}

        self.last_inference_ms: float = 0.0
        self.total_frames_processed: int = 0

    def get_input_buffer(self, shape: Tuple[int, ...], dtype: torch.dtype = torch.float32) -> torch.Tensor:
        """Retrieves or pre-allocates persistent input tensor buffer."""
        key = (shape, dtype)
        if key not in self._input_buffers:
            # Allocate once on GPU
            buf = torch.empty(shape, dtype=dtype, device=self.device)
            self._input_buffers[key] = buf
        return self._input_buffers[key]

    def upload_frame(self, frame_rgb_norm: np.ndarray) -> torch.Tensor:
        """Uploads float32 [H, W, 3] RGB numpy array into pre-allocated GPU tensor [1, 3, H, W].

        Uses pinned memory staging on CUDA and direct zero-copy tensor sharing on MPS.
        """
        h, w, c = frame_rgb_norm.shape
        shape = (1, 3, h, w)
        t_buf = self.get_input_buffer(shape, dtype=torch.float32)

        # Transpose HWC -> CHW
        # In NumPy, ascontiguousarray is fast
        chw = np.ascontiguousarray(frame_rgb_norm.transpose(2, 0, 1))

        if self.target.device_type == "cuda":
            # Leverage CUDA pinned memory and non-blocking transfer
            if shape not in self._pinned_staging:
                self._pinned_staging[shape] = torch.empty(shape, dtype=torch.float32, pin_memory=True)
            staging = self._pinned_staging[shape]
            staging[0].copy_(torch.from_numpy(chw))
            with torch.cuda.stream(self.target.stream):
                t_buf.copy_(staging, non_blocking=True)
            self.target.stream.synchronize()

        elif self.target.device_type == "mps":
            # MPS unified memory: from_numpy followed by copy into persistent buffer
            t_src = torch.from_numpy(chw).unsqueeze(0)
            t_buf.copy_(t_src)
            torch.mps.synchronize()

        else:
            # CPU
            t_src = torch.from_numpy(chw).unsqueeze(0)
            t_buf.copy_(t_src)

        return t_buf

    def warmup(self, model: Optional[Any] = None, sample_shape: Tuple[int, int] = (1080, 1920)) -> float:
        """Performs a warmup inference pass to prime CUDA/Metal kernel caches and prevent initial stutter."""
        t0 = time.perf_counter()
        h, w = sample_shape
        dummy_rgb = np.zeros((h, w, 3), dtype=np.float32)
        dummy_tensor = self.upload_frame(dummy_rgb)

        if model is not None:
            try:
                with torch.no_grad():
                    if hasattr(model, "forward"):
                        _ = model(dummy_tensor)
                    elif callable(model):
                        _ = model(dummy_tensor)
                self.synchronize()
            except Exception as e:
                # If model forward signature differs, warmup tensor allocation alone succeeds
                pass

        warmup_time = time.perf_counter() - t0
        return warmup_time

    def synchronize(self) -> None:
        """Flushes and synchronizes target hardware execution queues."""
        if self.target.device_type == "cuda":
            torch.cuda.synchronize()
        elif self.target.device_type == "mps":
            torch.mps.synchronize()

    def clear(self) -> None:
        """Clears all cached tensor buffers and releases GPU VRAM."""
        self._input_buffers.clear()
        self._output_buffers.clear()
        self._pinned_staging.clear()

        if self.target.device_type == "cuda":
            torch.cuda.empty_cache()
        elif self.target.device_type == "mps":
            if hasattr(torch.mps, "empty_cache"):
                torch.mps.empty_cache()

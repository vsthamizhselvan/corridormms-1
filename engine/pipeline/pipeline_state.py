"""CorridorKey 2.0 Desktop — Video Pipeline State & Metrics.

Tracks real-time progress across all three concurrent pipeline stages:
1. Video Decoding (FFmpeg/Hardware)
2. AI Inference (CorridorKey 2.0 Neural Engine)
3. Professional Encoding (ProRes, QTRLE, VP9, EXR, PNG)
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from typing import Dict, Optional


@dataclass
class PipelineProgress:
    job_id: str
    status: str  # 'running' | 'completed' | 'failed' | 'cancelled'
    overall_progress: float  # 0.0 to 1.0
    decoding_progress: float
    inference_progress: float
    encoding_progress: float
    frames_decoded: int
    frames_inferred: int
    frames_encoded: int
    total_frames: int
    fps: float
    eta_seconds: float
    current_stage: str
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)


class PipelineStateTracker:
    """Tracks frame progression and computes smoothed FPS and ETA metrics."""

    def __init__(self, job_id: str, total_frames: int):
        self.job_id = job_id
        self.total_frames = max(1, total_frames)
        self.frames_decoded = 0
        self.frames_inferred = 0
        self.frames_encoded = 0
        self.start_time = time.time()
        self.last_update_time = self.start_time
        self.current_stage = "Initializing"

    def update_decoding(self, count: int = 1):
        self.frames_decoded += count

    def update_inference(self, count: int = 1):
        self.frames_inferred += count

    def update_encoding(self, count: int = 1):
        self.frames_encoded += count

    def get_progress(self) -> PipelineProgress:
        now = time.time()
        elapsed = max(0.001, now - self.start_time)
        fps = self.frames_encoded / elapsed if self.frames_encoded > 0 else 0.0

        # Stage ratios: Decoding 20%, Inference 60%, Encoding 20%
        p_dec = min(1.0, self.frames_decoded / self.total_frames)
        p_inf = min(1.0, self.frames_inferred / self.total_frames)
        p_enc = min(1.0, self.frames_encoded / self.total_frames)

        overall = 0.20 * p_dec + 0.60 * p_inf + 0.20 * p_enc

        remaining_frames = max(0, self.total_frames - self.frames_encoded)
        eta = remaining_frames / fps if fps > 0 else 0.0

        if p_enc >= 1.0:
            stage = "Finalizing Output"
        elif p_inf > p_enc:
            stage = "Encoding & Color Management"
        elif p_dec > p_inf:
            stage = "Neural Matte Extraction"
        else:
            stage = "Decoding Source Footage"

        return PipelineProgress(
            job_id=self.job_id,
            status="running",
            overall_progress=round(overall, 4),
            decoding_progress=round(p_dec, 4),
            inference_progress=round(p_inf, 4),
            encoding_progress=round(p_enc, 4),
            frames_decoded=self.frames_decoded,
            frames_inferred=self.frames_inferred,
            frames_encoded=self.frames_encoded,
            total_frames=self.total_frames,
            fps=round(fps, 2),
            eta_seconds=round(eta, 1),
            current_stage=stage,
        )

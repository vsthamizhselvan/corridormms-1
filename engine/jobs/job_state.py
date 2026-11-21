"""CorridorKey 2.0 Desktop — AI Inference Job State Models."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class JobStatus(str, Enum):
    PENDING = "pending"
    INITIALIZING = "initializing"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class JobProgress:
    job_id: str
    processed_frames: int
    total_frames: int
    percentage: float
    fps: float = 0.0
    eta_seconds: float = 0.0
    current_stage: str = "Processing"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class JobConfig:
    job_id: str
    input_path: str
    output_dir: str
    outputs: List[str] = field(default_factory=lambda: ["alpha", "fg"])
    hann_chunk: int = 24
    hann_stride: int = 12
    low_vram: bool = False
    despill_strength: float = 0.5
    hint_first_frame: Optional[str] = None
    hint_video: Optional[str] = None
    hint_quality: float = 0.95
    device: str = "auto"
    output_format: str = "video"  # 'video' | 'exr'
    export_format: str = "prores_4444"  # 'prores_4444' | 'prores_4444_xq' | 'qtrle' | 'vp9' | 'openexr' | 'png_sequence'
    color_profile: str = "rec709"  # 'rec709' | 'srgb' | 'linear' | 'rec2020' | 'acescg'
    alpha_mode: str = "straight"  # 'straight' | 'premultiplied'
    preserve_audio: bool = True

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "JobConfig":
        return cls(
            job_id=d.get("job_id", ""),
            input_path=d.get("input_path", ""),
            output_dir=d.get("output_dir", ""),
            outputs=d.get("outputs", ["alpha", "fg"]),
            hann_chunk=int(d.get("hann_chunk", 24)),
            hann_stride=int(d.get("hann_stride", 12)),
            low_vram=bool(d.get("low_vram", False)),
            despill_strength=float(d.get("despill_strength", 0.5)),
            hint_first_frame=d.get("hint_first_frame"),
            hint_video=d.get("hint_video"),
            hint_quality=float(d.get("hint_quality", 0.95)),
            device=d.get("device", "auto"),
            output_format=d.get("output_format", "video"),
            export_format=d.get("export_format", "prores_4444"),
            color_profile=d.get("color_profile", "rec709"),
            alpha_mode=d.get("alpha_mode", "straight"),
            preserve_audio=bool(d.get("preserve_audio", True)),
        )


@dataclass
class JobRecord:
    config: JobConfig
    status: JobStatus = JobStatus.PENDING
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    processed_frames: int = 0
    total_frames: int = 0
    percentage: float = 0.0
    outputs: Dict[str, str] = field(default_factory=dict)
    error_message: Optional[str] = None
    error_code: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.config.job_id,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "elapsed_seconds": round((self.end_time or time.time()) - self.start_time, 2),
            "processed_frames": self.processed_frames,
            "total_frames": self.total_frames,
            "percentage": self.percentage,
            "outputs": self.outputs,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "config": asdict(self.config),
        }

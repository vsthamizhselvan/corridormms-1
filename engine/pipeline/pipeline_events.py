"""CorridorKey 2.0 Desktop — Pipeline Event Definitions.

Provides event serializations for real-time progress broadcast to the desktop UI.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

from engine.desktop_api.protocol import EngineEvent, EventType
from engine.pipeline.pipeline_state import PipelineProgress


def make_pipeline_progress_event(progress: PipelineProgress) -> EngineEvent:
    return EngineEvent(
        type=EventType.PROGRESS.value,
        job_id=progress.job_id,
        data=progress.to_dict(),
    )


def make_pipeline_completed_event(
    job_id: str,
    output_path: str,
    validation_data: Dict[str, Any],
    color_data: Dict[str, Any],
    elapsed_seconds: float,
) -> EngineEvent:
    return EngineEvent(
        type=EventType.JOB_COMPLETED.value,
        job_id=job_id,
        data={
            "job_id": job_id,
            "output_path": output_path,
            "validation": validation_data,
            "color_report": color_data,
            "elapsed_seconds": round(elapsed_seconds, 2),
        },
    )

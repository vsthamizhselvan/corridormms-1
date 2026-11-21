"""CorridorKey 2.0 Desktop — AI Engine Communication Protocol.

Defines the versioned JSON-lines protocol contract between the Tauri 2 Rust supervisor
and the Python AI worker process over stdin/stdout.

All messages transmitted across stdout must conform to this schema and are single-line JSON.
Standard diagnostics and Python tracebacks are directed to stderr.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

PROTOCOL_VERSION = 1


class CommandType(str, Enum):
    PING = "ping"
    DETECT_HARDWARE = "detect_hardware"
    CHECK_MODEL_STATUS = "check_model_status"
    LOAD_MODEL = "load_model"
    START_JOB = "start_job"
    CANCEL_JOB = "cancel_job"
    GET_JOB_STATUS = "get_job_status"
    GET_PERFORMANCE_METRICS = "get_performance_metrics"
    SHUTDOWN = "shutdown"


class EventType(str, Enum):
    READY = "ready"
    PONG = "pong"
    HARDWARE = "hardware"
    MODEL_STATUS = "model_status"
    MODEL_LOADED = "model_loaded"
    JOB_STARTED = "job_started"
    PROGRESS = "progress"
    JOB_COMPLETED = "job_completed"
    JOB_CANCELLED = "job_cancelled"
    JOB_STATUS = "job_status"
    PERFORMANCE_METRICS = "performance_metrics"
    ERROR = "error"


@dataclass
class EngineCommand:
    type: str
    command_id: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    protocol_version: int = PROTOCOL_VERSION

    @classmethod
    def from_json(cls, line: str) -> "EngineCommand":
        data = json.loads(line.strip())
        return cls(
            type=data.get("type", ""),
            command_id=data.get("command_id"),
            payload=data.get("payload", {}),
            protocol_version=data.get("protocol_version", PROTOCOL_VERSION),
        )

    def to_json(self) -> str:
        return json.dumps(asdict(self))


@dataclass
class EngineEvent:
    type: str
    protocol_version: int = PROTOCOL_VERSION
    command_id: Optional[str] = None
    job_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    def to_json(self) -> str:
        d = asdict(self)
        # Drop None fields for cleaner payloads
        clean = {k: v for k, v in d.items() if v is not None}
        return json.dumps(clean)

    @classmethod
    def from_json(cls, line: str) -> "EngineEvent":
        d = json.loads(line.strip())
        return cls(
            type=d.get("type", ""),
            protocol_version=d.get("protocol_version", PROTOCOL_VERSION),
            command_id=d.get("command_id"),
            job_id=d.get("job_id"),
            data=d.get("data", {}),
            error_code=d.get("error_code"),
            error_message=d.get("error_message"),
        )

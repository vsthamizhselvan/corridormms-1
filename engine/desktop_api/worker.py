"""CorridorKey 2.0 Desktop — AI Engine Worker Process.

Implements the standard input/output JSON-lines message dispatch loop,
handling hardware detection, model management, asynchronous inference jobs,
and real-time event streaming back to the Tauri 2 supervisor.
"""

from __future__ import annotations

import sys
import threading
from typing import Any, Optional

from engine.desktop_api.hardware import detect_system_hardware
from engine.desktop_api.model_manager import ModelManager
from engine.desktop_api.protocol import CommandType, EngineCommand, EngineEvent, EventType
from engine.jobs.job_manager import JobManager
from engine.jobs.job_state import JobConfig, JobProgress


class EngineWorker:
    def __init__(self):
        self.job_manager = JobManager.get_instance()
        self.model_manager = ModelManager.get_instance()
        self._running = False
        self._out_lock = threading.Lock()

    def emit(self, event: EngineEvent) -> None:
        """Atomically emits a single-line JSON protocol event to standard output."""
        line = event.to_json()
        with self._out_lock:
            sys.stdout.write(line + "\n")
            sys.stdout.flush()

    def run(self) -> None:
        """Starts the worker event loop listening on stdin."""
        self._running = True

        # Emit initial ready signal
        self.emit(
            EngineEvent(
                type=EventType.READY.value,
                data={
                    "worker": "corridorkey_ai_worker",
                    "version": "2.0.0",
                    "status": "ready",
                },
            )
        )
        print("[Worker] CorridorKey AI Engine Worker initialized and ready.", file=sys.stderr)

        for line in sys.stdin:
            if not self._running:
                break

            line_str = line.strip()
            if not line_str:
                continue

            try:
                cmd = EngineCommand.from_json(line_str)
                self.handle_command(cmd)
            except Exception as e:
                print(f"[Worker] Error parsing command: {e}", file=sys.stderr)
                self.emit(
                    EngineEvent(
                        type=EventType.ERROR.value,
                        error_code="INVALID_COMMAND",
                        error_message=str(e),
                    )
                )

    def handle_command(self, cmd: EngineCommand) -> None:
        cmd_type = cmd.type

        # 1. PING
        if cmd_type == CommandType.PING.value:
            self.emit(EngineEvent(type=EventType.PONG.value, command_id=cmd.command_id))

        # 2. DETECT HARDWARE
        elif cmd_type == CommandType.DETECT_HARDWARE.value:
            profile = detect_system_hardware()
            self.emit(
                EngineEvent(
                    type=EventType.HARDWARE.value,
                    command_id=cmd.command_id,
                    data=profile.to_dict(),
                )
            )

        # 3. CHECK MODEL STATUS
        elif cmd_type == CommandType.CHECK_MODEL_STATUS.value:
            status = self.model_manager.check_assets()
            self.emit(
                EngineEvent(
                    type=EventType.MODEL_STATUS.value,
                    command_id=cmd.command_id,
                    data=status.to_dict(),
                )
            )

        # 4. LOAD MODEL
        elif cmd_type == CommandType.LOAD_MODEL.value:
            device = cmd.payload.get("device", "auto")
            ok, msg = self.model_manager.load_model(target_device=device)
            if ok:
                self.emit(
                    EngineEvent(
                        type=EventType.MODEL_LOADED.value,
                        command_id=cmd.command_id,
                        data={
                            "success": True,
                            "message": msg,
                            "device": self.model_manager.active_device,
                        },
                    )
                )
            else:
                self.emit(
                    EngineEvent(
                        type=EventType.ERROR.value,
                        command_id=cmd.command_id,
                        error_code="MODEL_LOAD_FAILED",
                        error_message=msg,
                    )
                )

        # 5. START JOB
        elif cmd_type == CommandType.START_JOB.value:
            job_cfg = JobConfig.from_dict(cmd.payload)
            record = self.job_manager.create_job(job_cfg)

            self.emit(
                EngineEvent(
                    type=EventType.JOB_STARTED.value,
                    command_id=cmd.command_id,
                    job_id=job_cfg.job_id,
                    data={"job_id": job_cfg.job_id, "status": record.status.value},
                )
            )

            # Define callbacks for asynchronous event streaming
            def _on_progress(progress: JobProgress):
                self.emit(
                    EngineEvent(
                        type=EventType.PROGRESS.value,
                        job_id=job_cfg.job_id,
                        data=progress.to_dict(),
                    )
                )

            def _on_completed(job_id: str, outputs: dict):
                self.emit(
                    EngineEvent(
                        type=EventType.JOB_COMPLETED.value,
                        job_id=job_id,
                        data={"job_id": job_id, "outputs": outputs},
                    )
                )

            def _on_error(job_id: str, code: str, msg: str):
                self.emit(
                    EngineEvent(
                        type=EventType.ERROR.value,
                        job_id=job_id,
                        error_code=code,
                        error_message=msg,
                    )
                )

            # Start on background thread
            self.job_manager.execute_job_async(
                job_id=job_cfg.job_id,
                on_progress=_on_progress,
                on_completed=_on_completed,
                on_error=_on_error,
                model_instance=self.model_manager.model_instance,
            )

        # 6. CANCEL JOB
        elif cmd_type == CommandType.CANCEL_JOB.value:
            job_id = cmd.payload.get("job_id", "")
            success = self.job_manager.cancel_job(job_id)
            self.emit(
                EngineEvent(
                    type=EventType.JOB_CANCELLED.value,
                    command_id=cmd.command_id,
                    job_id=job_id,
                    data={"job_id": job_id, "cancelled": success},
                )
            )

        # 7. GET JOB STATUS
        elif cmd_type == CommandType.GET_JOB_STATUS.value:
            job_id = cmd.payload.get("job_id", "")
            job = self.job_manager.get_job(job_id)
            if job:
                self.emit(
                    EngineEvent(
                        type=EventType.JOB_STATUS.value,
                        command_id=cmd.command_id,
                        job_id=job_id,
                        data=job.to_dict(),
                    )
                )
            else:
                self.emit(
                    EngineEvent(
                        type=EventType.ERROR.value,
                        command_id=cmd.command_id,
                        error_code="JOB_NOT_FOUND",
                        error_message=f"No job found with id {job_id}",
                    )
                )

        # 8. GET PERFORMANCE METRICS
        elif cmd_type == CommandType.GET_PERFORMANCE_METRICS.value:
            from engine.pipeline.frame_cache import IntelligentFrameCache
            from engine.pipeline.memory_guard import MemoryGuard

            guard = MemoryGuard()
            mem_status = guard.get_memory_status()
            cache_stats = IntelligentFrameCache.get_instance().get_stats()

            perf_data = {
                "memory": {
                    "total_ram_mb": mem_status.total_ram_mb,
                    "available_ram_mb": mem_status.available_ram_mb,
                    "process_rss_mb": mem_status.process_rss_mb,
                    "gpu_allocated_mb": mem_status.gpu_allocated_mb,
                    "gpu_reserved_mb": mem_status.gpu_reserved_mb,
                    "is_pressure": mem_status.is_pressure,
                },
                "cache": cache_stats.to_dict(),
                "jobs": {
                    "active_jobs": len([j for j in self.job_manager.list_jobs() if j.status.value in ("running", "queued")]),
                    "total_jobs": len(self.job_manager.list_jobs()),
                },
            }

            self.emit(
                EngineEvent(
                    type=EventType.PERFORMANCE_METRICS.value,
                    command_id=cmd.command_id,
                    data=perf_data,
                )
            )

        # 9. SHUTDOWN
        elif cmd_type == CommandType.SHUTDOWN.value:
            print("[Worker] Received shutdown command. Exiting cleanly.", file=sys.stderr)
            self._running = False
            sys.exit(0)

        else:
            self.emit(
                EngineEvent(
                    type=EventType.ERROR.value,
                    command_id=cmd.command_id,
                    error_code="UNKNOWN_COMMAND",
                    error_message=f"Command type '{cmd_type}' is unrecognized.",
                )
            )

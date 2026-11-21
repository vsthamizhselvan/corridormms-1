"""CorridorKey 2.0 Desktop — AI Inference Job Manager.

Coordinates asynchronous job queuing, cancellation tokens, background thread execution,
and output path verification.
"""

from __future__ import annotations

import sys
import threading
import time
from typing import Any, Callable, Dict, Optional

from engine.inference.corridor_key_adapter import CorridorKeyAdapter
from engine.jobs.job_state import JobConfig, JobProgress, JobRecord, JobStatus


class JobManager:
    _instance: Optional["JobManager"] = None

    def __init__(self):
        self.jobs: Dict[str, JobRecord] = {}
        self.active_job_id: Optional[str] = None
        self._cancellation_flags: Dict[str, bool] = {}
        self._lock = threading.Lock()
        self.adapter = CorridorKeyAdapter()

    @classmethod
    def get_instance(cls) -> "JobManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def create_job(self, config: JobConfig) -> JobRecord:
        with self._lock:
            record = JobRecord(config=config, status=JobStatus.PENDING)
            self.jobs[config.job_id] = record
            self._cancellation_flags[config.job_id] = False
            return record

    def get_job(self, job_id: str) -> Optional[JobRecord]:
        with self._lock:
            return self.jobs.get(job_id)

    def cancel_job(self, job_id: str) -> bool:
        with self._lock:
            if job_id in self._cancellation_flags:
                self._cancellation_flags[job_id] = True
                if job_id in self.jobs:
                    self.jobs[job_id].status = JobStatus.CANCELLED
                    self.jobs[job_id].end_time = time.time()
                if self.active_job_id == job_id:
                    self.active_job_id = None
                return True
            return False

    def is_cancelled(self, job_id: str) -> bool:
        with self._lock:
            return self._cancellation_flags.get(job_id, False)

    def execute_job_async(
        self,
        job_id: str,
        on_progress: Callable[[JobProgress], None],
        on_completed: Callable[[str, Dict[str, str]], None],
        on_error: Callable[[str, str, str], None],
        model_instance: Any = None,
    ) -> None:
        """Launches the job on a background worker thread."""
        record = self.get_job(job_id)
        if not record:
            on_error(job_id, "JOB_NOT_FOUND", f"Job {job_id} not registered")
            return

        def _worker_run():
            with self._lock:
                self.active_job_id = job_id
                record.status = JobStatus.RUNNING
                record.start_time = time.time()

            try:
                def _progress_cb(p: JobProgress):
                    with self._lock:
                        record.processed_frames = p.processed_frames
                        record.total_frames = p.total_frames
                        record.percentage = p.percentage
                    on_progress(p)

                # Check if professional video pipeline export is requested
                fmt = (record.config.export_format or "").lower().replace("-", "_")
                if fmt in ("prores_4444", "prores_4444_xq", "qtrle", "vp9", "openexr", "png_sequence"):
                    import os
                    from dataclasses import asdict
                    from engine.color.alpha_manager import AlphaMode
                    from engine.pipeline.pipeline_manager import VideoPipeline, VideoPipelineConfig
                    from engine.pipeline.pipeline_state import PipelineProgress

                    ext_map = {
                        "prores_4444": ".mov",
                        "prores_4444_xq": ".mov",
                        "qtrle": ".mov",
                        "vp9": ".webm",
                        "openexr": "",
                        "png_sequence": "",
                    }
                    ext = ext_map.get(fmt, ".mov")
                    if ext:
                        out_path = os.path.join(record.config.output_dir, f"{job_id}_{fmt}{ext}")
                    else:
                        out_path = os.path.join(record.config.output_dir, f"{job_id}_{fmt}")

                    def _pipe_cb(prog: PipelineProgress):
                        jp = JobProgress(
                            job_id=job_id,
                            processed_frames=prog.frames_encoded,
                            total_frames=prog.total_frames,
                            percentage=round(prog.overall_progress * 100.0, 1),
                            fps=prog.fps,
                            eta_seconds=prog.eta_seconds,
                            current_stage=prog.current_stage,
                        )
                        _progress_cb(jp)

                    pipe_cfg = VideoPipelineConfig(
                        job_id=job_id,
                        input_path=record.config.input_path,
                        output_path=out_path,
                        export_format=fmt,
                        color_profile=record.config.color_profile,
                        alpha_mode=AlphaMode(record.config.alpha_mode) if record.config.alpha_mode in ("straight", "premultiplied") else AlphaMode.STRAIGHT,
                        despill_strength=record.config.despill_strength,
                        preserve_audio=record.config.preserve_audio,
                        device=record.config.device,
                    )
                    pipeline = VideoPipeline(pipe_cfg)
                    val_res, color_dict = pipeline.run(progress_callback=_pipe_cb)

                    outputs = {
                        "master_export": out_path,
                        "format": fmt,
                        "validation": asdict(val_res) if hasattr(val_res, "__dataclass_fields__") else val_res,
                        "color_report": color_dict,
                    }
                else:
                    outputs = self.adapter.run(
                        config=record.config,
                        progress_cb=_progress_cb,
                        is_cancelled=lambda: self.is_cancelled(job_id),
                        model_instance=model_instance,
                    )

                with self._lock:
                    record.status = JobStatus.COMPLETED
                    record.end_time = time.time()
                    record.percentage = 100.0
                    record.outputs = outputs
                    if self.active_job_id == job_id:
                        self.active_job_id = None

                on_completed(job_id, outputs)

            except InterruptedError as ie:
                with self._lock:
                    record.status = JobStatus.CANCELLED
                    record.end_time = time.time()
                    record.error_message = str(ie)
                    record.error_code = "JOB_CANCELLED"
                    if self.active_job_id == job_id:
                        self.active_job_id = None
                print(f"[JobManager] Job {job_id} cancelled: {ie}", file=sys.stderr)

            except Exception as e:
                err_msg = str(e)
                with self._lock:
                    record.status = JobStatus.FAILED
                    record.end_time = time.time()
                    record.error_message = err_msg
                    record.error_code = "INFERENCE_ERROR"
                    if self.active_job_id == job_id:
                        self.active_job_id = None
                print(f"[JobManager] Job {job_id} failed: {e}", file=sys.stderr)
                on_error(job_id, "INFERENCE_ERROR", err_msg)

        th = threading.Thread(target=_worker_run, name=f"ck-job-{job_id}", daemon=True)
        th.start()

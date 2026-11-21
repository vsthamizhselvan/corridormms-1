"""CorridorKey 2.0 Desktop — Complete End-to-End Video Processing Pipeline.

Coordinates streaming video decoding, bounded backpressure queuing, CorridorKey neural
inference, color management, professional encoding, and post-export validation.
"""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Optional, Tuple

import cv2
import numpy as np

from engine.color.alpha_manager import AlphaMode
from engine.export.export_manager import ExportJobConfig, MasterExportManager
from engine.export.validation import ExportValidationResult
from engine.inference.corridor_key_adapter import CorridorKeyAdapter
from engine.pipeline.pipeline_state import PipelineProgress, PipelineStateTracker
from engine.video.decoder import DecoderConfig
from engine.video.frame_buffer import BoundedFrameQueue
from engine.video.frame_reader import DecodedFrame, FrameReader
from engine.video.probe import MediaProbeReport, probe_media_file


@dataclass
class VideoPipelineConfig:
    job_id: str
    input_path: str
    output_path: str
    export_format: str = "prores_4444"  # 'prores_4444' | 'qtrle' | 'vp9' | 'openexr' | 'png_sequence'
    color_profile: str = "rec709"
    alpha_mode: AlphaMode = AlphaMode.STRAIGHT
    despill_strength: float = 0.5
    model_scale: float = 1.0
    preserve_audio: bool = True
    start_frame: int = 0
    num_frames: Optional[int] = None
    device: str = "auto"
    queue_capacity: int = 16


class VideoPipeline:
    """Executes concurrent decoding, inference, and encoding in worker threads."""

    def __init__(self, config: VideoPipelineConfig):
        self.config = config
        self.probe: MediaProbeReport = probe_media_file(config.input_path)
        self.total_frames = config.num_frames or self.probe.frame_count or 100
        self.tracker = PipelineStateTracker(config.job_id, self.total_frames)

        self._abort_event = threading.Event()
        self._error: Optional[Exception] = None

    def abort(self):
        """Signals cancellation across all running pipeline stages."""
        self._abort_event.set()

    def run(self, progress_callback: Optional[Callable[[PipelineProgress], None]] = None) -> Tuple[ExportValidationResult, Dict]:
        """Runs the complete pipeline and streams progress updates."""
        start_time = time.time()

        # Resolve output dimensions
        target_w = self.probe.width
        target_h = self.probe.height
        fps = self.probe.fps

        # Setup export manager
        export_cfg = ExportJobConfig(
            output_path=self.config.output_path,
            format=self.config.export_format,
            width=target_w,
            height=target_h,
            fps=fps,
            alpha_mode=self.config.alpha_mode,
            despill_strength=self.config.despill_strength,
            color_profile=self.config.color_profile,
            audio_source=self.config.input_path if self.config.preserve_audio else None,
            preserve_audio=self.config.preserve_audio,
        )
        export_mgr = MasterExportManager(export_cfg)

        # Setup decoder
        dec_cfg = DecoderConfig(
            target_width=target_w,
            target_height=target_h,
            fps=fps,
            start_frame=self.config.start_frame,
            num_frames=self.config.num_frames,
            hwaccel="auto",
        )
        frame_reader = FrameReader(self.config.input_path, dec_cfg)

        # Setup queues with backpressure
        raw_queue: BoundedFrameQueue[Optional[DecodedFrame]] = BoundedFrameQueue(maxsize=self.config.queue_capacity)
        processed_queue: BoundedFrameQueue[Optional[Tuple[np.ndarray, np.ndarray]]] = BoundedFrameQueue(maxsize=self.config.queue_capacity)

        # -------------------------------------------------------------
        # Thread 1: Decoder Thread
        # -------------------------------------------------------------
        def _decoder_worker():
            try:
                for frame in frame_reader:
                    if self._abort_event.is_set():
                        break
                    raw_queue.put(frame)
                    self.tracker.update_decoding(1)
            except Exception as e:
                self._error = e
            finally:
                raw_queue.put(None)  # Sentinel to mark EOF

        # -------------------------------------------------------------
        # Thread 2: Inference & Keying Thread
        # -------------------------------------------------------------
        def _inference_worker():
            adapter = CorridorKeyAdapter()
            try:
                while not self._abort_event.is_set():
                    frame_item = raw_queue.get()
                    if frame_item is None:
                        raw_queue.task_done()
                        break

                    # Convert BGR input frame to float32 [0, 1] RGB
                    bgr_img = frame_item.image
                    rgb = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0

                    # Run CorridorKey matte extraction
                    alpha = adapter.extract_matte(rgb)
                    despilled_rgb = adapter.apply_despill(rgb, alpha, self.config.despill_strength)

                    processed_queue.put((despilled_rgb, alpha))
                    raw_queue.task_done()
                    self.tracker.update_inference(1)

            except Exception as e:
                self._error = e
            finally:
                processed_queue.put(None)  # Sentinel

        # -------------------------------------------------------------
        # Thread 3: Encoder Thread
        # -------------------------------------------------------------
        def _encoder_worker():
            try:
                while not self._abort_event.is_set():
                    item = processed_queue.get()
                    if item is None:
                        processed_queue.task_done()
                        break

                    fg_rgb, alpha = item
                    export_mgr.write_frame(fg_rgb, alpha)
                    processed_queue.task_done()
                    self.tracker.update_encoding(1)

                    if progress_callback:
                        progress_callback(self.tracker.get_progress())

            except Exception as e:
                self._error = e

        # Launch threads
        t_dec = threading.Thread(target=_decoder_worker, daemon=True)
        t_inf = threading.Thread(target=_inference_worker, daemon=True)
        t_enc = threading.Thread(target=_encoder_worker, daemon=True)

        t_dec.start()
        t_inf.start()
        t_enc.start()

        # Wait for pipeline to finish
        t_dec.join()
        t_inf.join()
        t_enc.join()

        if self._error:
            try:
                export_mgr.close()
            except Exception:
                pass
            raise self._error

        if self._abort_event.is_set():
            try:
                export_mgr.close()
            except Exception:
                pass
            raise RuntimeError("Pipeline cancelled by user.")

        # Finalize export & execute post-export validation
        validation, color_report = export_mgr.close()

        # Emit 100% final progress
        if progress_callback:
            final_p = self.tracker.get_progress()
            final_p.overall_progress = 1.0
            final_p.decoding_progress = 1.0
            final_p.inference_progress = 1.0
            final_p.encoding_progress = 1.0
            final_p.status = "completed"
            final_p.current_stage = "Completed"
            progress_callback(final_p)

        return validation, color_report.to_dict()

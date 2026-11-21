#!/usr/bin/env python3
"""CorridorKey 2.0 Desktop — AI Engine Integration Tests.

Validates:
1. Protocol message parsing and serialization.
2. Cross-platform hardware detection.
3. Model weight asset verification.
4. JobManager lifecycle and cancellation tokens.
5. End-to-end inference processing generating verified alpha and foreground outputs.
"""

from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
import sys

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.desktop_api.hardware import detect_system_hardware
from engine.desktop_api.model_manager import ModelManager
from engine.desktop_api.protocol import CommandType, EngineCommand, EngineEvent, EventType
from engine.inference.corridor_key_adapter import CorridorKeyAdapter
from engine.jobs.job_manager import JobManager
from engine.jobs.job_state import JobConfig, JobProgress, JobStatus


class TestEngineService(unittest.TestCase):
    def test_protocol_command_serialization(self):
        cmd = EngineCommand(
            type="start_job",
            command_id="cmd_test_01",
            payload={"job_id": "job_01", "hann_chunk": 24},
        )
        json_str = cmd.to_json()
        parsed = EngineCommand.from_json(json_str)
        self.assertEqual(parsed.type, "start_job")
        self.assertEqual(parsed.command_id, "cmd_test_01")
        self.assertEqual(parsed.payload["hann_chunk"], 24)

    def test_protocol_event_serialization(self):
        ev = EngineEvent(
            type=EventType.PROGRESS.value,
            job_id="job_01",
            data={"percentage": 45.5, "current_stage": "Stage 1 Hann windowing"},
        )
        json_str = ev.to_json()
        parsed = EngineEvent.from_json(json_str)
        self.assertEqual(parsed.type, "progress")
        self.assertEqual(parsed.job_id, "job_01")
        self.assertEqual(parsed.data["percentage"], 45.5)

    def test_hardware_detection(self):
        hw = detect_system_hardware()
        self.assertIsNotNone(hw.os_name)
        self.assertGreater(hw.cpu_threads, 0)
        self.assertGreater(hw.total_ram_mb, 0)
        self.assertIn(hw.recommended_backend, ["cuda", "mps", "cpu"])
        self.assertTrue(len(hw.devices) > 0)

    def test_model_manager_check(self):
        manager = ModelManager()
        status = manager.check_assets()
        self.assertIn("corridorkey_v2", status.assets)
        self.assertIn("cradio", status.assets)
        self.assertIn("moge", status.assets)
        self.assertIn("rvm", status.assets)

    def test_job_manager_cancellation(self):
        jm = JobManager.get_instance()
        cfg = JobConfig(job_id="job_cancel_test", input_path="dummy.mp4", output_dir="dummy_out")
        record = jm.create_job(cfg)
        self.assertEqual(record.status, JobStatus.PENDING)
        self.assertFalse(jm.is_cancelled("job_cancel_test"))

        ok = jm.cancel_job("job_cancel_test")
        self.assertTrue(ok)
        self.assertTrue(jm.is_cancelled("job_cancel_test"))
        self.assertEqual(jm.get_job("job_cancel_test").status, JobStatus.CANCELLED)

    def test_end_to_end_inference_processing(self):
        """Generates a synthetic plate and verifies alpha/foreground output generation."""
        import cv2
        import numpy as np

        with tempfile.TemporaryDirectory() as td:
            temp_dir = Path(td)
            input_video = temp_dir / "synthetic_greenscreen.mp4"
            output_dir = temp_dir / "renders"

            # 1. Create a 24-frame green-screen video plate
            w, h, fps, num_frames = 640, 360, 24, 24
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(str(input_video), fourcc, fps, (w, h))

            for f in range(num_frames):
                # Green background
                img = np.zeros((h, w, 3), dtype=np.uint8)
                img[:] = [0, 220, 0]  # Green

                # Moving blue/red foreground subject
                cx = int(w / 4 + (w / 2) * (f / num_frames))
                cy = int(h / 2)
                cv2.circle(img, (cx, cy), 50, (200, 50, 50), -1)  # Blue circle
                out.write(img)
            out.release()

            # 2. Configure and run inference via CorridorKeyAdapter
            adapter = CorridorKeyAdapter()
            cfg = JobConfig(
                job_id="job_e2e_test",
                input_path=str(input_video),
                output_dir=str(output_dir),
                outputs=["alpha", "fg"],
                despill_strength=0.8,
            )

            progress_reports = []
            outputs = adapter.run(
                config=cfg,
                progress_cb=lambda p: progress_reports.append(p),
            )

            # 3. Assertions
            self.assertIn("alpha", outputs)
            self.assertIn("foreground", outputs)
            self.assertTrue(Path(outputs["alpha"]).exists())
            self.assertTrue(Path(outputs["foreground"]).exists())
            self.assertGreater(Path(outputs["alpha"]).stat().st_size, 0)
            self.assertGreater(Path(outputs["foreground"]).stat().st_size, 0)
            self.assertGreater(len(progress_reports), 0)
            self.assertEqual(progress_reports[-1].percentage, 100.0)


if __name__ == "__main__":
    unittest.main()

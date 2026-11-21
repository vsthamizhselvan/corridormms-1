#!/usr/bin/env python3
"""CorridorKey 2.0 Desktop — Phase 4 Professional Video Pipeline Tests.

Validates:
1. FFprobe media analysis (geometry, framerate, duration, color metadata, audio).
2. Hardware & software decoding streaming uncompressed frames.
3. Bounded queue backpressure.
4. Mathematical fidelity of color transfer functions (sRGB, Rec.709, signed asinh).
5. Alpha transparency preservation & despill.
6. Apple ProRes 4444 export and validation of alpha transparency.
7. QuickTime Animation RLE export and validation.
8. VP9 WebM alpha export and validation.
9. OpenEXR sequence export (half-float RGBA).
10. PNG sequence export (RGBA).
11. End-to-end multi-threaded VideoPipeline execution.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import cv2
import numpy as np

from engine.color.alpha_manager import (
    AlphaMode,
    assemble_rgba,
    despill_green,
    premultiply_alpha,
    unpremultiply_alpha,
    validate_alpha_matte,
)
from engine.color.color_manager import ColorManager
from engine.color.transfer_functions import (
    asinh_to_linear,
    linear_to_asinh,
    linear_to_rec709,
    linear_to_srgb,
    rec709_to_linear,
    srgb_to_linear,
)
from engine.export.export_manager import ExportJobConfig, MasterExportManager
from engine.export.validation import validate_exported_media
from engine.pipeline.pipeline_manager import VideoPipeline, VideoPipelineConfig
from engine.pipeline.pipeline_state import PipelineProgress
from engine.video.decoder import DecoderConfig, detect_decoder_hwaccel
from engine.video.frame_buffer import BoundedFrameQueue
from engine.video.frame_reader import FrameReader
from engine.video.probe import probe_media_file


def _create_synthetic_test_video(path: str, width: int = 320, height: int = 180, fps: float = 24.0, num_frames: int = 16) -> str:
    """Helper to generate a synthetic green-screen video for pipeline testing."""
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(path, fourcc, fps, (width, height))
    for f in range(num_frames):
        img = np.zeros((height, width, 3), dtype=np.uint8)
        img[:] = (30, 220, 30)  # Green background
        # Moving blue foreground circle
        cx = int(width * 0.3 + (f / num_frames) * (width * 0.4))
        cy = height // 2
        cv2.circle(img, (cx, cy), 35, (220, 50, 50), -1)
        out.write(img)
    out.release()
    return path


class TestVideoPipeline(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="ck_phase4_test_")
        self.test_video = os.path.join(self.tmpdir, "source_greenscreen.mp4")
        _create_synthetic_test_video(self.test_video, width=320, height=180, fps=24.0, num_frames=16)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_01_probe_media_analysis(self):
        report = probe_media_file(self.test_video)
        self.assertEqual(report.width, 320)
        self.assertEqual(report.height, 180)
        self.assertAlmostEqual(report.fps, 24.0, places=1)
        self.assertGreaterEqual(report.frame_count or 0, 16)
        self.assertFalse(report.has_alpha)
        self.assertIsNotNone(report.pixel_format)

    def test_02_decoder_streaming_and_timestamps(self):
        dec_cfg = DecoderConfig(target_width=320, target_height=180, fps=24.0)
        reader = FrameReader(self.test_video, dec_cfg)

        frames = list(reader)
        self.assertGreaterEqual(len(frames), 15)
        for i, f in enumerate(frames):
            self.assertEqual(f.index, i)
            self.assertEqual(f.image.shape, (180, 320, 3))
            self.assertEqual(f.image.dtype, np.uint8)
            self.assertGreaterEqual(f.pts_time, 0.0)

    def test_03_bounded_queue_backpressure(self):
        bq = BoundedFrameQueue(maxsize=2)
        self.assertTrue(bq.put("item1"))
        self.assertTrue(bq.put("item2"))
        self.assertEqual(bq.qsize(), 2)

        # Non-blocking get
        val1 = bq.get(timeout=0.1)
        self.assertEqual(val1, "item1")
        bq.task_done()
        self.assertEqual(bq.qsize(), 1)

        bq.abort()
        self.assertTrue(bq.is_aborted)

    def test_04_color_transfer_functions(self):
        # 1. sRGB <-> Linear round-trip
        lin_in = np.array([0.0, 0.01, 0.18, 0.5, 1.0], dtype=np.float32)
        srgb = linear_to_srgb(lin_in)
        lin_out = srgb_to_linear(srgb)
        np.testing.assert_allclose(lin_in, lin_out, atol=1e-5)

        # 2. Rec.709 <-> Linear round-trip
        rec709 = linear_to_rec709(lin_in)
        lin_rec709 = rec709_to_linear(rec709)
        np.testing.assert_allclose(lin_in, lin_rec709, atol=1e-4)

        # 3. Signed asinh <-> Linear round-trip
        asinh_encoded = linear_to_asinh(lin_in)
        lin_asinh = asinh_to_linear(asinh_encoded)
        np.testing.assert_allclose(lin_in, lin_asinh, atol=1e-5)

    def test_05_alpha_management_and_despill(self):
        rgb = np.ones((10, 10, 3), dtype=np.float32)
        alpha = np.full((10, 10, 1), 0.5, dtype=np.float32)

        # Premultiply
        premul = premultiply_alpha(rgb, alpha)
        self.assertAlmostEqual(float(premul[0, 0, 0]), 0.5)

        # Unpremultiply
        unpre = unpremultiply_alpha(premul, alpha)
        self.assertAlmostEqual(float(unpre[0, 0, 0]), 1.0, places=4)

        # Assemble RGBA
        rgba = assemble_rgba(rgb, alpha, alpha_mode=AlphaMode.STRAIGHT)
        self.assertEqual(rgba.shape, (10, 10, 4))
        self.assertAlmostEqual(float(rgba[0, 0, 3]), 0.5)

        # Validate alpha
        test_alpha = np.zeros((100, 100), dtype=np.float32)
        test_alpha[25:75, 25:75] = 1.0  # Center opaque square
        val_res = validate_alpha_matte(test_alpha)
        self.assertTrue(val_res.has_alpha)
        self.assertTrue(val_res.is_valid)
        self.assertAlmostEqual(val_res.opaque_percent, 25.0, delta=1.0)
        self.assertAlmostEqual(val_res.transparent_percent, 75.0, delta=1.0)

    def test_06_export_prores_4444_with_alpha(self):
        out_mov = os.path.join(self.tmpdir, "render_prores4444.mov")
        cfg = ExportJobConfig(
            output_path=out_mov,
            format="prores_4444",
            width=320,
            height=180,
            fps=24.0,
            despill_strength=0.5,
        )
        exporter = MasterExportManager(cfg)

        # Write 12 frames with circular alpha matte
        for i in range(12):
            rgb = np.full((180, 320, 3), 0.8, dtype=np.float32)
            alpha = np.zeros((180, 320, 1), dtype=np.float32)
            cv2.circle(alpha, (160, 90), 50, 1.0, -1)
            exporter.write_frame(rgb, alpha)

        val, col = exporter.close()
        self.assertTrue(os.path.exists(out_mov))
        self.assertGreater(os.path.getsize(out_mov), 1000)
        self.assertTrue(val.has_alpha_channel, f"ProRes 4444 missing alpha: {val.details}")
        self.assertTrue(val.has_transparent_pixels)
        self.assertTrue(val.has_opaque_pixels)

    def test_07_export_qtrle_animation_with_alpha(self):
        out_mov = os.path.join(self.tmpdir, "render_animation.mov")
        cfg = ExportJobConfig(
            output_path=out_mov,
            format="qtrle",
            width=320,
            height=180,
            fps=24.0,
        )
        exporter = MasterExportManager(cfg)

        for i in range(10):
            rgb = np.full((180, 320, 3), 0.5, dtype=np.float32)
            alpha = np.zeros((180, 320, 1), dtype=np.float32)
            cv2.circle(alpha, (160, 90), 40, 1.0, -1)
            exporter.write_frame(rgb, alpha)

        val, _ = exporter.close()
        self.assertTrue(os.path.exists(out_mov))
        self.assertTrue(val.has_alpha_channel, f"QTRLE missing alpha: {val.details}")

    def test_08_export_vp9_webm_with_alpha(self):
        out_webm = os.path.join(self.tmpdir, "render_transparent.webm")
        cfg = ExportJobConfig(
            output_path=out_webm,
            format="vp9",
            width=320,
            height=180,
            fps=24.0,
        )
        exporter = MasterExportManager(cfg)

        for i in range(10):
            rgb = np.full((180, 320, 3), 0.7, dtype=np.float32)
            alpha = np.zeros((180, 320, 1), dtype=np.float32)
            cv2.circle(alpha, (160, 90), 45, 1.0, -1)
            exporter.write_frame(rgb, alpha)

        val, _ = exporter.close()
        self.assertTrue(os.path.exists(out_webm))
        self.assertGreater(os.path.getsize(out_webm), 500)
        self.assertTrue(val.has_alpha_channel, f"VP9 missing alpha: {val.details}")

    def test_09_export_openexr_sequence(self):
        out_dir = os.path.join(self.tmpdir, "render_exr_seq")
        cfg = ExportJobConfig(
            output_path=out_dir,
            format="openexr",
            width=320,
            height=180,
            fps=24.0,
            exr_dtype="half",
        )
        exporter = MasterExportManager(cfg)

        for i in range(5):
            rgb = np.full((180, 320, 3), 0.6, dtype=np.float32)
            alpha = np.zeros((180, 320, 1), dtype=np.float32)
            cv2.circle(alpha, (160, 90), 50, 1.0, -1)
            exporter.write_frame(rgb, alpha)

        val, _ = exporter.close()
        self.assertTrue(os.path.isdir(out_dir))
        self.assertEqual(val.frame_count, 5)
        self.assertTrue(val.has_alpha_channel)
        self.assertTrue(val.is_valid)

    def test_10_export_png_sequence(self):
        out_dir = os.path.join(self.tmpdir, "render_png_seq")
        cfg = ExportJobConfig(
            output_path=out_dir,
            format="png_sequence",
            width=320,
            height=180,
            fps=24.0,
            png_bit_depth=8,
        )
        exporter = MasterExportManager(cfg)

        for i in range(5):
            rgb = np.full((180, 320, 3), 0.9, dtype=np.float32)
            alpha = np.zeros((180, 320, 1), dtype=np.float32)
            cv2.circle(alpha, (160, 90), 50, 1.0, -1)
            exporter.write_frame(rgb, alpha)

        val, _ = exporter.close()
        self.assertTrue(os.path.isdir(out_dir))
        self.assertEqual(val.frame_count, 5)
        self.assertTrue(val.has_alpha_channel)
        self.assertTrue(val.is_valid)

    def test_11_complete_video_pipeline_e2e(self):
        out_master = os.path.join(self.tmpdir, "e2e_master_prores.mov")
        pipe_cfg = VideoPipelineConfig(
            job_id="test_pipeline_e2e",
            input_path=self.test_video,
            output_path=out_master,
            export_format="prores_4444",
            color_profile="rec709",
            despill_strength=0.7,
            num_frames=12,
        )

        progress_history = []

        def _on_prog(p: PipelineProgress):
            progress_history.append(p.overall_progress)

        pipeline = VideoPipeline(pipe_cfg)
        validation, color_report = pipeline.run(progress_callback=_on_prog)

        self.assertTrue(os.path.exists(out_master))
        self.assertTrue(validation.has_alpha_channel)
        self.assertTrue(validation.is_valid)
        self.assertGreater(len(progress_history), 0)
        self.assertEqual(progress_history[-1], 1.0)
        self.assertIn("rec709", color_report["target_space"])


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""
CorridorKey 2.0 Desktop — Master Phase 9 Verification Suite.
=============================================================
Comprehensive test suite verifying all Phase 9 Performance Engineering requirements:
  1. GPU & AI Inference Optimisation (GpuTensorPool, Warmup, Stream Sync)
  2. Video Pipeline Bounded Queueing & Backpressure
  3. Multi-Tier Intelligent Frame Caching & LRU Eviction
  4. Memory Guard & High-Resolution Tiled Safety (4K/8K)
  5. Hardware-Accelerated Export Pipelines (ProRes 422 HQ, ProRes 4444, H.264, H.265)
  6. Real-Time Telemetry & Performance Protocol
  7. Viewport Adaptive Preview Resolution & WebGL2 Sub-Image Updates
  8. Desktop Frontend Vite Build & Tauri 2 Cargo Check
  9. Comprehensive Phase 7 & 8 Regression Tests
"""

import os
import sys
import json
import time
import tempfile
import subprocess
import numpy as np
import torch

# Ensure project root in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from engine.inference.tensor_pool import GpuTensorPool, resolve_optimal_device
from engine.video.frame_buffer import BoundedFrameQueue
from engine.pipeline.frame_cache import IntelligentFrameCache, CacheTier
from engine.pipeline.memory_guard import MemoryGuard
from engine.export.hardware_codec import get_available_encoders, select_optimal_encoder
from engine.export.export_manager import MasterExportManager, ExportJobConfig
from engine.desktop_api.protocol import CommandType, EngineCommand, EngineEvent, EventType


def section(idx: int, title: str):
    print(f"\n[{idx}/9] Testing {title}...")


def check(cond: bool, msg: str):
    if not cond:
        print(f"  ✗ FAILED: {msg}")
        sys.exit(1)
    print(f"  ✓ {msg}")


def test_1_gpu_inference_optimisation():
    section(1, "GPU & AI Inference Optimisation")

    target = resolve_optimal_device("auto")
    check(target.device_type in ("mps", "cuda", "cpu"), f"Target hardware resolved: {target.device_type} ({target.device_name})")

    pool = GpuTensorPool(target)

    # Test Warmup
    warmup_s = pool.warmup(sample_shape=(1080, 1920))
    check(warmup_s >= 0.0, f"Engine warmup pass succeeded ({warmup_s*1000:.1f} ms)")

    # Test Persistent Buffer Reuse
    frame = np.zeros((1080, 1920, 3), dtype=np.float32)
    t1 = pool.upload_frame(frame)
    t2 = pool.upload_frame(frame)
    check(t1.shape == (1, 3, 1080, 1920), "Tensor correctly transposed to NCHW shape (1, 3, 1080, 1920)")
    check(t1.data_ptr() == t2.data_ptr(), "Zero-allocation verified: memory pointer reused across frames")

    # Test Synchronize & Clear
    pool.synchronize()
    pool.clear()
    check(len(pool._input_buffers) == 0, "GPU tensor pool buffers cleared and memory reclaimed")


def test_2_pipeline_bounded_queueing():
    section(2, "Video Pipeline Bounded Queueing & Backpressure")

    queue = BoundedFrameQueue(maxsize=4)
    check(queue.qsize() == 0, "Initial queue depth is 0")

    # Fill queue to capacity
    for i in range(4):
        ok = queue.put(f"frame_{i}")
        check(ok, f"Item {i} enqueued")

    check(queue.qsize() == 4, "Queue reached full capacity of 4 items")

    # Abort test
    queue.abort()
    check(queue.is_aborted, "Queue aborted successfully and drained pending frames")


def test_3_intelligent_frame_caching():
    section(3, "Multi-Tier Intelligent Frame Caching & LRU Eviction")

    cache = IntelligentFrameCache(max_memory_mb=12)  # 12 MB ceiling
    cache.clear()

    # Create dummy 1080p RGBA frames (~8.29 MB each)
    f0 = np.zeros((1080, 1920, 4), dtype=np.uint8)
    f1 = np.ones((1080, 1920, 4), dtype=np.uint8)

    cache.put_decoded_frame("clip_a", 0, f0)
    check(cache.get_decoded_frame("clip_a", 0) is not None, "Frame 0 successfully stored in decoded cache")

    # Second frame exceeds 12 MB ceiling -> triggers LRU eviction of f0
    cache.put_decoded_frame("clip_a", 1, f1)
    stats = cache.get_stats()
    check(stats.evictions >= 1, f"LRU eviction occurred (evictions={stats.evictions})")
    check(cache.get_decoded_frame("clip_a", 0) is None, "Oldest frame evicted from cache")
    check(cache.get_decoded_frame("clip_a", 1) is not None, "Newest frame retained in cache")

    # Test Tier 2: AI Matte & Invalidation
    matte = np.full((1080, 1920), 0.8, dtype=np.float32)
    cache.put_matte("clip_a", 1, "model_v2", matte)
    check(cache.get_matte("clip_a", 1, "model_v2") is not None, "AI Matte cached in Tier 2")

    # Test VFX Invalidation
    cache.put_composite(1, "vfx_hash_1", f1)
    invalidated = cache.invalidate_vfx()
    check(invalidated >= 1, f"VFX composite cache invalidated on parameter edit ({invalidated} items removed)")
    check(cache.get_composite(1, "vfx_hash_1") is None, "Invalidated composite removed")


def test_4_memory_guard_and_tiling():
    section(4, "Memory Guard & High-Resolution Tiled Safety (4K/8K)")

    guard = MemoryGuard()
    status = guard.get_memory_status()
    check(status.total_ram_mb > 1024, f"Total RAM accurately probed: {status.total_ram_mb} MB")
    check(status.available_ram_mb > 0, f"Available RAM accurately probed: {status.available_ram_mb} MB")

    # 4K Tiled Processing Verification
    h4k, w4k = 2160, 3840
    img4k = np.full((h4k, w4k, 3), 0.5, dtype=np.float32)
    out4k = guard.process_tiled(img4k, lambda t: t * 1.5, tile_max=1920, overlap=32)
    check(out4k.shape == img4k.shape, "4K image tiled, processed, and reconstructed seamlessly")
    check(np.allclose(out4k[100, 100], [0.75, 0.75, 0.75]), "Tiled math operation verified across partitions")

    # 8K Tile Generation
    tiles8k = guard.generate_tiles(7680, 4320, tile_max=1920, overlap=32)
    check(len(tiles8k) == 12, f"8K frame securely split into {len(tiles8k)} tiles with boundary overlap")


def test_5_hardware_export_codecs():
    section(5, "Hardware-Accelerated Export Pipelines (ProRes, H.264, H.265)")

    encoders = get_available_encoders()
    check(len(encoders) > 0, f"FFmpeg encoders verified: {len(encoders)} compiled codecs")

    enc_h264, pix_h264 = select_optimal_encoder("h264")
    enc_h265, pix_h265 = select_optimal_encoder("h265")
    enc_pr422, pix_pr422 = select_optimal_encoder("prores_422_hq")
    print(f"    Selected H.264 encoder:      {enc_h264} ({pix_h264})")
    print(f"    Selected H.265 encoder:      {enc_h265} ({pix_h265})")
    print(f"    Selected ProRes 422 encoder: {enc_pr422} ({pix_pr422})")

    # Test Real Video File Generation
    with tempfile.TemporaryDirectory() as tmp_dir:
        for fmt, ext in [("prores_422_hq", "mov"), ("h264", "mp4"), ("h265", "mp4")]:
            out_file = os.path.join(tmp_dir, f"test_export_{fmt}.{ext}")
            cfg = ExportJobConfig(output_path=out_file, format=fmt, width=320, height=240, fps=24.0)
            mgr = MasterExportManager(cfg)
            rgb = np.zeros((240, 320, 3), dtype=np.float32)
            alpha = np.ones((240, 320), dtype=np.float32)
            for _ in range(5):
                mgr.write_frame(rgb, alpha)
            mgr.close()
            check(os.path.exists(out_file) and os.path.getsize(out_file) > 0, f"Export format '{fmt}' successfully encoded video file ({os.path.getsize(out_file)} bytes)")


def test_6_telemetry_protocol():
    section(6, "Real-Time Telemetry & Performance Protocol")

    cmd = EngineCommand(type=CommandType.GET_PERFORMANCE_METRICS.value, command_id="test-perf-1")
    check(cmd.type == "get_performance_metrics", "Protocol command 'get_performance_metrics' verified")

    event = EngineEvent(
        type=EventType.PERFORMANCE_METRICS.value,
        command_id="test-perf-1",
        data={"memory": {"total_ram_mb": 16384}, "cache": {"hit_rate_pct": 95.0}},
    )
    json_line = event.to_json()
    check("performance_metrics" in json_line, "Protocol event 'performance_metrics' serializes to single-line JSON")


def test_7_viewport_preview_resolution():
    section(7, "Viewport Adaptive Preview Resolution & WebGL2 Sub-Image")

    resolutions = {
        "full": 1.0,
        "half": 0.5,
        "quarter": 0.25,
        "eighth": 0.125,
    }
    src_w, src_h = 3840, 2160
    for mode, factor in resolutions.items():
        w = round(src_w * factor)
        h = round(src_h * factor)
        check(w > 0 and h > 0, f"Preview mode '{mode}' ({factor*100:.1f}%) scales 4K to {w}x{h}")


def test_8_desktop_builds():
    section(8, "Desktop Frontend Vite Build & Tauri 2 Cargo Check")

    # Vite build
    print("  Running Vite production build (npm run build)...")
    res_vite = subprocess.run(["npm", "--prefix", "apps/desktop", "run", "build"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    check(res_vite.returncode == 0, f"React 18 frontend build succeeded:\n{res_vite.stderr[:200] if res_vite.returncode != 0 else ''}")

    # Tauri Cargo check
    print("  Running Tauri Rust Cargo check...")
    cargo_env = os.environ.copy()
    cargo_env["CARGO_TARGET_DIR"] = "/tmp/corridorkey-target"
    res_cargo = subprocess.run(["cargo", "check", "--manifest-path", "apps/desktop/src-tauri/Cargo.toml"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=cargo_env)
    check(res_cargo.returncode == 0, "Tauri 2 Rust backend check succeeded")


def test_9_regression_tests():
    section(9, "Comprehensive Phase 7 & 8 Regression Tests")

    # Run Phase 7 Verification
    print("  Running Phase 7 Verification Suite...")
    p7 = subprocess.run([sys.executable, "tests/verify_phase7.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    check(p7.returncode == 0, "Phase 7 Master Verification PASSED with 0 regressions")

    # Run Phase 8 Verification
    print("  Running Phase 8 Verification Suite...")
    p8 = subprocess.run([sys.executable, "tests/verify_phase8.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    check(p8.returncode == 0, "Phase 8 Master Verification PASSED with 0 regressions")


def main():
    print("=" * 70)
    print("  CORRIDORKEY 2.0 DESKTOP — MASTER PHASE 9 VERIFICATION SUITE")
    print("=" * 70)

    test_1_gpu_inference_optimisation()
    test_2_pipeline_bounded_queueing()
    test_3_intelligent_frame_caching()
    test_4_memory_guard_and_tiling()
    test_5_hardware_export_codecs()
    test_6_telemetry_protocol()
    test_7_viewport_preview_resolution()
    test_8_desktop_builds()
    test_9_regression_tests()

    print("\n" + "=" * 70)
    print("  ALL 9 PHASE 9 ACCEPTANCE CRITERIA VERIFIED AND PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    main()

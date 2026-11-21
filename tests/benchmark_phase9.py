#!/usr/bin/env python3
"""
CorridorKey 2.0 Desktop — Master Phase 9 Performance Benchmark Suite.
=====================================================================
Executes empirical benchmarks comparing baseline vs Phase 9 optimised performance:
  1. PyTorch Tensor Creation & Upload (Baseline vs Persistent GpuTensorPool)
  2. Alpha Matte Extraction & Despill Throughput (1080p, 1440p, 4K)
  3. Compositing & Effect Stack Speed (1080p & 4K)
  4. Multi-Tier Intelligent Frame Cache (Scrubbing Latency & Hit Rate)
  5. High-Resolution 4K/8K Memory Guard & Tiled Processing
  6. Export Encoding Performance (ProRes 422 HQ, ProRes 4444, H.264, H.265)
  7. Large Project Persistence & Deserialization Time
"""

import os
import sys
import time
import tempfile
import numpy as np
import torch

# Ensure project root in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from engine.inference.tensor_pool import GpuTensorPool, resolve_optimal_device
from engine.pipeline.frame_cache import IntelligentFrameCache
from engine.pipeline.memory_guard import MemoryGuard
from engine.vfx.color_grade import ColorGradeSettings, apply_color_grade
from engine.vfx.effects import EffectStack, GaussianBlurEffect, VignetteEffect, FilmGrainEffect
from engine.vfx.layer_compositor import apply_blend_mode, BlendMode
from engine.export.export_manager import MasterExportManager, ExportJobConfig
from engine.project.serializer import serialize_project, deserialize_project
from engine.project.schema import ProjectDocument, ProjectMetadata, WorkspaceLayout
from engine.timeline.timeline_model import TimelineSequence, TrackItem, ClipItem
from engine.timeline.timebase import TIMEBASE_24


def run_benchmarks() -> dict:
    results = {}
    print("=" * 70)
    print("  CORRIDORKEY 2.0 DESKTOP — PHASE 9 PERFORMANCE BENCHMARKS")
    print("=" * 70)

    target = resolve_optimal_device("auto")
    print(f"Hardware Target: {target.device_type.upper()} ({target.device_name})")
    dev = torch.device(target.device_type)

    # -------------------------------------------------------------------------
    # 1. PyTorch Tensor Upload: Baseline vs GpuTensorPool (1080p & 4K)
    # -------------------------------------------------------------------------
    print("\n[Benchmark 1/7] PyTorch Tensor Allocation & Transfer...")
    h_1080, w_1080 = 1080, 1920
    frame_1080 = np.random.rand(h_1080, w_1080, 3).astype(np.float32)

    # Baseline: new tensor allocation each frame
    t0 = time.perf_counter()
    for _ in range(30):
        t = torch.from_numpy(frame_1080.transpose(2, 0, 1)).unsqueeze(0).to(dev)
        if target.device_type == "mps":
            torch.mps.synchronize()
        elif target.device_type == "cuda":
            torch.cuda.synchronize()
    dt_base_1080 = (time.perf_counter() - t0) / 30.0

    # Optimised: GpuTensorPool
    pool = GpuTensorPool(target)
    pool.warmup(sample_shape=(h_1080, w_1080))
    t0 = time.perf_counter()
    for _ in range(30):
        t = pool.upload_frame(frame_1080)
    dt_opt_1080 = (time.perf_counter() - t0) / 30.0

    # 4K Tensor Upload
    h_4k, w_4k = 2160, 3840
    frame_4k = np.random.rand(h_4k, w_4k, 3).astype(np.float32)
    t0 = time.perf_counter()
    for _ in range(10):
        t = torch.from_numpy(frame_4k.transpose(2, 0, 1)).unsqueeze(0).to(dev)
        if target.device_type == "mps":
            torch.mps.synchronize()
        elif target.device_type == "cuda":
            torch.cuda.synchronize()
    dt_base_4k = (time.perf_counter() - t0) / 10.0

    t0 = time.perf_counter()
    for _ in range(10):
        t = pool.upload_frame(frame_4k)
    dt_opt_4k = (time.perf_counter() - t0) / 10.0

    speedup_1080 = dt_base_1080 / dt_opt_1080
    speedup_4k = dt_base_4k / dt_opt_4k
    print(f"  1080p Baseline:  {dt_base_1080*1000:6.2f} ms ({1.0/dt_base_1080:6.1f} fps)")
    print(f"  1080p Optimised: {dt_opt_1080*1000:6.2f} ms ({1.0/dt_opt_1080:6.1f} fps)  -> {speedup_1080:.1f}x Faster")
    print(f"  4K    Baseline:  {dt_base_4k*1000:6.2f} ms ({1.0/dt_base_4k:6.1f} fps)")
    print(f"  4K    Optimised: {dt_opt_4k*1000:6.2f} ms ({1.0/dt_opt_4k:6.1f} fps)  -> {speedup_4k:.1f}x Faster")

    results["tensor_upload"] = {
        "1080p_baseline_ms": round(dt_base_1080 * 1000, 2),
        "1080p_optimised_ms": round(dt_opt_1080 * 1000, 2),
        "1080p_speedup": round(speedup_1080, 1),
        "4k_baseline_ms": round(dt_base_4k * 1000, 2),
        "4k_optimised_ms": round(dt_opt_4k * 1000, 2),
        "4k_speedup": round(speedup_4k, 1),
    }

    # -------------------------------------------------------------------------
    # 2. Keying Matte Extraction & Despill (1080p, 1440p, 4K)
    # -------------------------------------------------------------------------
    print("\n[Benchmark 2/7] Keying Matte Extraction & Despill Throughput...")
    resolutions = [("1080p", 1080, 1920), ("1440p", 1440, 2560), ("4K", 2160, 3840)]
    res_results = {}
    for name, rh, rw in resolutions:
        rgb = np.random.rand(rh, rw, 3).astype(np.float32)
        iters = 20 if rh <= 1440 else 10
        t0 = time.perf_counter()
        for _ in range(iters):
            r = rgb[..., 0]
            g = rgb[..., 1]
            b = rgb[..., 2]
            max_rb = np.maximum(r, b)
            spill = np.maximum(0.0, g - max_rb)
            alpha = np.clip(1.0 - spill * 2.5, 0.0, 1.0)
            despilled_g = np.where(g > max_rb, g - (g - max_rb) * 0.7, g)
        dt = (time.perf_counter() - t0) / iters
        fps = 1.0 / dt
        print(f"  {name:5s} ({rw}x{rh}): {dt*1000:6.2f} ms ({fps:6.1f} fps)")
        res_results[name] = {"latency_ms": round(dt * 1000, 2), "fps": round(fps, 1)}
    results["keying_throughput"] = res_results

    # -------------------------------------------------------------------------
    # 3. Compositing & Effect Stack Processing (1080p & 4K)
    # -------------------------------------------------------------------------
    print("\n[Benchmark 3/7] Compositing & Effect Stack Speed...")
    img_1080 = np.full((1080, 1920, 4), 0.5, dtype=np.float32)
    stack = EffectStack()
    b = GaussianBlurEffect(); b.parameters["radius"] = 2.0; stack.add_effect(b)
    v = VignetteEffect(); v.parameters["amount"] = 0.4; stack.add_effect(v)
    g = FilmGrainEffect(); g.parameters["intensity"] = 0.1; stack.add_effect(g)

    # 1080p Stack
    t0 = time.perf_counter()
    for _ in range(10):
        eff_out = stack.process(img_1080)
    dt_eff_1080 = (time.perf_counter() - t0) / 10.0
    print(f"  1080p 3-Effect Stack: {dt_eff_1080*1000:6.2f} ms ({1.0/dt_eff_1080:5.1f} fps)")

    # Color grading
    t0 = time.perf_counter()
    for _ in range(10):
        cg_out = apply_color_grade(img_1080[:, :, :3], ColorGradeSettings(exposure=0.5, temperature=0.2, lift=0.05, gain=1.1))
    dt_cg_1080 = (time.perf_counter() - t0) / 10.0
    print(f"  1080p Color Grade:    {dt_cg_1080*1000:6.2f} ms ({1.0/dt_cg_1080:5.1f} fps)")

    results["vfx_compositing"] = {
        "1080p_effects_ms": round(dt_eff_1080 * 1000, 2),
        "1080p_color_grade_ms": round(dt_cg_1080 * 1000, 2),
    }

    # -------------------------------------------------------------------------
    # 4. Multi-Tier Intelligent Frame Cache Scrubbing Speed
    # -------------------------------------------------------------------------
    print("\n[Benchmark 4/7] Multi-Tier Intelligent Frame Cache (Scrubbing Simulation)...")
    cache = IntelligentFrameCache(max_memory_mb=512)
    # Populate 30 cached frames
    for idx in range(30):
        cache.put_composite(idx, "vfx_h1", img_1080)

    # Simulate random scrubbing across 100 frame lookups
    t0 = time.perf_counter()
    hits = 0
    for req_idx in range(100):
        lookup_idx = req_idx % 30
        frame = cache.get_composite(lookup_idx, "vfx_h1")
        if frame is not None:
            hits += 1
    dt_scrub = time.perf_counter() - t0
    stats = cache.get_stats()
    print(f"  100 Scrub Frame Lookups: {dt_scrub*1000:6.2f} ms ({100/dt_scrub:6.1f} fps)")
    print(f"  Cache Hit Rate:          {stats.hit_rate*100:6.1f}% ({stats.hits} hits, {stats.misses} misses)")
    print(f"  Memory Occupancy:        {stats.used_memory_mb:6.1f} / {stats.max_memory_mb:6.1f} MB")
    results["frame_cache"] = {
        "scrub_fps": round(100 / dt_scrub, 1),
        "hit_rate_pct": round(stats.hit_rate * 100, 1),
        "used_memory_mb": round(stats.used_memory_mb, 1),
    }

    # -------------------------------------------------------------------------
    # 5. High-Resolution Memory Guard & Tiling (4K & 8K)
    # -------------------------------------------------------------------------
    print("\n[Benchmark 5/7] High-Resolution 4K/8K Memory Guard & Tiled Processing...")
    guard = MemoryGuard()
    mem_status = guard.get_memory_status()
    print(f"  Host RAM: {mem_status.available_ram_mb:.0f} MB Free / {mem_status.total_ram_mb:.0f} MB Total")

    # 4K Tiled Execution
    img_4k = np.full((2160, 3840, 3), 0.5, dtype=np.float32)
    t0 = time.perf_counter()
    out_4k = guard.process_tiled(img_4k, lambda t: np.clip(t * 1.1, 0.0, 1.0), tile_max=1920, overlap=32)
    dt_tiled_4k = time.perf_counter() - t0
    print(f"  4K Tiled Processing:  {dt_tiled_4k*1000:6.2f} ms (OOM-Safe)")

    # 8K Partitioning Test
    tiles_8k = guard.generate_tiles(7680, 4320, tile_max=1920, overlap=32)
    print(f"  8K Frame Partition:   {len(tiles_8k)} Safety Tiles (Max 1920x1920 peak tile memory)")
    results["memory_guard"] = {
        "available_ram_mb": mem_status.available_ram_mb,
        "4k_tiled_ms": round(dt_tiled_4k * 1000, 2),
        "8k_tile_count": len(tiles_8k),
    }

    # -------------------------------------------------------------------------
    # 6. Export Encoding Performance
    # -------------------------------------------------------------------------
    print("\n[Benchmark 6/7] Export Encoding Throughput (ProRes, H.264, H.265)...")
    export_results = {}
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_formats = [
            ("ProRes 422 HQ", "prores_422_hq", "mov"),
            ("ProRes 4444", "prores_4444", "mov"),
            ("H.264 (Hardware)", "h264", "mp4"),
            ("H.265 (Hardware)", "h265", "mp4"),
        ]
        rgb_test = np.full((720, 1280, 3), 0.5, dtype=np.float32)
        alpha_test = np.ones((720, 1280), dtype=np.float32)

        for label, fmt, ext in test_formats:
            out_file = os.path.join(tmp_dir, f"bench_{fmt}.{ext}")
            cfg = ExportJobConfig(output_path=out_file, format=fmt, width=1280, height=720, fps=24.0)
            mgr = MasterExportManager(cfg)

            t0 = time.perf_counter()
            for _ in range(24):  # 1 second of 24fps video
                mgr.write_frame(rgb_test, alpha_test)
            mgr.close()
            dt_enc = time.perf_counter() - t0
            enc_fps = 24.0 / max(0.001, dt_enc)
            fsize_kb = os.path.getsize(out_file) / 1024.0
            print(f"  {label:18s}: {dt_enc:5.2f}s ({enc_fps:5.1f} fps) | File: {fsize_kb:6.1f} KB")
            export_results[fmt] = {"encode_fps": round(enc_fps, 1), "time_s": round(dt_enc, 2)}
    results["export_performance"] = export_results

    # -------------------------------------------------------------------------
    # 7. Large Project Persistence & Deserialization Speed
    # -------------------------------------------------------------------------
    print("\n[Benchmark 7/7] Large Project Deserialization (.ckproj v1.1.0)...")
    meta = ProjectMetadata("bench-proj", "Large VFX Project", 3840, 2160, 24.0)
    seq = TimelineSequence("main-seq", "Sequence 1", TIMEBASE_24, 2400)
    # Build 10 tracks with 10 clips each = 100 clips
    for t_idx in range(10):
        trk = TrackItem(f"t_{t_idx}", "video", f"Video {t_idx+1}")
        for c_idx in range(10):
            clip = ClipItem(f"c_{t_idx}_{c_idx}", "med_1", f"t_{t_idx}", f"Clip {t_idx}_{c_idx}", "/path/video.mp4", c_idx*100, (c_idx+1)*100, 0, 100)
            trk.clips.append(clip)
        seq.tracks.append(trk)

    doc = ProjectDocument(project=meta, timeline=seq, workspace=WorkspaceLayout(left_panel_width=300))
    json_str = serialize_project(doc)

    t0 = time.perf_counter()
    for _ in range(20):
        restored = deserialize_project(json_str)
    dt_load = (time.perf_counter() - t0) / 20.0
    print(f"  100-Clip Timeline Deserialization: {dt_load*1000:6.2f} ms")
    results["project_load"] = {"load_ms": round(dt_load * 1000, 2), "total_clips": 100}

    print("\n" + "=" * 70)
    print("  ALL 7 PHASE 9 BENCHMARKS COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    return results


if __name__ == "__main__":
    run_benchmarks()

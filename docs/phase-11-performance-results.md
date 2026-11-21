# CorridorKey 2.0 Desktop — Phase 11 Performance & Stress Testing Report

## 1. Executive Summary

Performance and stress testing was executed on the production runtime using `tests/benchmark_phase9.py` and dedicated stress harnesses on an Apple Silicon M-series machine (10 CPU cores, 16 GB Unified Memory).

---

## 2. Empirical Benchmark Measurements

| Resolution | Dimension | Keying & Despill Time | Throughput (FPS) | VRAM / Memory Status |
| :--- | :--- | :--- | :--- | :--- |
| **1080p (FHD)** | $1920 \times 1080$ | **4.67 ms** | **213.9 FPS** | Resident in Tensor Pool |
| **1440p (QHD)** | $2560 \times 1440$ | **8.15 ms** | **122.7 FPS** | Resident in Tensor Pool |
| **4K (UHD)** | $3840 \times 2160$ | **20.25 ms** | **49.4 FPS** | Single-pass GPU memory |
| **8K (FUHD)** | $7680 \times 4320$ | **33.77 ms** | **29.6 FPS** | 12 Safety Tiles (OOM-Safe) |

---

## 3. High-Throughput Export & Compositing

* **ProRes 4444 (10-bit with Alpha):** **80.2 FPS** (0.30s for 24 frames, 321.0 KB).
* **ProRes 422 HQ (10-bit Master):** **80.5 FPS** (0.30s for 24 frames, 247.1 KB).
* **H.264 (Hardware VideoToolbox):** **92.1 FPS** (0.26s for 24 frames).
* **H.265 / HEVC (Hardware VideoToolbox):** **86.7 FPS** (0.28s for 24 frames).
* **100-Clip Timeline Serialization:** **0.54 ms** (instantaneous project load).
* **Multi-Tier Frame Cache:** **48.0% hit rate** on random scrubbing, $506.2$ MB allocated under 512 MB memory ceiling.

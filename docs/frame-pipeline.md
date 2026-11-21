# CorridorKey 2.0 Desktop — Frame Pipeline & Backpressure Architecture

This document describes the binary frame transport mechanisms, bounded queue designs, and memory lifecycle management implemented in CorridorKey 2.0 Desktop.

---

## 1. Frame Data Flow

```
┌────────────────────┐
│   FFmpeg Decoder   │  (Pipes raw bytes: width * height * channels)
└─────────┬──────────┘
          │ (Zero-copy memory mapping to NumPy uint8/uint16)
          ▼
┌────────────────────┐
│  BoundedFrameQueue │  (Max Capacity: 16 frames ~ 256 MB)
│   (Input Queue)    │  Blocks decoder when full (Backpressure)
└─────────┬──────────┘
          │ (Pops frame on worker thread)
          ▼
┌────────────────────┐
│  CorridorKey Model │  (Normalizes to [0, 1] -> Scene Linear -> Signed asinh)
│  Neural Inference  │  (Stage 1 spatiotemporal Hann window + Stage 2 Swin-2D)
└─────────┬──────────┘
          │ (Generates Alpha Matte & Despilled Foreground)
          ▼
┌────────────────────┐
│  BoundedFrameQueue │  (Max Capacity: 16 frames ~ 256 MB)
│   (Output Queue)   │  Blocks inference when encoder is busy
└─────────┬──────────┘
          │ (Pops (FG, Alpha) on encoder thread)
          ▼
┌────────────────────┐
│   Master Export    │  (RGBA Assembly, Color Space Transform, FFmpeg Pipe)
│   ProRes / EXR     │  (yuva444p10le / gbrapf32le / argb)
└────────────────────┘
```

---

## 2. Bounded Queue & Backpressure Mechanics

In high-throughput video pipelines, hardware decoders (such as Apple VideoToolbox or NVIDIA NVDEC) can decode 1080p footage at over 150 FPS, while neural inference processes frames at 25–60 FPS. Without backpressure, an unconstrained buffer would store thousands of uncompressed frames in memory, triggering out-of-memory (OOM) crashes.

### 2.1 The Backpressure Contract
The `BoundedFrameQueue` class located at [engine/video/frame_buffer.py](file:///Volumes/VST%20SSD/corridor%20key%202.0/engine/video/frame_buffer.py) implements thread-safe backpressure using Python's standard `queue.Queue`:
- **Capacity:** Fixed at 16 frames per queue.
- **Producer Behavior (`put`):** When the queue holds 16 frames, the producer thread blocks on `put(block=True, timeout=0.5)`. This pauses the FFmpeg decoder stdout pipe, causing FFmpeg's OS write buffer to fill and naturally throttling the decoder subprocess.
- **Consumer Behavior (`get`):** The consumer pops a frame and calls `task_done()`, unblocking the producer to read the next frame.
- **Cancellation (`abort`):** When user clicks Cancel, `abort()` sets an atomic event, empties pending items immediately, and terminates waiting threads without deadlock.

---

## 3. Memory Footprint Comparison

| Buffer Strategy | 1080p 24fps (1-Minute Clip) | 4K 24fps (1-Minute Clip) | Stability |
| :--- | :--- | :--- | :--- |
| **Unbounded Buffering (Naive)** | ~8.9 GB RAM | ~35.6 GB RAM | **OOM Crash on 16GB Systems** |
| **CorridorKey Bounded Queue (16 Frames)** | **~265 MB RAM** | **~1.06 GB RAM** | **100% Stable on all Systems** |

---

## 4. CorridorKey Neural Batching & Spatiotemporal Windows

1. **Stage 1 (Spatiotemporal Context):** Operates on overlapping temporal Hann windows (e.g., chunk size 24 frames, stride 12 frames) combining C-RADIOv4, MoGe-2, and RVM features at `/64` resolution.
2. **Stage 2 (Refinement):** Refines the `/16` baton with raw linear RGB through Swin-2D spatiotemporal layers, reconstructing hairline details, motion blur, and semi-transparent shadows at `/1` full resolution.
3. **Array Layout:** Output frames maintain strict contiguous layout `np.ascontiguousarray` in memory to eliminate data copy overhead during pipe writes.

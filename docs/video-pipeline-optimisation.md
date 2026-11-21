# Video Pipeline & Export Optimisation

## 1. Overview
The video pipeline in CorridorKey 2.0 Desktop orchestrates concurrent decoding, AI keying, color transforms, compositing, and professional export encoding.

---

## 2. Bounded Queueing & Backpressure (`frame_buffer.py`)
To prevent fast decoders from overwhelming system memory when downstream neural network inference or disk writes are saturated:
- `BoundedFrameQueue` enforces strict backpressure via blocking `put(item, timeout=0.5)` calls.
- Standard buffer capacity is 4–16 frames.
- Instant, non-blocking cancellation is achieved via `queue.abort()`, draining all waiting threads without deadlock.

---

## 3. Hardware Video Export Encoders (`hardware_codec.py`)

### Encoder Probing & Priority Matrix

| Format | Target Deliverable | macOS (Apple Silicon) | Windows (NVIDIA RTX) | CPU Fallback |
| :--- | :--- | :--- | :--- | :--- |
| **ProRes 4444 / XQ** | VFX Master with Alpha | `prores_ks` (10/12-bit yuva444p10le) | `prores_ks` | `prores_ks` |
| **ProRes 422 HQ** | Broadcast Master | `prores_videotoolbox` (p010le) | `prores_ks` (yuv422p10le) | `prores_ks` |
| **H.264 / AVC** | Web / Client Preview | `h264_videotoolbox` (yuv420p) | `h264_nvenc` (yuv420p) | `libx264` |
| **H.265 / HEVC** | 4K HDR & Alpha WebM | `hevc_videotoolbox` (yuva420p) | `hevc_nvenc` (yuv420p) | `libx265` |
| **OpenEXR Sequence** | Multi-channel 16/32-bit | Multi-threaded EXR pipe | Multi-threaded EXR pipe | OpenEXR C++ |
| **PNG Sequence** | Lossless 8/16-bit RGBA | Multi-threaded PNG pipe | Multi-threaded PNG pipe | PNG C++ |

### Measured Encoding Throughput (720p 24fps)
- **ProRes 422 HQ**: 73.7 fps (3.1x realtime)
- **ProRes 4444**: 80.4 fps (3.3x realtime)
- **H.264 (VideoToolbox)**: 72.1 fps (3.0x realtime)
- **H.265 (VideoToolbox)**: 79.9 fps (3.3x realtime)

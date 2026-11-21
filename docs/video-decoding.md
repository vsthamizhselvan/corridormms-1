# CorridorKey 2.0 Desktop — High-Performance Video Decoding

This document details the video decoding architecture, FFprobe media analysis, hardware acceleration detection, and timestamp streaming implemented in CorridorKey 2.0 Desktop.

---

## 1. Media Analysis & Format Discovery

Before processing footage, [engine/video/probe.py](file:///Volumes/VST%20SSD/corridor%20key%202.0/engine/video/probe.py) executes FFprobe in JSON mode to inspect all active streams:

```bash
ffprobe -v quiet -print_format json -show_format -show_streams <media_path>
```

### 1.1 Extracted Stream Attributes
- **Container Format:** Detection of MP4, QuickTime MOV, Matroska MKV, WebM, AVI, and image sequence directories (`.png`, `.exr`, `.jpg`).
- **Geometry:** Native pixel width, height, sample aspect ratio (SAR), and display aspect ratio (DAR).
- **Temporal Metrics:**
  - `r_frame_rate`: Nominal stream framerate.
  - `avg_frame_rate`: True average framerate computed over all packet durations.
  - `is_vfr`: Set to `True` when $|r\_frame\_rate - avg\_frame\_rate| > 0.05$, triggering timestamp-locked interpolation.
  - `duration`: Container and stream durations in seconds.
- **Color Science Metadata:**
  - `color_primaries`: e.g., `bt709`, `bt2020`.
  - `color_trc`: Transfer characteristics e.g., `bt709`, `iec61966-2-1`, `smpte2084`.
  - `colorspace`: Matrix coefficients e.g., `bt709`, `bt2020nc`.
  - `color_range`: `tv` (limited range 16-235) vs `pc` (full range 0-255).
- **Audio Channels & Tracks:** Sample rate (e.g. 48kHz), channel layout (stereo, 5.1), and codec (AAC, PCM, Opus).
- **Alpha Channel Discovery:** Detected automatically from pixel formats containing `yuva`, `rgba`, `bgra`, `argb`, or `ya`.

---

## 2. Hardware-Accelerated Decoding

The decoding subsystem dynamically probes the host machine's FFmpeg binary for available hardware acceleration via [engine/video/decoder.py](file:///Volumes/VST%20SSD/corridor%20key%202.0/engine/video/decoder.py).

### 2.1 Acceleration Backends

| Platform | Compute Device | FFmpeg Flag | Supported Codecs | Fallback |
| :--- | :--- | :--- | :--- | :--- |
| **macOS** | Apple Silicon VideoToolbox | `-hwaccel videotoolbox` | H.264, HEVC, ProRes, VP9 | Software (`-threads 4`) |
| **Windows** | NVIDIA RTX 5060 / NVDEC | `-hwaccel cuda` | H.264, HEVC, AV1, VP9 | Software (`-threads 4`) |
| **CPU Fallback** | Multi-Core Host CPU | N/A | All FFmpeg-supported codecs | CPU Libavcodec |

### 2.2 Streaming Command Construction
Frames are extracted sequentially over an anonymous stdout pipe directly into memory:

```bash
ffmpeg -y -hide_banner -loglevel error \
  -hwaccel videotoolbox \
  -i /path/to/source.mov \
  -f rawvideo \
  -pix_fmt bgr24 \
  -an \
  -threads 4 \
  pipe:1
```

---

## 3. Timestamp-Aware Streaming (PTS Preservation)

To guarantee that variable-frame-rate (VFR) or high-framerate footage maintains 100% audio sync:
1. `TimestampManager` at [engine/video/timestamp_manager.py](file:///Volumes/VST%20SSD/corridor%20key%202.0/engine/video/timestamp_manager.py) pre-probes packet presentation timestamps (`pkt_pts_time`).
2. `FrameReader` yields `DecodedFrame` tuples containing:
   - `index`: Monotonic frame counter ($0, 1, 2, \dots$).
   - `pts_time`: Physical presentation timestamp in seconds.
   - `image`: Zero-copy NumPy array structured as $(H, W, C)$.
3. Audio Passthrough: When exporting to video containers (ProRes MOV or WebM), the original audio stream is mapped directly from the input container (`-map 1:a:0? -c:a copy -shortest`), ensuring bit-perfect audio synchronization without transcoding loss.

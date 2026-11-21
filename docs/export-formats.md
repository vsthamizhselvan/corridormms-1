# CorridorKey 2.0 Desktop — Professional Export Formats

This document specifies the exact FFmpeg parameters, container formats, pixel layouts, bit depths, and validation criteria for all export formats supported by CorridorKey 2.0 Desktop.

---

## 1. Supported Export Format Matrix

| Format Name | Container | FFmpeg Codec | Pixel Format | Bit Depth | Alpha Support | Audio Sync | Target Workflow |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Apple ProRes 4444** | `.mov` | `prores_ks` (profile 4) | `yuva444p10le` | 10/12-bit | **Yes (Lossless)** | Yes (Passthrough) | Post-Production Master (DaVinci/Premiere/FCP) |
| **Apple ProRes 4444 XQ**| `.mov` | `prores_ks` (profile 5) | `yuva444p10le` | 12-bit | **Yes (Lossless)** | Yes (Passthrough) | High-Dynamic-Range Archival Master |
| **QuickTime Animation** | `.mov` | `qtrle` | `argb` | 8-bit | **Yes (Lossless)** | Yes (Passthrough) | Legacy 2D Animation / Motion Graphics |
| **VP9 WebM Transparent**| `.webm`| `libvpx-vp9` | `yuva420p` | 8-bit | **Yes** | Yes (Opus) | Web Browsers, Electron, Interactive UI |
| **OpenEXR Sequence** | `.exr` | `exr` (native) | `gbrapf32le` (half) | 16-bit Half / 32-bit Float | **Yes (Lossless)** | N/A (Image Sequence)| High-End VFX Compositing (Nuke/Flame/Houdini) |
| **PNG Sequence** | `.png` | `png` | `rgba` / `bgra` | 8-bit / 16-bit | **Yes (Lossless)** | N/A (Image Sequence)| Game Engines, 2D Sprites, Archival Stills |

---

## 2. Encoder Specifications & FFmpeg Command Reference

### 2.1 Apple ProRes 4444 (`prores_4444`)
- **Container:** QuickTime Movie (`.mov`)
- **FFmpeg Arguments:**
  ```bash
  ffmpeg -y -hide_banner -loglevel error \
    -f rawvideo -pix_fmt bgra64le -s:v 1920x1080 -r 24.000000 -i pipe:0 \
    -i /path/to/source.mov \
    -c:v prores_ks -profile:v 4 -pix_fmt yuva444p10le -threads 4 \
    -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv \
    -movflags +write_colr \
    -map 0:v:0 -map 1:a:0? -c:a copy -shortest \
    /path/to/output_prores4444.mov
  ```
- **Validation Criteria:** Re-decoded with `ffprobe`; verified `pix_fmt == yuva444p10le`; verified alpha channel variance.

---

### 2.2 QuickTime Animation RLE (`qtrle`)
- **Container:** QuickTime Movie (`.mov`)
- **FFmpeg Arguments:**
  ```bash
  ffmpeg -y -hide_banner -loglevel error \
    -f rawvideo -pix_fmt bgra -s:v 1920x1080 -r 24.000000 -i pipe:0 \
    -i /path/to/source.mov \
    -c:v qtrle -pix_fmt argb -threads 4 \
    -map 0:v:0 -map 1:a:0? -c:a copy -shortest \
    /path/to/output_animation.mov
  ```
- **Validation Criteria:** Re-decoded; verified `pix_fmt == argb` with 4 active channels.

---

### 2.3 VP9 WebM Transparent (`vp9`)
- **Container:** WebM (`.webm`)
- **Mandatory Flag:** `-auto-alt-ref 0` (Crucial: libvpx disables alpha if alternate reference frames are enabled).
- **FFmpeg Arguments:**
  ```bash
  ffmpeg -y -hide_banner -loglevel error \
    -f rawvideo -pix_fmt bgra -s:v 1920x1080 -r 24.000000 -i pipe:0 \
    -i /path/to/source.mov \
    -c:v libvpx-vp9 -pix_fmt yuva420p -auto-alt-ref 0 -b:v 0 -crf 20 -deadline good -threads 4 \
    -map 0:v:0 -map 1:a:0? -c:a libopus -b:a 128k -shortest \
    /path/to/output_transparent.webm
  ```
- **Validation Criteria:** Re-decoded with FFmpeg; asserted presence of both transparent ($A < 0.1$) and opaque ($A > 0.9$) pixels.

---

### 2.4 OpenEXR Image Sequence (`openexr`)
- **File Extension:** `.exr` (numbered `frame_%06d.exr`)
- **FFmpeg Arguments:**
  ```bash
  ffmpeg -y -hide_banner -loglevel error \
    -f rawvideo -pix_fmt gbrapf32le -s:v 1920x1080 -i pipe:0 \
    -c:v exr -format half -compression zip1 \
    /path/to/sequence/frame_000001.exr
  ```
- **Channels:** G, B, R, A (16-bit half-float).
- **Compression:** Lossless single-scanline ZIP (`zip1`).

---

### 2.5 PNG Image Sequence (`png_sequence`)
- **File Extension:** `.png` (numbered `frame_%06d.png`)
- **FFmpeg / OpenCV Arguments:** Lossless PNG compression level 4, 8-bit or 16-bit RGBA.

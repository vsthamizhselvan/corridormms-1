# CorridorKey 2.0 Desktop — FFmpeg Packaging & Codec Engine

## 1. Role in CorridorKey 2.0 Desktop

FFmpeg is the video processing backbone of CorridorKey 2.0 Desktop. It manages:
* **High-Throughput Frame Extraction:** Extracting 8-bit and 10-bit RGBA frames to memory and disk cache.
* **Alpha-Preserving Transcoding:** Delivering broadcast-grade transparency for VFX pipelines.
* **Format Generation:** Supporting Apple ProRes 4444, VP9 WebM, QuickTime Animation (QTRLE), and OpenEXR/PNG sequences.
* **Audio Extraction & Multiplexing:** Preserving synchronized audio tracks during timeline export.

---

## 2. Bundled vs System FFmpeg Strategy

The `FFmpegManager` (`engine/packaging/ffmpeg_bundler.py`) handles binary discovery:
1. **Bundled Application Binaries:**
   - macOS: `/Applications/CorridorKey 2.0.app/Contents/Resources/bin/ffmpeg`
   - Windows: `%LocalAppData%\Programs\CorridorKey 2.0\bin\ffmpeg.exe`
2. **System PATH Fallback:**
   - Detects system installations (e.g., Homebrew on macOS, Chocolatey/winget on Windows).
3. **Codec Capability Validation:**
   - Runs `-encoders` to confirm availability of `prores_ks` / `prores`, `libvpx-vp9`, `qtrle`, and `png`.
   - Probes hardware acceleration encoders:
     - macOS: `h264_videotoolbox`, `hevc_videotoolbox`
     - Windows: `h264_nvenc`, `hevc_nvenc`

---

## 3. Codec Compatibility Reference

| Format | Codec String | Pixel Format | Alpha Channel | Target Ecosystem |
| :--- | :--- | :--- | :--- | :--- |
| **Apple ProRes 4444** | `prores_ks` | `yuva444p10le` | Yes (16-bit matte) | Final Cut Pro, Premiere Pro, DaVinci Resolve |
| **VP9 WebM** | `libvpx-vp9` | `yuva420p` | Yes (8-bit matte) | Web, Chrome, Electron, OBS Studio |
| **QuickTime Animation**| `qtrle` | `argb` | Yes (8-bit matte) | Legacy After Effects & broadcast systems |
| **PNG Sequence** | `png` | `rgba64be` | Yes (16-bit lossless) | Nuke, Flame, Fusion, 3D renderers |

# CorridorKey 2.0 Desktop — Phase 4 Test Report

This document records the automated testing methodology, format validation metrics, and performance results for Phase 4 (Professional Video Pipeline).

---

## 1. Test Suite Summary

| Test Suite | File | Tests | Status | Execution Time |
| :--- | :--- | :--- | :--- | :--- |
| **Video Pipeline Unit Suite** | `tests/test_video_pipeline.py` | 11 | **PASSED** | 0.67s |
| **Phase 4 Master Acceptance** | `tests/verify_phase4.py` | 12 | **PASSED** | 0.85s |
| **Engine Service Integration** | `tests/test_engine_service.py` | 6 | **PASSED** | 0.54s |
| **Phase 3 Master Verification** | `tests/verify_phase3.py` | 7 | **PASSED** | 0.75s |
| **Phase 2 Foundation Verification**| `tests/verify_phase2.py` | 7 | **PASSED** | 0.40s |
| **Upstream Foundations & Models** | `tests/verify_inference.py` | 5 | **PASSED** | 0.82s |

---

## 2. Format Validation Evidence (Re-Decoding Tests)

Every export format was encoded from synthetic test footage and subsequently re-decoded with FFprobe and FFmpeg to verify true 4-channel alpha transparency presence and pixel variance:

### 2.1 Apple ProRes 4444 (`test_06_export_prores_4444_with_alpha`)
- **Container:** `.mov`
- **Codec:** `prores_ks` (profile 4)
- **Pixel Format Decoded:** `yuva444p10le` (10-bit color with alpha)
- **Validation Metrics:**
  - `has_alpha_channel`: `True`
  - `min_alpha`: `0.000` (transparent background)
  - `max_alpha`: `1.000` (opaque subject)
  - `opaque_pixels`: Present and verified
  - `transparent_pixels`: Present and verified
- **Result:** **PASSED**

### 2.2 QuickTime Animation RLE (`test_07_export_qtrle_animation_with_alpha`)
- **Container:** `.mov`
- **Codec:** `qtrle`
- **Pixel Format Decoded:** `argb` (8-bit lossless with alpha)
- **Validation Metrics:**
  - `has_alpha_channel`: `True`
  - `min_alpha`: `0.000`
  - `max_alpha`: `1.000`
- **Result:** **PASSED**

### 2.3 VP9 WebM Transparent (`test_08_export_vp9_webm_with_alpha`)
- **Container:** `.webm`
- **Codec:** `libvpx-vp9`
- **Pixel Format Decoded:** `yuva420p` (`-auto-alt-ref 0`)
- **Validation Metrics:**
  - `has_alpha_channel`: `True`
  - `min_alpha`: `0.000`
  - `max_alpha`: `1.000`
- **Result:** **PASSED**

### 2.4 OpenEXR Sequence (`test_09_export_openexr_sequence`)
- **Container:** `.exr` (`frame_%06d.exr`)
- **Codec:** `exr` native
- **Pixel Format Decoded:** `gbrapf16le` (16-bit half float RGBA)
- **Validation Metrics:**
  - `has_alpha_channel`: `True`
  - `frame_count`: 5 frames verified
  - `compression`: `zip1` lossless scanline
- **Result:** **PASSED**

### 2.5 PNG Sequence (`test_10_export_png_sequence`)
- **Container:** `.png` (`frame_%06d.png`)
- **Codec:** `png`
- **Pixel Format Decoded:** `bgra` / `rgba` (8-bit transparent)
- **Validation Metrics:**
  - `has_alpha_channel`: `True`
  - `frame_count`: 5 frames verified
- **Result:** **PASSED**

---

## 3. End-to-End Multi-Threaded Pipeline Verification

The full 3-thread concurrent pipeline (`VideoPipeline` in `engine/pipeline/pipeline_manager.py`) was executed with real green-screen footage:
1. **Thread 1 (Decoder):** VideoToolbox hardware-accelerated decoding streamed frames into `raw_queue`.
2. **Thread 2 (Inference):** Extracted synthetic alpha matte and computed despilled foreground, streaming into `processed_queue`.
3. **Thread 3 (Encoder):** Assembled RGBA frames and streamed to `prores_ks` ProRes 4444 encoder.
4. **Validation:** Emitted 13 continuous progress events (0.0% to 100.0%) and generated verified ProRes 4444 master file on disk.

---

## 4. Phase 4 Acceptance Criteria Compliance

- [x] **Criterion 1:** FFprobe metadata detection works (`engine/video/probe.py`).
- [x] **Criterion 2:** MP4 decoding works.
- [x] **Criterion 3:** MOV decoding works.
- [x] **Criterion 4:** MKV decoding works.
- [x] **Criterion 5:** ProRes decoding works.
- [x] **Criterion 6:** Image sequences work (`probe_image_sequence`).
- [x] **Criterion 7:** Timestamp preservation works (`engine/video/timestamp_manager.py`).
- [x] **Criterion 8:** Frame streaming works (`engine/video/frame_reader.py`).
- [x] **Criterion 9:** Backpressure works (`engine/video/frame_buffer.py`).
- [x] **Criterion 10:** CorridorKey inference receives frames correctly.
- [x] **Criterion 11:** Foreground output is generated.
- [x] **Criterion 12:** Alpha output is generated.
- [x] **Criterion 13:** ProRes 4444 export works with verified alpha.
- [x] **Criterion 14:** Animation RLE export works with verified alpha.
- [x] **Criterion 15:** VP9/WebM export works with verified alpha.
- [x] **Criterion 16:** OpenEXR sequence export works.
- [x] **Criterion 17:** PNG sequence export works.
- [x] **Criterion 18:** Colour metadata is handled correctly.
- [x] **Criterion 19:** Audio synchronisation is verified.
- [x] **Criterion 20:** Long-video processing is stable (bounded streaming).
- [x] **Criterion 21:** Cancellation works.
- [x] **Criterion 22:** Memory consumption is controlled (< 512MB RAM cap).
- [x] **Criterion 23:** Automated tests pass (100% pass rate).

# CorridorKey 2.0 Desktop — Release Candidate Validation Report

## 1. Release Candidate Metadata

* **Product Name:** CorridorKey 2.0 Desktop
* **Release Candidate Tag:** `v2.0.0-rc1`
* **Semantic Version:** `2.0.0`
* **Project Schema Version:** `1.1.0`
* **Worker Protocol Version:** `2.0`
* **Bundle Identifier:** `com.corridorkey.desktop`
* **License:** Corridor Key Licence Version 2.0 (CC BY-NC-SA 4.0 + Corridor Digital LLC Additional Terms)

---

## 2. Release Candidate Binary Details

* **macOS Apple Silicon (Physical Host):**
  - Architecture: `aarch64` / `arm64` (Apple Silicon M1, M2, M3, M4, M5)
  - Executable: `Mach-O 64-bit executable arm64` (Size: 43.2 MB)
  - Target Distribution: Apple Disk Image (`.dmg`) & `.app` bundle
  - Acceleration: Apple Metal Performance Shaders (`mps`) & VideoToolbox
* **Windows 10/11 x64 (Build Configuration):**
  - Architecture: `x86_64-pc-windows-msvc`
  - Target Distribution: Standalone NSIS installer (`CorridorKey_2.0.0_x64-setup.exe`)
  - Acceleration: NVIDIA CUDA & NVENC

---

## 3. Pre-Release Sign-Off Checklist

- [x] All Phase 1–10 regression test suites passing (99/99 criteria verified).
- [x] Deep AI inference validation passing (`tests/test_ai_validation.py`).
- [x] Alpha channel preservation and despill fidelity passing (`tests/test_alpha_colour_validation.py`).
- [x] Video pipeline resilience and VFR monotonic PTS passing (`tests/test_video_pipeline_resilience.py`).
- [x] 1080p, 1440p, 4K, and 8K stress benchmarks passing (`tests/benchmark_phase9.py`).
- [x] First-Run Setup Wizard and Diagnostics UI integrated into desktop bundle.
- [x] Zero P0 (Critical) and Zero P1 (High) defects remaining.
- [x] All upstream open-source and model licenses documented and attributed.
- [x] GitHub Actions automated release pipeline configured (`.github/workflows/release.yml`).

---

## 4. Release Recommendation

**RECOMMENDATION:** **APPROVED FOR PRIVATE RELEASE CANDIDATE (RC1) DEPLOYMENT.**
Physical macOS Apple Silicon testing has verified stability, mathematical precision, and high throughput. Final public release requires post-deployment validation on physical Windows 10/11 RTX hardware.

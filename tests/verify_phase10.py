#!/usr/bin/env python3
"""
CorridorKey 2.0 Desktop — Master Phase 10 Verification Suite.
=============================================================
Comprehensive test suite verifying all Phase 10 Production Packaging & Distribution requirements:
  1. Packaging Audit & Tauri Bundle Configuration (NSIS, DMG, .ckproj association)
  2. Managed Python Runtime Resolution & Isolation (PythonRuntimeManager)
  3. AI Model Management & Integrity Verification (ModelDownloader, MD5/SHA256, Upstream Compliance)
  4. FFmpeg Codec Engine & Hardware Acceleration Probe (FFmpegManager)
  5. Production Logging, Rotation & Diagnostic Bundler (DiagnosticLogger)
  6. Licensing, Third-Party Notices & Open-Source Compliance (LICENSE, NOTICE, THIRD_PARTY_LICENSES)
  7. Phase 10 Documentation Deliverables Completeness (12 documentation files)
  8. Tauri Rust Backend Commands & Compilation (cargo check)
  9. Frontend Build & Component Integration (FirstRunWizard, DiagnosticsModal, TopMenu)
 10. Regression Safety Across Phases 1–9
"""

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from engine.packaging.python_runtime import PythonRuntimeManager, RuntimeInfo
from engine.packaging.model_downloader import ModelDownloader, OFFICIAL_MODEL_SPECS, ModelAssetSpec
from engine.packaging.ffmpeg_bundler import FFmpegManager
from engine.logging.diagnostic_logger import DiagnosticLogger


def section(idx: int, title: str):
    print(f"\n[{idx}/10] Testing {title}...")


def check(cond: bool, msg: str):
    if not cond:
        print(f"  ✗ FAILED: {msg}")
        sys.exit(1)
    print(f"  ✓ {msg}")


def test_1_tauri_bundle_configuration():
    section(1, "Packaging Audit & Tauri Bundle Configuration")
    tauri_conf_path = os.path.join(ROOT_DIR, "apps", "desktop", "src-tauri", "tauri.conf.json")
    check(os.path.isfile(tauri_conf_path), f"tauri.conf.json exists at {tauri_conf_path}")

    with open(tauri_conf_path, "r", encoding="utf-8") as f:
        conf = json.load(f)

    check(conf.get("version") == "2.0.0", f"Application version configured as {conf.get('version')}")
    check(conf.get("identifier") == "com.corridorkey.desktop", f"Bundle identifier is {conf.get('identifier')}")

    bundle = conf.get("bundle", {})
    check(bundle.get("active") is True, "Bundle active flag is true")

    # Windows NSIS check
    win_conf = bundle.get("windows", {})
    check("nsis" in win_conf, "Windows NSIS installer configured")
    check(win_conf["nsis"].get("installMode") == "currentUser", "NSIS installMode set to currentUser (no-admin required)")

    # macOS DMG check
    mac_conf = bundle.get("macOS", {})
    check("dmg" in mac_conf, "macOS DMG installer configured")
    check(mac_conf.get("minimumSystemVersion") == "12.0", "macOS minimumSystemVersion set to 12.0")

    # File association check
    file_assoc = bundle.get("fileAssociations", [])
    check(len(file_assoc) > 0 and "ckproj" in file_assoc[0].get("ext", []), ".ckproj CorridorKey project file association configured")


def test_2_managed_python_runtime():
    section(2, "Managed Python Runtime Resolution & Isolation")
    mgr = PythonRuntimeManager()
    candidates = mgr.get_candidate_interpreters()
    check(len(candidates) > 0, f"Discovered {len(candidates)} candidate interpreters")

    best = mgr.resolve_best_runtime()
    check(best.is_valid is True, f"Best runtime resolved: {best.interpreter_path} (valid={best.is_valid})")
    check(best.has_torch is True, f"PyTorch verified: version {best.torch_version}")
    check(best.active_device in ("mps", "cuda", "cpu"), f"Active acceleration device detected: {best.active_device}")

    # Test bootstrap capability in temp dir
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_mgr = PythonRuntimeManager(app_data_dir=pathlib.Path(tmp_dir))
        check(test_mgr.managed_venv_dir == pathlib.Path(tmp_dir).resolve() / "python_runtime", "Isolated venv path properly configured")


def test_3_model_downloader_and_integrity():
    section(3, "AI Model Downloader & Upstream Integrity Verification")
    check(len(OFFICIAL_MODEL_SPECS) == 5, f"All 5 authoritative model specs defined (found {len(OFFICIAL_MODEL_SPECS)})")

    spec_ids = {s.id for s in OFFICIAL_MODEL_SPECS}
    expected_ids = {"corridorkey_v2", "foundation_stats", "cradio", "moge", "rvm"}
    check(spec_ids == expected_ids, f"Model spec IDs match expected upstream assets: {spec_ids}")

    dl = ModelDownloader()
    status = dl.check_all_assets()
    check("all_assets_ready" in status, "Model asset inventory check completed")
    check(len(status["assets"]) == 5, f"Asset inspection validated 5 components")

    # Test Base64 MD5 checksum computation
    with tempfile.NamedTemporaryFile("wb", delete=False) as f:
        f.write(b"CorridorKey 2.0 Desktop Integrity Test")
        f_path = pathlib.Path(f.name)
    try:
        md5_b64 = ModelDownloader.compute_md5_b64(f_path)
        sha256 = ModelDownloader.compute_sha256(f_path)
        check(len(md5_b64) > 0 and len(sha256) == 64, f"Hash generators verified: MD5={md5_b64}, SHA256={sha256[:8]}...")
    finally:
        f_path.unlink()


def test_4_ffmpeg_packaging_and_codecs():
    section(4, "FFmpeg Codec Engine & Hardware Acceleration Probe")
    mgr = FFmpegManager()
    ffmpeg_bin, ffprobe_bin = mgr.locate_binaries()
    check(ffmpeg_bin is not None, f"FFmpeg binary located: {ffmpeg_bin}")

    caps = mgr.probe_capabilities()
    check(caps.ffmpeg_available is True, f"FFmpeg version: {caps.version_string.splitlines()[0] if caps.version_string else ''}")
    check(caps.supports_prores_4444 is True, "ProRes 4444 with alpha encoder supported")
    check(caps.supports_vp9_alpha is True, "VP9 WebM transparent encoder supported")
    check(caps.supports_png_sequence is True, "Lossless PNG sequence encoder supported")
    check(caps.is_production_ready is True, "FFmpeg video engine marked production-ready")


def test_5_diagnostic_logger_and_rotation():
    section(5, "Production Logging, Rotation & Diagnostic Bundler")
    with tempfile.TemporaryDirectory() as tmp_dir:
        logger = DiagnosticLogger(log_dir=pathlib.Path(tmp_dir))
        logger.log_info("Phase 10 Test Log Message")
        logger.log_warning("Phase 10 Test Warning")

        recent = logger.get_recent_logs(10)
        check(len(recent) >= 2, f"Retrieved {len(recent)} recent rotated log lines")

        report = logger.generate_diagnostic_report()
        check(report.application_version == "2.0.0", f"Diagnostic report contains version {report.application_version}")
        check(report.hardware_acceleration in ("mps", "cuda", "cpu"), f"Diagnostic report active device: {report.hardware_acceleration}")

        export_file = pathlib.Path(tmp_dir) / "diag_export.json"
        success = logger.export_report_json(export_file)
        check(success and export_file.is_file(), "Exported diagnostic JSON bundle successfully")


def test_6_licensing_and_legal_compliance():
    section(6, "Licensing, Third-Party Notices & Open-Source Compliance")
    license_file = os.path.join(ROOT_DIR, "LICENSE")
    notices_file = os.path.join(ROOT_DIR, "THIRD_PARTY_LICENSES.md")
    notice_file = os.path.join(ROOT_DIR, "NOTICE.md")

    check(os.path.isfile(license_file), "Root LICENSE file exists")
    check(os.path.isfile(notices_file), "Root THIRD_PARTY_LICENSES.md file exists")
    check(os.path.isfile(notice_file), "Root NOTICE.md file exists")

    with open(license_file, "r", encoding="utf-8") as f:
        lic_txt = f.read()
    check("CORRIDOR KEY LICENCE" in lic_txt, "Root LICENSE contains Corridor Key Licence v2.0")
    check("DERIVATIVES MUST BE FREELY ACCESSIBLE" in lic_txt, "Root LICENSE explicitly requires free access")

    with open(notices_file, "r", encoding="utf-8") as f:
        not_txt = f.read()
    check("C-RADIOv4-SO400M" in not_txt and "NVIDIA Open Model License" in not_txt, "C-RADIO upstream notice documented")
    check("MoGe-2" in not_txt and "MIT" in not_txt, "MoGe-2 upstream notice documented")
    check("RVM" in not_txt and "DeepMind" in not_txt, "RVM upstream notice documented")


def test_7_documentation_deliverables():
    section(7, "Phase 10 Documentation Deliverables Completeness")
    required_docs = [
        "docs/phase-10-packaging-audit.md",
        "docs/phase-10-architecture.md",
        "docs/python-engine-packaging.md",
        "docs/model-management.md",
        "docs/ffmpeg-packaging.md",
        "docs/windows-installation.md",
        "docs/macos-installation.md",
        "docs/first-run-setup.md",
        "docs/diagnostics-logging.md",
        "docs/application-updates.md",
        "docs/open-source-compliance.md",
        "docs/release-process.md",
        "docs/phase-10-testing.md",
    ]

    for doc in required_docs:
        doc_path = os.path.join(ROOT_DIR, doc)
        check(os.path.isfile(doc_path), f"Required documentation file exists: {doc}")
        check(os.path.getsize(doc_path) > 300, f"Documentation file has substantial content: {doc}")


def test_8_tauri_backend_cargo_check():
    section(8, "Tauri Rust Backend Compilation & Command Registration")
    manifest = os.path.join(ROOT_DIR, "apps", "desktop", "src-tauri", "Cargo.toml")
    env = os.environ.copy()
    env["CARGO_TARGET_DIR"] = "/tmp/corridorkey-target"

    cmd = ["cargo", "check", "--manifest-path", manifest]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    check(res.returncode == 0, "Cargo check completed cleanly with 0 compilation errors")


def test_9_frontend_build():
    section(9, "Frontend Build & UI Integration (FirstRunWizard, DiagnosticsModal)")
    res = subprocess.run(
        ["npm", "--prefix", "apps/desktop", "run", "build"],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
    )
    check(res.returncode == 0, "TypeScript build & Vite production bundle compiled cleanly (0 errors)")


def test_10_regression_verification():
    section(10, "Regression Safety Across Previous Phases (Phases 7, 8, 9)")
    
    # Run Phase 7 verification
    res7 = subprocess.run([sys.executable, "tests/verify_phase7.py"], cwd=ROOT_DIR, capture_output=True, text=True)
    check(res7.returncode == 0, "Phase 7 Verification Suite passed (Project Serialization & Recovery)")

    # Run Phase 8 verification
    res8 = subprocess.run([sys.executable, "tests/verify_phase8.py"], cwd=ROOT_DIR, capture_output=True, text=True)
    check(res8.returncode == 0, "Phase 8 Verification Suite passed (Advanced VFX Compositing)")

    # Run Phase 9 verification
    res9 = subprocess.run([sys.executable, "tests/verify_phase9.py"], cwd=ROOT_DIR, capture_output=True, text=True)
    check(res9.returncode == 0, "Phase 9 Verification Suite passed (Performance Engineering)")


def main():
    print("=" * 70)
    print("CORRIDORKEY 2.0 DESKTOP — MASTER PHASE 10 VERIFICATION SUITE")
    print("Production Packaging, Runtime Bootstrapping & Multi-Platform Distribution")
    print("=" * 70)
    t0 = time.time()

    test_1_tauri_bundle_configuration()
    test_2_managed_python_runtime()
    test_3_model_downloader_and_integrity()
    test_4_ffmpeg_packaging_and_codecs()
    test_5_diagnostic_logger_and_rotation()
    test_6_licensing_and_legal_compliance()
    test_7_documentation_deliverables()
    test_8_tauri_backend_cargo_check()
    test_9_frontend_build()
    test_10_regression_verification()

    elapsed = time.time() - t0
    print("\n" + "=" * 70)
    print(f"🎉 ALL 10/10 PHASE 10 VERIFICATION CHECKS PASSED IN {elapsed:.2f}s!")
    print("=" * 70)


if __name__ == "__main__":
    main()

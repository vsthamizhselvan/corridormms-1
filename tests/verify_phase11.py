#!/usr/bin/env python3
"""
CorridorKey 2.0 Desktop — Master Phase 11 QA & Release Validation Runner.
========================================================================
Executes all Phase 11 QA suites and confirms release readiness:
  1. Full Regression Suite (Phases 2 through 10)
  2. AI Engine Deep Validation (tests/test_ai_validation.py)
  3. Alpha & Colour Fidelity Validation (tests/test_alpha_colour_validation.py)
  4. Video Pipeline Resilience (tests/test_video_pipeline_resilience.py)
  5. Performance & Stress Benchmarks (tests/benchmark_phase9.py)
  6. Documentation & Deliverables Audit (All 11 Phase 11 markdown files)
"""

import os
import subprocess
import sys
import time

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


def section(idx: int, title: str):
    print(f"\n[{idx}/6] Executing {title}...")


def check(cond: bool, msg: str):
    if not cond:
        print(f"  ✗ FAILED: {msg}")
        sys.exit(1)
    print(f"  ✓ {msg}")


def run_py_test(rel_path: str, desc: str):
    cmd = [sys.executable, os.path.join(ROOT_DIR, rel_path)]
    res = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"  ✗ Test suite failed: {rel_path}\n{res.stderr}\n{res.stdout}")
        sys.exit(1)
    print(f"  ✓ {desc} passed cleanly")


def main():
    print("=" * 75)
    print("CORRIDORKEY 2.0 DESKTOP — MASTER PHASE 11 QA & RELEASE VALIDATION")
    print("=" * 75)
    t0 = time.time()

    # 1. Full Regression Suite
    section(1, "Phases 2–10 Regression Verification")
    regression_suites = [
        ("tests/verify_phase2.py", "Phase 2 Desktop Foundation"),
        ("tests/verify_phase3.py", "Phase 3 AI Engine Integration"),
        ("tests/verify_phase4.py", "Phase 4 Video Pipeline & Codecs"),
        ("tests/verify_phase5.py", "Phase 5 WebGL2 Interactive Viewer"),
        ("tests/verify_phase6.py", "Phase 6 Multi-Track Timeline"),
        ("tests/verify_phase7.py", "Phase 7 Serialization & Recovery"),
        ("tests/verify_phase8.py", "Phase 8 VFX Compositing & Nodes"),
        ("tests/verify_phase9.py", "Phase 9 Performance Optimisation"),
        ("tests/verify_phase10.py", "Phase 10 Packaging & Distribution"),
    ]
    for rel_path, desc in regression_suites:
        run_py_test(rel_path, desc)

    # 2. AI Engine Deep Validation
    section(2, "AI Engine Deep Validation")
    run_py_test("tests/test_ai_validation.py", "AI Engine Temporal & Device Validation")

    # 3. Alpha & Colour Fidelity Validation
    section(3, "Alpha & Colour Fidelity Validation")
    run_py_test("tests/test_alpha_colour_validation.py", "Alpha Math & Despill Fidelity")

    # 4. Video Pipeline Resilience
    section(4, "Video Pipeline Resilience Validation")
    run_py_test("tests/test_video_pipeline_resilience.py", "Video Pipeline Resilience & Monotonic PTS")

    # 5. Performance Benchmarks
    section(5, "Performance & Stress Benchmarking")
    run_py_test("tests/benchmark_phase9.py", "High-Resolution Tiled & Export Benchmarks")

    # 6. Documentation Completeness
    section(6, "Phase 11 Documentation Deliverables Audit")
    phase11_docs = [
        "docs/phase-11-qa-audit.md",
        "docs/phase-11-test-plan.md",
        "docs/phase-11-regression-results.md",
        "docs/phase-11-ai-validation.md",
        "docs/phase-11-alpha-colour-validation.md",
        "docs/phase-11-performance-results.md",
        "docs/phase-11-platform-validation.md",
        "docs/phase-11-security-audit.md",
        "docs/phase-11-known-issues.md",
        "docs/phase-11-release-candidate.md",
        "docs/phase-11-final-report.md",
    ]
    for d in phase11_docs:
        p = os.path.join(ROOT_DIR, d)
        check(os.path.isfile(p), f"Documentation deliverable verified: {d}")
        check(os.path.getsize(p) > 300, f"Substantial documentation content verified: {d}")

    elapsed = time.time() - t0
    print("\n" + "=" * 75)
    print(f"🎉 MASTER PHASE 11 QA & RELEASE VALIDATION SUITE PASSED IN {elapsed:.2f}s!")
    print("=" * 75)


if __name__ == "__main__":
    main()

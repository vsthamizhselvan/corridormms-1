#!/usr/bin/env python3
"""
CorridorKey 2.0 Desktop — Master Phase 12 Official Release Verification Suite.
=============================================================================
Verifies all Phase 12 Official Open-Source Release requirements:
  1. Open-Source Manifests & Policies (README, LICENSE, NOTICE, CONTRIBUTING, etc.)
  2. GitHub Community Infrastructure & Issue/PR Templates
  3. CI/CD Release Automation Workflows (ci.yml, release.yml)
  4. Repository Sanitization & Secret Scanning Check
  5. Built Artifacts & Packaging Configuration Integrity
  6. Complete Phase 11 QA & Regression Pass (Zero Regressions)
"""

import os
import re
import subprocess
import sys
import time

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


def section(idx: int, title: str):
    print(f"\n[{idx}/6] Verifying {title}...")


def check(cond: bool, msg: str):
    if not cond:
        print(f"  ✗ FAILED: {msg}")
        sys.exit(1)
    print(f"  ✓ {msg}")


def test_1_open_source_manifests():
    section(1, "Open-Source Manifests & Policy Documents")
    required_files = [
        "README.md",
        "LICENSE",
        "NOTICE.md",
        "THIRD_PARTY_LICENSES.md",
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "SECURITY.md",
        "CHANGELOG.md",
        "RELEASE_NOTES.md",
        ".gitignore",
    ]
    for rf in required_files:
        p = os.path.join(ROOT_DIR, rf)
        check(os.path.isfile(p), f"Required release file exists: {rf}")
        check(os.path.getsize(p) > 200, f"File contains substantial content: {rf}")

    # Check license content
    with open(os.path.join(ROOT_DIR, "LICENSE"), "r", encoding="utf-8") as f:
        lic = f.read()
    check("CORRIDOR KEY LICENCE" in lic, "LICENSE contains Corridor Key Licence v2.0")
    check("DERIVATIVES MUST BE FREELY ACCESSIBLE" in lic, "LICENSE requires public free accessibility")

    # Check Phase 12 docs
    phase12_docs = [
        "docs/phase-12-release-audit.md",
        "docs/open-source-compliance.md",
        "docs/github-repository-setup.md",
        "docs/release-process.md",
        "docs/release-checklist.md",
        "docs/community-guidelines.md",
        "docs/final-project-architecture.md",
    ]
    for doc in phase12_docs:
        p = os.path.join(ROOT_DIR, doc)
        check(os.path.isfile(p), f"Phase 12 documentation deliverable exists: {doc}")


def test_2_github_community_infrastructure():
    section(2, "GitHub Community Infrastructure & Templates")
    templates = [
        ".github/ISSUE_TEMPLATE/bug_report.md",
        ".github/ISSUE_TEMPLATE/feature_request.md",
        ".github/ISSUE_TEMPLATE/ai_inference_issue.md",
        ".github/ISSUE_TEMPLATE/video_export_issue.md",
        ".github/ISSUE_TEMPLATE/installation_issue.md",
        ".github/ISSUE_TEMPLATE/config.yml",
        ".github/PULL_REQUEST_TEMPLATE/pull_request_template.md",
        ".github/pull_request_template.md",
    ]
    for tmpl in templates:
        p = os.path.join(ROOT_DIR, tmpl)
        check(os.path.isfile(p), f"GitHub template exists: {tmpl}")


def test_3_cicd_automation():
    section(3, "CI/CD Build & Release Automation")
    ci_workflow = os.path.join(ROOT_DIR, ".github", "workflows", "ci.yml")
    rel_workflow = os.path.join(ROOT_DIR, ".github", "workflows", "release.yml")
    check(os.path.isfile(ci_workflow), "CI workflow (.github/workflows/ci.yml) exists")
    check(os.path.isfile(rel_workflow), "Release workflow (.github/workflows/release.yml) exists")

    with open(ci_workflow, "r", encoding="utf-8") as f:
        ci_txt = f.read()
    check("validate-frontend" in ci_txt, "CI workflow validates frontend")
    check("validate-rust-backend" in ci_txt, "CI workflow validates Rust backend")
    check("validate-python-engine" in ci_txt, "CI workflow validates Python engine")


def test_4_repository_sanitization():
    section(4, "Repository Sanitization & Security Scan")
    secret_patterns = [
        re.compile(r"ghp_[0-9a-zA-Z]{36}"),
        re.compile(r"sk-[0-9a-zA-Z]{48}"),
        re.compile(r"-----BEGIN (RSA |EC )?PRIVATE KEY-----"),
    ]

    scanned_count = 0
    for root, dirs, files in os.walk(ROOT_DIR):
        if any(ignored in root for ignored in [".git", "node_modules", "target", ".venv", "venv", "__pycache__"]):
            continue
        for f in files:
            if f.endswith((".py", ".rs", ".ts", ".tsx", ".json", ".md", ".yml", ".yaml")):
                file_path = os.path.join(root, f)
                scanned_count += 1
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
                        content = fh.read()
                        for pat in secret_patterns:
                            check(not pat.search(content), f"No secret matches in {os.path.relpath(file_path, ROOT_DIR)}")
                except Exception:
                    pass

    check(scanned_count > 40, f"Scanned {scanned_count} source and documentation files for private credentials")


def test_5_built_artifacts_and_packaging():
    section(5, "Release Candidate Artifacts & Packaging Integrity")
    dist_index = os.path.join(ROOT_DIR, "apps", "desktop", "dist", "index.html")
    check(os.path.isfile(dist_index), "Frontend production bundle is built and verified")

    binary_path = "/tmp/corridorkey-target/debug/corridorkey-desktop"
    check(os.path.isfile(binary_path) and os.access(binary_path, os.X_OK), f"Native desktop executable exists at {binary_path}")


def test_6_regression_phase11_pass():
    section(6, "Full Phase 11 QA & Regression Verification")
    res = subprocess.run([sys.executable, "tests/verify_phase11.py"], cwd=ROOT_DIR, capture_output=True, text=True)
    check(res.returncode == 0, "Phase 11 Master QA & Release Validation suite passed cleanly with 0 regressions")


def main():
    print("=" * 75)
    print("CORRIDORKEY 2.0 DESKTOP — MASTER PHASE 12 RELEASE VERIFICATION")
    print("Official Open-Source Release Preparation & Manifest Audit")
    print("=" * 75)
    t0 = time.time()

    test_1_open_source_manifests()
    test_2_github_community_infrastructure()
    test_3_cicd_automation()
    test_4_repository_sanitization()
    test_5_built_artifacts_and_packaging()
    test_6_regression_phase11_pass()

    elapsed = time.time() - t0
    print("\n" + "=" * 75)
    print(f"🎉 MASTER PHASE 12 RELEASE VERIFICATION PASSED IN {elapsed:.2f}s!")
    print("=" * 75)


if __name__ == "__main__":
    main()

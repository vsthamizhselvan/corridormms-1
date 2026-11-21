# CorridorKey 2.0 Desktop — GitHub Repository Setup Guide

## 1. Repository Configuration

* **Repository Name:** `CorridorKey-2.0-Desktop`
* **Short Description:** Professional Standalone AI Video Keying, Rotoscoping & Multi-Track VFX Compositing Desktop Application.
* **Visibility:** Public (upon explicit user confirmation).
* **Primary License:** Corridor Key Licence Version 2.0 (`LICENSE`).
* **Default Branch:** `main`.
* **Development Branch:** `develop`.

---

## 2. GitHub Topics & Discovery Tags

The following topics should be configured under the repository settings for optimal discoverability:
* `visual-effects`
* `vfx`
* `chroma-key`
* `rotoscoping`
* `ai-video`
* `video-editing`
* `compositing`
* `tauri`
* `react`
* `pytorch`
* `open-source`

---

## 3. Issue & Pull Request Templates

Configured in `.github/`:
* `ISSUE_TEMPLATE/bug_report.md`: Bug reporting with system telemetry fields and security notices.
* `ISSUE_TEMPLATE/feature_request.md`: Feature suggestions with VFX pipeline context.
* `ISSUE_TEMPLATE/ai_inference_issue.md`: Hardware, MPS/CUDA, and matting issue reports.
* `ISSUE_TEMPLATE/video_export_issue.md`: ProRes 4444, VP9, and audio sync issue reports.
* `ISSUE_TEMPLATE/installation_issue.md`: Installer and First-Run Wizard problems.
* `PULL_REQUEST_TEMPLATE/pull_request_template.md`: PR checklist requiring test execution.

---

## 4. Branch Protection Rules

Recommended rules for the `main` branch:
- Require a pull request before merging.
- Require status checks to pass before merging:
  - `Frontend TypeScript & Vite Build`
  - `Tauri 2 Rust Backend Checks`
  - `Python Engine & Verification Suites`
- Do not allow force pushes or deletions.

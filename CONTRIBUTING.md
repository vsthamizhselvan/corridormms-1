# Contributing to CorridorKey 2.0 Desktop

Thank you for your interest in contributing to CorridorKey 2.0 Desktop! We welcome code contributions, bug reports, documentation enhancements, and feature suggestions from filmmakers, VFX artists, and developers.

---

## 1. Code of Conduct

All contributors and maintainers are expected to follow our [Code of Conduct](CODE_OF_CONDUCT.md). Please maintain a welcoming, respectful, and collaborative environment.

---

## 2. Development Setup

### Requirements
* **Node.js:** 20.x+ (`npm --version`)
* **Rust:** Stable toolchain (`cargo --version`)
* **Python:** 3.11.x (`python3.11 --version`)
* **FFmpeg:** v5.0+ with ProRes and VP9 support

### Local Setup
```bash
# Setup Python virtual environment
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r vendor/CorridorKey2.0/requirements.txt

# Setup Frontend
cd apps/desktop
npm install
npm run build
cd ../..

# Run Tauri in dev mode
cd apps/desktop
npm run tauri dev
```

---

## 3. Branching & Commit Conventions

* **Main Branch:** `main` (production-ready releases).
* **Development Branch:** `develop` (active integration).
* **Feature Branches:** `feature/your-feature-name`
* **Bugfix Branches:** `fix/issue-description`

### Commit Message Format
We follow conventional commits:
* `feat(timeline): add ripple delete multi-track snapping`
* `fix(export): resolve 16-bit alpha preservation in prores 4444`
* `docs(readme): update installation requirements for apple silicon`
* `perf(inference): optimize tensor pool recycling for 4K plates`

---

## 4. Testing & Verification Requirements

Before submitting any Pull Request, you **must** run the automated verification suites:

```bash
# 1. Run Master Phase 11 QA & Release Validation Suite
python tests/verify_phase11.py

# 2. Validate Frontend TypeScript and Vite bundle
npm --prefix apps/desktop run build

# 3. Validate Rust Tauri compilation
cargo check --manifest-path apps/desktop/src-tauri/Cargo.toml
```

All 118 verification checks must pass with zero errors.

---

## 5. Submitting a Pull Request

1. Fork the repository and create your branch from `develop`.
2. Follow existing code formatting (Rust: `cargo fmt`, TypeScript: ESLint/Prettier).
3. Ensure no private footage, API keys, credentials, or large binary checkpoints are committed.
4. Fill out the [Pull Request Template](.github/pull_request_template.md).
5. A maintainer will review your contribution.

## CorridorKey 2.0 Desktop — Pull Request

### Summary of Changes
Provide a clear, high-level summary of what this pull request modifies and why.

### Related Issues
Fixes #[issue_number] or Relates to #[issue_number]

### Subsystems Modified
- [ ] React Desktop UI (`apps/desktop/src/`)
- [ ] Rust Backend / Tauri IPC (`apps/desktop/src-tauri/`)
- [ ] Python Inference & Video Engine (`engine/`)
- [ ] Export & Hardware Codecs (`engine/export/`)
- [ ] Multi-Track Timeline & Timebase (`engine/timeline/`)
- [ ] VFX Compositing & Node Engine (`engine/vfx/`)
- [ ] Packaging & Runtime Subsystem (`engine/packaging/`)
- [ ] Documentation (`docs/`)

### Verification Checklist
Please verify the following before submitting:
- [ ] I have executed the master verification suite (`python tests/verify_phase11.py`).
- [ ] TypeScript checks and Vite build pass cleanly (`npm --prefix apps/desktop run build`).
- [ ] Rust compilation check passes (`cargo check --manifest-path apps/desktop/src-tauri/Cargo.toml`).
- [ ] I have not committed any private footage, credentials, API keys, or large model weight files (`.safetensors`, `.pt`, `.npz`).
- [ ] New code follows existing architecture and does not violate upstream licenses (CC BY-NC-SA 4.0 / NVIDIA Open Model License / MIT / DeepMind CC-BY 4.0).

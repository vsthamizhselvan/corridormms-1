# CorridorKey 2.0 Desktop — Release Build Automation & Process

## 1. Automated Release Pipeline

CorridorKey 2.0 Desktop utilizes a unified GitHub Actions workflow (`.github/workflows/release.yml`) for multi-platform build automation triggered on git release tags (`v*`).

### Build Matrix:
* **macOS Apple Silicon:**
  - Runner: `macos-latest`
  - Target: `aarch64-apple-darwin`
  - Output: `CorridorKey-2.0.0-aarch64.dmg` and `CorridorKey 2.0.app`
  - Optimizations: Apple Silicon Metal MPS acceleration, hardened runtime.
* **Windows 10/11 x64:**
  - Runner: `windows-latest`
  - Target: `x86_64-pc-windows-msvc`
  - Output: `CorridorKey_2.0.0_x64-setup.exe` (NSIS) and MSI package.
  - Optimizations: NVIDIA CUDA and NVENC hardware video pipelines.

---

## 2. Local Manual Build Commands

### macOS Local Build:
```bash
# Frontend build
npm --prefix apps/desktop run build

# Tauri desktop bundle
cd apps/desktop
npm run tauri build
```

### Windows Local Build:
```powershell
# Frontend build
npm --prefix apps/desktop run build

# Tauri desktop installer (NSIS)
cd apps/desktop
npm run tauri build -- --bundles nsis
```

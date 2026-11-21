# CorridorKey 2.0 Desktop — Managed Python Runtime Packaging

## 1. Overview & Isolation Architecture

CorridorKey 2.0 Desktop relies on an AI inference engine powered by Python 3.11, PyTorch (with Apple Metal MPS or NVIDIA CUDA support), and specialized computer vision packages.

To ensure end users are not required to install Python, configure pip, or resolve system dependency conflicts, CorridorKey 2.0 employs a **Managed Python Runtime Subsystem** (`engine/packaging/python_runtime.py`).

```
System Python (Untouched)
       |
       x  (Isolated Boundary)
       |
User Application Data Directory:
  macOS:   ~/Library/Application Support/CorridorKey/python_runtime/
  Windows: %LocalAppData%\CorridorKey\python_runtime\
       |
       +---> bin/python3 (or Scripts/python.exe)
       +---> lib/site-packages/ (Torch 2.15.0, Safetensors, HuggingFace Hub)
```

---

## 2. Runtime Discovery Sequence

When the desktop application launches, the Rust backend and Python runtime manager probe candidate interpreters in the following deterministic sequence:

1. **Active Environment:** If running in an active virtualenv (e.g. during development), prioritize `sys.executable`.
2. **Managed User Runtime:** Checks for the isolated runtime inside the user's application data directory.
3. **Bundled Standalone Runtime:** If distributed as a self-contained bundle (e.g. `cpython-portable`), checks `embedded_python/`.
4. **Project Local Virtualenv:** Checks `.venv` and `venv` directories in the application root.

---

## 3. Hardware Acceleration Resolution

During interpreter probing, a non-blocking diagnostic execution inspects hardware backend capabilities:
- **macOS Apple Silicon:** Validates `torch.backends.mps.is_available()`. Yields `mps` backend utilizing unified memory.
- **Windows 10/11:** Validates `torch.cuda.is_available()`. Yields `cuda` backend utilizing NVIDIA Tensor Cores.
- **CPU Fallback:** If hardware acceleration is absent or disabled, transparently falls back to optimized CPU threads.

---

## 4. Bootstrapping & Auto-Repair

If no valid PyTorch environment is detected:
1. The First-Run Setup Wizard prompts the user.
2. `PythonRuntimeManager.bootstrap_virtualenv()` creates a dedicated virtualenv in the user application data directory.
3. Pinned requirements are installed cleanly without administrator/root privileges.
4. Health-check pings verify JSON-RPC IPC responsiveness before inference jobs are allowed to start.

# CorridorKey 2.0 Desktop — First-Run Setup Wizard

## 1. Purpose & User Experience

The **First-Run Setup Wizard** (`FirstRunWizard.tsx`) ensures that every new user has a seamless, turnkey onboarding experience without having to understand terminal commands, PyTorch environments, or model weight directories.

It automatically launches on first run (detected via `.first_run_done` marker) or can be triggered at any time from **Help > Initial Setup Wizard...**.

---

## 2. Five-Step Wizard Flow

1. **Welcome Screen:**
   - Introduces CorridorKey 2.0 Desktop and summarizes configured components.
2. **Hardware & System Compatibility:**
   - Scans CPU, RAM, OS, and GPU.
   - Validates active hardware acceleration (Apple Metal MPS or NVIDIA CUDA).
3. **Managed Python & PyTorch Runtime:**
   - Confirms isolated execution environment inside user application data.
   - Verifies PyTorch acceleration and JSON-RPC IPC handshake.
4. **AI Models & Licensing Compliance:**
   - Displays required model weights (CorridorKey v2, C-RADIO, MoGe-2, RVM).
   - Validates on-disk presence and clarifies upstream license terms.
5. **FFmpeg & Codec Engine Ready:**
   - Validates FFmpeg and FFprobe availability.
   - Verifies ProRes 4444, VP9 alpha, and PNG sequence rendering capabilities.
   - Marks setup complete and transitions to the main editing workspace.

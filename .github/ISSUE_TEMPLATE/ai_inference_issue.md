---
name: AI Inference Issue
about: Report a problem with model loading, matting quality, CUDA/MPS acceleration, or GPU memory
title: '[AI] '
labels: ['ai-engine', 'model', 'gpu']
assignees: ''
---

**AI Subsystem Problem**
- [ ] Model weights download failure / checksum mismatch
- [ ] GPU out of memory (VRAM spike)
- [ ] Apple Silicon Metal (MPS) fallback failure
- [ ] NVIDIA CUDA backend not detected
- [ ] Alpha matte flickering or missing frames
- [ ] Green spill bleeding / edge fringing

**Hardware & Model Details:**
- **OS & Architecture:** [e.g. macOS 14.5 arm64 / Windows 11 x64]
- **GPU Model:** [e.g. NVIDIA RTX 5060 8GB / Apple M2 Pro]
- **PyTorch Version:** [from Diagnostics panel]
- **Model Download Status:** [e.g. all present / missing cradio]

**Steps to Reproduce:**
1. Import test plate at resolution: [e.g. 1920x1080 or 3840x2160]
2. Enable keying with settings: [...]
3. Observe artifact / crash.

**Relevant Engine Logs:**
```text
[Paste relevant logs from Help > System Diagnostics & Logs]
```

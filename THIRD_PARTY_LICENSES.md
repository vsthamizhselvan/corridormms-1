# CorridorKey 2.0 Desktop — Third-Party Licenses and Notices

CorridorKey 2.0 Desktop integrates and builds upon several open-source libraries, models, and tools. Each component remains under the license granted by its original copyright holders.

---

## 1. AI Foundation Models

### C-RADIOv4-SO400M
* **Publisher:** NVIDIA Corporation
* **Source:** https://huggingface.co/nvidia/C-RADIOv4-SO400M
* **License:** [NVIDIA Open Model License Agreement](https://developer.download.nvidia.com/licenses/nvidia-open-model-license-agreement-june-2024.pdf)
* **Usage:** Frozen visual feature extractor. Model weights downloaded on demand to `vfms/cradio/`.

### MoGe-2 ViT-B
* **Publisher:** Microsoft Corporation
* **Source:** https://github.com/microsoft/MoGe / https://huggingface.co/Ruicheng/moge-2-vitb-normal
* **License:** MIT License
* **Usage:** Monocular geometry & surface normal feature extractor. Model code vendored in `third_party/MoGe/`; weights downloaded to `vfms/moge/`.
* **Included Components:** DINOv2 (Meta Platforms, Inc., Apache License 2.0).

### Recurrent Video MAE (RVM)
* **Publisher:** Google DeepMind
* **Source:** https://github.com/google-deepmind/representations4d
* **License:** Apache License 2.0 (code), Creative Commons Attribution 4.0 (weights)
* **Usage:** Temporal recurrent video feature extractor. Checkpoint fetched to `vfms/rvm/`.

---

## 2. Core Desktop & Native Frameworks

### Tauri 2
* **Copyright:** The Tauri Programme in The Commons Conservancy
* **License:** MIT License or Apache License 2.0
* **Usage:** Desktop application window management, native system integration, and IPC.

### PyTorch
* **Copyright:** Facebook, Inc. and its affiliates / PyTorch Contributors
* **License:** BSD-3-Clause License
* **Usage:** Deep learning tensor execution on Apple Metal (MPS) and NVIDIA CUDA backends.

### FFmpeg / FFprobe
* **Copyright:** FFmpeg developers (https://ffmpeg.org)
* **License:** GNU Lesser General Public License (LGPL) version 2.1+ or GNU General Public License (GPL) version 2+
* **Usage:** Video decoding, frame extraction, and ProRes 4444 / VP9 / PNG sequence rendering.
* **Compliance Note:** FFmpeg is invoked as an external subprocess or linked dynamically. Source code and build configurations are publicly available at https://ffmpeg.org.

---

## 3. Frontend & UI Libraries

### React & React DOM
* **Copyright:** Meta Platforms, Inc. and affiliates
* **License:** MIT License

### Tailwind CSS
* **Copyright:** Tailwind Labs, Inc.
* **License:** MIT License

### Lucide React
* **Copyright:** Lucide Contributors
* **License:** ISC License

### Zustand
* **Copyright:** Paul Henschel and Zustand Contributors
* **License:** MIT License

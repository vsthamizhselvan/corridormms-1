# CorridorKey 2.0 Desktop — Open-Source Compliance & Licensing

## 1. Primary License

CorridorKey 2.0 Desktop is distributed under the **Corridor Key Licence Version 2.0** based on the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International Public License (CC BY-NC-SA 4.0) with additional terms from Corridor Digital LLC:
* **User Content Ownership:** All media processed or rendered using CorridorKey 2.0 belongs completely to the user with full commercial rights.
* **No Closed Repackaging / Sale:** The software, code, and model weights cannot be sold as a closed proprietary product.
* **Derivatives Freely Accessible:** Derivative works must be made freely accessible to the public.
* **Enterprise Licensing:** Organizations exceeding $20,000,000 gross annual revenue require a commercial seat license from Corridor Digital LLC.

---

## 2. Foundation Model Compliance

The application strictly honors third-party foundation model terms:
* **C-RADIOv4-SO400M:** NVIDIA Open Model License (NVIDIA Corporation).
* **MoGe-2 ViT-B:** MIT License (Microsoft Corporation) and DINOv2 Apache 2.0 (Meta Platforms, Inc.).
* **RVM:** Creative Commons Attribution 4.0 (Google DeepMind).

Weights are retrieved dynamically at user request and verified via checksums, never redistributed illegally in prepackaged binary installer installers.

---

## 3. Subprocess & Library Compliance

* **FFmpeg:** Invoked as an external binary executable under LGPL v2.1+ / GPL v2+. No static proprietary linkage is performed.
* **Tauri 2:** Dual-licensed under MIT and Apache 2.0.
* **PyTorch:** Licensed under BSD-3-Clause.

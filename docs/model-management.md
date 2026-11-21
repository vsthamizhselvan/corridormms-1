# CorridorKey 2.0 Desktop — AI Model Management & Integrity

## 1. Overview & Compliance Principles

CorridorKey 2.0 uses a transformer-native two-stage matting architecture combining custom CorridorKey weights with three foundation models:
1. **CorridorKey v2 Primary Weights & Foundation Stats** (Corridor Digital LLC)
2. **C-RADIOv4-SO400M Visual Backbone** (NVIDIA Corporation)
3. **MoGe-2 ViT-B Geometry Extractor** (Microsoft Corporation)
4. **Recurrent Video MAE (RVM)** (Google DeepMind)

Under the **Corridor Key Licence v2.0** and upstream third-party terms, model weights must **not** be baked directly into closed, redistributable binary installers for resale. Instead, the application downloads and validates model weights directly from authorized publishers to the user's local workstation.

---

## 2. Model Catalog Specification

| Asset ID | Target Subdirectory | Publisher | Upstream Source | Verification | Size (MB) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `corridorkey_v2` | `weights/corridorkey_v2.safetensors` | Corridor Digital | HF: `nikopueringer/CorridorKey2.0` | Non-empty file | 420 MB |
| `foundation_stats`| `weights/foundation_stats.safetensors`| Corridor Digital | HF: `nikopueringer/CorridorKey2.0` | Non-empty file | 1.5 MB |
| `cradio` | `vfms/cradio/C-RADIOv4-SO400M` | NVIDIA Corp | HF: `nvidia/C-RADIOv4-SO400M@c0457f5` | Snapshot directory | 1,700 MB |
| `moge` | `vfms/moge/model.pt` | Microsoft | HF: `Ruicheng/moge-2-vitb-normal@ca5f0e0`| Non-empty file | 350 MB |
| `rvm` | `vfms/rvm/pretrain_rvm_small16...` | Google DeepMind | GCS: `representations4d/checkpoints` | MD5 Checksum | 145 MB |

---

## 3. Integrity Verification & Resumable Downloads

The `ModelDownloader` (`engine/packaging/model_downloader.py`) implements:
* **Resume Support:** Interrupted network transfers resume from the existing `.part` file using HTTP `Range` headers.
* **Atomic Installation:** Files are downloaded to `.part` buffers and verified via MD5/SHA-256 before being atomically swapped into place.
* **Corruption Recovery:** If an asset fails verification or has 0 bytes, it is safely purged and re-fetched without corrupting the broader environment.

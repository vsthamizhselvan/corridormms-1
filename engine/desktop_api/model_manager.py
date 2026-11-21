"""CorridorKey 2.0 Desktop — Model Asset & Memory Manager.

Verifies, loads, caches, and inspects CorridorKey v2 model weights and
third-party foundation models (C-RADIO, MoGe-2, RVM).
"""

from __future__ import annotations

import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
VENDOR_ROOT = PROJECT_ROOT / "vendor" / "CorridorKey2.0"

# Add vendor root to path so corridorkey package can be imported
if str(VENDOR_ROOT) not in sys.path:
    sys.path.insert(0, str(VENDOR_ROOT))


@dataclass
class ModelAssetInfo:
    name: str
    path: str
    exists: bool
    size_mb: float
    required: bool = True


@dataclass
class ModelStatusReport:
    model_name: str
    is_loaded: bool
    active_device: Optional[str]
    all_assets_present: bool
    total_size_gb: float
    assets: Dict[str, ModelAssetInfo]
    load_error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["assets"] = {k: asdict(v) for k, v in self.assets.items()}
        return d


class ModelManager:
    _instance: Optional["ModelManager"] = None

    def __init__(self, package_root: Path = VENDOR_ROOT):
        self.package_root = Path(package_root).resolve()
        self.weights_dir = self.package_root / "weights"
        self.vfms_dir = self.package_root / "vfms"
        self.model_instance: Any = None
        self.active_device: Optional[str] = None
        self.last_error: Optional[str] = None

    @classmethod
    def get_instance(cls) -> "ModelManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def check_assets(self) -> ModelStatusReport:
        assets_spec = {
            "corridorkey_v2": self.weights_dir / "corridorkey_v2.safetensors",
            "foundation_stats": self.weights_dir / "foundation_stats.safetensors",
            "rvm": self.vfms_dir / "rvm" / "pretrain_rvm_small16_256_204031069.npz",
            "moge": self.vfms_dir / "moge" / "model.pt",
            "cradio": self.vfms_dir / "cradio" / "C-RADIOv4-SO400M",
        }

        total_bytes = 0
        all_present = True
        asset_info_map: Dict[str, ModelAssetInfo] = {}

        for name, p in assets_spec.items():
            exists = p.exists()
            size = p.stat().st_size if exists and p.is_file() else 0
            if exists and p.is_dir():
                # Directory size sum
                size = sum(f.stat().st_size for f in p.rglob("*") if f.is_file())

            total_bytes += size
            if not exists:
                all_present = False

            asset_info_map[name] = ModelAssetInfo(
                name=name,
                path=str(p.relative_to(PROJECT_ROOT) if p.is_relative_to(PROJECT_ROOT) else p),
                exists=exists,
                size_mb=round(size / (1024 * 1024), 2),
            )

        return ModelStatusReport(
            model_name="CorridorKey 2.0 (Transformer-Native Two-Stage)",
            is_loaded=self.model_instance is not None,
            active_device=self.active_device,
            all_assets_present=all_present,
            total_size_gb=round(total_bytes / (1024 * 1024 * 1024), 2),
            assets=asset_info_map,
            load_error=self.last_error,
        )

    def load_model(self, target_device: str = "auto") -> tuple[bool, str]:
        """Loads CorridorKey v2 into memory and caches it."""
        if self.model_instance is not None and (target_device == "auto" or target_device == self.active_device):
            return True, f"Model is already loaded on {self.active_device}"

        status = self.check_assets()
        if not status.all_assets_present:
            missing = [k for k, v in status.assets.items() if not v.exists]
            err = f"Missing model assets: {', '.join(missing)}. Run `python vendor/CorridorKey2.0/scripts/download_weights.py`."
            self.last_error = err
            return False, err

        try:
            import torch
            from corridorkey.runtime import RuntimePaths, load_model

            # Determine device
            if target_device == "auto":
                if torch.cuda.is_available():
                    device = "cuda"
                elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                    device = "mps"
                else:
                    device = "cpu"
            else:
                device = target_device

            paths = RuntimePaths.from_package(self.package_root)
            paths.validate()

            # Load model
            print(f"[ModelManager] Loading CorridorKey v2 onto device={device}...", file=sys.stderr)
            self.model_instance = load_model(paths, device=device)
            self.active_device = device
            self.last_error = None
            return True, f"CorridorKey 2.0 successfully loaded on {device}"

        except Exception as e:
            err_msg = f"Model load failed: {str(e)}"
            self.last_error = err_msg
            self.model_instance = None
            self.active_device = None
            return False, err_msg

    def unload_model(self) -> None:
        """Frees model instance and clears GPU/MPS memory cache."""
        if self.model_instance is not None:
            del self.model_instance
            self.model_instance = None
            self.active_device = None

            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                elif hasattr(torch.mps, "empty_cache"):
                    torch.mps.empty_cache()
            except Exception:
                pass

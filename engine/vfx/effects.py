"""CorridorKey 2.0 Desktop — Modular VFX Effect Stack & Implementations.

Defines the BaseVFXEffect interface and 10 production-quality effect implementations:
1. Gaussian Blur
2. Sharpen
3. Glow
4. Drop Shadow
5. Gaussian Noise
6. Film Grain
7. Vignette
8. Hue/Saturation
9. Colour Correction
10. Chroma Spill Suppression
"""

from __future__ import annotations

import copy
import math
import uuid
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Type

import cv2
import numpy as np


class BaseVFXEffect(ABC):
    """Abstract base class for all non-destructive image effects."""

    effect_type: str = "base"

    def __init__(
        self,
        effect_id: Optional[str] = None,
        name: Optional[str] = None,
        enabled: bool = True,
        order_index: int = 0,
        parameters: Optional[Dict[str, Any]] = None,
    ):
        self.effect_id = effect_id or f"eff-{uuid.uuid4().hex[:8]}"
        self.name = name or self.default_name()
        self.enabled = enabled
        self.order_index = order_index
        self.parameters = self.default_parameters()
        if parameters:
            self.parameters.update(parameters)

    @abstractmethod
    def default_name(self) -> str:
        pass

    @abstractmethod
    def default_parameters(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def apply(self, rgba: np.ndarray) -> np.ndarray:
        """Applies effect to float32 RGBA image in [0.0, 1.0]."""
        pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            "effect_id": self.effect_id,
            "effect_type": self.effect_type,
            "name": self.name,
            "enabled": self.enabled,
            "order_index": self.order_index,
            "parameters": copy.deepcopy(self.parameters),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "BaseVFXEffect":
        return cls(
            effect_id=d.get("effect_id"),
            name=d.get("name"),
            enabled=bool(d.get("enabled", True)),
            order_index=int(d.get("order_index", 0)),
            parameters=d.get("parameters", {}),
        )


# -------------------------------------------------------------
# 1. Gaussian Blur
# -------------------------------------------------------------
class GaussianBlurEffect(BaseVFXEffect):
    effect_type = "gaussian_blur"

    def default_name(self) -> str:
        return "Gaussian Blur"

    def default_parameters(self) -> Dict[str, Any]:
        return {"radius": 10.0}  # pixels

    def apply(self, rgba: np.ndarray) -> np.ndarray:
        if not self.enabled:
            return rgba
        radius = float(self.parameters.get("radius", 10.0))
        if radius < 0.5:
            return rgba

        ksize = int(round(radius * 2.5)) * 2 + 1
        sigma = radius / 2.0
        return cv2.GaussianBlur(rgba, (ksize, ksize), sigmaX=sigma, sigmaY=sigma)


# -------------------------------------------------------------
# 2. Sharpen
# -------------------------------------------------------------
class SharpenEffect(BaseVFXEffect):
    effect_type = "sharpen"

    def default_name(self) -> str:
        return "Sharpen"

    def default_parameters(self) -> Dict[str, Any]:
        return {"strength": 1.0, "radius": 1.5}

    def apply(self, rgba: np.ndarray) -> np.ndarray:
        if not self.enabled:
            return rgba
        strength = float(self.parameters.get("strength", 1.0))
        radius = float(self.parameters.get("radius", 1.5))
        if strength <= 0.01:
            return rgba

        ksize = int(round(radius * 2)) * 2 + 1
        blurred = cv2.GaussianBlur(rgba, (ksize, ksize), sigmaX=radius)
        # Unsharp mask formula: img + strength * (img - blurred)
        sharpened = rgba + strength * (rgba - blurred)
        return np.clip(sharpened, 0.0, 1.0)


# -------------------------------------------------------------
# 3. Glow
# -------------------------------------------------------------
class GlowEffect(BaseVFXEffect):
    effect_type = "glow"

    def default_name(self) -> str:
        return "Glow"

    def default_parameters(self) -> Dict[str, Any]:
        return {
            "threshold": 0.6,  # 0.0 to 1.0
            "radius": 20.0,  # pixels
            "intensity": 1.0,  # 0.0 to 3.0
            "color_tint": [1.0, 1.0, 1.0],  # RGB multiplier
        }

    def apply(self, rgba: np.ndarray) -> np.ndarray:
        if not self.enabled:
            return rgba
        th = float(self.parameters.get("threshold", 0.6))
        radius = float(self.parameters.get("radius", 20.0))
        intensity = float(self.parameters.get("intensity", 1.0))
        tint = np.array(self.parameters.get("color_tint", [1.0, 1.0, 1.0]), dtype=np.float32)

        rgb = rgba[:, :, :3]
        alpha = rgba[:, :, 3:4] if rgba.shape[2] == 4 else None

        # Extract highlights above threshold
        luma = 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]
        highlight_mask = np.clip((luma - th) / (1.0 - th + 1e-5), 0.0, 1.0)[:, :, np.newaxis]
        highlights = rgb * highlight_mask

        # Blur highlights
        ksize = int(round(radius * 2.5)) * 2 + 1
        glow_layer = cv2.GaussianBlur(highlights, (ksize, ksize), sigmaX=radius / 2.0)
        glow_layer = glow_layer * tint * intensity

        # Screen blend glow onto original
        screened_rgb = 1.0 - (1.0 - rgb) * (1.0 - np.clip(glow_layer, 0.0, 1.0))
        if alpha is not None:
            return np.concatenate([screened_rgb, alpha], axis=2)
        return screened_rgb


# -------------------------------------------------------------
# 4. Drop Shadow
# -------------------------------------------------------------
class DropShadowEffect(BaseVFXEffect):
    effect_type = "drop_shadow"

    def default_name(self) -> str:
        return "Drop Shadow"

    def default_parameters(self) -> Dict[str, Any]:
        return {
            "distance": 15.0,  # pixels
            "angle": 45.0,  # degrees
            "blur": 10.0,  # pixels
            "opacity": 0.75,  # 0.0 to 1.0
            "shadow_color": [0.0, 0.0, 0.0],  # RGB
        }

    def apply(self, rgba: np.ndarray) -> np.ndarray:
        if not self.enabled or rgba.shape[2] != 4:
            return rgba

        dist = float(self.parameters.get("distance", 15.0))
        angle_rad = math.radians(float(self.parameters.get("angle", 45.0)))
        blur = float(self.parameters.get("blur", 10.0))
        opacity = float(self.parameters.get("opacity", 0.75))
        color = np.array(self.parameters.get("shadow_color", [0.0, 0.0, 0.0]), dtype=np.float32)

        h, w = rgba.shape[:2]
        dx = int(round(dist * math.cos(angle_rad)))
        dy = int(round(dist * math.sin(angle_rad)))

        # Shift alpha to create shadow matte
        shadow_matte = np.zeros((h, w), dtype=np.float32)
        src_alpha = rgba[:, :, 3]

        # Translate
        y1_src, y2_src = max(0, -dy), min(h, h - dy)
        x1_src, x2_src = max(0, -dx), min(w, w - dx)
        y1_dst, y2_dst = max(0, dy), min(h, h + dy)
        x1_dst, x2_dst = max(0, dx), min(w, w + dx)

        if y2_dst > y1_dst and x2_dst > x1_dst:
            shadow_matte[y1_dst:y2_dst, x1_dst:x2_dst] = src_alpha[y1_src:y2_src, x1_src:x2_src]

        # Blur shadow
        if blur > 0.5:
            ksize = int(round(blur * 2.5)) * 2 + 1
            shadow_matte = cv2.GaussianBlur(shadow_matte, (ksize, ksize), sigmaX=blur / 2.0)

        shadow_matte = shadow_matte * opacity

        # Composite foreground over shadow
        fg_rgb = rgba[:, :, :3]
        fg_a = rgba[:, :, 3:4]
        sh_a = shadow_matte[:, :, np.newaxis]
        sh_rgb = np.zeros_like(fg_rgb) + color

        # Over formula: FG over Shadow
        out_a = fg_a + sh_a * (1.0 - fg_a)
        out_rgb = np.where(out_a > 1e-5, (fg_rgb * fg_a + sh_rgb * sh_a * (1.0 - fg_a)) / np.maximum(out_a, 1e-5), 0.0)

        return np.concatenate([np.clip(out_rgb, 0.0, 1.0), np.clip(out_a, 0.0, 1.0)], axis=2)


# -------------------------------------------------------------
# 5. Gaussian Noise
# -------------------------------------------------------------
class GaussianNoiseEffect(BaseVFXEffect):
    effect_type = "gaussian_noise"

    def default_name(self) -> str:
        return "Gaussian Noise"

    def default_parameters(self) -> Dict[str, Any]:
        return {"amount": 0.05, "monochromatic": True}

    def apply(self, rgba: np.ndarray) -> np.ndarray:
        if not self.enabled:
            return rgba
        amount = float(self.parameters.get("amount", 0.05))
        mono = bool(self.parameters.get("monochromatic", True))
        if amount <= 0.001:
            return rgba

        h, w = rgba.shape[:2]
        if mono:
            noise = np.random.normal(0.0, amount, (h, w, 1)).astype(np.float32)
            noise_rgb = np.repeat(noise, 3, axis=2)
        else:
            noise_rgb = np.random.normal(0.0, amount, (h, w, 3)).astype(np.float32)

        out = rgba.copy()
        out[:, :, :3] = np.clip(out[:, :, :3] + noise_rgb, 0.0, 1.0)
        return out


# -------------------------------------------------------------
# 6. Film Grain
# -------------------------------------------------------------
class FilmGrainEffect(BaseVFXEffect):
    effect_type = "film_grain"

    def default_name(self) -> str:
        return "Film Grain"

    def default_parameters(self) -> Dict[str, Any]:
        return {"intensity": 0.08, "size": 1.5, "roughness": 0.5}

    def apply(self, rgba: np.ndarray) -> np.ndarray:
        if not self.enabled:
            return rgba
        intensity = float(self.parameters.get("intensity", 0.08))
        size = max(1.0, float(self.parameters.get("size", 1.5)))
        if intensity <= 0.001:
            return rgba

        h, w = rgba.shape[:2]
        # Low-res noise upscaled creates natural film grain clumps
        nw, nh = max(2, int(w / size)), max(2, int(h / size))
        small_noise = np.random.normal(0.0, intensity, (nh, nw, 1)).astype(np.float32)
        grain = cv2.resize(small_noise, (w, h), interpolation=cv2.INTER_LINEAR)[:, :, np.newaxis]

        # Grain is more pronounced in midtones than deep blacks or blown whites
        luma = 0.2126 * rgba[:, :, 0] + 0.7152 * rgba[:, :, 1] + 0.0722 * rgba[:, :, 2]
        grain_envelope = (1.0 - 4.0 * (luma - 0.5) ** 2)[:, :, np.newaxis]
        grain_envelope = np.clip(grain_envelope, 0.2, 1.0)

        out = rgba.copy()
        out[:, :, :3] = np.clip(out[:, :, :3] + grain * grain_envelope, 0.0, 1.0)
        return out


# -------------------------------------------------------------
# 7. Vignette
# -------------------------------------------------------------
class VignetteEffect(BaseVFXEffect):
    effect_type = "vignette"

    def default_name(self) -> str:
        return "Vignette"

    def default_parameters(self) -> Dict[str, Any]:
        return {
            "amount": 0.5,  # 0.0 (none) to 1.0 (black edges)
            "radius": 0.75,  # normalized radius
            "softness": 0.4,  # transition width
        }

    def apply(self, rgba: np.ndarray) -> np.ndarray:
        if not self.enabled:
            return rgba
        amount = float(self.parameters.get("amount", 0.5))
        radius = float(self.parameters.get("radius", 0.75))
        softness = max(0.01, float(self.parameters.get("softness", 0.4)))
        if amount <= 0.001:
            return rgba

        h, w = rgba.shape[:2]
        y, x = np.ogrid[:h, :w]
        # Normalized distance from center [-1.0, 1.0]
        nx = (x - w / 2.0) / (w / 2.0)
        ny = (y - h / 2.0) / (h / 2.0)
        dist = np.sqrt(nx * nx + ny * ny)

        # Smooth falloff mask
        vignette_mask = np.clip((dist - radius) / softness, 0.0, 1.0)
        factor = 1.0 - (vignette_mask * amount)[:, :, np.newaxis]

        out = rgba.copy()
        out[:, :, :3] = np.clip(out[:, :, :3] * factor, 0.0, 1.0)
        return out


# -------------------------------------------------------------
# 8. Hue / Saturation
# -------------------------------------------------------------
class HueSaturationEffect(BaseVFXEffect):
    effect_type = "hue_saturation"

    def default_name(self) -> str:
        return "Hue / Saturation"

    def default_parameters(self) -> Dict[str, Any]:
        return {
            "hue_shift": 0.0,  # -180 to +180 degrees
            "saturation": 1.0,  # 0.0 to 2.5
            "lightness": 0.0,  # -1.0 to 1.0
        }

    def apply(self, rgba: np.ndarray) -> np.ndarray:
        if not self.enabled:
            return rgba
        hue_shift = float(self.parameters.get("hue_shift", 0.0))
        sat = float(self.parameters.get("saturation", 1.0))
        light = float(self.parameters.get("lightness", 0.0))

        # Convert to HSV (OpenCV expects uint8 or float32 HSV)
        rgb_uint8 = (np.clip(rgba[:, :, :3], 0.0, 1.0) * 255.0).astype(np.uint8)
        hsv = cv2.cvtColor(rgb_uint8, cv2.COLOR_RGB2HSV).astype(np.float32)

        # H is [0, 180] in OpenCV uint8
        if abs(hue_shift) > 0.1:
            hsv[:, :, 0] = (hsv[:, :, 0] + (hue_shift / 2.0)) % 180.0

        if abs(sat - 1.0) > 0.01:
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * sat, 0.0, 255.0)

        if abs(light) > 0.01:
            hsv[:, :, 2] = np.clip(hsv[:, :, 2] + light * 255.0, 0.0, 255.0)

        rgb_mod = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB).astype(np.float32) / 255.0
        out = rgba.copy()
        out[:, :, :3] = rgb_mod
        return out


# -------------------------------------------------------------
# 9. Colour Correction
# -------------------------------------------------------------
class ColorCorrectionEffect(BaseVFXEffect):
    effect_type = "color_correction"

    def default_name(self) -> str:
        return "Color Correction"

    def default_parameters(self) -> Dict[str, Any]:
        return {
            "exposure": 0.0,  # EV
            "contrast": 1.0,
            "saturation": 1.0,
            "temperature": 0.0,
        }

    def apply(self, rgba: np.ndarray) -> np.ndarray:
        if not self.enabled:
            return rgba
        from engine.vfx.color_grade import ColorGradeSettings, apply_color_grade
        settings = ColorGradeSettings(
            exposure=float(self.parameters.get("exposure", 0.0)),
            contrast=float(self.parameters.get("contrast", 1.0)),
            saturation=float(self.parameters.get("saturation", 1.0)),
            temperature=float(self.parameters.get("temperature", 0.0)),
        )
        return apply_color_grade(rgba, settings)


# -------------------------------------------------------------
# 10. Chroma Spill Suppression
# -------------------------------------------------------------
class ChromaSpillSuppressionEffect(BaseVFXEffect):
    effect_type = "spill_suppression"

    def default_name(self) -> str:
        return "Spill Suppression"

    def default_parameters(self) -> Dict[str, Any]:
        return {
            "spill_type": "green",  # "green" | "blue"
            "strength": 0.8,
        }

    def apply(self, rgba: np.ndarray) -> np.ndarray:
        if not self.enabled:
            return rgba
        spill_type = self.parameters.get("spill_type", "green")
        strength = float(self.parameters.get("strength", 0.8))
        if strength <= 0.01:
            return rgba

        out = rgba.copy()
        r = out[:, :, 0]
        g = out[:, :, 1]
        b = out[:, :, 2]

        if spill_type == "green":
            max_rb = np.maximum(r, b)
            excess = np.maximum(0.0, g - max_rb) * strength
            out[:, :, 1] = np.clip(g - excess, 0.0, 1.0)
        elif spill_type == "blue":
            max_rg = np.maximum(r, g)
            excess = np.maximum(0.0, b - max_rg) * strength
            out[:, :, 2] = np.clip(b - excess, 0.0, 1.0)

        return out


# -------------------------------------------------------------
# Effect Registry and Stack Manager
# -------------------------------------------------------------
EFFECT_REGISTRY: Dict[str, Type[BaseVFXEffect]] = {
    "gaussian_blur": GaussianBlurEffect,
    "sharpen": SharpenEffect,
    "glow": GlowEffect,
    "drop_shadow": DropShadowEffect,
    "gaussian_noise": GaussianNoiseEffect,
    "film_grain": FilmGrainEffect,
    "vignette": VignetteEffect,
    "hue_saturation": HueSaturationEffect,
    "color_correction": ColorCorrectionEffect,
    "spill_suppression": ChromaSpillSuppressionEffect,
}


class EffectStack:
    """Manages an ordered stack of VFX effects."""

    def __init__(self, effects: Optional[List[BaseVFXEffect]] = None):
        self.effects: List[BaseVFXEffect] = effects or []

    def add_effect(self, effect: BaseVFXEffect) -> BaseVFXEffect:
        effect.order_index = len(self.effects)
        self.effects.append(effect)
        return effect

    def remove_effect(self, effect_id: str) -> Optional[BaseVFXEffect]:
        for i, eff in enumerate(self.effects):
            if eff.effect_id == effect_id:
                removed = self.effects.pop(i)
                self._reindex()
                return removed
        return None

    def duplicate_effect(self, effect_id: str) -> Optional[BaseVFXEffect]:
        for eff in self.effects:
            if eff.effect_id == effect_id:
                new_dict = eff.to_dict()
                new_dict["effect_id"] = f"eff-{uuid.uuid4().hex[:8]}"
                new_dict["name"] = f"{eff.name} (Copy)"
                cls = EFFECT_REGISTRY.get(eff.effect_type, BaseVFXEffect)
                dup = cls.from_dict(new_dict)
                self.add_effect(dup)
                return dup
        return None

    def reorder_effect(self, effect_id: str, new_index: int) -> bool:
        idx = -1
        for i, eff in enumerate(self.effects):
            if eff.effect_id == effect_id:
                idx = i
                break
        if idx == -1 or new_index < 0 or new_index >= len(self.effects):
            return False

        moved = self.effects.pop(idx)
        self.effects.insert(new_index, moved)
        self._reindex()
        return True

    def process(self, rgba: np.ndarray) -> np.ndarray:
        """Processes an image sequentially through all enabled effects in the stack."""
        img = rgba.astype(np.float32).copy()
        for eff in sorted(self.effects, key=lambda e: e.order_index):
            if eff.enabled:
                img = eff.apply(img)
        return img

    def _reindex(self):
        for i, eff in enumerate(self.effects):
            eff.order_index = i

    def to_list(self) -> List[Dict[str, Any]]:
        return [eff.to_dict() for eff in self.effects]

    @classmethod
    def from_list(cls, items: List[Dict[str, Any]]) -> "EffectStack":
        effects = []
        for item in items:
            eff_type = item.get("effect_type", "")
            eff_cls = EFFECT_REGISTRY.get(eff_type)
            if eff_cls:
                effects.append(eff_cls.from_dict(item))
        return cls(effects)

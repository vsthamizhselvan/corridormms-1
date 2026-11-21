"""CorridorKey 2.0 Desktop — Advanced Alpha Matte Refinement Subsystem.

Provides non-destructive matte post-processing: choke/expand, edge feather,
alpha blur, contrast, brightness, thresholding, edge decontamination, and despill.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np


@dataclass
class MatteRefineSettings:
    contrast: float = 1.0  # 0.1 to 3.0
    brightness: float = 0.0  # -1.0 to 1.0
    edge_softness: float = 0.0  # 0.0 to 20.0 pixels
    edge_feather: float = 0.0  # 0.0 to 50.0 pixels
    choke_expand: float = 0.0  # -20.0 (choke) to +20.0 (expand) pixels
    alpha_blur: float = 0.0  # 0.0 to 30.0 pixels
    alpha_threshold: float = 0.0  # 0.0 to 1.0
    invert: bool = False
    edge_decontamination: float = 0.0  # 0.0 to 1.0
    foreground_restoration: float = 0.0  # 0.0 to 1.0
    spill_suppression: float = 0.0  # 0.0 to 1.0 (0.0 = none, 1.0 = full)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "MatteRefineSettings":
        return cls(
            contrast=float(d.get("contrast", 1.0)),
            brightness=float(d.get("brightness", 0.0)),
            edge_softness=float(d.get("edge_softness", 0.0)),
            edge_feather=float(d.get("edge_feather", 0.0)),
            choke_expand=float(d.get("choke_expand", 0.0)),
            alpha_blur=float(d.get("alpha_blur", 0.0)),
            alpha_threshold=float(d.get("alpha_threshold", 0.0)),
            invert=bool(d.get("invert", False)),
            edge_decontamination=float(d.get("edge_decontamination", 0.0)),
            foreground_restoration=float(d.get("foreground_restoration", 0.0)),
            spill_suppression=float(d.get("spill_suppression", 0.0)),
        )


def refine_alpha_matte(
    alpha: np.ndarray,
    rgb: Optional[np.ndarray] = None,
    settings: Optional[MatteRefineSettings] = None,
) -> Tuple[np.ndarray, Optional[np.ndarray]]:
    """Refines an alpha matte and optional RGB frame based on MatteRefineSettings.

    Args:
        alpha: 2D float32 array in [0.0, 1.0] (H, W).
        rgb: Optional 3D float32 array in [0.0, 1.0] (H, W, 3).
        settings: MatteRefineSettings configuration.

    Returns:
        Tuple of (refined_alpha, decontaminated_rgb).
    """
    if settings is None:
        settings = MatteRefineSettings()

    matte = alpha.astype(np.float32).copy()
    refined_rgb = rgb.astype(np.float32).copy() if rgb is not None else None

    # 1. Choke and Expand (Morphological Erosion and Dilation)
    if abs(settings.choke_expand) >= 0.5:
        radius = int(round(abs(settings.choke_expand)))
        ksize = radius * 2 + 1
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))
        if settings.choke_expand > 0:
            # Expand (Dilation)
            matte = cv2.dilate(matte, kernel)
        else:
            # Choke (Erosion)
            matte = cv2.erode(matte, kernel)

    # 2. Alpha Threshold / Pedestal
    if settings.alpha_threshold > 0.001:
        th = settings.alpha_threshold
        matte = np.clip((matte - th) / (1.0 - th + 1e-6), 0.0, 1.0)

    # 3. Brightness & Contrast
    if abs(settings.brightness) > 0.001:
        matte = np.clip(matte + settings.brightness, 0.0, 1.0)

    if abs(settings.contrast - 1.0) > 0.001:
        matte = np.clip((matte - 0.5) * settings.contrast + 0.5, 0.0, 1.0)

    # 4. Edge Softness & Feather (Gaussian Blur on transitions)
    total_blur = settings.edge_softness + settings.edge_feather + settings.alpha_blur
    if total_blur > 0.5:
        ksize = int(round(total_blur * 2.5)) * 2 + 1
        sigma = total_blur / 2.0
        matte = cv2.GaussianBlur(matte, (ksize, ksize), sigmaX=sigma, sigmaY=sigma)

    # 5. Inversion
    if settings.invert:
        matte = 1.0 - matte

    # 6. Spill Suppression & Edge Decontamination on RGB
    if refined_rgb is not None:
        # Chroma Spill Suppression (Green Screen by default)
        if settings.spill_suppression > 0.01:
            r = refined_rgb[:, :, 0]
            g = refined_rgb[:, :, 1]
            b = refined_rgb[:, :, 2]
            max_rb = np.maximum(r, b)
            spill = np.maximum(0.0, g - max_rb) * settings.spill_suppression
            refined_rgb[:, :, 1] = np.clip(g - spill, 0.0, 1.0)

        # Edge Decontamination: desaturate or blend edge pixels towards foreground core
        if settings.edge_decontamination > 0.01:
            # Detect edge mask: where alpha is between 0.1 and 0.9
            edge_mask = (matte > 0.05) & (matte < 0.95)
            if np.any(edge_mask):
                decontam_factor = settings.edge_decontamination
                # Lower saturation along semi-transparent fringe
                luma = 0.2126 * refined_rgb[:, :, 0] + 0.7152 * refined_rgb[:, :, 1] + 0.0722 * refined_rgb[:, :, 2]
                for c in range(3):
                    channel = refined_rgb[:, :, c]
                    channel[edge_mask] = (1.0 - decontam_factor) * channel[edge_mask] + decontam_factor * luma[edge_mask]

    return np.clip(matte, 0.0, 1.0), refined_rgb

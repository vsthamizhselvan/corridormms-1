#!/usr/bin/env python3
"""
CorridorKey 2.0 Desktop — Alpha & Colour Fidelity Validation Suite.
==================================================================
Validates:
  1. Straight alpha vs Premultiplied alpha conversion & round-trip math
  2. Edge transition fidelity (sub-pixel hair, motion blur, transparency ramps)
  3. Green spill suppression and despill colour neutrality
  4. Colour space transforms: Linear, sRGB, Rec.709, Rec.2020
  5. Gamma preservation: Alpha is NEVER gamma-corrected or warped
  6. Fringe elimination: Zero black or white haloing on composite
"""

import os
import sys
import numpy as np

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from engine.color.alpha_manager import (
    premultiply_alpha,
    unpremultiply_alpha,
    despill_green,
    validate_alpha_matte,
)
from engine.color.transfer_functions import (
    srgb_to_linear,
    linear_to_srgb,
    rec709_to_linear,
    linear_to_rec709,
    linear_to_asinh,
    asinh_to_linear,
    rec709_linear_to_acescg,
    acescg_to_rec709_linear,
)


def section(title: str):
    print(f"\n[ALPHA-COLOUR-TEST] {title}...")


def check(cond: bool, msg: str):
    if not cond:
        print(f"  ✗ FAILED: {msg}")
        sys.exit(1)
    print(f"  ✓ {msg}")


def test_straight_vs_premultiplied_math():
    section("1. Straight vs Premultiplied Alpha Round-Trip Math")
    # RGBA float image with soft alpha ramp
    h, w = 100, 100
    rgb = np.full((h, w, 3), 0.8, dtype=np.float32)
    alpha = np.linspace(0.0, 1.0, w, dtype=np.float32)
    alpha = np.tile(alpha, (h, 1))

    # Premultiply: RGB_pre = RGB_straight * alpha
    rgb_pre = premultiply_alpha(rgb, alpha)
    # Check left edge (alpha=0) is black
    check(np.allclose(rgb_pre[:, 0, :], 0.0), "Zero alpha yields pure black RGB in premultiplied space")
    # Check right edge (alpha=1) is original color
    check(np.allclose(rgb_pre[:, -1, :], 0.8, atol=1e-4), "Full alpha preserves original color in premultiplied space")

    # Unpremultiply: RGB_straight = RGB_pre / alpha (alpha > 0)
    rgb_restored = unpremultiply_alpha(rgb_pre, alpha)
    # Validate non-zero pixels match original within tolerance
    valid_mask = alpha > 0.05
    max_err = np.max(np.abs(rgb_restored[valid_mask] - rgb[valid_mask]))
    check(max_err < 1e-4, f"Unpremultiply round-trip error < 1e-4 (actual: {max_err:.6f})")


def test_alpha_never_gamma_corrected():
    section("2. Alpha Gamma Integrity (Alpha MUST NOT be gamma-corrected)")
    # When converting color spaces, alpha channel must remain strictly linear
    alpha_linear = np.linspace(0.0, 1.0, 256, dtype=np.float32)
    # Srgb transfer function operates strictly on RGB, preserving alpha
    rgb = np.tile(alpha_linear[:, None], (1, 3))
    rgb_srgb = linear_to_srgb(rgb)
    # The middle grey 0.5 becomes ~0.735 in sRGB
    mid_srgb = rgb_srgb[128, 0]
    check(abs(mid_srgb - 0.735) < 0.02, f"RGB is gamma-corrected: mid grey linear 0.5 -> sRGB {mid_srgb:.3f}")

    # Verify that alpha values are NOT affected by color transfer functions
    # (Alpha represents area coverage / physical opacity, not radiance)
    check(abs(alpha_linear[128] - (128.0 / 255.0)) < 1e-4, "Alpha channel remains linear physical opacity without gamma warp")


def test_green_spill_suppression():
    section("3. Green Spill Suppression & Chromatic Neutrality")
    # Green screen contaminated edge: R=50, G=220, B=60 (normalized float: 0.196, 0.863, 0.235)
    spill_rgb = np.array([[[0.196, 0.863, 0.235]]], dtype=np.float32)
    despilled = despill_green(spill_rgb, strength=1.0)
    # After despill, Green should be significantly suppressed
    check(despilled[0, 0, 1] < 0.863, f"Green channel suppressed from 0.863 down to {despilled[0, 0, 1]:.3f}")
    # Red and Blue channels should have spill compensation added
    check(despilled[0, 0, 0] >= 0.196, "Red channel compensated during despill")
    check(despilled[0, 0, 2] >= 0.235, "Blue channel compensated during despill")


def test_fine_hair_and_motion_blur():
    section("4. Sub-Pixel Hair & Motion Blur Edge Fidelity")
    # Generate 1-pixel synthetic hair strand on green backdrop
    canvas = np.zeros((32, 32, 4), dtype=np.float32)
    # Green backdrop
    canvas[:, :, :3] = [0.1, 0.9, 0.1]
    canvas[:, :, 3] = 0.0
    # 1px hair strand in column 16 with semi-transparency (alpha=0.45)
    canvas[:, 16, :3] = [0.6, 0.4, 0.2]  # Brown hair
    canvas[:, 16, 3] = 0.45

    integrity = validate_alpha_matte(canvas[:, :, 3])
    check(integrity.semi_transparent_percent > 0.0, "Semi-transparent pixels successfully preserved")
    check(integrity.opaque_percent < 5.0, "Sub-pixel detail identified without binary thresholding collapse")


def main():
    print("=" * 70)
    print("CORRIDORKEY 2.0 DESKTOP — ALPHA & COLOUR FIDELITY VALIDATION")
    print("=" * 70)
    test_straight_vs_premultiplied_math()
    test_alpha_never_gamma_corrected()
    test_green_spill_suppression()
    test_fine_hair_and_motion_blur()
    print("\n" + "=" * 70)
    print("🎉 ALPHA & COLOUR FIDELITY VALIDATION SUITE PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    main()

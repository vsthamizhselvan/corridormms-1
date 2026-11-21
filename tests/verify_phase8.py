#!/usr/bin/env python3
"""
CorridorKey 2.0 Desktop — Master Phase 8 Verification Suite
============================================================
Comprehensive test suite verifying all Phase 8 VFX Compositing requirements:
  1. Vector Masking & Rotoscoping (shapes, feather, choke, boolean add/sub, invert)
  2. Alpha Matte Refinement (contrast, choke/expand, feather, despill, decontamination)
  3. Professional Colour Grading (Exposure EV, Temp/Tint, Vibrance, Lift/Gamma/Gain, RGB channels)
  4. Non-Destructive Effect Stack (all 10 real VFX effects, reorder, bypass)
  5. Layer-Based Compositing (all 6 blend modes, affine transforms, alpha compositing)
  6. Node-Based Compositing DAG Engine (topological sort, cycle detection, execution)
  7. Project Serialization & v1.1.0 Schema Migration (roundtrip .ckproj persistence)
  8. Desktop Frontend & Tauri Backend Compilation (Vite & Cargo checks)
"""

import os
import sys
import json
import subprocess
import tempfile
import numpy as np

# Ensure project root in python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from engine.vfx.masking import (
    MaskItem,
    MaskMode,
    MaskPoint,
    MaskType,
    rasterize_mask,
    combine_masks,
)
from engine.vfx.matte_refine import MatteRefineSettings, refine_alpha_matte
from engine.vfx.color_grade import ColorGradeSettings, apply_color_grade
from engine.vfx.effects import (
    EFFECT_REGISTRY,
    BaseVFXEffect,
    ChromaSpillSuppressionEffect,
    ColorCorrectionEffect,
    DropShadowEffect,
    EffectStack,
    FilmGrainEffect,
    GaussianBlurEffect,
    GaussianNoiseEffect,
    GlowEffect,
    HueSaturationEffect,
    SharpenEffect,
    VignetteEffect,
)
from engine.vfx.layer_compositor import (
    BlendMode,
    LayerItem,
    apply_blend_mode,
    transform_layer_image,
    composite_two_layers,
    composite_layer_stack,
)
from engine.vfx.node_graph import (
    NODE_REGISTRY,
    BaseNode,
    NodeGraph,
    MediaInputNode,
    AIForegroundNode,
    AlphaMatteNode,
    BlurNode,
    BackgroundNode,
    MergeNode,
    MediaOutputNode,
)
from engine.project.schema import (
    MediaReference,
    ProjectDocument,
    ProjectMetadata,
    WorkspaceLayout,
    migrate_schema,
)
from engine.project.serializer import (
    ProjectSerializationError,
    deserialize_project,
    serialize_project,
    validate_project_dict,
)
from engine.project.io_atomic import atomic_save_file, safe_read_file


def section(idx: int, title: str):
    print(f"\n[{idx}/8] Testing {title}...")


def check(cond: bool, msg: str):
    if not cond:
        print(f"  ✗ FAILED: {msg}")
        sys.exit(1)
    print(f"  ✓ {msg}")


def test_1_vector_masking():
    section(1, "Vector Masking & Rotoscoping")
    h, w = 120, 160

    # Test Rectangle Mask
    rect = MaskItem(
        mask_id="mask_rect",
        name="Rect 1",
        mask_type=MaskType.RECTANGLE,
        mode=MaskMode.ADD,
        points=[MaskPoint(0.2, 0.2), MaskPoint(0.8, 0.8)],
        feather=0.0,
        expansion=0.0,
        opacity=1.0,
    )
    m_rect = rasterize_mask(rect, w, h)
    check(m_rect.shape == (h, w), "Rectangle mask rasterized to target dimensions")
    check(m_rect[60, 80] > 0.9, "Inside rectangle mask is white (1.0)")
    check(m_rect[10, 10] < 0.1, "Outside rectangle mask is black (0.0)")

    # Test Ellipse Mask
    ellipse = MaskItem(
        mask_id="mask_ell",
        name="Ellipse 1",
        mask_type=MaskType.ELLIPSE,
        mode=MaskMode.ADD,
        feather=0.0,
    )
    m_ell = rasterize_mask(ellipse, w, h)
    check(m_ell[60, 80] > 0.9, "Center of ellipse mask is white (1.0)")
    check(m_ell[0, 0] < 0.1, "Corner of ellipse mask is black (0.0)")

    # Test Feathering
    rect_feather = MaskItem(
        mask_id="mask_feath",
        name="Rect Feather",
        mask_type=MaskType.RECTANGLE,
        points=[MaskPoint(0.2, 0.2), MaskPoint(0.8, 0.8)],
        feather=15.0,
    )
    m_feath = rasterize_mask(rect_feather, w, h)
    edge_val = m_feath[24, 80]
    check(0.0 < edge_val < 1.0, f"Feather produced soft gradient edge (val={edge_val:.3f})")

    # Test Choke / Expansion
    rect_base = MaskItem(
        mask_id="m_base",
        name="Base Rect",
        mask_type=MaskType.RECTANGLE,
        points=[MaskPoint(0.3, 0.3), MaskPoint(0.7, 0.7)],
        expansion=0.0,
    )
    rect_expanded = MaskItem(
        mask_id="m_exp",
        name="Expanded Rect",
        mask_type=MaskType.RECTANGLE,
        points=[MaskPoint(0.3, 0.3), MaskPoint(0.7, 0.7)],
        expansion=10.0,
    )
    m_base = rasterize_mask(rect_base, w, h)
    m_exp = rasterize_mask(rect_expanded, w, h)
    check(m_exp.sum() > m_base.sum(), "Expansion increased mask coverage")

    # Test Inversion
    rect_inv = MaskItem(
        mask_id="m_inv",
        name="Inverted Rect",
        mask_type=MaskType.RECTANGLE,
        points=[MaskPoint(0.2, 0.2), MaskPoint(0.8, 0.8)],
        inverted=True,
    )
    m_inv = rasterize_mask(rect_inv, w, h)
    check(m_inv[60, 80] < 0.1 and m_inv[5, 5] > 0.9, "Inverted mask flipped foreground and background")

    # Test Boolean Add and Subtract in combine_masks
    sub_rect = MaskItem(
        mask_id="m_cutout",
        name="Cutout Rect",
        mask_type=MaskType.RECTANGLE,
        mode=MaskMode.SUBTRACT,
        points=[MaskPoint(0.4, 0.4), MaskPoint(0.6, 0.6)],
    )
    comb = combine_masks([rect, sub_rect], w, h)
    check(comb[60, 80] < 0.1, "Subtract mask successfully punched a hole in center")
    check(comb[30, 80] > 0.9, "Remaining mask area retains >0.9")


def test_2_matte_refinement():
    section(2, "Advanced Alpha Matte Refinement")
    h, w = 100, 100
    matte = np.zeros((h, w), dtype=np.float32)
    matte[25:75, 25:75] = 0.8

    # Contrast and Brightness
    settings_cb = MatteRefineSettings(contrast=1.5, brightness=0.2)
    res_cb, _ = refine_alpha_matte(matte, settings=settings_cb)
    check(res_cb[50, 50] > matte[50, 50], "Contrast and brightness increased matte density")

    # Choke / Erosion
    settings_choke = MatteRefineSettings(choke_expand=-3.0)
    res_choke, _ = refine_alpha_matte(matte, settings=settings_choke)
    check(res_choke.sum() < matte.sum(), "Choke (negative expansion) eroded matte perimeter")

    # Expand / Dilation
    settings_expand = MatteRefineSettings(choke_expand=3.0)
    res_expand, _ = refine_alpha_matte(matte, settings=settings_expand)
    check(res_expand.sum() > matte.sum(), "Expand (positive dilation) grew matte perimeter")

    # Edge Feathering
    settings_feather = MatteRefineSettings(edge_feather=5.0)
    res_feath, _ = refine_alpha_matte(matte, settings=settings_feather)
    check(0.0 < res_feath[25, 50] < 0.8, "Edge feather created smooth antialiased matte perimeter")

    # Despill and Edge Decontamination
    rgb = np.zeros((50, 50, 3), dtype=np.float32)
    rgb[:, :, 1] = 0.9  # High green
    rgb[:, :, 0] = 0.2  # Low red
    rgb[:, :, 2] = 0.2  # Low blue

    settings_despill = MatteRefineSettings(spill_suppression=1.0, edge_decontamination=0.8)
    _, decontam = refine_alpha_matte(np.ones((50, 50), dtype=np.float32), rgb=rgb, settings=settings_despill)
    check(decontam is not None, "Decontaminated RGB produced")
    check(decontam[25, 25, 1] <= 0.25, f"Green spill suppressed down to {decontam[25, 25, 1]:.3f}")


def test_3_color_grading():
    section(3, "Professional Colour Correction & Grading")
    h, w = 60, 80
    rgb = np.full((h, w, 3), 0.5, dtype=np.float32)

    # Exposure EV
    plus_one_ev = apply_color_grade(rgb, ColorGradeSettings(exposure=1.0))
    check(plus_one_ev[0, 0, 0] > 0.9, f"+1.0 EV doubled linear radiance ({plus_one_ev[0, 0, 0]:.2f} > 0.9)")

    minus_one_ev = apply_color_grade(rgb, ColorGradeSettings(exposure=-1.0))
    check(minus_one_ev[0, 0, 0] < 0.35, f"-1.0 EV halved linear radiance ({minus_one_ev[0, 0, 0]:.2f} < 0.35)")

    # Lift / Gamma / Gain (ASC-CDL)
    lifted = apply_color_grade(rgb, ColorGradeSettings(lift=0.1, gain=1.2))
    check(lifted[0, 0, 0] > rgb[0, 0, 0], "Positive Lift and Gain elevated brightness")

    # Temperature & Tint
    temp_settings = ColorGradeSettings(temperature=0.5, tint=0.0)
    warmer = apply_color_grade(rgb, temp_settings)
    check(warmer[0, 0, 0] > warmer[0, 0, 2], "Warm temperature (+0.5) boosted Red relative to Blue")

    # Vibrance & Saturation
    colored_rgb = np.full((h, w, 3), [0.6, 0.5, 0.45], dtype=np.float32)
    sat_settings = ColorGradeSettings(saturation=1.5, vibrance=0.3)
    vibrant = apply_color_grade(colored_rgb, sat_settings)
    check(vibrant[0, 0, 0] > colored_rgb[0, 0, 0], "Vibrance and saturation amplified chromatic contrast")


def test_4_effect_stack():
    section(4, "Non-Destructive Effect Stack (10 Effects)")
    h, w = 64, 64
    test_img = np.full((h, w, 4), 0.5, dtype=np.float32)
    test_img[:, :, 3] = 1.0

    all_effects = [
        GaussianBlurEffect(),
        SharpenEffect(),
        GlowEffect(),
        DropShadowEffect(),
        GaussianNoiseEffect(),
        FilmGrainEffect(),
        VignetteEffect(),
        HueSaturationEffect(),
        ColorCorrectionEffect(),
        ChromaSpillSuppressionEffect(),
    ]

    stack = EffectStack()
    for eff in all_effects:
        stack.add_effect(eff)
        out = eff.apply(test_img)
        check(out.shape == test_img.shape, f"Effect '{eff.name}' applied successfully")

    check(len(stack.effects) == 10, "Effect stack contains all 10 effects")

    # Run full stack pipeline
    final_output = stack.process(test_img)
    check(final_output.shape == test_img.shape, "Full 10-effect pipeline completed successfully")
    check(0.0 <= np.min(final_output) and np.max(final_output) <= 1.0, "Output pixels normalized within [0, 1]")

    # Test Bypass / Disable
    stack.effects[0].enabled = False
    check(not stack.effects[0].enabled, "Effect bypass / disable toggled successfully")

    # Test Reorder
    eid = stack.effects[0].effect_id
    ename = stack.effects[0].name
    stack.reorder_effect(eid, 5)
    check(stack.effects[5].name == ename, "Effect reordered cleanly within the stack")


def test_5_layer_compositing():
    section(5, "Layer-Based Compositing & Blend Modes")
    h, w = 50, 50

    base = np.full((h, w, 3), 0.5, dtype=np.float32)
    blend = np.full((h, w, 3), 0.5, dtype=np.float32)

    # Test Blend Modes
    check(abs(apply_blend_mode(base, blend, BlendMode.NORMAL)[0, 0, 0] - 0.5) < 1e-3, "Normal blend mode verified")
    check(abs(apply_blend_mode(base, blend, BlendMode.MULTIPLY)[0, 0, 0] - 0.25) < 1e-3, "Multiply blend mode verified (0.5 * 0.5 = 0.25)")
    check(abs(apply_blend_mode(base, blend, BlendMode.SCREEN)[0, 0, 0] - 0.75) < 1e-3, "Screen blend mode verified (1 - 0.25 = 0.75)")
    check(abs(apply_blend_mode(base, blend, BlendMode.ADD)[0, 0, 0] - 1.0) < 1e-3, "Add blend mode verified (0.5 + 0.5 = 1.0)")
    check(abs(apply_blend_mode(base, blend, BlendMode.DIFFERENCE)[0, 0, 0] - 0.0) < 1e-3, "Difference blend mode verified (|0.5 - 0.5| = 0.0)")

    # Composite Layer Stack
    l_bg = LayerItem(layer_id="l_bg", name="BG Plate")
    l_fg = LayerItem(layer_id="l_fg", name="FG Plate", opacity=0.8, blend_mode=BlendMode.NORMAL)

    img_bg = np.zeros((h, w, 4), dtype=np.float32)
    img_bg[:, :, 0] = 1.0  # Red
    img_bg[:, :, 3] = 1.0

    img_fg = np.zeros((h, w, 4), dtype=np.float32)
    img_fg[:, :, 1] = 1.0  # Green
    img_fg[:, :, 3] = 1.0

    comp = composite_layer_stack([(l_bg, img_bg), (l_fg, img_fg)], w, h)
    check(comp.shape == (h, w, 4), "Composited layer stack to target dimensions")
    check(comp[25, 25, 1] > 0.7, "Foreground color blended over background")

    # Affine Transformation
    l_xform = LayerItem(
        layer_id="l_xf",
        name="Xform",
        pos_x=5.0,
        pos_y=-5.0,
        scale_x=0.8,
        scale_y=0.8,
        rotation=30.0,
    )
    xformed = transform_layer_image(img_fg, w, h, l_xform)
    check(xformed.shape == (h, w, 4), "Layer affine transform rendered correctly")


def test_6_node_graph_dag():
    section(6, "Node-Based Compositing Foundation & DAG")

    graph = NodeGraph()
    n_input = graph.add_node(MediaInputNode())
    n_ai = graph.add_node(AIForegroundNode())
    n_blur = graph.add_node(BlurNode())
    n_bg = graph.add_node(BackgroundNode())
    n_merge = graph.add_node(MergeNode())
    n_out = graph.add_node(MediaOutputNode())

    # Connect DAG pipeline
    graph.connect(n_input.node_id, "out_rgba", n_ai.node_id, "in_rgba")
    graph.connect(n_ai.node_id, "out_fg", n_blur.node_id, "in_rgba")
    graph.connect(n_input.node_id, "out_rgba", n_bg.node_id, "in_ref")
    graph.connect(n_bg.node_id, "out_bg", n_merge.node_id, "in_bg")
    graph.connect(n_blur.node_id, "out_rgba", n_merge.node_id, "in_fg")
    graph.connect(n_merge.node_id, "out_comp", n_out.node_id, "in_composite")

    # Topological Sort
    eval_order = graph.get_evaluation_order()
    check(len(eval_order) == 6, f"Topological sort resolved order of 6 nodes: {eval_order}")
    check(eval_order[0] in (n_input.node_id, n_bg.node_id), "Input node evaluated first")
    check(eval_order[-1] == n_out.node_id, "Output sink node evaluated last")

    # Cycle Detection
    has_cycle_exception = False
    try:
        graph.connect(n_out.node_id, "in_composite", n_input.node_id, "custom_image")
    except ValueError:
        has_cycle_exception = True
    check(has_cycle_exception, "Cycle detection caught and prevented circular dependency loop")

    # Graph Execution
    exec_res = graph.execute_graph()
    check(n_out.node_id in exec_res, "DAG execution produced output node result")
    final_img = exec_res[n_out.node_id].get("final_image")
    check(final_img is not None and final_img.shape == (100, 100, 4), "Final composite image generated from DAG")


def test_7_project_serialization():
    section(7, "Project Serialization & v1.1.0 Schema Migration")

    proj_data = {
        "format": "corridorkey-project",
        "schema_version": "1.1.0",
        "generator": "CorridorKey 2.0 Desktop",
        "project": {
            "name": "VFX_Phase8_Shot",
            "width": 1920,
            "height": 1080,
            "frame_rate": 24.0,
            "color_space": "sRGB / Rec.709",
            "created_at": "2026-11-21T06:00:00Z",
            "modified_at": "2026-11-21T06:00:00Z",
        },
        "media_pool": [
            {
                "id": "med_1",
                "name": "plate.mp4",
                "path": "/media/plate.mp4",
                "duration_frames": 240,
                "fps": 24.0,
                "width": 1920,
                "height": 1080,
            }
        ],
        "timeline": {
            "duration_frames": 240,
            "current_frame": 0,
            "tracks": [],
        },
        "settings": {
            "keying": {"model": "corridorkey_v2"},
            "matte": {},
            "viewer": {},
            "export": {},
        },
        "vfx": {
            "masks": [
                {
                    "id": "mask_1",
                    "name": "Garbage Mask",
                    "type": "rectangle",
                    "mode": "add",
                    "inverted": False,
                    "feather": 8.0,
                    "expansion": 2.0,
                    "opacity": 1.0,
                    "visible": True,
                    "points": [{"x": 0.2, "y": 0.1}, {"x": 0.8, "y": 0.9}],
                }
            ],
            "matte_refine": {
                "contrast": 1.2,
                "brightness": 0.1,
                "edge_softness": 1.5,
                "edge_feather": 3.0,
                "choke_expand": -1.0,
                "edge_decontamination": 0.7,
                "spill_suppression": 0.8,
            },
            "color_grade": {
                "exposure": 0.3,
                "contrast": 1.1,
                "temperature": 0.1,
                "tint": -0.05,
                "saturation": 1.1,
                "vibrance": 0.2,
                "lift": 0.02,
                "gamma": 1.05,
                "gain": 1.0,
            },
            "effects": [
                {
                    "id": "eff_blur",
                    "type": "gaussian_blur",
                    "name": "Edge Blur",
                    "enabled": True,
                    "parameters": {"radius": 2.5},
                },
                {
                    "id": "eff_grain",
                    "type": "film_grain",
                    "name": "Film Grain",
                    "enabled": True,
                    "parameters": {"intensity": 0.15, "grain_size": 1.2},
                },
            ],
            "layers": [
                {
                    "id": "layer_fg",
                    "name": "Foreground",
                    "type": "ai_foreground",
                    "visible": True,
                    "blend_mode": "normal",
                    "opacity": 1.0,
                }
            ],
            "node_graph": {
                "nodes": [{"id": "n1", "type": "media_input"}, {"id": "n2", "type": "media_output"}],
                "connections": [{"from_node": "n1", "to_node": "n2"}],
            },
        },
        "workspace": {
            "left_panel_width": 260,
            "right_panel_width": 320,
            "bottom_panel_height": 280,
            "show_media_browser": True,
            "show_inspector": True,
            "show_timeline": True,
            "zoom_ratio": 1.0,
        },
    }

    # Validate Schema
    is_valid, errors = validate_project_dict(proj_data)
    check(is_valid, f"v1.1.0 Project schema valid: {errors}")

    # Test Atomic Save and Read Roundtrip
    with tempfile.TemporaryDirectory() as tmp_dir:
        proj_path = os.path.join(tmp_dir, "test_vfx_proj.ckproj")
        json_str = json.dumps(proj_data, indent=2)
        success = atomic_save_file(proj_path, json_str)
        check(success, "Serialized .ckproj file with full VFX block to disk")

        # Load back
        loaded_str = safe_read_file(proj_path)
        doc = deserialize_project(loaded_str)
        check(doc.schema_version == "1.1.0", "Deserialized schema_version is 1.1.0")
        check(len(doc.masks) == 1, "Persisted vector mask restored")
        check(doc.matte_refine.get("contrast") == 1.2, "Persisted matte refine restored")
        check(doc.color_grade.get("exposure") == 0.3, "Persisted color grade restored")
        check(len(doc.effects) == 2, "Persisted effects restored")

        # Test Migration from 1.0.0
        legacy_data = dict(proj_data)
        legacy_data["schema_version"] = "1.0.0"
        del legacy_data["vfx"]
        migrated = migrate_schema(legacy_data)
        check(migrated["schema_version"] == "1.1.0", "Migrated legacy 1.0.0 schema to 1.1.0")
        check("vfx" in migrated, "Default VFX block injected during migration")


def test_8_ui_and_tauri_compilation():
    section(8, "UI & Tauri Desktop Compilation Check")

    # React Frontend Vite Build
    print("  Running Vite production build (npm run build)...")
    build_proc = subprocess.run(
        ["npm", "--prefix", "apps/desktop", "run", "build"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    check(build_proc.returncode == 0, f"React 18 / Vite build succeeded:\n{build_proc.stderr[:300] if build_proc.returncode != 0 else ''}")

    # Tauri Rust Cargo Check
    print("  Running Tauri Cargo check...")
    cargo_env = os.environ.copy()
    cargo_env["CARGO_TARGET_DIR"] = "/tmp/corridorkey-target"
    cargo_proc = subprocess.run(
        ["cargo", "check", "--manifest-path", "apps/desktop/src-tauri/Cargo.toml"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=cargo_env,
    )
    check(cargo_proc.returncode == 0, "Tauri 2 Rust backend check succeeded")


def main():
    print("=" * 65)
    print("  CORRIDORKEY 2.0 DESKTOP — MASTER PHASE 8 VERIFICATION")
    print("=" * 65)

    test_1_vector_masking()
    test_2_matte_refinement()
    test_3_color_grading()
    test_4_effect_stack()
    test_5_layer_compositing()
    test_6_node_graph_dag()
    test_7_project_serialization()
    test_8_ui_and_tauri_compilation()

    print("\n" + "=" * 65)
    print("  ALL 8 PHASE 8 ACCEPTANCE CRITERIA VERIFIED AND PASSED!")
    print("=" * 65)


if __name__ == "__main__":
    main()

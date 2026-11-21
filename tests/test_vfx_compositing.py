"""Unit tests for CorridorKey 2.0 Desktop Advanced VFX Compositing Subsystem."""

import os
import sys
import unittest
import numpy as np

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.vfx.color_grade import ColorGradeSettings, apply_color_grade
from engine.vfx.effects import (
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
    composite_layer_stack,
    composite_two_layers,
    transform_layer_image,
)
from engine.vfx.masking import (
    MaskItem,
    MaskMode,
    MaskPoint,
    MaskType,
    combine_masks,
    rasterize_mask,
)
from engine.vfx.matte_refine import MatteRefineSettings, refine_alpha_matte
from engine.vfx.node_graph import (
    AIForegroundNode,
    AlphaMatteNode,
    BackgroundNode,
    BlurNode,
    ColorCorrectionNode,
    MediaInputNode,
    MediaOutputNode,
    MergeNode,
    NodeGraph,
    TransformNode,
)


class TestVFXCompositing(unittest.TestCase):
    def test_masking_geometry_and_modes(self):
        # 1. Rectangle mask
        m_rect = MaskItem(
            mask_id="m1",
            name="Rect",
            mask_type=MaskType.RECTANGLE,
            points=[MaskPoint(0.2, 0.2), MaskPoint(0.8, 0.8)],
            feather=0.0,
        )
        r_rect = rasterize_mask(m_rect, 100, 100)
        self.assertEqual(r_rect.shape, (100, 100))
        self.assertGreater(r_rect[50, 50], 0.9)
        self.assertLess(r_rect[10, 10], 0.1)

        # 2. Ellipse mask with feather
        m_ellipse = MaskItem(
            mask_id="m2",
            name="Ellipse",
            mask_type=MaskType.ELLIPSE,
            feather=5.0,
        )
        r_ellipse = rasterize_mask(m_ellipse, 100, 100)
        self.assertGreater(r_ellipse[50, 50], 0.9)

        # 3. Polygon & Bezier mask
        m_poly = MaskItem(
            mask_id="m3",
            name="Poly",
            mask_type=MaskType.POLYGON,
            points=[MaskPoint(0.3, 0.3), MaskPoint(0.7, 0.3), MaskPoint(0.5, 0.8)],
        )
        r_poly = rasterize_mask(m_poly, 100, 100)
        self.assertGreater(r_poly[50, 50], 0.9)

        # 4. Add & Subtract combination
        m_sub = MaskItem(
            mask_id="m4",
            name="Sub",
            mask_type=MaskType.RECTANGLE,
            mode=MaskMode.SUBTRACT,
            points=[MaskPoint(0.4, 0.4), MaskPoint(0.6, 0.6)],
        )
        combined = combine_masks([m_rect, m_sub], 100, 100)
        # Center should be subtracted
        self.assertLess(combined[50, 50], 0.1)
        # Outside subtracted region but inside rect should be 1.0
        self.assertGreater(combined[30, 30], 0.9)

    def test_matte_refinement(self):
        # Create a synthetic noisy alpha matte with fuzzy edges
        alpha = np.zeros((100, 100), dtype=np.float32)
        alpha[30:70, 30:70] = 0.8  # Core

        settings = MatteRefineSettings(
            choke_expand=-2.0,  # Erosion
            contrast=1.5,
            edge_feather=2.0,
            alpha_threshold=0.1,
        )
        refined, _ = refine_alpha_matte(alpha, settings=settings)
        self.assertEqual(refined.shape, (100, 100))
        self.assertTrue(0.0 <= np.min(refined) and np.max(refined) <= 1.0)

        # Test despill on green screen RGB
        rgb = np.zeros((50, 50, 3), dtype=np.float32)
        rgb[:, :, 1] = 0.9  # High green
        rgb[:, :, 0] = 0.2  # Low red
        rgb[:, :, 2] = 0.2  # Low blue

        settings_despill = MatteRefineSettings(spill_suppression=1.0)
        _, decontam = refine_alpha_matte(np.ones((50, 50), dtype=np.float32), rgb=rgb, settings=settings_despill)
        self.assertIsNotNone(decontam)
        # Green channel should be suppressed down to max(R, B) = 0.2
        self.assertAlmostEqual(decontam[25, 25, 1], 0.2, places=2)

    def test_colour_correction(self):
        rgb = np.full((50, 50, 3), 0.5, dtype=np.float32)

        # 1. Exposure test (+1 EV should double 0.5 to 1.0)
        s_exp = ColorGradeSettings(exposure=1.0)
        g_exp = apply_color_grade(rgb, s_exp)
        self.assertAlmostEqual(g_exp[25, 25, 0], 1.0, places=2)

        # 2. Temperature test (Warm shift increases Red, decreases Blue)
        s_temp = ColorGradeSettings(temperature=0.5)
        g_temp = apply_color_grade(rgb, s_temp)
        self.assertGreater(g_temp[25, 25, 0], g_temp[25, 25, 2])

        # 3. Lift / Gamma / Gain test
        s_cdl = ColorGradeSettings(gain=1.5, lift=0.1)
        g_cdl = apply_color_grade(rgb, s_cdl)
        self.assertGreater(g_cdl[25, 25, 0], 0.5)

    def test_effect_stack(self):
        img = np.full((64, 64, 4), 0.5, dtype=np.float32)
        img[:, :, 3] = 1.0

        stack = EffectStack()
        # Add 10 effects
        stack.add_effect(GaussianBlurEffect())
        stack.add_effect(SharpenEffect())
        stack.add_effect(GlowEffect())
        stack.add_effect(DropShadowEffect())
        stack.add_effect(GaussianNoiseEffect())
        stack.add_effect(FilmGrainEffect())
        stack.add_effect(VignetteEffect())
        stack.add_effect(HueSaturationEffect())
        stack.add_effect(ColorCorrectionEffect())
        stack.add_effect(ChromaSpillSuppressionEffect())

        self.assertEqual(len(stack.effects), 10)

        # Process through all 10 effects
        out = stack.process(img)
        self.assertEqual(out.shape, (64, 64, 4))
        self.assertTrue(0.0 <= np.min(out) and np.max(out) <= 1.0)

        # Test duplicate and reorder
        dup = stack.duplicate_effect(stack.effects[0].effect_id)
        self.assertIsNotNone(dup)
        self.assertEqual(len(stack.effects), 11)

        ok = stack.reorder_effect(dup.effect_id, 0)
        self.assertTrue(ok)
        self.assertEqual(stack.effects[0].effect_id, dup.effect_id)

    def test_layer_compositing_and_blend_modes(self):
        base = np.full((10, 10, 3), 0.5, dtype=np.float32)
        blend = np.full((10, 10, 3), 0.5, dtype=np.float32)

        # Multiply: 0.5 * 0.5 = 0.25
        self.assertAlmostEqual(apply_blend_mode(base, blend, BlendMode.MULTIPLY)[0, 0, 0], 0.25)
        # Screen: 1 - (1 - 0.5)*(1 - 0.5) = 0.75
        self.assertAlmostEqual(apply_blend_mode(base, blend, BlendMode.SCREEN)[0, 0, 0], 0.75)
        # Difference: |0.5 - 0.5| = 0.0
        self.assertAlmostEqual(apply_blend_mode(base, blend, BlendMode.DIFFERENCE)[0, 0, 0], 0.0)

        # Composite layers
        layer_bg = LayerItem(layer_id="l-bg", name="BG")
        layer_fg = LayerItem(layer_id="l-fg", name="FG", opacity=0.8, blend_mode=BlendMode.NORMAL)

        img_bg = np.zeros((100, 100, 4), dtype=np.float32)
        img_bg[:, :, 0] = 1.0  # Red BG
        img_bg[:, :, 3] = 1.0

        img_fg = np.zeros((100, 100, 4), dtype=np.float32)
        img_fg[:, :, 1] = 1.0  # Green FG
        img_fg[:, :, 3] = 1.0

        comp = composite_layer_stack([(layer_bg, img_bg), (layer_fg, img_fg)], 100, 100)
        self.assertEqual(comp.shape, (100, 100, 4))
        # Green foreground with 0.8 opacity over red background
        self.assertGreater(comp[50, 50, 1], 0.7)
        self.assertGreater(comp[50, 50, 0], 0.1)

    def test_node_graph_dag(self):
        graph = NodeGraph()
        n_input = graph.add_node(MediaInputNode())
        n_ai = graph.add_node(AIForegroundNode())
        n_blur = graph.add_node(BlurNode())
        n_bg = graph.add_node(BackgroundNode())
        n_merge = graph.add_node(MergeNode())
        n_out = graph.add_node(MediaOutputNode())

        # Connect pipeline:
        # MediaInput -> AI Foreground -> Blur -> Merge (FG)
        # Background -> Merge (BG)
        # Merge -> Media Output
        graph.connect(n_input.node_id, "out_rgba", n_ai.node_id, "in_rgba")
        graph.connect(n_ai.node_id, "out_fg", n_blur.node_id, "in_rgba")
        graph.connect(n_input.node_id, "out_rgba", n_bg.node_id, "in_ref")
        graph.connect(n_bg.node_id, "out_bg", n_merge.node_id, "in_bg")
        graph.connect(n_blur.node_id, "out_rgba", n_merge.node_id, "in_fg")
        graph.connect(n_merge.node_id, "out_comp", n_out.node_id, "in_composite")

        # Verify no cycles and topological order
        self.assertFalse(graph.detect_cycle())
        eval_order = graph.get_evaluation_order()
        self.assertEqual(len(eval_order), 6)
        # Output must be last
        self.assertEqual(eval_order[-1], n_out.node_id)

        # Test cycle detection
        with self.assertRaises(ValueError):
            # Attempt to connect output back to input creating a cycle
            graph.connect(n_out.node_id, "in_composite", n_input.node_id, "custom_image")

        # Execute graph
        res = graph.execute_graph()
        self.assertIn(n_out.node_id, res)
        final_img = res[n_out.node_id].get("final_image")
        self.assertIsNotNone(final_img)
        self.assertEqual(final_img.shape, (100, 100, 4))


if __name__ == "__main__":
    unittest.main()

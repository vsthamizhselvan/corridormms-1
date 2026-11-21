"""CorridorKey 2.0 Desktop — Advanced VFX Compositing Subsystem."""

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
    GlowEffect,
    GaussianNoiseEffect,
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
    NODE_REGISTRY,
    AIForegroundNode,
    AlphaMatteNode,
    BackgroundNode,
    BaseNode,
    BlurNode,
    ColorCorrectionNode,
    MaskNode,
    MediaInputNode,
    MediaOutputNode,
    MergeNode,
    NodeConnection,
    NodeGraph,
    NodeSocket,
    TransformNode,
)

__all__ = [
    # Masking
    "MaskType",
    "MaskMode",
    "MaskPoint",
    "MaskItem",
    "rasterize_mask",
    "combine_masks",
    # Matte Refinement
    "MatteRefineSettings",
    "refine_alpha_matte",
    # Colour Correction
    "ColorGradeSettings",
    "apply_color_grade",
    # Effects
    "BaseVFXEffect",
    "EFFECT_REGISTRY",
    "EffectStack",
    "GaussianBlurEffect",
    "SharpenEffect",
    "GlowEffect",
    "DropShadowEffect",
    "GaussianNoiseEffect",
    "FilmGrainEffect",
    "VignetteEffect",
    "HueSaturationEffect",
    "ColorCorrectionEffect",
    "ChromaSpillSuppressionEffect",
    # Layer Compositing
    "BlendMode",
    "LayerItem",
    "apply_blend_mode",
    "transform_layer_image",
    "composite_two_layers",
    "composite_layer_stack",
    # Node Graph
    "NodeSocket",
    "NodeConnection",
    "BaseNode",
    "NodeGraph",
    "NODE_REGISTRY",
    "MediaInputNode",
    "AIForegroundNode",
    "AlphaMatteNode",
    "MaskNode",
    "BlurNode",
    "ColorCorrectionNode",
    "TransformNode",
    "BackgroundNode",
    "MergeNode",
    "MediaOutputNode",
]

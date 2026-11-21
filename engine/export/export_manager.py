"""CorridorKey 2.0 Desktop — Master Export Manager.

Unified factory and orchestrator for professional VFX video exports:
- Apple ProRes 4444 & 4444 XQ (.mov)
- QuickTime Animation RLE (.mov)
- VP9 WebM with Alpha (.webm)
- OpenEXR Sequence (.exr)
- PNG Sequence (.png)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np

from engine.color.alpha_manager import AlphaMode, assemble_rgba
from engine.color.color_manager import ColorConversionReport, ColorManager
from engine.export.h264 import H264Config, H264Exporter
from engine.export.h265 import H265Config, H265Exporter
from engine.export.openexr import ExrConfig, OpenExrExporter
from engine.export.png_sequence import PngConfig, PngSequenceExporter
from engine.export.prores import ProResConfig, ProResExporter
from engine.export.qtrle import QtrleConfig, QtrleExporter
from engine.export.validation import ExportValidationResult, validate_exported_media
from engine.export.vp9 import Vp9Config, Vp9Exporter


@dataclass
class ExportJobConfig:
    output_path: str
    format: str  # 'prores_4444' | 'prores_4444_xq' | 'qtrle' | 'vp9' | 'openexr' | 'png_sequence'
    width: int
    height: int
    fps: float
    alpha_mode: AlphaMode = AlphaMode.STRAIGHT
    despill_strength: float = 0.5
    color_profile: str = "rec709"
    audio_source: Optional[str] = None
    preserve_audio: bool = True
    exr_dtype: str = "half"  # 'half' or 'float'
    png_bit_depth: int = 8


class MasterExportManager:
    """Manages video frame assembly, color transforms, encoding, and output validation."""

    def __init__(self, config: ExportJobConfig):
        self.config = config
        self.color_manager = ColorManager(source_space="rec709", target_space=config.color_profile)
        self.exporter: Union[ProResExporter, QtrleExporter, Vp9Exporter, OpenExrExporter, PngSequenceExporter] = (
            self._create_exporter()
        )
        self._frames_processed = 0

    def _create_exporter(self):
        fmt = self.config.format.lower().replace("-", "_")
        audio_src = self.config.audio_source if self.config.preserve_audio else None

        if fmt in ("prores", "prores_4444", "prores4444"):
            cfg = ProResConfig(
                profile=4,
                color_profile=self.config.color_profile,
                audio_source=audio_src,
            )
            return ProResExporter(self.config.output_path, self.config.width, self.config.height, self.config.fps, cfg)

        elif fmt in ("prores_422_hq", "prores_422", "prores422", "prores422hq"):
            cfg = ProResConfig(
                profile=3,
                color_profile=self.config.color_profile,
                audio_source=audio_src,
            )
            return ProResExporter(self.config.output_path, self.config.width, self.config.height, self.config.fps, cfg)

        elif fmt in ("prores_xq", "prores_4444_xq", "prores4444xq"):
            cfg = ProResConfig(
                profile=5,
                color_profile=self.config.color_profile,
                audio_source=audio_src,
            )
            return ProResExporter(self.config.output_path, self.config.width, self.config.height, self.config.fps, cfg)

        elif fmt in ("h264", "avc", "mp4"):
            cfg = H264Config(
                color_profile=self.config.color_profile,
                audio_source=audio_src,
            )
            return H264Exporter(self.config.output_path, self.config.width, self.config.height, self.config.fps, cfg)

        elif fmt in ("h265", "hevc"):
            cfg = H265Config(
                color_profile=self.config.color_profile,
                audio_source=audio_src,
            )
            return H265Exporter(self.config.output_path, self.config.width, self.config.height, self.config.fps, cfg)

        elif fmt in ("qtrle", "animation", "quicktime_animation"):
            cfg = QtrleConfig(audio_source=audio_src)
            return QtrleExporter(self.config.output_path, self.config.width, self.config.height, self.config.fps, cfg)

        elif fmt in ("vp9", "webm", "webm_alpha"):
            cfg = Vp9Config(audio_source=audio_src)
            return Vp9Exporter(self.config.output_path, self.config.width, self.config.height, self.config.fps, cfg)

        elif fmt in ("exr", "openexr", "exr_sequence"):
            cfg = ExrConfig(dtype=self.config.exr_dtype)
            return OpenExrExporter(self.config.output_path, self.config.width, self.config.height, self.config.fps, cfg)

        elif fmt in ("png", "png_sequence"):
            cfg = PngConfig(bit_depth=self.config.png_bit_depth)
            return PngSequenceExporter(self.config.output_path, self.config.width, self.config.height, self.config.fps, cfg)

        else:
            # Default to ProRes 4444 for professional VFX delivery
            cfg = ProResConfig(profile=4, audio_source=audio_src)
            return ProResExporter(self.config.output_path, self.config.width, self.config.height, self.config.fps, cfg)

    def write_frame(self, rgb: np.ndarray, alpha: np.ndarray):
        """Processes RGB and Alpha components and delivers RGBA frame to active encoder."""
        rgba = assemble_rgba(
            rgb=rgb,
            alpha=alpha,
            alpha_mode=self.config.alpha_mode,
            despill_strength=self.config.despill_strength,
        )
        self.exporter.write_frame_rgba(rgba)
        self._frames_processed += 1

    def close(self) -> Tuple[ExportValidationResult, ColorConversionReport]:
        """Finalizes the video encoder and executes post-export transparency validation."""
        self.exporter.close()

        validation = validate_exported_media(self.config.output_path, self.config.format)
        color_report = self.color_manager.get_conversion_report()

        return validation, color_report

    @property
    def frames_processed(self) -> int:
        return self._frames_processed

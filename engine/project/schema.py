"""CorridorKey 2.0 Desktop — Native Project Schema Specification (.ckproj).

Defines the native v1.1.0 JSON schema for project persistence,
version migration hooks, and strongly-typed data structures supporting
masking, alpha refinement, color grading, effects, layers, and node graphs.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from engine.timeline.timebase import TIMEBASE_24, Timebase
from engine.timeline.timeline_model import TimelineSequence

CURRENT_SCHEMA_VERSION = "1.1.0"
SUPPORTED_SCHEMA_VERSIONS = ["0.9.0", "1.0.0", "1.1.0"]


@dataclass
class ProjectMetadata:
    project_id: str
    name: str
    width: int = 1920
    height: int = 1080
    frame_rate: float = 24.0
    timebase_numerator: int = 24
    timebase_denominator: int = 1
    color_space: str = "Rec.709"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    modified_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ProjectMetadata":
        return cls(
            project_id=d.get("project_id", f"proj-{uuid.uuid4().hex[:8]}"),
            name=d.get("name", "Untitled Project"),
            width=int(d.get("width", 1920)),
            height=int(d.get("height", 1080)),
            frame_rate=float(d.get("frame_rate", 24.0)),
            timebase_numerator=int(d.get("timebase_numerator", 24)),
            timebase_denominator=int(d.get("timebase_denominator", 1)),
            color_space=d.get("color_space", "Rec.709"),
            created_at=d.get("created_at", datetime.utcnow().isoformat() + "Z"),
            modified_at=d.get("modified_at", datetime.utcnow().isoformat() + "Z"),
        )


@dataclass
class MediaReference:
    asset_id: str
    name: str
    relative_path: str
    absolute_path: str
    width: int
    height: int
    frame_rate: float
    duration_frames: int
    duration_seconds: float
    codec: str
    file_size_bytes: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "MediaReference":
        return cls(
            asset_id=d.get("asset_id") or d.get("id", "asset"),
            name=d.get("name", "Media"),
            relative_path=d.get("relative_path", ""),
            absolute_path=d.get("absolute_path") or d.get("path", ""),
            width=int(d.get("width", 1920)),
            height=int(d.get("height", 1080)),
            frame_rate=float(d.get("frame_rate") or d.get("fps", 24.0)),
            duration_frames=int(d.get("duration_frames", 0)),
            duration_seconds=float(d.get("duration_seconds", 0.0)),
            codec=d.get("codec", "H.264"),
            file_size_bytes=int(d.get("file_size_bytes", 0)),
        )


@dataclass
class KeyingSettings:
    hann_chunk: int = 96
    hann_stride: int = 48
    low_vram: bool = False
    despill_strength: float = 0.7
    hint_mode: str = "first_frame"
    hint_quality: int = 3

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MatteSettings:
    contrast: float = 1.0
    edge_refinement: float = 0.0
    invert: bool = False
    alpha_threshold: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ViewerSettings:
    display_mode: str = "composite"
    background_type: str = "checkerboard"
    background_color: str = "#000000"
    gradient_color_a: str = "#1e293b"
    gradient_color_b: str = "#0f172a"
    compare_mode: str = "off"
    wipe_position: float = 0.5
    alpha_mode: str = "premultiplied"
    exposure: float = 0.0
    saturation: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExportSettings:
    format: str = "prores4444"
    resolution: str = "source"
    color_space: str = "Rec.709"
    include_alpha: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class WorkspaceLayout:
    left_panel_width: int = 300
    right_panel_width: int = 340
    bottom_panel_height: int = 260
    show_media_browser: bool = True
    show_inspector: bool = True
    show_timeline: bool = True
    zoom_ratio: float = 1.5

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "WorkspaceLayout":
        return cls(
            left_panel_width=int(d.get("left_panel_width", 300)),
            right_panel_width=int(d.get("right_panel_width", 340)),
            bottom_panel_height=int(d.get("bottom_panel_height", 260)),
            show_media_browser=bool(d.get("show_media_browser", True)),
            show_inspector=bool(d.get("show_inspector", True)),
            show_timeline=bool(d.get("show_timeline", True)),
            zoom_ratio=float(d.get("zoom_ratio", 1.5)),
        )


@dataclass
class ProjectDocument:
    format: str = "corridorkey-project"
    schema_version: str = CURRENT_SCHEMA_VERSION
    generator: str = "CorridorKey 2.0 Desktop"
    project: ProjectMetadata = field(default_factory=lambda: ProjectMetadata(f"proj-{uuid.uuid4().hex[:8]}", "Untitled Project"))
    media_pool: List[MediaReference] = field(default_factory=list)
    timeline: Optional[TimelineSequence] = None
    keying_settings: KeyingSettings = field(default_factory=KeyingSettings)
    matte_settings: MatteSettings = field(default_factory=MatteSettings)
    viewer_settings: ViewerSettings = field(default_factory=ViewerSettings)
    export_settings: ExportSettings = field(default_factory=ExportSettings)
    workspace: WorkspaceLayout = field(default_factory=WorkspaceLayout)

    # Phase 8 VFX Extensions
    masks: List[Dict[str, Any]] = field(default_factory=list)
    matte_refine: Dict[str, Any] = field(default_factory=dict)
    color_grade: Dict[str, Any] = field(default_factory=dict)
    effects: List[Dict[str, Any]] = field(default_factory=list)
    node_graph: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "format": self.format,
            "schema_version": self.schema_version,
            "generator": self.generator,
            "project": self.project.to_dict(),
            "media_pool": [m.to_dict() for m in self.media_pool],
            "timeline": self.timeline.to_dict() if self.timeline else None,
            "settings": {
                "keying": self.keying_settings.to_dict(),
                "matte": self.matte_settings.to_dict(),
                "viewer": self.viewer_settings.to_dict(),
                "export": self.export_settings.to_dict(),
            },
            "workspace": self.workspace.to_dict(),
            "vfx": {
                "masks": self.masks,
                "matte_refine": self.matte_refine,
                "color_grade": self.color_grade,
                "effects": self.effects,
                "node_graph": self.node_graph,
            },
        }


def migrate_schema(raw_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Migrates older schema versions (0.9.0, 1.0.0) to current CURRENT_SCHEMA_VERSION (1.1.0)."""
    version = raw_dict.get("schema_version", "0.9.0")

    if version == CURRENT_SCHEMA_VERSION:
        return raw_dict

    migrated = dict(raw_dict)

    # 1. Legacy 0.9.0 -> 1.0.0 Migration
    if version == "0.9.0" or "schema_version" not in raw_dict:
        if "media" in migrated and "media_pool" not in migrated:
            migrated["media_pool"] = migrated.pop("media")

        if "timeline" in migrated and isinstance(migrated["timeline"], dict):
            tl = migrated["timeline"]
            if "timebase" not in tl:
                fps = migrated.get("project", {}).get("frameRate", 24.0)
                tl["timebase"] = {"numerator": int(round(fps)), "denominator": 1}

        migrated["schema_version"] = "1.0.0"
        version = "1.0.0"

    # 2. 1.0.0 -> 1.1.0 Migration (Phase 8 VFX additions)
    if version == "1.0.0":
        if "vfx" not in migrated:
            migrated["vfx"] = {
                "masks": [],
                "matte_refine": {},
                "color_grade": {},
                "effects": [],
                "node_graph": None,
            }
        migrated["schema_version"] = "1.1.0"

    return migrated

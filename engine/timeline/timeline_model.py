"""CorridorKey 2.0 Desktop — Non-Destructive Timeline Data Models.

Defines the core representations for Sequences, Video/Audio Tracks, Clips,
and Animated Parameters using integer frame tick math.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from engine.timeline.keyframe_engine import PropertyTrack
from engine.timeline.timebase import TIMEBASE_24, Timebase


@dataclass
class ClipItem:
    clip_id: str
    media_id: str
    track_id: str
    name: str
    source_path: str
    source_in: int  # in source media frames
    source_out: int  # in source media frames
    timeline_start: int  # placement on timeline in frame ticks
    timeline_end: int  # placement end on timeline in frame ticks
    speed: float = 1.0
    volume: float = 1.0
    is_muted: bool = False
    color_tag: str = "#0d9488"
    properties: Dict[str, PropertyTrack] = field(default_factory=dict)

    def __post_init__(self):
        if not self.properties:
            self.properties = {
                "posX": PropertyTrack("posX", 0.0),
                "posY": PropertyTrack("posY", 0.0),
                "scale": PropertyTrack("scale", 100.0),
                "rotation": PropertyTrack("rotation", 0.0),
                "opacity": PropertyTrack("opacity", 100.0),
            }

    @property
    def duration(self) -> int:
        return self.timeline_end - self.timeline_start

    def get_source_frame(self, timeline_frame: int) -> int:
        """Calculates exact source frame index from timeline frame."""
        delta = timeline_frame - self.timeline_start
        return self.source_in + int(round(delta * self.speed))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "clip_id": self.clip_id,
            "media_id": self.media_id,
            "track_id": self.track_id,
            "name": self.name,
            "source_path": self.source_path,
            "source_in": self.source_in,
            "source_out": self.source_out,
            "timeline_start": self.timeline_start,
            "timeline_end": self.timeline_end,
            "duration": self.duration,
            "speed": self.speed,
            "volume": self.volume,
            "is_muted": self.is_muted,
            "color_tag": self.color_tag,
            "properties": {k: v.to_dict() for k, v in self.properties.items()},
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ClipItem":
        props = {}
        for k, v in d.get("properties", {}).items():
            props[k] = PropertyTrack.from_dict(v)

        return cls(
            clip_id=d["clip_id"],
            media_id=d["media_id"],
            track_id=d["track_id"],
            name=d["name"],
            source_path=d.get("source_path", ""),
            source_in=int(d["source_in"]),
            source_out=int(d["source_out"]),
            timeline_start=int(d["timeline_start"]),
            timeline_end=int(d["timeline_end"]),
            speed=float(d.get("speed", 1.0)),
            volume=float(d.get("volume", 1.0)),
            is_muted=bool(d.get("is_muted", False)),
            color_tag=d.get("color_tag", "#0d9488"),
            properties=props,
        )


@dataclass
class TrackItem:
    track_id: str
    type: str  # 'video' | 'audio'
    name: str
    visible: bool = True
    locked: bool = False
    muted: bool = False
    solo: bool = False
    order_index: int = 0
    clips: List[ClipItem] = field(default_factory=list)

    def find_clip_at_frame(self, frame: int) -> Optional[ClipItem]:
        """Returns the active clip at the specified integer frame tick, if any."""
        for c in self.clips:
            if c.timeline_start <= frame < c.timeline_end:
                return c
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track_id": self.track_id,
            "type": self.type,
            "name": self.name,
            "visible": self.visible,
            "locked": self.locked,
            "muted": self.muted,
            "solo": self.solo,
            "order_index": self.order_index,
            "clips": [c.to_dict() for c in self.clips],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TrackItem":
        clips = [ClipItem.from_dict(c) for c in d.get("clips", [])]
        return cls(
            track_id=d["track_id"],
            type=d["type"],
            name=d["name"],
            visible=bool(d.get("visible", True)),
            locked=bool(d.get("locked", False)),
            muted=bool(d.get("muted", False)),
            solo=bool(d.get("solo", False)),
            order_index=int(d.get("order_index", 0)),
            clips=clips,
        )


@dataclass
class TimelineSequence:
    sequence_id: str
    name: str
    timebase: Timebase = TIMEBASE_24
    duration_frames: int = 240
    tracks: List[TrackItem] = field(default_factory=list)

    def get_video_tracks(self) -> List[TrackItem]:
        """Returns video tracks sorted bottom-to-top (V1, V2, V3)."""
        return sorted([t for t in self.tracks if t.type == "video"], key=lambda t: t.order_index)

    def get_audio_tracks(self) -> List[TrackItem]:
        """Returns audio tracks."""
        return sorted([t for t in self.tracks if t.type == "audio"], key=lambda t: t.order_index)

    def find_clip(self, clip_id: str) -> Optional[Tuple[TrackItem, ClipItem]]:
        for t in self.tracks:
            for c in t.clips:
                if c.clip_id == clip_id:
                    return t, c
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sequence_id": self.sequence_id,
            "name": self.name,
            "timebase": {"numerator": self.timebase.numerator, "denominator": self.timebase.denominator},
            "duration_frames": self.duration_frames,
            "tracks": [t.to_dict() for t in self.tracks],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TimelineSequence":
        tb_data = d.get("timebase", {"numerator": 24, "denominator": 1})
        tb = Timebase(int(tb_data["numerator"]), int(tb_data["denominator"]))
        tracks = [TrackItem.from_dict(t) for t in d.get("tracks", [])]
        return cls(
            sequence_id=d.get("sequence_id", "seq_1"),
            name=d.get("name", "Main Sequence"),
            timebase=tb,
            duration_frames=int(d.get("duration_frames", 240)),
            tracks=tracks,
        )

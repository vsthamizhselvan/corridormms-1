"""CorridorKey 2.0 Desktop — Non-Destructive Timeline Render Graph.

Evaluates the multi-track composition hierarchy at any integer frame tick,
resolving layer order, active clips, keyframe property transforms,
and producing an execution plan for the WebGL2 GPU viewer and export pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from engine.timeline.audio_engine import AudioMixVoice, TimelineAudioEngine
from engine.timeline.timeline_model import ClipItem, TimelineSequence, TrackItem


@dataclass
class RenderLayerPlan:
    track_id: str
    track_name: str
    order_index: int
    clip_id: str
    clip_name: str
    source_path: str
    source_frame: int
    opacity: float  # 0.0 - 100.0 %
    pos_x: float  # pixels offset
    pos_y: float  # pixels offset
    scale: float  # percentage (100.0 = 1x)
    rotation: float  # degrees

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track_id": self.track_id,
            "track_name": self.track_name,
            "order_index": self.order_index,
            "clip_id": self.clip_id,
            "clip_name": self.clip_name,
            "source_path": self.source_path,
            "source_frame": self.source_frame,
            "opacity": self.opacity,
            "pos_x": self.pos_x,
            "pos_y": self.pos_y,
            "scale": self.scale,
            "rotation": self.rotation,
        }


@dataclass
class TimelineFrameCompositePlan:
    frame: int
    timecode: str
    layers: List[RenderLayerPlan] = field(default_factory=list)
    audio_voices: List[AudioMixVoice] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frame": self.frame,
            "timecode": self.timecode,
            "layers": [layer.to_dict() for layer in self.layers],
            "audio_voices": [
                {
                    "clip_id": v.clip_id,
                    "track_id": v.track_id,
                    "source_path": v.source_path,
                    "source_frame": v.source_frame,
                    "volume": v.volume,
                    "is_audible": v.is_audible,
                }
                for v in self.audio_voices
            ],
        }


class TimelineRenderGraph:
    """Evaluates the state of a multi-track sequence for rendering at frame F."""

    def __init__(self, sequence: TimelineSequence):
        self.sequence = sequence

    def evaluate_frame(self, frame: int) -> TimelineFrameCompositePlan:
        """Evaluates all visible video tracks from bottom to top and active audio voices."""
        timecode = self.sequence.timebase.frame_to_timecode(frame)
        layers: List[RenderLayerPlan] = []

        # Video tracks are sorted bottom-to-top (V1 at index 0, V2 at 1, etc.)
        video_tracks = self.sequence.get_video_tracks()

        for track in video_tracks:
            if not track.visible:
                continue

            clip = track.find_clip_at_frame(frame)
            if not clip:
                continue

            # Evaluate source frame
            src_frame = clip.get_source_frame(frame)

            # Evaluate keyframed transform properties
            pos_x = clip.properties["posX"].evaluate(frame) if "posX" in clip.properties else 0.0
            pos_y = clip.properties["posY"].evaluate(frame) if "posY" in clip.properties else 0.0
            scale = clip.properties["scale"].evaluate(frame) if "scale" in clip.properties else 100.0
            rot = clip.properties["rotation"].evaluate(frame) if "rotation" in clip.properties else 0.0
            op = clip.properties["opacity"].evaluate(frame) if "opacity" in clip.properties else 100.0

            layers.append(
                RenderLayerPlan(
                    track_id=track.track_id,
                    track_name=track.name,
                    order_index=track.order_index,
                    clip_id=clip.clip_id,
                    clip_name=clip.name,
                    source_path=clip.source_path,
                    source_frame=src_frame,
                    opacity=op,
                    pos_x=pos_x,
                    pos_y=pos_y,
                    scale=scale,
                    rotation=rot,
                )
            )

        # Audio evaluation
        audio_voices = TimelineAudioEngine.evaluate_audio_at_frame(self.sequence, frame)

        return TimelineFrameCompositePlan(
            frame=frame,
            timecode=timecode,
            layers=layers,
            audio_voices=audio_voices,
        )

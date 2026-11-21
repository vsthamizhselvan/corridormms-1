"""CorridorKey 2.0 Desktop — Non-Destructive Audio Engine & Waveform Visualizer.

Manages audio track mixing, mute/solo resolution, gain calculation,
and waveform envelope generation for UI rendering.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional

from engine.timeline.timeline_model import ClipItem, TimelineSequence, TrackItem


@dataclass
class AudioMixVoice:
    clip_id: str
    track_id: str
    source_path: str
    source_frame: int
    volume: float  # 0.0 - 1.0 (or > 1.0 for gain boost)
    is_audible: bool


class TimelineAudioEngine:
    """Evaluates multi-track audio states, mute/solo routing, and clip gain."""

    @staticmethod
    def resolve_track_audibility(tracks: List[TrackItem]) -> Dict[str, bool]:
        """Resolves whether each audio track is audible given mute and solo states."""
        audio_tracks = [t for t in tracks if t.type == "audio"]
        has_solo = any(t.solo for t in audio_tracks)

        audibility: Dict[str, bool] = {}
        for t in audio_tracks:
            if has_solo:
                audibility[t.track_id] = t.solo and not t.muted
            else:
                audibility[t.track_id] = not t.muted
        return audibility

    @classmethod
    def evaluate_audio_at_frame(
        cls,
        sequence: TimelineSequence,
        frame: int,
    ) -> List[AudioMixVoice]:
        """Evaluates active audio voices at the given timeline frame tick."""
        audibility = cls.resolve_track_audibility(sequence.tracks)
        voices: List[AudioMixVoice] = []

        for track in sequence.get_audio_tracks():
            track_audible = audibility.get(track.track_id, False)
            clip = track.find_clip_at_frame(frame)
            if not clip:
                continue

            is_audible = track_audible and not clip.is_muted
            vol = clip.volume if is_audible else 0.0
            source_frame = clip.get_source_frame(frame)

            voices.append(
                AudioMixVoice(
                    clip_id=clip.clip_id,
                    track_id=track.track_id,
                    source_path=clip.source_path,
                    source_frame=source_frame,
                    volume=vol,
                    is_audible=is_audible,
                )
            )

        return voices

    @staticmethod
    def generate_synthetic_waveform_envelope(
        num_samples: int = 100,
        frequency: float = 4.0,
        seed: int = 42,
    ) -> List[float]:
        """Generates a normalized [0.0, 1.0] peak envelope for visual waveform display."""
        peaks: List[float] = []
        for i in range(num_samples):
            t = i / max(num_samples - 1, 1)
            # Harmonic combination with modulated amplitude envelope
            envelope = math.sin(math.pi * t)
            harmonics = (
                0.6 * abs(math.sin(2.0 * math.pi * frequency * t))
                + 0.3 * abs(math.sin(4.0 * math.pi * frequency * t + 0.5))
                + 0.1 * abs(math.cos(10.0 * math.pi * frequency * t))
            )
            peak = min(1.0, max(0.05, envelope * harmonics))
            peaks.append(round(peak, 3))
        return peaks

"""CorridorKey 2.0 Desktop — Non-Destructive Timeline Edit Operations.

Provides professional non-destructive editing operations:
- Move clip (same track or cross-track)
- Trim in / Trim out
- Razor / Split clip
- Delete clip
- Ripple delete (shifts downstream clips left by deleted duration)
- Duplicate clip
- Magnetic snapping to playhead, clip boundaries, and markers
"""

from __future__ import annotations

import copy
import uuid
from typing import List, Optional, Tuple

from engine.timeline.timeline_model import ClipItem, TrackItem


def can_place_clip(
    track: TrackItem,
    start_frame: int,
    end_frame: int,
    ignore_clip_id: Optional[str] = None,
) -> bool:
    """Checks whether a clip placement collides with existing clips on the track."""
    if start_frame >= end_frame:
        return False

    for c in track.clips:
        if ignore_clip_id and c.clip_id == ignore_clip_id:
            continue
        # Check overlap: max(start1, start2) < min(end1, end2)
        if max(start_frame, c.timeline_start) < min(end_frame, c.timeline_end):
            return False
    return True


def move_clip(
    track_from: TrackItem,
    track_to: TrackItem,
    clip: ClipItem,
    new_start_frame: int,
) -> bool:
    """Moves a clip to a new position, potentially across tracks. Non-destructive."""
    duration = clip.duration
    new_end_frame = new_start_frame + duration

    if new_start_frame < 0:
        return False

    # Check collision on destination track
    if not can_place_clip(track_to, new_start_frame, new_end_frame, ignore_clip_id=clip.clip_id):
        return False

    # If cross-track move, remove from source track and append to dest track
    if track_from.track_id != track_to.track_id:
        track_from.clips = [c for c in track_from.clips if c.clip_id != clip.clip_id]
        clip.track_id = track_to.track_id
        track_to.clips.append(clip)

    clip.timeline_start = new_start_frame
    clip.timeline_end = new_end_frame
    track_to.clips.sort(key=lambda c: c.timeline_start)
    return True


def trim_clip_in(clip: ClipItem, new_start_frame: int) -> bool:
    """Trims the beginning (In-point) of a clip.
    Adjusts timeline_start and advances source_in proportionally.
    """
    if new_start_frame >= clip.timeline_end:
        return False  # Cannot trim in past timeline_end

    frame_delta = new_start_frame - clip.timeline_start
    source_delta = int(round(frame_delta * clip.speed))
    new_source_in = clip.source_in + source_delta

    if new_source_in >= clip.source_out:
        return False

    clip.timeline_start = new_start_frame
    clip.source_in = new_source_in
    return True


def trim_clip_out(clip: ClipItem, new_end_frame: int) -> bool:
    """Trims the end (Out-point) of a clip.
    Adjusts timeline_end and adjusts source_out proportionally.
    """
    if new_end_frame <= clip.timeline_start:
        return False  # Cannot trim out before timeline_start

    frame_delta = new_end_frame - clip.timeline_start
    new_source_out = clip.source_in + int(round(frame_delta * clip.speed))

    if new_source_out <= clip.source_in:
        return False

    clip.timeline_end = new_end_frame
    clip.source_out = new_source_out
    return True


def split_clip(
    track: TrackItem,
    clip: ClipItem,
    split_frame: int,
) -> Optional[Tuple[ClipItem, ClipItem]]:
    """Splits a clip into two independent non-destructive clips at split_frame (Razor Tool)."""
    if not (clip.timeline_start < split_frame < clip.timeline_end):
        return None  # Split point must be strictly inside clip boundaries

    # Calculate exact source cut point
    delta = split_frame - clip.timeline_start
    source_cut = clip.source_in + int(round(delta * clip.speed))

    # Duplicate properties for second half
    new_props = copy.deepcopy(clip.properties)

    # First half keeps clip_id and ends at split_frame
    first_half = clip
    original_timeline_end = clip.timeline_end
    original_source_out = clip.source_out

    first_half.timeline_end = split_frame
    first_half.source_out = source_cut

    # Second half starts at split_frame
    second_half = ClipItem(
        clip_id=f"clip-{uuid.uuid4().hex[:8]}",
        media_id=clip.media_id,
        track_id=track.track_id,
        name=f"{clip.name} (Split)",
        source_path=clip.source_path,
        source_in=source_cut,
        source_out=original_source_out,
        timeline_start=split_frame,
        timeline_end=original_timeline_end,
        speed=clip.speed,
        volume=clip.volume,
        is_muted=clip.is_muted,
        color_tag=clip.color_tag,
        properties=new_props,
    )

    track.clips.append(second_half)
    track.clips.sort(key=lambda c: c.timeline_start)
    return first_half, second_half


def delete_clip(track: TrackItem, clip_id: str) -> Optional[ClipItem]:
    """Deletes a clip from a track leaving an empty gap."""
    for i, c in enumerate(track.clips):
        if c.clip_id == clip_id:
            return track.clips.pop(i)
    return None


def ripple_delete(track: TrackItem, clip_id: str) -> Optional[ClipItem]:
    """Ripple-deletes a clip from a track, closing the gap by shifting
    all downstream clips left by the deleted clip's duration.
    """
    clip_to_delete = None
    delete_index = -1
    for i, c in enumerate(track.clips):
        if c.clip_id == clip_id:
            clip_to_delete = c
            delete_index = i
            break

    if clip_to_delete is None:
        return None

    duration = clip_to_delete.duration
    track.clips.pop(delete_index)

    # Shift subsequent clips left
    for c in track.clips:
        if c.timeline_start >= clip_to_delete.timeline_end:
            c.timeline_start -= duration
            c.timeline_end -= duration

    track.clips.sort(key=lambda c: c.timeline_start)
    return clip_to_delete


def duplicate_clip(track: TrackItem, clip: ClipItem) -> Optional[ClipItem]:
    """Duplicates a clip and places the duplicate immediately following it or in the first available slot."""
    new_props = copy.deepcopy(clip.properties)
    desired_start = clip.timeline_end
    duration = clip.duration

    # Look for placement after clip
    if not can_place_clip(track, desired_start, desired_start + duration):
        # Find next available frame after all clips
        max_end = max((c.timeline_end for c in track.clips), default=0)
        desired_start = max_end

    dup = ClipItem(
        clip_id=f"clip-{uuid.uuid4().hex[:8]}",
        media_id=clip.media_id,
        track_id=track.track_id,
        name=f"{clip.name} (Copy)",
        source_path=clip.source_path,
        source_in=clip.source_in,
        source_out=clip.source_out,
        timeline_start=desired_start,
        timeline_end=desired_start + duration,
        speed=clip.speed,
        volume=clip.volume,
        is_muted=clip.is_muted,
        color_tag=clip.color_tag,
        properties=new_props,
    )
    track.clips.append(dup)
    track.clips.sort(key=lambda c: c.timeline_start)
    return dup


def find_snap_target(frame: int, snap_candidates: List[int], tolerance: int = 5) -> Optional[int]:
    """Finds the closest magnetic snap target within tolerance frames, if any."""
    best_target = None
    min_dist = tolerance + 1

    for target in snap_candidates:
        dist = abs(frame - target)
        if dist <= tolerance and dist < min_dist:
            min_dist = dist
            best_target = target

    return best_target

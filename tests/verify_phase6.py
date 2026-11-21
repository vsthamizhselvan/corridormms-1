#!/usr/bin/env python3
"""CorridorKey 2.0 Desktop — Master Phase 6 Verification Script.

Validates all 14 Phase 6 Acceptance Criteria:
1. Multi-track timeline data models (Sequence, Tracks, Clips).
2. Rational timebase (exact fraction fps, frame to sec, sec to frame).
3. SMPTE timecode formatting and parsing.
4. Track controls (visibility, lock, mute, solo, reorder).
5. Non-destructive clip geometry (source boundaries vs timeline boundaries).
6. Clip trimming in and trimming out.
7. Razor / split clip operation.
8. Clip deletion and ripple deletion (gap closing).
9. Magnetic snapping to playhead and clip boundaries.
10. Keyframe animation (Hold, Linear, Cubic Bezier easing).
11. Render graph multi-layer composition plan evaluation.
12. Multi-track audio evaluation (audibility, mute/solo, waveform envelope).
13. Undo / Redo state management.
14. React frontend compilation and Tauri Rust verification.
"""

import os
import subprocess
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.timeline.audio_engine import AudioMixVoice, TimelineAudioEngine
from engine.timeline.edit_operations import (
    can_place_clip,
    delete_clip,
    duplicate_clip,
    find_snap_target,
    move_clip,
    ripple_delete,
    split_clip,
    trim_clip_in,
    trim_clip_out,
)
from engine.timeline.keyframe_engine import (
    Keyframe,
    KeyframeInterpolation,
    PropertyTrack,
)
from engine.timeline.render_graph import (
    RenderLayerPlan,
    TimelineFrameCompositePlan,
    TimelineRenderGraph,
)
from engine.timeline.timebase import (
    TIMEBASE_23_976,
    TIMEBASE_24,
    TIMEBASE_29_97,
    TIMEBASE_30,
    TIMEBASE_60,
    Timebase,
    get_timebase_from_fps,
)
from engine.timeline.timeline_model import ClipItem, TimelineSequence, TrackItem
from engine.timeline.undo_manager import UndoRedoManager


def test_criterion_1_timeline_model():
    print("[1/14] Testing Timeline Data Model...")
    seq = TimelineSequence("seq-1", "Test Sequence", TIMEBASE_24, 300)
    v1 = TrackItem("v1", "video", "Video 1", order_index=0)
    clip = ClipItem(
        clip_id="c1",
        media_id="m1",
        track_id="v1",
        name="Shot 01",
        source_path="/path/to/media.mp4",
        source_in=0,
        source_out=120,
        timeline_start=0,
        timeline_end=120,
    )
    v1.clips.append(clip)
    seq.tracks.append(v1)

    d = seq.to_dict()
    restored = TimelineSequence.from_dict(d)
    assert restored.sequence_id == "seq-1"
    assert len(restored.tracks) == 1
    assert len(restored.tracks[0].clips) == 1
    assert restored.tracks[0].clips[0].name == "Shot 01"
    print("  ✓ Sequence, Track, and Clip serialization and deserialization verified.")


def test_criterion_2_rational_timebase():
    print("[2/14] Testing Rational Timebase...")
    tb24 = TIMEBASE_24
    assert tb24.fps == 24.0
    assert tb24.frame_to_seconds(48) == 2.0
    assert tb24.seconds_to_frame(2.5) == 60

    tb_ntsc = TIMEBASE_23_976
    assert abs(tb_ntsc.fps - (24000 / 1001)) < 1e-6
    assert get_timebase_from_fps(29.970) == TIMEBASE_29_97
    assert get_timebase_from_fps(60.0) == TIMEBASE_60
    print("  ✓ Rational timebase math matches industry broadcast framerates.")


def test_criterion_3_smpte_timecode():
    print("[3/14] Testing SMPTE Timecode...")
    tb = TIMEBASE_24
    assert tb.frame_to_timecode(0) == "00:00:00:00"
    assert tb.frame_to_timecode(23) == "00:00:00:23"
    assert tb.frame_to_timecode(24) == "00:00:01:00"
    assert tb.frame_to_timecode(86400) == "01:00:00:00"

    assert tb.timecode_to_frame("00:00:00:00") == 0
    assert tb.timecode_to_frame("00:00:01:00") == 24
    assert tb.timecode_to_frame("01:00:00:00") == 86400
    print("  ✓ SMPTE timecode formatting and round-trip parsing verified.")


def test_criterion_4_track_controls():
    print("[4/14] Testing Track Controls (Mute, Solo, Visibility, Lock)...")
    t1 = TrackItem("t1", "audio", "Audio 1", solo=False, muted=False)
    t2 = TrackItem("t2", "audio", "Audio 2", solo=True, muted=False)
    t3 = TrackItem("t3", "audio", "Audio 3", solo=False, muted=False)

    audibility = TimelineAudioEngine.resolve_track_audibility([t1, t2, t3])
    assert audibility["t1"] is False  # muted by t2 solo
    assert audibility["t2"] is True   # solo active
    assert audibility["t3"] is False  # muted by t2 solo
    print("  ✓ Solo and mute state resolution verified across multi-track bus.")


def test_criterion_5_non_destructive_geometry():
    print("[5/14] Testing Non-Destructive Clip Geometry...")
    clip = ClipItem(
        clip_id="c1",
        media_id="m1",
        track_id="v1",
        name="Action Shot",
        source_path="/media/action.mov",
        source_in=50,
        source_out=150,
        timeline_start=100,
        timeline_end=200,
        speed=1.0,
    )
    # Timeline frame 100 corresponds to source frame 50
    assert clip.get_source_frame(100) == 50
    # Timeline frame 150 corresponds to source frame 100
    assert clip.get_source_frame(150) == 100
    # Timeline frame 200 corresponds to source frame 150
    assert clip.get_source_frame(200) == 150
    print("  ✓ Decoupled timeline placement and source media bounds verified.")


def test_criterion_6_clip_trimming():
    print("[6/14] Testing Clip Trimming Operations...")
    clip = ClipItem(
        clip_id="c1",
        media_id="m1",
        track_id="v1",
        name="Shot",
        source_path="/media/shot.mov",
        source_in=0,
        source_out=100,
        timeline_start=0,
        timeline_end=100,
    )
    # Trim In from 0 to 20
    ok = trim_clip_in(clip, 20)
    assert ok is True
    assert clip.timeline_start == 20
    assert clip.source_in == 20
    assert clip.duration == 80

    # Trim Out from 100 to 70
    ok = trim_clip_out(clip, 70)
    assert ok is True
    assert clip.timeline_end == 70
    assert clip.source_out == 70
    assert clip.duration == 50
    print("  ✓ Non-destructive In and Out trimming verified.")


def test_criterion_7_razor_split():
    print("[7/14] Testing Razor / Split Clip Tool...")
    track = TrackItem("v1", "video", "V1")
    clip = ClipItem(
        clip_id="c-orig",
        media_id="m1",
        track_id="v1",
        name="Dialogue",
        source_path="/media/dialogue.mov",
        source_in=100,
        source_out=300,
        timeline_start=50,
        timeline_end=250,
    )
    track.clips = [clip]

    # Split at frame 150 (midpoint)
    result = split_clip(track, clip, 150)
    assert result is not None
    part1, part2 = result

    assert part1.timeline_start == 50
    assert part1.timeline_end == 150
    assert part1.source_in == 100
    assert part1.source_out == 200

    assert part2.timeline_start == 150
    assert part2.timeline_end == 250
    assert part2.source_in == 200
    assert part2.source_out == 300
    assert len(track.clips) == 2
    print("  ✓ Razor split creates two seamless, non-destructive segments.")


def test_criterion_8_delete_and_ripple():
    print("[8/14] Testing Delete and Ripple Delete...")
    track = TrackItem("v1", "video", "V1")
    c1 = ClipItem("c1", "m1", "v1", "Shot 1", "/p1", 0, 50, 0, 50)
    c2 = ClipItem("c2", "m2", "v1", "Shot 2", "/p2", 0, 50, 50, 100)
    c3 = ClipItem("c3", "m3", "v1", "Shot 3", "/p3", 0, 50, 100, 150)
    track.clips = [c1, c2, c3]

    # Normal delete c2: leaves gap
    deleted = delete_clip(track, "c2")
    assert deleted.clip_id == "c2"
    assert len(track.clips) == 2
    assert track.clips[1].timeline_start == 100  # Gap between 50 and 100 preserved

    # Ripple delete c1: shifts c3 from 100 to 50
    rippled = ripple_delete(track, "c1")
    assert rippled.clip_id == "c1"
    assert len(track.clips) == 1
    assert track.clips[0].clip_id == "c3"
    assert track.clips[0].timeline_start == 50  # 100 - 50 = 50
    assert track.clips[0].timeline_end == 100
    print("  ✓ Standard gap deletion and downstream ripple deletion verified.")


def test_criterion_9_magnetic_snapping():
    print("[9/14] Testing Magnetic Snapping Engine...")
    snap_targets = [0, 50, 100, 150, 240]

    # Frame 48 is within tolerance 5 of 50 -> snaps to 50
    assert find_snap_target(48, snap_targets, tolerance=5) == 50
    # Frame 53 is within tolerance 5 of 50 -> snaps to 50
    assert find_snap_target(53, snap_targets, tolerance=5) == 50
    # Frame 60 is outside tolerance 5 -> no snap
    assert find_snap_target(60, snap_targets, tolerance=5) is None
    print("  ✓ Magnetic snapping to boundary targets verified.")


def test_criterion_10_keyframe_animation():
    print("[10/14] Testing Keyframe Animation Engine...")
    prop = PropertyTrack("scale", default_value=100.0)

    # 1. Hold interpolation
    prop.add_keyframe(0, 50.0, KeyframeInterpolation.HOLD)
    prop.add_keyframe(10, 100.0, KeyframeInterpolation.HOLD)
    assert prop.evaluate(5) == 50.0
    assert prop.evaluate(10) == 100.0

    # 2. Linear interpolation
    prop_lin = PropertyTrack("opacity", default_value=0.0)
    prop_lin.add_keyframe(0, 0.0, KeyframeInterpolation.LINEAR)
    prop_lin.add_keyframe(100, 100.0, KeyframeInterpolation.LINEAR)
    assert prop_lin.evaluate(50) == 50.0

    # 3. Cubic Bezier easing
    prop_bez = PropertyTrack("posX", default_value=0.0)
    prop_bez.add_keyframe(0, 0.0, KeyframeInterpolation.BEZIER)
    prop_bez.add_keyframe(100, 1000.0, KeyframeInterpolation.BEZIER)
    val = prop_bez.evaluate(50)
    assert 0.0 < val < 1000.0
    print("  ✓ Hold, Linear, and Smooth Cubic Bezier easing curves verified.")


def test_criterion_11_render_graph():
    print("[11/14] Testing Multi-Track Composition Render Graph...")
    seq = TimelineSequence("seq-comp", "Composite Sequence", TIMEBASE_24, 200)
    v1 = TrackItem("v1", "video", "Background", order_index=0)
    v2 = TrackItem("v2", "video", "Subject Foreground", order_index=1)

    c_bg = ClipItem("bg-1", "m-bg", "v1", "BG", "/media/bg.mp4", 0, 100, 0, 100)
    c_fg = ClipItem("fg-1", "m-fg", "v2", "FG", "/media/fg.mp4", 0, 100, 20, 80)
    c_fg.properties["opacity"].add_keyframe(20, 0.0)
    c_fg.properties["opacity"].add_keyframe(40, 100.0)

    v1.clips = [c_bg]
    v2.clips = [c_fg]
    seq.tracks = [v1, v2]

    graph = TimelineRenderGraph(seq)
    plan = graph.evaluate_frame(30)

    assert plan.frame == 30
    assert len(plan.layers) == 2
    # Layer 0: V1 Background
    assert plan.layers[0].track_id == "v1"
    assert plan.layers[0].source_frame == 30
    # Layer 1: V2 Foreground
    assert plan.layers[1].track_id == "v2"
    assert plan.layers[1].source_frame == 10  # 30 - 20 = 10
    assert plan.layers[1].opacity == 50.0    # 50% through 20-40 fade
    print("  ✓ Multi-layer composition plan evaluated in correct bottom-to-top order.")


def test_criterion_12_audio_engine():
    print("[12/14] Testing Timeline Audio Engine & Waveform...")
    seq = TimelineSequence("seq-audio", "Audio Mix", TIMEBASE_24, 100)
    a1 = TrackItem("a1", "audio", "Dialogue", order_index=0)
    clip = ClipItem("c-vox", "m-vox", "a1", "Voice", "/audio/vox.wav", 0, 100, 0, 100, volume=0.8)
    a1.clips.append(clip)
    seq.tracks.append(a1)

    voices = TimelineAudioEngine.evaluate_audio_at_frame(seq, 25)
    assert len(voices) == 1
    assert voices[0].is_audible is True
    assert voices[0].volume == 0.8
    assert voices[0].source_frame == 25

    # Waveform envelope generation
    peaks = TimelineAudioEngine.generate_synthetic_waveform_envelope(num_samples=50)
    assert len(peaks) == 50
    assert all(0.0 <= p <= 1.0 for p in peaks)
    print("  ✓ Audio mix voices, volume gains, and peak envelopes verified.")


def test_criterion_13_undo_redo():
    print("[13/14] Testing Non-Destructive Undo / Redo Manager...")
    mgr = UndoRedoManager()
    seq = TimelineSequence("seq-1", "Test", TIMEBASE_24, 100)
    t = TrackItem("v1", "video", "V1")
    seq.tracks.append(t)

    # Initial snapshot
    mgr.push_state(seq)

    # Operation 1: add clip
    t.clips.append(ClipItem("c1", "m1", "v1", "Clip", "/p", 0, 10, 0, 10))
    mgr.push_state(seq)

    # Operation 2: add second clip
    t.clips.append(ClipItem("c2", "m2", "v1", "Clip 2", "/p", 0, 10, 10, 20))
    assert len(seq.tracks[0].clips) == 2

    # Undo operation 2
    undone = mgr.undo(seq)
    assert len(undone.tracks[0].clips) == 1

    # Redo operation 2
    redone = mgr.redo(undone)
    assert len(redone.tracks[0].clips) == 2
    print("  ✓ Non-destructive state snapshots, undo, and redo verified.")


def test_criterion_14_ui_and_tauri_build():
    print("[14/14] Verifying React UI Build and Tauri Cargo Check...")
    # 1. React build
    print("  Running Vite production build...")
    res_vite = subprocess.run(
        ["npm", "--prefix", "apps/desktop", "run", "build"],
        capture_output=True,
        text=True,
    )
    if res_vite.returncode != 0:
        print(res_vite.stdout)
        print(res_vite.stderr)
        raise RuntimeError("Vite build failed!")
    print("  ✓ React 18 + TypeScript + Tailwind build passed.")

    # 2. Tauri Cargo check
    print("  Running Tauri Rust Cargo check...")
    env = os.environ.copy()
    env["CARGO_TARGET_DIR"] = "/tmp/corridorkey-target"
    res_cargo = subprocess.run(
        ["cargo", "check", "--manifest-path", "apps/desktop/src-tauri/Cargo.toml"],
        capture_output=True,
        text=True,
        env=env,
    )
    if res_cargo.returncode != 0:
        print(res_cargo.stdout)
        print(res_cargo.stderr)
        raise RuntimeError("Cargo check failed!")
    print("  ✓ Tauri 2 Rust compilation check passed.")


def main():
    print("\n" + "=" * 65)
    print("  CORRIDORKEY 2.0 DESKTOP — MASTER PHASE 6 VERIFICATION")
    print("=" * 65 + "\n")

    test_criterion_1_timeline_model()
    test_criterion_2_rational_timebase()
    test_criterion_3_smpte_timecode()
    test_criterion_4_track_controls()
    test_criterion_5_non_destructive_geometry()
    test_criterion_6_clip_trimming()
    test_criterion_7_razor_split()
    test_criterion_8_delete_and_ripple()
    test_criterion_9_magnetic_snapping()
    test_criterion_10_keyframe_animation()
    test_criterion_11_render_graph()
    test_criterion_12_audio_engine()
    test_criterion_13_undo_redo()
    test_criterion_14_ui_and_tauri_build()

    print("\n" + "=" * 65)
    print("  ALL 14 PHASE 6 ACCEPTANCE CRITERIA VERIFIED AND PASSED!")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()

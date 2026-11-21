"""Unit tests for CorridorKey 2.0 Desktop Non-Destructive Timeline Engine."""

import unittest

from engine.timeline.audio_engine import TimelineAudioEngine
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
    KeyframeInterpolation,
    PropertyTrack,
)
from engine.timeline.render_graph import TimelineRenderGraph
from engine.timeline.timebase import (
    TIMEBASE_23_976,
    TIMEBASE_24,
    TIMEBASE_29_97,
    TIMEBASE_30,
    get_timebase_from_fps,
)
from engine.timeline.timeline_model import ClipItem, TimelineSequence, TrackItem
from engine.timeline.undo_manager import UndoRedoManager


class TestTimelineEngine(unittest.TestCase):
    def test_rational_timebase(self):
        tb24 = TIMEBASE_24
        self.assertEqual(tb24.fps, 24.0)
        self.assertEqual(tb24.frame_to_seconds(48), 2.0)
        self.assertEqual(tb24.seconds_to_frame(2.0), 48)
        self.assertEqual(tb24.frame_to_timecode(0), "00:00:00:00")
        self.assertEqual(tb24.frame_to_timecode(25), "00:00:01:01")
        self.assertEqual(tb24.timecode_to_frame("00:00:01:01"), 25)

        tb_ntsc = TIMEBASE_23_976
        self.assertAlmostEqual(tb_ntsc.fps, 23.9760239, places=4)
        self.assertEqual(get_timebase_from_fps(29.97), TIMEBASE_29_97)

    def test_keyframe_interpolation(self):
        track = PropertyTrack("opacity", default_value=100.0)
        self.assertEqual(track.evaluate(10), 100.0)

        track.add_keyframe(10, 0.0, KeyframeInterpolation.LINEAR)
        track.add_keyframe(20, 100.0, KeyframeInterpolation.LINEAR)

        # Before first keyframe
        self.assertEqual(track.evaluate(5), 0.0)
        # Linear interpolation
        self.assertEqual(track.evaluate(15), 50.0)
        # After last keyframe
        self.assertEqual(track.evaluate(25), 100.0)

        # Bezier interpolation
        track_bezier = PropertyTrack("scale", default_value=100.0)
        track_bezier.add_keyframe(0, 0.0, KeyframeInterpolation.BEZIER)
        track_bezier.add_keyframe(100, 200.0, KeyframeInterpolation.BEZIER)
        mid_val = track_bezier.evaluate(50)
        self.assertGreater(mid_val, 0.0)
        self.assertLess(mid_val, 200.0)

    def test_edit_operations(self):
        track = TrackItem(track_id="v1", type="video", name="Video 1")
        clip1 = ClipItem(
            clip_id="c1",
            media_id="m1",
            track_id="v1",
            name="Shot 1",
            source_path="/path/to/shot1.mp4",
            source_in=0,
            source_out=100,
            timeline_start=0,
            timeline_end=100,
        )
        clip2 = ClipItem(
            clip_id="c2",
            media_id="m2",
            track_id="v1",
            name="Shot 2",
            source_path="/path/to/shot2.mp4",
            source_in=50,
            source_out=150,
            timeline_start=120,
            timeline_end=220,
        )
        track.clips = [clip1, clip2]

        # 1. Trimming In
        ok = trim_clip_in(clip1, 10)
        self.assertTrue(ok)
        self.assertEqual(clip1.timeline_start, 10)
        self.assertEqual(clip1.source_in, 10)
        self.assertEqual(clip1.duration, 90)

        # 2. Trimming Out
        ok = trim_clip_out(clip1, 80)
        self.assertTrue(ok)
        self.assertEqual(clip1.timeline_end, 80)
        self.assertEqual(clip1.source_out, 80)
        self.assertEqual(clip1.duration, 70)

        # 3. Splitting clip (Razor)
        res = split_clip(track, clip2, 160)
        self.assertIsNotNone(res)
        h1, h2 = res
        self.assertEqual(h1.timeline_start, 120)
        self.assertEqual(h1.timeline_end, 160)
        self.assertEqual(h2.timeline_start, 160)
        self.assertEqual(h2.timeline_end, 220)
        self.assertEqual(len(track.clips), 3)

        # 4. Ripple delete
        # Delete first half of split clip (duration = 40 frames)
        rippled = ripple_delete(track, h1.clip_id)
        self.assertEqual(rippled.clip_id, h1.clip_id)
        self.assertEqual(len(track.clips), 2)
        # Verify second half shifted left by 40 frames: 160 - 40 = 120
        self.assertEqual(h2.timeline_start, 120)
        self.assertEqual(h2.timeline_end, 180)

        # 5. Magnetic Snapping
        candidates = [0, 80, 120, 180]
        self.assertEqual(find_snap_target(78, candidates, tolerance=5), 80)
        self.assertIsNone(find_snap_target(70, candidates, tolerance=5))

    def test_render_graph(self):
        seq = TimelineSequence(sequence_id="seq-1", name="Main Comp", duration_frames=240)
        v1 = TrackItem(track_id="t-v1", type="video", name="V1", order_index=0)
        v2 = TrackItem(track_id="t-v2", type="video", name="V2", order_index=1)
        a1 = TrackItem(track_id="t-a1", type="audio", name="A1", order_index=0)

        c1 = ClipItem(
            clip_id="c-bg",
            media_id="m-bg",
            track_id="t-v1",
            name="Background",
            source_path="/media/bg.mov",
            source_in=0,
            source_out=200,
            timeline_start=0,
            timeline_end=200,
        )
        c2 = ClipItem(
            clip_id="c-fg",
            media_id="m-fg",
            track_id="t-v2",
            name="Subject Foreground",
            source_path="/media/fg.mov",
            source_in=10,
            source_out=110,
            timeline_start=50,
            timeline_end=150,
        )
        c2.properties["opacity"].add_keyframe(50, 0.0)
        c2.properties["opacity"].add_keyframe(70, 100.0)

        v1.clips = [c1]
        v2.clips = [c2]
        seq.tracks = [v1, v2, a1]

        graph = TimelineRenderGraph(seq)

        # Frame 20: Only V1 is active
        plan20 = graph.evaluate_frame(20)
        self.assertEqual(len(plan20.layers), 1)
        self.assertEqual(plan20.layers[0].clip_id, "c-bg")
        self.assertEqual(plan20.layers[0].source_frame, 20)

        # Frame 60: Both V1 and V2 active; V2 has 50% opacity
        plan60 = graph.evaluate_frame(60)
        self.assertEqual(len(plan60.layers), 2)
        self.assertEqual(plan60.layers[0].clip_id, "c-bg")
        self.assertEqual(plan60.layers[1].clip_id, "c-fg")
        self.assertEqual(plan60.layers[1].source_frame, 20)  # 10 + (60 - 50) = 20
        self.assertEqual(plan60.layers[1].opacity, 50.0)

    def test_undo_redo(self):
        seq = TimelineSequence(sequence_id="seq-1", name="Sequence", duration_frames=100)
        track = TrackItem(track_id="v1", type="video", name="V1")
        seq.tracks.append(track)

        undo_mgr = UndoRedoManager()
        self.assertFalse(undo_mgr.can_undo)

        # Push state before change
        undo_mgr.push_state(seq)

        # Make change: add clip
        c = ClipItem("c1", "m1", "v1", "Clip 1", "/path", 0, 50, 0, 50)
        track.clips.append(c)
        self.assertEqual(len(seq.tracks[0].clips), 1)

        # Undo
        restored = undo_mgr.undo(seq)
        self.assertIsNotNone(restored)
        self.assertEqual(len(restored.tracks[0].clips), 0)
        self.assertTrue(undo_mgr.can_redo)

        # Redo
        redone = undo_mgr.redo(restored)
        self.assertIsNotNone(redone)
        self.assertEqual(len(redone.tracks[0].clips), 1)


if __name__ == "__main__":
    unittest.main()

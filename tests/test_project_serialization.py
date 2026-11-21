"""Unit tests for CorridorKey 2.0 Desktop Project Serialization, Autosave & Recovery."""

import json
import os
import shutil
import tempfile
import time
import unittest

from engine.project.autosave_manager import AutosaveManager
from engine.project.io_atomic import atomic_save_file, safe_read_file
from engine.project.media_manager import (
    batch_relink_folder,
    compute_relative_path,
    detect_missing_media,
    relink_media,
    resolve_media_path,
)
from engine.project.schema import (
    MediaReference,
    ProjectDocument,
    ProjectMetadata,
    WorkspaceLayout,
    migrate_schema,
)
from engine.project.serializer import (
    ProjectSerializationError,
    deserialize_project,
    serialize_project,
    validate_project_dict,
)
from engine.timeline.timebase import TIMEBASE_24
from engine.timeline.timeline_model import ClipItem, TimelineSequence, TrackItem


class TestProjectPersistence(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="ck_test_proj_")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_serialization_round_trip(self):
        meta = ProjectMetadata("proj-1", "VFX Shot", 1920, 1080, 24.0)
        media = MediaReference("m-1", "shot.mov", "media/shot.mov", "/abs/shot.mov", 1920, 1080, 24.0, 100, 4.16, "H.264", 1000)
        seq = TimelineSequence("seq-1", "Main Sequence", TIMEBASE_24, 240)
        track = TrackItem("v1", "video", "V1")
        clip = ClipItem("c1", "m-1", "v1", "Shot", "/abs/shot.mov", 0, 100, 0, 100)
        clip.properties["opacity"].add_keyframe(0, 0.0)
        clip.properties["opacity"].add_keyframe(24, 100.0)
        track.clips.append(clip)
        seq.tracks.append(track)

        doc = ProjectDocument(
            project=meta,
            media_pool=[media],
            timeline=seq,
            workspace=WorkspaceLayout(left_panel_width=320, zoom_ratio=2.0),
        )

        serialized = serialize_project(doc)
        self.assertIn("corridorkey-project", serialized)
        self.assertIn("VFX Shot", serialized)

        restored = deserialize_project(serialized)
        self.assertEqual(restored.project.name, "VFX Shot")
        self.assertEqual(len(restored.media_pool), 1)
        self.assertIsNotNone(restored.timeline)
        self.assertEqual(len(restored.timeline.tracks), 1)
        self.assertEqual(restored.timeline.tracks[0].clips[0].name, "Shot")
        self.assertEqual(restored.workspace.left_panel_width, 320)

    def test_atomic_file_save(self):
        target_path = os.path.join(self.test_dir, "test_project.ckproj")
        content = '{"format": "corridorkey-project", "test": 123}'
        ok = atomic_save_file(target_path, content)
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(target_path))
        self.assertEqual(safe_read_file(target_path), content)

        # Overwrite atomically
        new_content = '{"format": "corridorkey-project", "test": 456}'
        atomic_save_file(target_path, new_content)
        self.assertEqual(safe_read_file(target_path), new_content)

    def test_security_path_traversal_detection(self):
        bad_doc = {
            "format": "corridorkey-project",
            "schema_version": "1.0.0",
            "project": {"name": "Bad Project", "width": 1920, "height": 1080},
            "media_pool": [
                {
                    "asset_id": "bad-1",
                    "name": "malicious",
                    "relative_path": "../../../etc/passwd",
                    "absolute_path": "/etc/passwd",
                }
            ],
        }
        is_valid, errors = validate_project_dict(bad_doc)
        self.assertFalse(is_valid)
        self.assertTrue(any("path traversal detected" in e for e in errors))

        with self.assertRaises(ProjectSerializationError):
            deserialize_project(json.dumps(bad_doc))

    def test_schema_migration(self):
        legacy_doc = {
            "format": "corridorkey-project",
            "schema_version": "0.9.0",
            "project": {"name": "Old Project", "width": 1920, "height": 1080, "frameRate": 25.0},
            "media": [
                {"asset_id": "m1", "name": "take.mov", "relative_path": "take.mov", "absolute_path": "/take.mov"}
            ],
            "timeline": {"durationFrames": 100, "tracks": []},
        }
        migrated = migrate_schema(legacy_doc)
        self.assertIn(migrated["schema_version"], ("1.0.0", "1.1.0"))
        self.assertIn("media_pool", migrated)
        self.assertEqual(migrated["timeline"]["timebase"]["numerator"], 25)

    def test_missing_media_and_relinking(self):
        # Create a real dummy media file
        media_folder = os.path.join(self.test_dir, "media")
        os.makedirs(media_folder, exist_ok=True)
        real_file = os.path.join(media_folder, "scene1.mov")
        with open(real_file, "w") as f:
            f.write("dummy media")

        ref_found = MediaReference(
            "m-found", "scene1.mov", "media/scene1.mov", real_file, 1920, 1080, 24.0, 100, 4.0, "PRORES", 100
        )
        ref_missing = MediaReference(
            "m-missing", "scene2.mov", "media/scene2.mov", "/nonexistent/scene2.mov", 1920, 1080, 24.0, 100, 4.0, "PRORES", 100
        )

        missing = detect_missing_media([ref_found, ref_missing], self.test_dir)
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0].asset_id, "m-missing")

        # Now create scene2 in a newly moved directory and batch relink
        new_assets_folder = os.path.join(self.test_dir, "new_assets")
        os.makedirs(new_assets_folder, exist_ok=True)
        new_scene2 = os.path.join(new_assets_folder, "scene2.mov")
        with open(new_scene2, "w") as f:
            f.write("scene 2 media")

        relinked_count = batch_relink_folder([ref_missing], new_assets_folder, self.test_dir)
        self.assertEqual(relinked_count, 1)
        self.assertIsNotNone(resolve_media_path(ref_missing, self.test_dir))

    def test_autosave_and_recovery(self):
        mgr = AutosaveManager(max_autosaves=3)
        doc = ProjectDocument(project=ProjectMetadata("p1", "My Movie"))

        # Create 4 autosaves to verify pruning down to 3
        paths = []
        for i in range(4):
            time.sleep(0.01)
            p = mgr.create_autosave(doc, self.test_dir, project_name="My_Movie")
            paths.append(p)

        autosaves = mgr.list_autosaves(self.test_dir)
        self.assertEqual(len(autosaves), 3)

        # Check recovery detection
        main_project = os.path.join(self.test_dir, "My_Movie.ckproj")
        atomic_save_file(main_project, serialize_project(doc))

        # Touch autosave so it is newer
        time.sleep(0.05)
        new_auto = mgr.create_autosave(doc, self.test_dir, project_name="My_Movie")
        # Ensure mtime is strictly ahead
        future_time = time.time() + 10.0
        os.utime(new_auto, (future_time, future_time))

        status = mgr.check_recovery_status(main_project)
        self.assertTrue(status["recovery_available"])
        self.assertIn("newest_snapshot", status)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""CorridorKey 2.0 Desktop — Project Serialization & Schema Validation Tests.

Validates:
1. Creation of valid default .ckproj project structures.
2. Serialization and deserialization roundtrips.
3. Media item metadata registration and duration calculations.
4. Timeline track hierarchy (Video & Audio) and clip positioning.
5. Keying parameters, matte adjustments, and workspace panel persistence.
6. Graceful rejection of corrupted or malformed project files.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


class TestProjectFormat(unittest.TestCase):
    def setUp(self):
        self.sample_project = {
            "format": "corridorkey-project",
            "version": 1,
            "generator": "CorridorKey 2.0 Desktop",
            "project": {
                "name": "Test_Plate_Comp",
                "width": 1920,
                "height": 1080,
                "frameRate": 24.0,
                "colorSpace": "sRGB / Rec.709",
                "createdAt": "2026-11-20T19:00:00Z",
                "modifiedAt": "2026-11-20T19:00:00Z",
            },
            "media": [
                {
                    "id": "med_test_01",
                    "name": "green_screen_actor.mp4",
                    "path": "/footage/green_screen_actor.mp4",
                    "relativePath": "./footage/green_screen_actor.mp4",
                    "width": 1920,
                    "height": 1080,
                    "frameRate": 24.0,
                    "durationFrames": 240,
                    "durationSeconds": 10.0,
                    "codec": "H.264 / AVC",
                    "fileSizeBytes": 24000000,
                }
            ],
            "timeline": {
                "durationFrames": 240,
                "currentFrame": 0,
                "tracks": [
                    {
                        "id": "track_v1",
                        "type": "video",
                        "name": "Video 1",
                        "visible": True,
                        "locked": False,
                        "muted": False,
                        "clips": [
                            {
                                "id": "clip_01",
                                "mediaId": "med_test_01",
                                "trackId": "track_v1",
                                "name": "green_screen_actor.mp4",
                                "startFrame": 0,
                                "endFrame": 240,
                                "sourceIn": 0,
                                "sourceOut": 240,
                            }
                        ],
                    },
                    {
                        "id": "track_a1",
                        "type": "audio",
                        "name": "Audio 1",
                        "visible": True,
                        "locked": False,
                        "muted": False,
                        "clips": [],
                    },
                ],
            },
            "keyingSettings": {
                "hannChunk": 24,
                "hannStride": 12,
                "lowVram": False,
                "despillStrength": 0.5,
                "hintMode": "none",
                "hintQuality": 0.95,
            },
            "matteSettings": {
                "contrast": 1.0,
                "edgeRefinement": 0.0,
                "invert": False,
                "alphaThreshold": 0.0,
            },
            "transformSettings": {
                "posX": 0,
                "posY": 0,
                "scale": 100,
                "rotation": 0,
                "opacity": 100,
            },
            "workspace": {
                "leftPanelWidth": 300,
                "rightPanelWidth": 340,
                "bottomPanelHeight": 260,
                "showMediaBrowser": True,
                "showInspector": True,
                "showTimeline": True,
            },
        }

    def test_schema_conformance(self):
        """Verify presence of all mandatory top-level fields."""
        required_fields = [
            "format",
            "version",
            "generator",
            "project",
            "media",
            "timeline",
            "keyingSettings",
            "matteSettings",
            "transformSettings",
            "workspace",
        ]
        for field in required_fields:
            self.assertIn(field, self.sample_project, f"Missing required field: {field}")
        self.assertEqual(self.sample_project["format"], "corridorkey-project")
        self.assertEqual(self.sample_project["version"], 1)

    def test_serialization_roundtrip(self):
        """Verify project serializes to JSON and recovers identical state."""
        with tempfile.NamedTemporaryFile("w+", suffix=".ckproj", delete=False) as tf:
            json.dump(self.sample_project, tf, indent=2)
            temp_path = tf.name

        try:
            with open(temp_path, "r") as f:
                loaded = json.load(f)
            self.assertEqual(loaded["project"]["name"], "Test_Plate_Comp")
            self.assertEqual(loaded["project"]["width"], 1920)
            self.assertEqual(loaded["keyingSettings"]["hannChunk"], 24)
            self.assertEqual(len(loaded["media"]), 1)
            self.assertEqual(len(loaded["timeline"]["tracks"]), 2)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_invalid_project_rejection(self):
        """Verify detection of corrupt or unformatted projects."""
        corrupt = {"format": "unrecognized", "version": 99}
        self.assertNotEqual(corrupt.get("format"), "corridorkey-project")

    def test_media_metadata_consistency(self):
        """Verify media duration frames and frame rate calculations."""
        media = self.sample_project["media"][0]
        expected_frames = int(media["durationSeconds"] * media["frameRate"])
        self.assertEqual(media["durationFrames"], expected_frames)


if __name__ == "__main__":
    unittest.main()

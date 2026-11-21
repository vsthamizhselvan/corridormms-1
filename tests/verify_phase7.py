#!/usr/bin/env python3
"""CorridorKey 2.0 Desktop — Master Phase 7 Verification Script.

Validates all 12 Phase 7 Acceptance Criteria:
1. Native .ckproj format compliance.
2. Complete timeline serialization (tracks, clips, keyframes, timebases).
3. Media references persistence (asset IDs, relative & absolute paths).
4. Full round-trip project save & reopen.
5. Autosave system (atomic writes & snapshot retention pruning).
6. Crash recovery detection and snapshot inspection.
7. Missing media detection and folder batch-relinking.
8. Manual backup snapshots in .ck_backups/.
9. Workspace layout persistence and restoration.
10. Schema version migration (0.9.0 -> 1.0.0).
11. Corrupted file & path-traversal security rejection.
12. Frontend Vite build & Tauri Rust Cargo verification.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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
    CURRENT_SCHEMA_VERSION,
    ExportSettings,
    KeyingSettings,
    MatteSettings,
    MediaReference,
    ProjectDocument,
    ProjectMetadata,
    ViewerSettings,
    WorkspaceLayout,
    migrate_schema,
)
from engine.project.serializer import (
    ProjectSerializationError,
    deserialize_project,
    serialize_project,
    validate_project_dict,
)
from engine.timeline.keyframe_engine import KeyframeInterpolation
from engine.timeline.timebase import TIMEBASE_24, TIMEBASE_23_976
from engine.timeline.timeline_model import ClipItem, TimelineSequence, TrackItem


def test_criterion_1_native_format():
    print("[1/12] Testing Native .ckproj Format Specification...")
    doc = ProjectDocument()
    serialized = serialize_project(doc)
    d = json.loads(serialized)
    assert d["format"] == "corridorkey-project"
    assert d["schema_version"] in ("1.0.0", "1.1.0")
    assert "project" in d
    assert "media_pool" in d
    assert "settings" in d
    assert "workspace" in d
    print("  ✓ Native .ckproj schema structure verified.")


def test_criterion_2_timeline_serialization():
    print("[2/12] Testing Complete Timeline Serialization...")
    seq = TimelineSequence("seq-vfx", "Main VFX Comp", TIMEBASE_23_976, 240)
    v1 = TrackItem("t-v1", "video", "Background", order_index=0)
    v2 = TrackItem("t-v2", "video", "Foreground", order_index=1)

    c1 = ClipItem("c1", "m1", "t-v1", "BG Plate", "/path/bg.mov", 0, 240, 0, 240)
    c2 = ClipItem("c2", "m2", "t-v2", "Actor Green", "/path/actor.mov", 10, 110, 20, 120)
    c2.properties["opacity"].add_keyframe(20, 0.0, KeyframeInterpolation.LINEAR)
    c2.properties["opacity"].add_keyframe(40, 100.0, KeyframeInterpolation.BEZIER)

    v1.clips = [c1]
    v2.clips = [c2]
    seq.tracks = [v1, v2]

    doc = ProjectDocument(timeline=seq)
    raw_json = serialize_project(doc)
    restored = deserialize_project(raw_json)

    assert restored.timeline is not None
    assert len(restored.timeline.tracks) == 2
    assert restored.timeline.tracks[1].clips[0].name == "Actor Green"
    assert len(restored.timeline.tracks[1].clips[0].properties["opacity"].keyframes) == 2
    print("  ✓ Full timeline, tracks, clips, and keyframes verified across serialization.")


def test_criterion_3_media_references(tmp_dir):
    print("[3/12] Testing Media References Persistence...")
    dummy_media = os.path.join(tmp_dir, "footage.mov")
    with open(dummy_media, "w") as f:
        f.write("test video")

    rel = compute_relative_path(dummy_media, tmp_dir)
    ref = MediaReference(
        asset_id="asset-1",
        name="footage.mov",
        relative_path=rel,
        absolute_path=dummy_media,
        width=3840,
        height=2160,
        frame_rate=23.976,
        duration_frames=480,
        duration_seconds=20.0,
        codec="PRORES_4444",
        file_size_bytes=1024,
    )

    doc = ProjectDocument(media_pool=[ref])
    raw = serialize_project(doc)
    restored = deserialize_project(raw)

    assert len(restored.media_pool) == 1
    m = restored.media_pool[0]
    assert m.asset_id == "asset-1"
    assert m.width == 3840
    assert m.codec == "PRORES_4444"
    assert resolve_media_path(m, tmp_dir) == os.path.abspath(dummy_media)
    print("  ✓ Dual relative/absolute media references persist and resolve.")


def test_criterion_4_save_and_reopen(tmp_dir):
    print("[4/12] Testing Atomic Save & Reopen Cycle...")
    proj_path = os.path.join(tmp_dir, "Production_Shot.ckproj")
    doc = ProjectDocument(
        project=ProjectMetadata("p-prod", "Production Shot", 1920, 1080, 24.0)
    )

    # Atomic write
    atomic_save_file(proj_path, serialize_project(doc))
    assert os.path.exists(proj_path)

    # Reopen
    content = safe_read_file(proj_path)
    restored = deserialize_project(content)
    assert restored.project.name == "Production Shot"
    print("  ✓ Atomic write to disk and safe reopen cycle verified.")


def test_criterion_5_autosave_system(tmp_dir):
    print("[5/12] Testing Autosave Subsystem & Retention Pruning...")
    mgr = AutosaveManager(max_autosaves=3)
    doc = ProjectDocument(project=ProjectMetadata("p1", "Autosave Test"))

    # Generate 5 autosave snapshots
    for i in range(5):
        time.sleep(0.01)
        mgr.create_autosave(doc, tmp_dir, project_name="Autosave_Test")

    snapshots = mgr.list_autosaves(tmp_dir)
    assert len(snapshots) == 3, f"Expected 3 retained snapshots, got {len(snapshots)}"
    assert all("Autosave_Test_autosave_" in s["filename"] for s in snapshots)
    print("  ✓ Autosave snapshots created and pruned to retention limit.")


def test_criterion_6_crash_recovery(tmp_dir):
    print("[6/12] Testing Crash Recovery Detection...")
    mgr = AutosaveManager(max_autosaves=3)
    doc = ProjectDocument(project=ProjectMetadata("p1", "Crash Test"))

    main_proj = os.path.join(tmp_dir, "Crash_Test.ckproj")
    atomic_save_file(main_proj, serialize_project(doc))

    # Touch project mtime to past
    old_time = time.time() - 100.0
    os.utime(main_proj, (old_time, old_time))

    # Trigger newer autosave
    auto_path = mgr.create_autosave(doc, tmp_dir, project_name="Crash_Test")

    status = mgr.check_recovery_status(main_proj)
    assert status["recovery_available"] is True
    assert status["newest_snapshot"]["path"] == auto_path
    print("  ✓ Newer autosave detected as eligible crash recovery payload.")


def test_criterion_7_missing_media_and_relinking(tmp_dir):
    print("[7/12] Testing Missing Media Detection & Folder Batch-Relinking...")
    # Reference to non-existent file
    missing_ref = MediaReference(
        asset_id="lost-1",
        name="plate_v01.mov",
        relative_path="footage/plate_v01.mov",
        absolute_path="/old/drive/plate_v01.mov",
        width=1920,
        height=1080,
        frame_rate=24.0,
        duration_frames=100,
        duration_seconds=4.16,
        codec="H.264",
        file_size_bytes=100,
    )

    missing = detect_missing_media([missing_ref], tmp_dir)
    assert len(missing) == 1
    assert missing[0].name == "plate_v01.mov"

    # Now create new media folder and simulate relinking
    relinked_dir = os.path.join(tmp_dir, "relinked_assets")
    os.makedirs(relinked_dir, exist_ok=True)
    real_path = os.path.join(relinked_dir, "plate_v01.mov")
    with open(real_path, "w") as f:
        f.write("found")

    relinked_count = batch_relink_folder([missing_ref], relinked_dir, tmp_dir)
    assert relinked_count == 1
    assert resolve_media_path(missing_ref, tmp_dir) == os.path.abspath(real_path)
    print("  ✓ Missing media detected and batch-relinked from folder scan.")


def test_criterion_8_manual_backup(tmp_dir):
    print("[8/12] Testing Manual Backup Snapshots...")
    mgr = AutosaveManager()
    doc = ProjectDocument(project=ProjectMetadata("p1", "Backup Test"))

    backup_path = mgr.create_manual_backup(doc, tmp_dir, project_name="Backup_Test")
    assert os.path.exists(backup_path)
    assert ".ck_backups" in backup_path
    assert "Backup_Test_backup_" in os.path.basename(backup_path)
    print("  ✓ Timestamped manual backup generated in .ck_backups/.")


def test_criterion_9_workspace_restoration():
    print("[9/12] Testing Workspace Layout Restoration...")
    ws = WorkspaceLayout(
        left_panel_width=350,
        right_panel_width=400,
        bottom_panel_height=300,
        show_media_browser=False,
        show_inspector=True,
        show_timeline=True,
        zoom_ratio=2.5,
    )
    doc = ProjectDocument(workspace=ws)
    raw = serialize_project(doc)
    restored = deserialize_project(raw)

    assert restored.workspace.left_panel_width == 350
    assert restored.workspace.right_panel_width == 400
    assert restored.workspace.show_media_browser is False
    assert restored.workspace.zoom_ratio == 2.5
    print("  ✓ Panel dimensions, visibility flags, and zoom ratios persist.")


def test_criterion_10_schema_migration():
    print("[10/12] Testing Backward Schema Migration...")
    legacy = {
        "format": "corridorkey-project",
        "schema_version": "0.9.0",
        "project": {"name": "Legacy Project", "width": 1920, "height": 1080, "frameRate": 24.0},
        "media": [
            {"asset_id": "m1", "name": "take.mov", "relative_path": "take.mov", "absolute_path": "/take.mov"}
        ],
        "timeline": {"durationFrames": 120, "tracks": []},
    }
    migrated = migrate_schema(legacy)
    assert migrated["schema_version"] in ("1.0.0", "1.1.0")
    assert "media_pool" in migrated
    assert migrated["timeline"]["timebase"]["numerator"] == 24
    print("  ✓ Legacy 0.9.0 projects successfully upgraded to schema 1.0.0.")


def test_criterion_11_corrupted_and_security_rejection():
    print("[11/12] Testing Corrupted Project Handling & Security Checks...")
    # Corrupted JSON
    try:
        deserialize_project("{ broken json")
        assert False, "Should have raised exception on corrupted JSON"
    except ProjectSerializationError:
        pass

    # Malicious path traversal
    malicious = {
        "format": "corridorkey-project",
        "schema_version": "1.0.0",
        "project": {"name": "Exploit", "width": 1920, "height": 1080},
        "media_pool": [
            {"asset_id": "x", "name": "bad", "relative_path": "../../../sensitive.txt", "absolute_path": "/etc"}
        ],
    }
    try:
        deserialize_project(json.dumps(malicious))
        assert False, "Should have rejected path traversal"
    except ProjectSerializationError:
        pass
    print("  ✓ Corrupted payloads and path-traversal exploits rejected gracefully.")


def test_criterion_12_ui_and_tauri_build():
    print("[12/12] Testing React UI Compilation & Tauri Rust Cargo Check...")
    # 1. Vite Build
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
    print("  ✓ React 18 frontend build succeeded.")

    # 2. Tauri Cargo Check
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
    print("  ✓ Tauri 2 native Rust commands check succeeded.")


def main():
    print("\n" + "=" * 65)
    print("  CORRIDORKEY 2.0 DESKTOP — MASTER PHASE 7 VERIFICATION")
    print("=" * 65 + "\n")

    tmp_dir = tempfile.mkdtemp(prefix="ck_phase7_verify_")
    try:
        test_criterion_1_native_format()
        test_criterion_2_timeline_serialization()
        test_criterion_3_media_references(tmp_dir)
        test_criterion_4_save_and_reopen(tmp_dir)
        test_criterion_5_autosave_system(tmp_dir)
        test_criterion_6_crash_recovery(tmp_dir)
        test_criterion_7_missing_media_and_relinking(tmp_dir)
        test_criterion_8_manual_backup(tmp_dir)
        test_criterion_9_workspace_restoration()
        test_criterion_10_schema_migration()
        test_criterion_11_corrupted_and_security_rejection()
        test_criterion_12_ui_and_tauri_build()

        print("\n" + "=" * 65)
        print("  ALL 12 PHASE 7 ACCEPTANCE CRITERIA VERIFIED AND PASSED!")
        print("=" * 65 + "\n")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()

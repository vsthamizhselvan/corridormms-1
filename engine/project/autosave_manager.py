"""CorridorKey 2.0 Desktop — Autosave, Backup & Crash Recovery Subsystem.

Manages background non-blocking project autosaving, snapshot rotation,
timestamped manual backups, and crash recovery detection.
"""

from __future__ import annotations

import glob
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from engine.project.io_atomic import atomic_save_file, safe_read_file
from engine.project.schema import ProjectDocument
from engine.project.serializer import deserialize_project, serialize_project


class AutosaveManager:
    """Handles autosaves, backup snapshots, and recovery detection for projects."""

    AUTOSAVE_DIR_NAME = ".ck_autosaves"
    BACKUP_DIR_NAME = ".ck_backups"

    def __init__(self, max_autosaves: int = 5):
        self.max_autosaves = max_autosaves

    @classmethod
    def get_autosave_dir(cls, project_dir: str) -> str:
        d = os.path.join(project_dir, cls.AUTOSAVE_DIR_NAME)
        os.makedirs(d, exist_ok=True)
        return d

    @classmethod
    def get_backup_dir(cls, project_dir: str) -> str:
        d = os.path.join(project_dir, cls.BACKUP_DIR_NAME)
        os.makedirs(d, exist_ok=True)
        return d

    def create_autosave(
        self,
        doc: ProjectDocument,
        project_dir: str,
        project_name: Optional[str] = None,
    ) -> str:
        """Atomically saves an autosave snapshot and trims older snapshots."""
        autosave_dir = self.get_autosave_dir(project_dir)
        name = project_name or doc.project.name or "Untitled"
        # Sanitize filename
        safe_name = "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).rstrip().replace(" ", "_")
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{safe_name}_autosave_{timestamp}.ckproj"
        filepath = os.path.join(autosave_dir, filename)

        serialized = serialize_project(doc)
        atomic_save_file(filepath, serialized)

        # Enforce retention limit
        self._prune_autosaves(autosave_dir, safe_name)
        return filepath

    def create_manual_backup(
        self,
        doc: ProjectDocument,
        project_dir: str,
        project_name: Optional[str] = None,
    ) -> str:
        """Creates a timestamped backup snapshot in the backup directory."""
        backup_dir = self.get_backup_dir(project_dir)
        name = project_name or doc.project.name or "Untitled"
        safe_name = "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).rstrip().replace(" ", "_")
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{safe_name}_backup_{timestamp}.ckproj"
        filepath = os.path.join(backup_dir, filename)

        serialized = serialize_project(doc)
        atomic_save_file(filepath, serialized)
        return filepath

    def list_autosaves(self, project_dir: str) -> List[Dict[str, Any]]:
        """Returns list of autosave snapshots sorted newest to oldest."""
        autosave_dir = os.path.join(project_dir, self.AUTOSAVE_DIR_NAME)
        if not os.path.exists(autosave_dir):
            return []

        pattern = os.path.join(autosave_dir, "*_autosave_*.ckproj")
        files = glob.glob(pattern)
        files.sort(key=os.path.getmtime, reverse=True)

        snapshots: List[Dict[str, Any]] = []
        for f in files:
            stat = os.stat(f)
            snapshots.append({
                "path": f,
                "filename": os.path.basename(f),
                "modified_time": stat.st_mtime,
                "modified_iso": datetime.utcfromtimestamp(stat.st_mtime).isoformat() + "Z",
                "size_bytes": stat.st_size,
            })
        return snapshots

    def check_recovery_status(self, project_file_path: str) -> Dict[str, Any]:
        """Checks if a newer autosave snapshot exists relative to saved project file."""
        if not os.path.exists(project_file_path):
            return {"recovery_available": False, "reason": "Project file not found"}

        project_dir = os.path.dirname(os.path.abspath(project_file_path))
        autosaves = self.list_autosaves(project_dir)

        if not autosaves:
            return {"recovery_available": False, "snapshots": []}

        saved_mtime = os.path.getmtime(project_file_path)
        newest = autosaves[0]

        # If newest autosave is strictly newer than the project file by > 2 seconds
        if newest["modified_time"] > saved_mtime + 2.0:
            return {
                "recovery_available": True,
                "newest_snapshot": newest,
                "snapshots": autosaves,
                "saved_project_mtime": saved_mtime,
                "saved_project_iso": datetime.utcfromtimestamp(saved_mtime).isoformat() + "Z",
            }

        return {
            "recovery_available": False,
            "snapshots": autosaves,
            "saved_project_mtime": saved_mtime,
        }

    def _prune_autosaves(self, autosave_dir: str, safe_name: str) -> None:
        """Removes oldest autosave files exceeding max_autosaves."""
        pattern = os.path.join(autosave_dir, f"{safe_name}_autosave_*.ckproj")
        files = glob.glob(pattern)
        files.sort(key=os.path.getmtime)  # oldest first

        while len(files) > self.max_autosaves:
            oldest = files.pop(0)
            try:
                os.remove(oldest)
            except OSError:
                pass

"""CorridorKey 2.0 Desktop — Media Path Management & Relinking Subsystem.

Provides cross-platform asset portability by maintaining dual relative and absolute
path representations, detecting missing media assets, and supporting batch relinking.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional

from engine.project.schema import MediaReference


def compute_relative_path(abs_media_path: str, project_dir: str) -> str:
    """Computes portable relative path from project directory to media file."""
    try:
        rel = os.path.relpath(abs_media_path, project_dir)
        # Normalize to forward slashes for cross-platform portability
        return rel.replace("\\", "/")
    except ValueError:
        # Occurs on Windows if files reside on different drive letters (e.g. C: and D:)
        return os.path.basename(abs_media_path)


def resolve_media_path(media_ref: MediaReference, project_dir: str) -> Optional[str]:
    """Resolves existing path for media asset using relative path first, then absolute fallback."""
    # 1. Test relative path against project directory
    if media_ref.relative_path:
        cand_rel = os.path.normpath(os.path.join(project_dir, media_ref.relative_path))
        if os.path.exists(cand_rel) and os.path.isfile(cand_rel):
            return os.path.abspath(cand_rel)

    # 2. Test absolute path fallback
    if media_ref.absolute_path:
        if os.path.exists(media_ref.absolute_path) and os.path.isfile(media_ref.absolute_path):
            return os.path.abspath(media_ref.absolute_path)

    # 3. Test filename directly inside project directory or project/media subfolder
    filename = os.path.basename(media_ref.name or media_ref.relative_path or media_ref.absolute_path)
    cand_proj = os.path.join(project_dir, filename)
    if os.path.exists(cand_proj) and os.path.isfile(cand_proj):
        return os.path.abspath(cand_proj)

    cand_media_dir = os.path.join(project_dir, "media", filename)
    if os.path.exists(cand_media_dir) and os.path.isfile(cand_media_dir):
        return os.path.abspath(cand_media_dir)

    return None


def detect_missing_media(media_list: List[MediaReference], project_dir: str) -> List[MediaReference]:
    """Identifies all media references that cannot be found on storage."""
    missing: List[MediaReference] = []
    for m in media_list:
        resolved = resolve_media_path(m, project_dir)
        if not resolved:
            missing.append(m)
    return missing


def relink_media(media_ref: MediaReference, new_path: str, project_dir: str) -> bool:
    """Updates media reference with new path and recomputes relative path."""
    if not os.path.exists(new_path) or not os.path.isfile(new_path):
        return False

    abs_path = os.path.abspath(new_path)
    media_ref.absolute_path = abs_path
    media_ref.relative_path = compute_relative_path(abs_path, project_dir)
    media_ref.name = os.path.basename(abs_path)
    return True


def batch_relink_folder(
    media_list: List[MediaReference],
    search_folder: str,
    project_dir: str,
    recursive: bool = True,
) -> int:
    """Scans search folder for matching filenames and relinks any matching missing media."""
    if not os.path.exists(search_folder) or not os.path.isdir(search_folder):
        return 0

    # Build filename lookup table from search folder
    file_map: Dict[str, str] = {}
    if recursive:
        for root, _, files in os.walk(search_folder):
            for f in files:
                if f not in file_map:
                    file_map[f] = os.path.abspath(os.path.join(root, f))
    else:
        for f in os.listdir(search_folder):
            full = os.path.join(search_folder, f)
            if os.path.isfile(full):
                file_map[f] = os.path.abspath(full)

    relinked_count = 0
    for m in media_list:
        if resolve_media_path(m, project_dir) is None:
            # Media is missing; search filename
            fname = os.path.basename(m.name or m.relative_path or m.absolute_path)
            if fname in file_map:
                if relink_media(m, file_map[fname], project_dir):
                    relinked_count += 1

    return relinked_count

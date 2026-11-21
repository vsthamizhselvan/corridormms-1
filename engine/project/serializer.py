"""CorridorKey 2.0 Desktop — Project Serialization & Schema Validation.

Serializes and deserializes .ckproj project files with schema validation,
backward-compatibility migration, and untrusted input security checks.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from engine.project.schema import (
    CURRENT_SCHEMA_VERSION,
    SUPPORTED_SCHEMA_VERSIONS,
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
from engine.timeline.timeline_model import TimelineSequence


class ProjectSerializationError(Exception):
    """Raised when project serialization or deserialization fails."""
    pass


def validate_project_dict(d: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validates raw dictionary against .ckproj schema requirements and security rules."""
    errors: List[str] = []

    # 1. Format verification
    if d.get("format") != "corridorkey-project":
        errors.append(f"Invalid format identifier: expected 'corridorkey-project', got '{d.get('format')}'")

    # 2. Schema version verification
    ver = d.get("schema_version", "0.9.0")
    if ver not in SUPPORTED_SCHEMA_VERSIONS:
        errors.append(f"Unsupported schema version: '{ver}'. Supported: {SUPPORTED_SCHEMA_VERSIONS}")

    # 3. Project metadata
    if "project" not in d or not isinstance(d["project"], dict):
        errors.append("Missing required 'project' metadata block.")
    else:
        p = d["project"]
        if not p.get("name"):
            errors.append("Project metadata must include a non-empty 'name'.")
        if p.get("width", 0) <= 0 or p.get("height", 0) <= 0:
            errors.append("Project width and height must be positive integers.")

    # 4. Security checks on media paths (anti-path-traversal)
    media_list = d.get("media_pool") or d.get("media") or []
    if not isinstance(media_list, list):
        errors.append("'media_pool' must be a list.")
    else:
        for idx, m in enumerate(media_list):
            if not isinstance(m, dict):
                errors.append(f"Media item at index {idx} must be an object.")
                continue
            rel_path = m.get("relative_path", "")
            if ".." in rel_path.split("/"):
                errors.append(f"Security violation: path traversal detected in media relative_path: '{rel_path}'")

    # 5. Timeline integrity
    if "timeline" in d and d["timeline"] is not None:
        if not isinstance(d["timeline"], dict):
            errors.append("'timeline' must be an object or null.")
        else:
            tracks = d["timeline"].get("tracks", [])
            if not isinstance(tracks, list):
                errors.append("'timeline.tracks' must be a list.")

    return len(errors) == 0, errors


def serialize_project(doc: ProjectDocument, indent: int = 2) -> str:
    """Serializes a ProjectDocument into a formatted JSON string."""
    try:
        data = doc.to_dict()
        return json.dumps(data, indent=indent, ensure_ascii=False)
    except Exception as e:
        raise ProjectSerializationError(f"Failed to serialize project: {e}") from e


def deserialize_project(json_str: str) -> ProjectDocument:
    """Parses and validates a JSON string into a ProjectDocument."""
    try:
        raw_dict = json.loads(json_str)
    except Exception as e:
        raise ProjectSerializationError(f"Failed to parse project JSON: {e}") from e

    if not isinstance(raw_dict, dict):
        raise ProjectSerializationError("Root of project document must be a JSON object.")

    # Validate before migration
    is_valid, errors = validate_project_dict(raw_dict)
    if not is_valid:
        raise ProjectSerializationError(f"Project validation failed: {'; '.join(errors)}")

    # Migrate if needed
    data = migrate_schema(raw_dict)

    # Reconstruct document
    try:
        proj_meta = ProjectMetadata.from_dict(data["project"])
        media_pool = [MediaReference.from_dict(m) for m in data.get("media_pool", [])]

        timeline = None
        if data.get("timeline"):
            timeline = TimelineSequence.from_dict(data["timeline"])

        import inspect

        def filter_kwargs(cls, kwargs_dict):
            if not isinstance(kwargs_dict, dict):
                return {}
            sig = inspect.signature(cls)
            return {k: v for k, v in kwargs_dict.items() if k in sig.parameters}

        settings_dict = data.get("settings", {})
        keying = KeyingSettings(**filter_kwargs(KeyingSettings, settings_dict.get("keying", {})))
        matte = MatteSettings(**filter_kwargs(MatteSettings, settings_dict.get("matte", {})))
        viewer = ViewerSettings(**filter_kwargs(ViewerSettings, settings_dict.get("viewer", {})))
        export = ExportSettings(**filter_kwargs(ExportSettings, settings_dict.get("export", {})))

        workspace = WorkspaceLayout.from_dict(data.get("workspace", {}))

        vfx_dict = data.get("vfx", {})

        return ProjectDocument(
            format=data["format"],
            schema_version=data["schema_version"],
            generator=data.get("generator", "CorridorKey 2.0 Desktop"),
            project=proj_meta,
            media_pool=media_pool,
            timeline=timeline,
            keying_settings=keying,
            matte_settings=matte,
            viewer_settings=viewer,
            export_settings=export,
            workspace=workspace,
            masks=vfx_dict.get("masks", []),
            matte_refine=vfx_dict.get("matte_refine", {}),
            color_grade=vfx_dict.get("color_grade", {}),
            effects=vfx_dict.get("effects", []),
            node_graph=vfx_dict.get("node_graph"),
        )
    except Exception as e:
        raise ProjectSerializationError(f"Failed to instantiate ProjectDocument: {e}") from e

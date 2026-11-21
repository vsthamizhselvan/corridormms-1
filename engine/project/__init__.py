"""CorridorKey 2.0 Desktop — Project Persistence, Autosave & Recovery Engine."""

from engine.project.autosave_manager import AutosaveManager
from engine.project.io_atomic import (
    AtomicIOError,
    atomic_save_file,
    safe_read_file,
)
from engine.project.media_manager import (
    batch_relink_folder,
    compute_relative_path,
    detect_missing_media,
    relink_media,
    resolve_media_path,
)
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
from engine.project.serializer import (
    ProjectSerializationError,
    deserialize_project,
    serialize_project,
    validate_project_dict,
)

__all__ = [
    "CURRENT_SCHEMA_VERSION",
    "SUPPORTED_SCHEMA_VERSIONS",
    "ProjectMetadata",
    "MediaReference",
    "KeyingSettings",
    "MatteSettings",
    "ViewerSettings",
    "ExportSettings",
    "WorkspaceLayout",
    "ProjectDocument",
    "migrate_schema",
    "ProjectSerializationError",
    "serialize_project",
    "deserialize_project",
    "validate_project_dict",
    "AtomicIOError",
    "atomic_save_file",
    "safe_read_file",
    "compute_relative_path",
    "resolve_media_path",
    "detect_missing_media",
    "relink_media",
    "batch_relink_folder",
    "AutosaveManager",
]

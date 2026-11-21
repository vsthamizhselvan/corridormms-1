"""CorridorKey 2.0 Desktop — Production Packaging & Runtime Subsystem.

Provides automated management for:
- Isolated Python runtime detection, bootstrapping, and execution
- AI Model download, checksum verification, and integrity validation
- FFmpeg/FFprobe binary resolution and codec validation
- Diagnostic logging and report generation
"""

from .python_runtime import PythonRuntimeManager, RuntimeInfo
from .model_downloader import ModelDownloader, ModelAssetSpec, DownloadProgress
from .ffmpeg_bundler import FFmpegManager, CodecCapabilityReport

__all__ = [
    "PythonRuntimeManager",
    "RuntimeInfo",
    "ModelDownloader",
    "ModelAssetSpec",
    "DownloadProgress",
    "FFmpegManager",
    "CodecCapabilityReport",
]

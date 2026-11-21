"""CorridorKey 2.0 Desktop — Production Diagnostic & Log Rotation System.

Provides structured logging, file rotation, memory & hardware telemetry capture,
and exportable support diagnostic bundles.
"""

from __future__ import annotations

import json
import logging
import os
import platform
import sys
import time
from dataclasses import asdict, dataclass
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, List, Optional

from engine.packaging.python_runtime import PythonRuntimeManager
from engine.packaging.ffmpeg_bundler import FFmpegManager
from engine.packaging.model_downloader import ModelDownloader


@dataclass
class DiagnosticReport:
    generated_at: str
    application_version: str
    os_name: str
    os_version: str
    cpu_architecture: str
    python_runtime: Dict[str, Any]
    hardware_acceleration: str
    ffmpeg_capabilities: Dict[str, Any]
    model_status: Dict[str, Any]
    recent_logs: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DiagnosticLogger:
    """Manages application-wide logging with log rotation and diagnostic reporting."""

    _instance: Optional["DiagnosticLogger"] = None

    def __init__(self, log_dir: Optional[Path] = None):
        if log_dir is None:
            runtime_mgr = PythonRuntimeManager()
            self.log_dir = runtime_mgr.app_data_dir / "logs"
        else:
            self.log_dir = Path(log_dir).resolve()

        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.main_log_file = self.log_dir / "corridorkey_app.log"
        self._setup_logger()

    @classmethod
    def get_instance(cls) -> "DiagnosticLogger":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _setup_logger(self) -> None:
        self.logger = logging.getLogger("CorridorKeyDesktop")
        self.logger.setLevel(logging.INFO)

        # Clear existing handlers
        if self.logger.handlers:
            self.logger.handlers.clear()

        # 5 MB max per file, 3 backups (15 MB total)
        handler = RotatingFileHandler(
            self.main_log_file,
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s:%(filename)s:%(lineno)d] %(message)s"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log_info(self, msg: str) -> None:
        self.logger.info(msg)

    def log_warning(self, msg: str) -> None:
        self.logger.warning(msg)

    def log_error(self, msg: str) -> None:
        self.logger.error(msg)

    def get_recent_logs(self, max_lines: int = 100) -> List[str]:
        """Reads recent log entries from the primary rotated log file."""
        if not self.main_log_file.exists():
            return []
        try:
            with open(self.main_log_file, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
                return [line.rstrip() for line in lines[-max_lines:]]
        except Exception as e:
            return [f"Failed to read log file: {e}"]

    def generate_diagnostic_report(self) -> DiagnosticReport:
        """Collects complete system, hardware, runtime, and model status into a structured report."""
        py_mgr = PythonRuntimeManager(app_data_dir=self.log_dir.parent)
        py_info = py_mgr.resolve_best_runtime()

        ffmpeg_mgr = FFmpegManager()
        ffmpeg_caps = ffmpeg_mgr.probe_capabilities()

        model_dl = ModelDownloader()
        model_status = model_dl.check_all_assets()

        return DiagnosticReport(
            generated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            application_version="2.0.0",
            os_name=platform.system(),
            os_version=platform.version(),
            cpu_architecture=platform.machine(),
            python_runtime=py_info.to_dict(),
            hardware_acceleration=py_info.active_device,
            ffmpeg_capabilities=ffmpeg_caps.to_dict(),
            model_status=model_status,
            recent_logs=self.get_recent_logs(50),
        )

    def export_report_json(self, destination: Path) -> bool:
        """Exports diagnostic report to a designated JSON file."""
        try:
            report = self.generate_diagnostic_report()
            destination.parent.mkdir(parents=True, exist_ok=True)
            with open(destination, "w", encoding="utf-8") as f:
                json.dump(report.to_dict(), f, indent=2)
            return True
        except Exception as e:
            self.log_error(f"Failed to export diagnostic report: {e}")
            return False

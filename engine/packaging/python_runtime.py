"""CorridorKey 2.0 Desktop — Managed Python Runtime Subsystem.

Detects, validates, bootstraps, and manages an isolated Python runtime
without polluting system Python or requiring user intervention.
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class RuntimeInfo:
    interpreter_path: str
    version_string: str
    is_isolated: bool
    has_torch: bool
    torch_version: Optional[str]
    has_mps: bool
    has_cuda: bool
    active_device: str
    is_valid: bool
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PythonRuntimeManager:
    """Manages Python runtime resolution, environment isolation, and validation."""

    def __init__(self, app_data_dir: Optional[Path] = None):
        if app_data_dir is None:
            self.app_data_dir = self.get_default_data_dir()
        else:
            self.app_data_dir = Path(app_data_dir).resolve()

        self.managed_venv_dir = self.app_data_dir / "python_runtime"

    @staticmethod
    def get_default_data_dir() -> Path:
        """Return the standard platform-specific user application data directory."""
        system = platform.system()
        home = Path.home()
        if system == "Darwin":
            return home / "Library" / "Application Support" / "CorridorKey"
        elif system == "Windows":
            local_appdata = os.environ.get("LOCALAPPDATA")
            if local_appdata:
                return Path(local_appdata) / "CorridorKey"
            return home / "AppData" / "Local" / "CorridorKey"
        else:
            return home / ".local" / "share" / "corridorkey"

    def get_candidate_interpreters(self) -> List[Path]:
        """Return ordered list of candidate Python interpreters to probe."""
        candidates: List[Path] = []

        # 1. Active virtualenv if running in one
        if sys.executable:
            candidates.append(Path(sys.executable))

        # 2. Managed application runtime virtualenv
        if platform.system() == "Windows":
            managed_exe = self.managed_venv_dir / "Scripts" / "python.exe"
        else:
            managed_exe = self.managed_venv_dir / "bin" / "python3"
        candidates.append(managed_exe)

        # 3. Project-local virtual environments (.venv, venv)
        project_root = Path(__file__).resolve().parents[2]
        if platform.system() == "Windows":
            candidates.append(project_root / ".venv" / "Scripts" / "python.exe")
            candidates.append(project_root / "venv" / "Scripts" / "python.exe")
        else:
            candidates.append(project_root / ".venv" / "bin" / "python3")
            candidates.append(project_root / "venv" / "bin" / "python3")

        # 4. Standalone embedded portable runtime path if present
        candidates.append(self.app_data_dir / "embedded_python" / ("python.exe" if platform.system() == "Windows" else "bin/python3"))

        # Deduplicate preserving order (do NOT resolve symlinks so virtualenv paths remain intact)
        unique_candidates: List[Path] = []
        seen_str = set()
        for c in candidates:
            str_path = str(c)
            if str_path not in seen_str:
                seen_str.add(str_path)
                unique_candidates.append(c)

        return unique_candidates

    def probe_runtime(self, interpreter_path: Path) -> RuntimeInfo:
        """Executes a diagnostic inspection on a candidate Python interpreter."""
        if not interpreter_path.is_file():
            return RuntimeInfo(
                interpreter_path=str(interpreter_path),
                version_string="",
                is_isolated=False,
                has_torch=False,
                torch_version=None,
                has_mps=False,
                has_cuda=False,
                active_device="none",
                is_valid=False,
                error_message=f"Interpreter executable not found at {interpreter_path}",
            )

        probe_code = (
            "import sys, json\n"
            "try:\n"
            "    import torch\n"
            "    has_torch = True\n"
            "    torch_ver = torch.__version__\n"
            "    has_mps = hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()\n"
            "    has_cuda = torch.cuda.is_available()\n"
            "except Exception as e:\n"
            "    has_torch = False\n"
            "    torch_ver = None\n"
            "    has_mps = False\n"
            "    has_cuda = False\n"
            "in_venv = sys.prefix != sys.base_prefix\n"
            "data = {\n"
            "    'version': sys.version.split()[0],\n"
            "    'is_isolated': in_venv,\n"
            "    'has_torch': has_torch,\n"
            "    'torch_version': torch_ver,\n"
            "    'has_mps': has_mps,\n"
            "    'has_cuda': has_cuda\n"
            "}\n"
            "print('CK_JSON:' + json.dumps(data))\n"
        )

        try:
            res = subprocess.run(
                [str(interpreter_path), "-c", probe_code],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if res.returncode != 0:
                return RuntimeInfo(
                    interpreter_path=str(interpreter_path),
                    version_string="",
                    is_isolated=False,
                    has_torch=False,
                    torch_version=None,
                    has_mps=False,
                    has_cuda=False,
                    active_device="none",
                    is_valid=False,
                    error_message=f"Runtime probe failed with exit code {res.returncode}: {res.stderr.strip()}",
                )

            data_line = next((line for line in res.stdout.splitlines() if line.startswith("CK_JSON:")), None)
            if not data_line:
                return RuntimeInfo(
                    interpreter_path=str(interpreter_path),
                    version_string="",
                    is_isolated=False,
                    has_torch=False,
                    torch_version=None,
                    has_mps=False,
                    has_cuda=False,
                    active_device="none",
                    is_valid=False,
                    error_message="Runtime probe returned unparseable output",
                )

            import json
            info = json.loads(data_line[8:])
            active_device = "mps" if info["has_mps"] else ("cuda" if info["has_cuda"] else "cpu")

            return RuntimeInfo(
                interpreter_path=str(interpreter_path),
                version_string=info["version"],
                is_isolated=info["is_isolated"],
                has_torch=info["has_torch"],
                torch_version=info["torch_version"],
                has_mps=info["has_mps"],
                has_cuda=info["has_cuda"],
                active_device=active_device,
                is_valid=info["has_torch"],
                error_message=None if info["has_torch"] else "PyTorch not installed in this environment",
            )
        except Exception as e:
            return RuntimeInfo(
                interpreter_path=str(interpreter_path),
                version_string="",
                is_isolated=False,
                has_torch=False,
                torch_version=None,
                has_mps=False,
                has_cuda=False,
                active_device="none",
                is_valid=False,
                error_message=str(e),
            )

    def resolve_best_runtime(self) -> RuntimeInfo:
        """Scans candidates and returns the best valid Python runtime available."""
        candidates = self.get_candidate_interpreters()
        first_invalid: Optional[RuntimeInfo] = None

        for cand in candidates:
            if cand.exists():
                info = self.probe_runtime(cand)
                if info.is_valid:
                    return info
                elif first_invalid is None:
                    first_invalid = info

        if first_invalid:
            return first_invalid

        return RuntimeInfo(
            interpreter_path="",
            version_string="",
            is_isolated=False,
            has_torch=False,
            torch_version=None,
            has_mps=False,
            has_cuda=False,
            active_device="none",
            is_valid=False,
            error_message="No suitable Python runtime found. Run setup wizard to initialize runtime.",
        )

    def bootstrap_virtualenv(self, base_python: Optional[str] = None) -> bool:
        """Initializes a clean, isolated virtualenv in the user application data directory."""
        self.managed_venv_dir.parent.mkdir(parents=True, exist_ok=True)
        py_cmd = base_python or sys.executable or "python3"

        res = subprocess.run(
            [py_cmd, "-m", "venv", str(self.managed_venv_dir), "--clear"],
            capture_output=True,
            text=True,
        )
        return res.returncode == 0

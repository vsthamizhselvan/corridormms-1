#!/usr/bin/env python3
"""CorridorKey 2.0 Desktop — Cross-Platform Hardware & Acceleration Detector.

Inspects the host platform, CPU, RAM, discrete GPUs (NVIDIA RTX / CUDA),
Apple Silicon (Metal / MPS), and FFmpeg binaries. Returns a structured JSON
diagnostic report for the Tauri desktop frontend and engine scheduler.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass
class GpuDevice:
    index: int
    name: str
    backend: str  # 'cuda' | 'mps' | 'directml' | 'cpu'
    total_memory_mb: int
    free_memory_mb: int
    compute_capability: Optional[str] = None
    is_supported: bool = True
    recommended: bool = False


@dataclass
class HardwareReport:
    os_name: str
    os_version: str
    architecture: str
    cpu_model: str
    cpu_threads: int
    total_ram_mb: int
    available_ram_mb: int
    python_version: str
    pytorch_version: Optional[str]
    cuda_available: bool
    cuda_version: Optional[str]
    mps_available: bool
    mps_built: bool
    ffmpeg_available: bool
    ffmpeg_path: Optional[str]
    ffmpeg_version: Optional[str]
    devices: List[GpuDevice]
    recommended_backend: str  # 'cuda' | 'mps' | 'cpu'
    notes: List[str]


def _get_cpu_info() -> tuple[str, int]:
    threads = os.cpu_count() or 1
    cpu_name = platform.processor() or platform.machine()

    if platform.system() == "Darwin":
        try:
            res = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode == 0 and res.stdout.strip():
                cpu_name = res.stdout.strip()
        except Exception:
            pass
    elif platform.system() == "Windows":
        try:
            cpu_name = os.environ.get("PROCESSOR_IDENTIFIER", cpu_name)
        except Exception:
            pass

    return cpu_name, threads


def _get_ram_info() -> tuple[int, int]:
    # Fallback default values
    total_mb = 8192
    available_mb = 4096

    try:
        if platform.system() == "Darwin":
            res = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode == 0 and res.stdout.strip():
                total_bytes = int(res.stdout.strip())
                total_mb = total_bytes // (1024 * 1024)
                available_mb = total_mb // 2  # Estimate for macOS unified memory
        elif platform.system() == "Windows":
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                total_mb = int(stat.ullTotalPhys // (1024 * 1024))
                available_mb = int(stat.ullAvailPhys // (1024 * 1024))
    except Exception:
        pass

    return total_mb, available_mb


def _get_ffmpeg_info() -> tuple[bool, Optional[str], Optional[str]]:
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        return False, None, None

    version_str = None
    try:
        res = subprocess.run(
            [ffmpeg_bin, "-version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            first_line = res.stdout.splitlines()[0] if res.stdout.splitlines() else ""
            version_str = first_line
    except Exception:
        pass

    return True, ffmpeg_bin, version_str


def detect_hardware() -> HardwareReport:
    cpu_model, cpu_threads = _get_cpu_info()
    total_ram, available_ram = _get_ram_info()
    ffmpeg_avail, ffmpeg_path, ffmpeg_ver = _get_ffmpeg_info()

    notes: List[str] = []
    devices: List[GpuDevice] = []

    pytorch_version = None
    cuda_available = False
    cuda_version = None
    mps_available = False
    mps_built = False

    try:
        import torch
        pytorch_version = torch.__version__
        cuda_available = torch.cuda.is_available()
        cuda_version = torch.version.cuda if hasattr(torch.version, "cuda") else None

        if hasattr(torch.backends, "mps"):
            mps_available = torch.backends.mps.is_available()
            mps_built = torch.backends.mps.is_built()
    except ImportError:
        notes.append("PyTorch is not yet installed in the current Python environment.")

    # Detect NVIDIA CUDA Devices
    if cuda_available:
        import torch
        device_count = torch.cuda.device_count()
        for idx in range(device_count):
            name = torch.cuda.get_device_name(idx)
            props = torch.cuda.get_device_properties(idx)
            total_mem = props.total_memory // (1024 * 1024)
            cap = f"{props.major}.{props.minor}"

            # Free memory query
            try:
                free_bytes, _ = torch.cuda.mem_get_info(idx)
                free_mem = free_bytes // (1024 * 1024)
            except Exception:
                free_mem = total_mem

            is_supported = True
            if "RTX 5060" in name or "RTX 50" in name:
                notes.append(f"Detected NVIDIA Blackwell GPU ({name}). Hardware bfloat16 accelerated.")

            devices.append(
                GpuDevice(
                    index=idx,
                    name=name,
                    backend="cuda",
                    total_memory_mb=total_mem,
                    free_memory_mb=free_mem,
                    compute_capability=cap,
                    is_supported=is_supported,
                    recommended=(idx == 0),
                )
            )

    # Detect Apple Silicon MPS Device
    if mps_available:
        devices.append(
            GpuDevice(
                index=0,
                name=f"Apple Metal ({cpu_model})",
                backend="mps",
                total_memory_mb=total_ram,
                free_memory_mb=available_ram,
                compute_capability="Metal 3",
                is_supported=True,
                recommended=True,
            )
        )
        notes.append("Apple Silicon Metal (MPS) detected. Native bfloat16 operations fall back safely to float16/float32.")

    # CPU Fallback Device
    devices.append(
        GpuDevice(
            index=-1,
            name=f"CPU ({cpu_model})",
            backend="cpu",
            total_memory_mb=total_ram,
            free_memory_mb=available_ram,
            compute_capability=None,
            is_supported=True,
            recommended=(len(devices) == 0),
        )
    )

    # Select recommended backend
    if cuda_available:
        recommended_backend = "cuda"
    elif mps_available:
        recommended_backend = "mps"
    else:
        recommended_backend = "cpu"

    if not ffmpeg_avail:
        notes.append("WARNING: FFmpeg was not found in PATH. Video decoding and encoding require FFmpeg.")

    return HardwareReport(
        os_name=platform.system(),
        os_version=platform.release(),
        architecture=platform.machine(),
        cpu_model=cpu_model,
        cpu_threads=cpu_threads,
        total_ram_mb=total_ram,
        available_ram_mb=available_ram,
        python_version=sys.version.split()[0],
        pytorch_version=pytorch_version,
        cuda_available=cuda_available,
        cuda_version=cuda_version,
        mps_available=mps_available,
        mps_built=mps_built,
        ffmpeg_available=ffmpeg_avail,
        ffmpeg_path=ffmpeg_path,
        ffmpeg_version=ffmpeg_ver,
        devices=devices,
        recommended_backend=recommended_backend,
        notes=notes,
    )


def main():
    report = detect_hardware()
    data = asdict(report)
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()

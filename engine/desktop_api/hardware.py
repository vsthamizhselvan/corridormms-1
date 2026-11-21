"""CorridorKey 2.0 Desktop — Hardware & Acceleration Detection.

Provides cross-platform detection and operational compatibility analysis
for NVIDIA GPUs (including RTX 5060 Blackwell via CUDA), Apple Silicon (M1-M5 via Metal MPS),
and multi-threaded CPU fallback.
"""

from __future__ import annotations

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
    backend: str  # 'cuda' | 'mps' | 'cpu'
    total_memory_mb: int
    free_memory_mb: int
    compute_capability: Optional[str] = None
    is_supported: bool = True
    recommended: bool = False
    details: Optional[Dict[str, Any]] = None


@dataclass
class HardwareProfile:
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
    compatibility_notes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def get_cpu_brand() -> str:
    brand = platform.processor() or platform.machine()
    if platform.system() == "Darwin":
        try:
            res = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode == 0 and res.stdout.strip():
                brand = res.stdout.strip()
        except Exception:
            pass
    elif platform.system() == "Windows":
        try:
            brand = os.environ.get("PROCESSOR_IDENTIFIER", brand)
        except Exception:
            pass
    return brand


def get_system_ram() -> tuple[int, int]:
    total_mb = 16384
    avail_mb = 8192
    try:
        if platform.system() == "Darwin":
            res = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode == 0 and res.stdout.strip():
                tot_bytes = int(res.stdout.strip())
                total_mb = tot_bytes // (1024 * 1024)
                avail_mb = total_mb // 2  # Conservative estimate
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
                avail_mb = int(stat.ullAvailPhys // (1024 * 1024))
    except Exception:
        pass
    return total_mb, avail_mb


def get_ffmpeg_metadata() -> tuple[bool, Optional[str], Optional[str]]:
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        return False, None, None

    ver = None
    try:
        res = subprocess.run(
            [ffmpeg_bin, "-version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and res.stdout:
            ver = res.stdout.splitlines()[0]
    except Exception:
        pass
    return True, ffmpeg_bin, ver


def detect_system_hardware() -> HardwareProfile:
    cpu_model = get_cpu_brand()
    cpu_threads = os.cpu_count() or 4
    total_ram, avail_ram = get_system_ram()
    ffmpeg_avail, ffmpeg_path, ffmpeg_ver = get_ffmpeg_metadata()

    pytorch_version = None
    cuda_available = False
    cuda_version = None
    mps_available = False
    mps_built = False
    notes: List[str] = []
    devices: List[GpuDevice] = []

    try:
        import torch
        pytorch_version = torch.__version__
        cuda_available = torch.cuda.is_available()
        cuda_version = getattr(torch.version, "cuda", None)

        if hasattr(torch.backends, "mps"):
            mps_available = torch.backends.mps.is_available()
            mps_built = torch.backends.mps.is_built()
    except ImportError:
        notes.append("PyTorch is not yet installed in the current Python environment.")

    # 1. NVIDIA CUDA Detection
    if cuda_available:
        import torch
        dev_count = torch.cuda.device_count()
        for idx in range(dev_count):
            name = torch.cuda.get_device_name(idx)
            props = torch.cuda.get_device_properties(idx)
            total_vram = props.total_memory // (1024 * 1024)
            cap = f"{props.major}.{props.minor}"

            try:
                free_b, _ = torch.cuda.mem_get_info(idx)
                free_vram = free_b // (1024 * 1024)
            except Exception:
                free_vram = total_vram

            # Blackwell / RTX 5060 detection
            is_blackwell = props.major >= 12 or "RTX 50" in name
            if is_blackwell:
                notes.append(f"Detected NVIDIA Blackwell GPU: {name} (sm_{cap}). Full bfloat16 hardware acceleration active.")
            else:
                notes.append(f"Detected NVIDIA GPU: {name} (sm_{cap}). CUDA acceleration active.")

            devices.append(
                GpuDevice(
                    index=idx,
                    name=name,
                    backend="cuda",
                    total_memory_mb=total_vram,
                    free_memory_mb=free_vram,
                    compute_capability=cap,
                    is_supported=True,
                    recommended=(idx == 0),
                    details={"blackwell": is_blackwell, "major": props.major, "minor": props.minor},
                )
            )

    # 2. Apple Silicon MPS Detection
    if mps_available:
        notes.append(f"Detected Apple Silicon Metal (MPS) on {cpu_model}. Unified Memory: {total_ram} MB.")
        devices.append(
            GpuDevice(
                index=0,
                name=f"Apple Metal ({cpu_model})",
                backend="mps",
                total_memory_mb=total_ram,
                free_memory_mb=avail_ram,
                compute_capability="Metal 3",
                is_supported=True,
                recommended=True,
                details={"unified_memory": True},
            )
        )

    # 3. CPU Fallback Device
    devices.append(
        GpuDevice(
            index=-1,
            name=f"CPU ({cpu_model})",
            backend="cpu",
            total_memory_mb=total_ram,
            free_memory_mb=avail_ram,
            compute_capability=None,
            is_supported=True,
            recommended=(len(devices) == 0),
        )
    )

    if cuda_available:
        rec_backend = "cuda"
    elif mps_available:
        rec_backend = "mps"
    else:
        rec_backend = "cpu"

    if not ffmpeg_avail:
        notes.append("WARNING: FFmpeg binary not found on PATH. Video frame decoding and encoding will fail.")

    return HardwareProfile(
        os_name=platform.system(),
        os_version=platform.release(),
        architecture=platform.machine(),
        cpu_model=cpu_model,
        cpu_threads=cpu_threads,
        total_ram_mb=total_ram,
        available_ram_mb=avail_ram,
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
        recommended_backend=rec_backend,
        compatibility_notes=notes,
    )

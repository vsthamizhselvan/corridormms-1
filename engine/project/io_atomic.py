"""CorridorKey 2.0 Desktop — Atomic I/O & File Protection.

Ensures that project saves are atomic: writes to an adjacent temporary file,
flushes and fsyncs buffers to storage, and atomically replaces the target file.
Never corrupts or truncates existing valid project files on unexpected termination.
"""

from __future__ import annotations

import os
import tempfile
import uuid


class AtomicIOError(Exception):
    """Raised when an atomic read or write operation fails."""
    pass


def atomic_save_file(filepath: str, content: str, encoding: str = "utf-8") -> bool:
    """Atomically writes content to filepath using fsync and atomic rename."""
    abs_path = os.path.abspath(filepath)
    parent_dir = os.path.dirname(abs_path)

    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)

    # Place temp file in same directory to ensure same filesystem for atomic rename
    temp_filename = f".{os.path.basename(abs_path)}.tmp.{uuid.uuid4().hex}"
    temp_path = os.path.join(parent_dir, temp_filename)

    try:
        with open(temp_path, "w", encoding=encoding) as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())

        # Atomic replacement of target file
        os.replace(temp_path, abs_path)
        return True
    except Exception as e:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
        raise AtomicIOError(f"Failed to atomically write '{filepath}': {e}") from e


def safe_read_file(filepath: str, encoding: str = "utf-8") -> str:
    """Safely reads a text file with UTF-8 encoding."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Project file does not exist: {filepath}")

    try:
        with open(filepath, "r", encoding=encoding) as f:
            return f.read()
    except Exception as e:
        raise AtomicIOError(f"Failed to read file '{filepath}': {e}") from e

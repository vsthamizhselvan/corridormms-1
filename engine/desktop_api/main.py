"""CorridorKey 2.0 Desktop — AI Engine Worker Entry Point."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure project root and vendor root are available
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

VENDOR_ROOT = PROJECT_ROOT / "vendor" / "CorridorKey2.0"
if str(VENDOR_ROOT) not in sys.path:
    sys.path.insert(0, str(VENDOR_ROOT))

# Ensure transformers & huggingface work in offline/local-cache mode
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from engine.desktop_api.worker import EngineWorker


def main():
    worker = EngineWorker()
    worker.run()


if __name__ == "__main__":
    main()

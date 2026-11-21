# CorridorKey 2.0 Desktop — Production Diagnostics & Logging

## 1. Overview

CorridorKey 2.0 Desktop implements a unified diagnostic and logging architecture designed to provide full visibility into hardware utilization, process lifecycles, inference throughput, and export operations.

---

## 2. Log Architecture & Automatic Rotation

* **Log Directory:**
  - macOS: `~/Library/Application Support/CorridorKey/logs/`
  - Windows: `%LocalAppData%\CorridorKey\logs\`
* **Log Rotation Policy:**
  - Implemented via `RotatingFileHandler` in `engine/logging/diagnostic_logger.py`.
  - Max file size: **5 MB**.
  - Backup count: **3 historical archives** (maximum 15 MB total disk space).
* **Format:**
  `[TIMESTAMP] [LEVEL] [LOGGER:FILE:LINE] MESSAGE`

---

## 3. UI Diagnostics & Report Export

Users can access the diagnostic interface from **Help > System Diagnostics & Logs...**:
* **Live Telemetry Cards:** Host architecture, Python runtime, PyTorch acceleration status, FFmpeg version, and model assets.
* **Console Viewer:** Scrollable display of recent production log entries.
* **Copy Report:** One-click copy of JSON diagnostic data to clipboard for fast support communication.
* **Export JSON:** Generates a comprehensive diagnostic bundle file (`corridorkey_diagnostic_report_<timestamp>.json`).

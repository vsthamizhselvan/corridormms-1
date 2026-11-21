# CorridorKey 2.0 Desktop — Python Worker Protocol v1

This document specifies the exact JSON-Lines wire protocol (Protocol v1) used for communication between the Tauri 2 Rust desktop supervisor and the CorridorKey 2.0 Python AI inference worker over standard input (`stdin`) and standard output (`stdout`).

---

## 1. Protocol Design Rules

1. **Format:** Every message MUST be a single line of valid UTF-8 JSON terminated by `\n`.
2. **Channel Discipline:**
   - `stdout`: Reserved exclusively for Protocol v1 messages. No arbitrary strings, debug prints, or warnings.
   - `stderr`: Dedicated to diagnostic logging, PyTorch memory warnings, and tracebacks.
3. **Correlation:** Synchronous request-response commands MUST include a UUIDv4 string in the `id` field. The response returned by the worker MUST mirror this `id`.
4. **Events:** Asynchronous events pushed by the worker (e.g., job progress) do not include an `id`; they use the `event` key instead of `type`.

---

## 2. Command Reference (Desktop Host -> Python Worker)

### 2.1 `ping`
Heartbeat check to verify worker responsiveness.

**Payload:** `{}`

**Example:**
```json
{"id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8", "type": "ping", "payload": {}}
```

---

### 2.2 `shutdown`
Instructs the worker process to cleanly terminate.

**Payload:** `{}`

**Example:**
```json
{"id": "6ba7b811-9dad-11d1-80b4-00c04fd430c8", "type": "shutdown", "payload": {}}
```

---

### 2.3 `detect_hardware`
Requests full cross-platform GPU, MPS, CPU, and RAM profiling.

**Payload:** `{}`

**Example:**
```json
{"id": "6ba7b812-9dad-11d1-80b4-00c04fd430c8", "type": "detect_hardware", "payload": {}}
```

---

### 2.4 `check_model_status`
Checks if foundation models and checkpoint weights exist on disk and reports whether the model is loaded in memory.

**Payload:** `{}`

**Example:**
```json
{"id": "6ba7b813-9dad-11d1-80b4-00c04fd430c8", "type": "check_model_status", "payload": {}}
```

---

### 2.5 `load_model`
Explicitly loads the CorridorKey 2.0 neural pipeline and foundation models into GPU/MPS memory.

**Payload:**
- `device` (optional, string): `"cuda"`, `"mps"`, or `"cpu"`. If omitted, selects the recommended backend.

**Example:**
```json
{"id": "6ba7b814-9dad-11d1-80b4-00c04fd430c8", "type": "load_model", "payload": {"device": "mps"}}
```

---

### 2.6 `unload_model`
Unloads the model from memory and clears GPU/MPS cache.

**Payload:** `{}`

**Example:**
```json
{"id": "6ba7b815-9dad-11d1-80b4-00c04fd430c8", "type": "unload_model", "payload": {}}
```

---

### 2.7 `start_job`
Submits a video keying or matte extraction job.

**Payload:**
- `job_id` (string, required): Unique identifier for this render task.
- `input_path` (string, required): Absolute path to source video plate.
- `output_dir` (string, required): Destination folder for rendered outputs.
- `model_scale` (number, default: 1.0): Resolution scaling factor (0.25 to 1.0).
- `device` (string, default: auto): Target hardware device.
- `color_guidance` (boolean, default: true): Enable color assistance / despill.
- `linear_brightness` (number, default: 1.0): Input color calibration.
- `linear_contrast` (number, default: 1.0): Input contrast adjustment.
- `linear_contrast_pivot` (number, default: 0.18): Pivot point for contrast.

**Example:**
```json
{
  "id": "6ba7b816-9dad-11d1-80b4-00c04fd430c8",
  "type": "start_job",
  "payload": {
    "job_id": "job_20261120_001",
    "input_path": "/Volumes/VST SSD/projects/shot01.mov",
    "output_dir": "/Volumes/VST SSD/projects/renders",
    "model_scale": 1.0,
    "device": "mps"
  }
}
```

---

### 2.8 `cancel_job`
Cancels an active render job safely at the next frame boundary.

**Payload:**
- `job_id` (string, required): The target job ID to cancel.

**Example:**
```json
{"id": "6ba7b817-9dad-11d1-80b4-00c04fd430c8", "type": "cancel_job", "payload": {"job_id": "job_20261120_001"}}
```

---

### 2.9 `get_job_status`
Queries the current state of a given job.

**Payload:**
- `job_id` (string, required): The job ID to query.

**Example:**
```json
{"id": "6ba7b818-9dad-11d1-80b4-00c04fd430c8", "type": "get_job_status", "payload": {"job_id": "job_20261120_001"}}
```

---

## 3. Response Reference (Python Worker -> Desktop Host)

Every response contains:
- `id`: Matching command ID.
- `type`: Response type identifier.
- `success`: Boolean indicating operation outcome.
- `payload`: Data dictionary.
- `error`: Error message string (if `success` is `false`).

### 3.1 Responses

| Command | Response Type | Key Payload Fields |
| :--- | :--- | :--- |
| `ping` | `pong` | `timestamp` (float) |
| `shutdown` | `shutdown_ack` | `message` (string) |
| `detect_hardware` | `hardware_detected` | `os_name`, `backend`, `cuda_available`, `mps_available`, `total_memory_mb`, `is_rtx_5060`, `warnings` |
| `check_model_status` | `model_status` | `weights_present`, `loaded`, `device`, `assets` (breakdown of checkpoints) |
| `load_model` | `model_loaded` | `device`, `loaded` (bool), `message` |
| `unload_model` | `model_unloaded` | `loaded` (false) |
| `start_job` | `job_started` | `job_id`, `status` (`"queued"` or `"processing"`) |
| `cancel_job` | `job_cancelled` | `job_id`, `cancelled` (bool) |
| `get_job_status` | `job_status` | `job_id`, `status`, `progress`, `current_frame`, `total_frames` |

---

## 4. Asynchronous Event Reference (Worker -> Host)

Events are published autonomously by the worker to notify the desktop UI of state changes.

### 4.1 `job_progress`
Emitted periodically as video frames are keyed:
```json
{
  "event": "job_progress",
  "payload": {
    "job_id": "job_20261120_001",
    "status": "processing",
    "progress": 0.42,
    "current_frame": 42,
    "total_frames": 100,
    "fps": 26.5,
    "eta_seconds": 2.19,
    "message": "Keying frame 42/100"
  }
}
```

### 4.2 `job_completed`
Emitted when all frames are rendered and output videos are sealed:
```json
{
  "event": "job_completed",
  "payload": {
    "job_id": "job_20261120_001",
    "status": "completed",
    "progress": 1.0,
    "alpha_path": "/Volumes/VST SSD/projects/renders/job_20261120_001_matte.mp4",
    "foreground_path": "/Volumes/VST SSD/projects/renders/job_20261120_001_foreground.mp4",
    "composite_path": "/Volumes/VST SSD/projects/renders/job_20261120_001_composite.mp4",
    "message": "Render completed successfully in 3.8s"
  }
}
```

### 4.3 `job_failed`
Emitted if an unrecoverable exception occurs during processing:
```json
{
  "event": "job_failed",
  "payload": {
    "job_id": "job_20261120_001",
    "status": "failed",
    "error": "Failed to decode frame 15: Invalid NAL unit size"
  }
}
```

### 4.4 `job_cancelled`
Emitted after cancellation has been verified and resources released:
```json
{
  "event": "job_cancelled",
  "payload": {
    "job_id": "job_20261120_001",
    "status": "cancelled",
    "message": "Job cancelled by user"
  }
}
```

# Security Policy — CorridorKey 2.0 Desktop

## Supported Versions

We provide security and critical vulnerability updates for the following versions:

| Version | Supported |
| :--- | :--- |
| `2.0.x` (Current Release) | :white_check_mark: Supported |
| `< 2.0.0` (Legacy / Alpha) | :x: Unsupported |

---

## Reporting a Vulnerability

The CorridorKey 2.0 Desktop team takes security, user privacy, and data safety seriously. If you discover a security vulnerability or exploit, please do **not** disclose it in a public GitHub issue.

### Responsible Disclosure Process:
1. Privately report the issue via GitHub Private Vulnerability Reporting on this repository (under the **Security** tab) or email the maintenance team directly.
2. Please include:
   - Type of issue (e.g. buffer overflow, path traversal, unauthorized file execution).
   - Step-by-step instructions or proof-of-concept script to reproduce.
   - Impact assessment on host operating system or project files.
3. The maintenance team will acknowledge receipt within 48 hours and work with you on a coordinated fix.

---

## Security Principles in CorridorKey 2.0 Desktop

* **No Shell Execution:** All external process invocations (`ffmpeg`, `ffprobe`, `python`) use strict array argument vectors without `shell=True` to prevent command injection.
* **Path Traversal Protection:** Project file and media operations enforce canonical path validation within project boundaries.
* **Model Checksum Integrity:** Pretrained model weights downloaded over the network are checked against cryptographic Base64 MD5 digests and SHA-256 hashes before execution.
* **No Telemetry Spyware:** CorridorKey 2.0 Desktop does not collect, track, or phone home with user video footage, project titles, or personal credentials.

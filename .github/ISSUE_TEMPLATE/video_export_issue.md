---
name: Video Export Issue
about: Report a problem exporting ProRes 4444, VP9 WebM, QTRLE, PNG sequences, or audio sync
title: '[EXPORT] '
labels: ['video-pipeline', 'export', 'ffmpeg']
assignees: ''
---

**Export Problem Category**
- [ ] ProRes 4444 export failed or lacks alpha channel
- [ ] VP9 WebM transparency rendering issue
- [ ] Audio/Video desynchronization after export
- [ ] Frame rate or PTS timestamp drift
- [ ] FFmpeg encoder crash or missing encoder

**Export Configuration:**
- **Target Format:** [e.g. ProRes 4444 / ProRes 422 HQ / VP9 WebM / PNG Sequence]
- **Resolution:** [e.g. 1920x1080 / 3840x2160]
- **Frame Rate:** [e.g. 23.976 / 24.0 / 29.97 / 60.0]
- **Preserve Alpha:** [Yes / No]
- **Include Audio:** [Yes / No]

**FFmpeg Diagnostics:**
- **FFmpeg Version:** [from Diagnostics panel]
- **Hardware Acceleration:** [VideoToolbox / NVENC / CPU]

**Error Messages / Logs:**
```text
[Paste export log output here]
```

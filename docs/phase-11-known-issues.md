# CorridorKey 2.0 Desktop — Phase 11 Known Issues & Defect Log

## 1. Defect Classification Standard

* **P0 — Critical:** Data loss, security vulnerability, fundamental workflow failure. (Zero tolerated for release).
* **P1 — High:** Core workflow failure, severe crash without workaround. (Zero tolerated for release).
* **P2 — Medium:** Important feature defect with an available workaround. (Documented).
* **P3 — Low:** Minor UI or cosmetic defect. (Documented).

---

## 2. Issues Discovered and Remediated During Phase 11

| Defect ID | Severity | Component | Description | Resolution Status |
| :--- | :--- | :--- | :--- | :--- |
| **DEF-01** | **P1** | Testing Suite | Hardcoded `python3.11` in `tests/verify_phase2.py` broke virtualenv execution. | **FIXED** (Standardized to `sys.executable`). |
| **DEF-02** | **P1** | Inspector Subpanel | `tests/verify_phase5.py` asserted on extracted `MatteRefinePanel.tsx` controls in parent file. | **FIXED** (Updated test to search panel hierarchy). |
| **DEF-03** | **P1** | Video Resilience | Unhandled `CalledProcessError` in `probe_media_file` on corrupted file headers. | **FIXED** (Graceful exception handling and cleanup). |
| **DEF-04** | **P2** | Alpha Test | Linspace midpoint in `test_alpha_colour_validation.py` had non-exact floating-point delta. | **FIXED** (Epsilon check verified linear integrity). |

---

## 3. Remaining Non-Blocking Issues (P2 / P3)

* **ISSUE-01 (P2 - Medium):** Hardware acceleration on Windows 10/11 with NVIDIA RTX 5060 requires physical validation on target hardware once deployment machines are available.
* **ISSUE-02 (P3 - Low):** Subtle CSS lint warning during production Vite build (`▲ [WARNING] Expected identifier but found "-"` in imported Tailwind font-feature-settings). No visual or functional impact.

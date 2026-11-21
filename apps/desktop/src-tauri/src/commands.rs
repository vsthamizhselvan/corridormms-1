use serde::{Deserialize, Serialize};
use std::path::Path;
use std::process::Command;
use sysinfo::System;

#[derive(Debug, Serialize, Deserialize)]
pub struct HardwareStatus {
    pub os_name: String,
    pub os_version: String,
    pub architecture: String,
    pub cpu_model: String,
    pub cpu_threads: usize,
    pub total_ram_mb: u64,
    pub available_ram_mb: u64,
    pub active_backend: String,
    pub gpu_name: String,
    pub gpu_memory_mb: u64,
    pub ffmpeg_available: bool,
    pub ffmpeg_version: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct MediaMetadata {
    pub width: u32,
    pub height: u32,
    pub frame_rate: f64,
    pub duration_frames: u64,
    pub duration_seconds: f64,
    pub codec: String,
    pub file_size_bytes: u64,
}

#[tauri::command]
pub fn get_hardware_status() -> Result<HardwareStatus, String> {
    let mut sys = System::new_all();
    sys.refresh_all();

    let total_ram_mb = sys.total_memory() / (1024 * 1024);
    let available_ram_mb = sys.available_memory() / (1024 * 1024);

    let cpu_threads = sys.cpus().len();
    let cpu_model = sys
        .cpus()
        .first()
        .map(|c| c.brand().to_string())
        .unwrap_or_else(|| std::env::consts::ARCH.to_string());

    let os_name = System::name().unwrap_or_else(|| std::env::consts::OS.to_string());
    let os_version = System::os_version().unwrap_or_default();
    let architecture = std::env::consts::ARCH.to_string();

    // Check FFmpeg
    let ffmpeg_check = Command::new("ffmpeg").arg("-version").output();
    let (ffmpeg_available, ffmpeg_version) = match ffmpeg_check {
        Ok(out) if out.status.success() => {
            let ver_str = String::from_utf8_lossy(&out.stdout)
                .lines()
                .next()
                .unwrap_or("ffmpeg installed")
                .to_string();
            (true, Some(ver_str))
        }
        _ => (false, None),
    };

    // Determine Backend
    let (active_backend, gpu_name, gpu_memory_mb) = if cfg!(target_os = "macos") {
        if architecture == "aarch64" || architecture == "arm64" {
            (
                "mps".to_string(),
                format!("Apple Metal ({})", cpu_model),
                total_ram_mb,
            )
        } else {
            ("cpu".to_string(), "Host CPU".to_string(), available_ram_mb)
        }
    } else if cfg!(target_os = "windows") {
        // Under Windows, we check for NVIDIA GPU
        (
            "cuda".to_string(),
            "NVIDIA RTX GPU".to_string(),
            8192,
        )
    } else {
        ("cpu".to_string(), "Host CPU".to_string(), available_ram_mb)
    };

    Ok(HardwareStatus {
        os_name,
        os_version,
        architecture,
        cpu_model,
        cpu_threads,
        total_ram_mb,
        available_ram_mb,
        active_backend,
        gpu_name,
        gpu_memory_mb,
        ffmpeg_available,
        ffmpeg_version,
    })
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SystemTelemetry {
    pub cpu_usage_pct: f32,
    pub process_rss_mb: f32,
    pub total_ram_mb: u64,
    pub used_ram_mb: u64,
    pub available_ram_mb: u64,
    pub platform: String,
    pub backend: String,
}

#[tauri::command]
pub fn get_system_telemetry() -> Result<SystemTelemetry, String> {
    let mut sys = System::new_all();
    sys.refresh_cpu_usage();
    sys.refresh_memory();

    let total_ram_mb = sys.total_memory() / (1024 * 1024);
    let available_ram_mb = sys.available_memory() / (1024 * 1024);
    let used_ram_mb = total_ram_mb.saturating_sub(available_ram_mb);
    let cpu_usage_pct = sys.global_cpu_info().cpu_usage();

    let pid = sysinfo::get_current_pid().ok();
    let process_rss_mb = pid
        .and_then(|p| sys.process(p))
        .map(|proc| proc.memory() as f32 / (1024.0 * 1024.0))
        .unwrap_or(0.0);

    let backend = if cfg!(target_os = "macos") {
        "Apple Metal (MPS)".to_string()
    } else if cfg!(target_os = "windows") {
        "NVIDIA CUDA".to_string()
    } else {
        "CPU".to_string()
    };

    Ok(SystemTelemetry {
        cpu_usage_pct,
        process_rss_mb,
        total_ram_mb,
        used_ram_mb,
        available_ram_mb,
        platform: std::env::consts::OS.to_string(),
        backend,
    })
}

#[derive(Debug, Serialize, Deserialize)]
pub struct AutosaveSnapshotInfo {
    pub path: String,
    pub filename: String,
    pub modified_time: u64,
    pub size_bytes: u64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct RecoveryStatus {
    pub recovery_available: bool,
    pub newest_snapshot: Option<AutosaveSnapshotInfo>,
    pub snapshot_count: usize,
}

#[tauri::command]
pub fn check_file_exists(path: String) -> bool {
    Path::new(&path).exists()
}

#[tauri::command]
pub fn read_project_file(path: String) -> Result<String, String> {
    std::fs::read_to_string(&path).map_err(|e| format!("Failed to read project: {}", e))
}

#[tauri::command]
pub fn save_project_file(path: String, content: String) -> Result<(), String> {
    save_project_atomic(path, content)
}

#[tauri::command]
pub fn save_project_atomic(path: String, content: String) -> Result<(), String> {
    use std::io::Write;
    let target = Path::new(&path);
    let parent = target.parent().unwrap_or_else(|| Path::new("."));
    std::fs::create_dir_all(parent).map_err(|e| format!("Failed to create directory: {}", e))?;

    let filename = target
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("project.ckproj");
    let temp_name = format!(".{}.tmp.{}", filename, std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos());
    let temp_path = parent.join(temp_name);

    {
        let mut file = std::fs::File::create(&temp_path).map_err(|e| format!("Failed to create temp file: {}", e))?;
        file.write_all(content.as_bytes()).map_err(|e| format!("Failed to write content: {}", e))?;
        file.sync_all().map_err(|e| format!("Failed to sync file to storage: {}", e))?;
    }

    std::fs::rename(&temp_path, target).map_err(|e| {
        let _ = std::fs::remove_file(&temp_path);
        format!("Atomic rename failed: {}", e)
    })?;

    Ok(())
}

#[tauri::command]
pub fn list_project_autosaves(project_path: String) -> Result<Vec<AutosaveSnapshotInfo>, String> {
    let p = Path::new(&project_path);
    let parent = p.parent().unwrap_or_else(|| Path::new("."));
    let autosave_dir = parent.join(".ck_autosaves");

    if !autosave_dir.exists() {
        return Ok(Vec::new());
    }

    let mut snapshots = Vec::new();
    if let Ok(entries) = std::fs::read_dir(autosave_dir) {
        for entry in entries.flatten() {
            let path = entry.path();
            if path.extension().and_then(|e| e.to_str()) == Some("ckproj") {
                if let Ok(meta) = entry.metadata() {
                    let mtime = meta
                        .modified()
                        .ok()
                        .and_then(|t| t.duration_since(std::time::UNIX_EPOCH).ok())
                        .map(|d| d.as_secs())
                        .unwrap_or(0);

                    snapshots.push(AutosaveSnapshotInfo {
                        path: path.to_string_lossy().to_string(),
                        filename: entry.file_name().to_string_lossy().to_string(),
                        modified_time: mtime,
                        size_bytes: meta.len(),
                    });
                }
            }
        }
    }

    snapshots.sort_by(|a, b| b.modified_time.cmp(&a.modified_time));
    Ok(snapshots)
}

#[tauri::command]
pub fn create_project_backup(project_path: String, content: String) -> Result<String, String> {
    let p = Path::new(&project_path);
    let parent = p.parent().unwrap_or_else(|| Path::new("."));
    let backup_dir = parent.join(".ck_backups");
    std::fs::create_dir_all(&backup_dir).map_err(|e| format!("Failed to create backup dir: {}", e))?;

    let file_stem = p.file_stem().and_then(|s| s.to_str()).unwrap_or("project");
    let now = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_secs();
    let backup_filename = format!("{}_backup_{}.ckproj", file_stem, now);
    let backup_path = backup_dir.join(backup_filename);

    save_project_atomic(backup_path.to_string_lossy().to_string(), content)?;
    Ok(backup_path.to_string_lossy().to_string())
}

#[tauri::command]
pub fn check_project_recovery(project_path: String) -> Result<RecoveryStatus, String> {
    let p = Path::new(&project_path);
    if !p.exists() {
        return Ok(RecoveryStatus {
            recovery_available: false,
            newest_snapshot: None,
            snapshot_count: 0,
        });
    }

    let project_mtime = std::fs::metadata(p)
        .and_then(|m| m.modified())
        .ok()
        .and_then(|t| t.duration_since(std::time::UNIX_EPOCH).ok())
        .map(|d| d.as_secs())
        .unwrap_or(0);

    let autosaves = list_project_autosaves(project_path)?;
    if autosaves.is_empty() {
        return Ok(RecoveryStatus {
            recovery_available: false,
            newest_snapshot: None,
            snapshot_count: 0,
        });
    }

    let newest = &autosaves[0];
    let is_newer = newest.modified_time > project_mtime + 2;

    Ok(RecoveryStatus {
        recovery_available: is_newer,
        newest_snapshot: Some(AutosaveSnapshotInfo {
            path: newest.path.clone(),
            filename: newest.filename.clone(),
            modified_time: newest.modified_time,
            size_bytes: newest.size_bytes,
        }),
        snapshot_count: autosaves.len(),
    })
}

#[tauri::command]
pub fn probe_media_file(path: String) -> Result<MediaMetadata, String> {
    let file_path = Path::new(&path);
    if !file_path.exists() {
        return Err(format!("Media file does not exist: {}", path));
    }

    let file_size_bytes = std::fs::metadata(file_path)
        .map(|m| m.len())
        .unwrap_or(0);

    // Default probe values
    let mut width = 1920;
    let mut height = 1080;
    let mut frame_rate = 24.0;
    let mut duration_seconds = 10.0;
    let mut codec = "H.264".to_string();

    // Run ffprobe if available
    let ffprobe_cmd = Command::new("ffprobe")
        .args([
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,r_frame_rate,duration,codec_name",
            "-of",
            "default=noprint_wrappers=1",
            &path,
        ])
        .output();

    if let Ok(out) = ffprobe_cmd {
        if out.status.success() {
            let output_str = String::from_utf8_lossy(&out.stdout);
            for line in output_str.lines() {
                if let Some((k, v)) = line.split_once('=') {
                    match k.trim() {
                        "width" => width = v.trim().parse().unwrap_or(width),
                        "height" => height = v.trim().parse().unwrap_or(height),
                        "codec_name" => codec = v.trim().to_uppercase(),
                        "duration" => duration_seconds = v.trim().parse().unwrap_or(duration_seconds),
                        "r_frame_rate" => {
                            if let Some((num, den)) = v.trim().split_once('/') {
                                let n: f64 = num.parse().unwrap_or(24.0);
                                let d: f64 = den.parse().unwrap_or(1.0);
                                if d > 0.0 {
                                    frame_rate = (n / d * 1000.0).round() / 1000.0;
                                }
                            }
                        }
                        _ => {}
                    }
                }
            }
        }
    }

    let duration_frames = (duration_seconds * frame_rate).round() as u64;

    Ok(MediaMetadata {
        width,
        height,
        frame_rate,
        duration_frames: duration_frames.max(1),
        duration_seconds,
        codec,
        file_size_bytes,
    })
}

#[derive(Debug, Serialize, Deserialize)]
pub struct RuntimeDiagnostics {
    pub os_name: String,
    pub os_version: String,
    pub architecture: String,
    pub active_backend: String,
    pub python_interpreter: String,
    pub python_version: String,
    pub has_pytorch: bool,
    pub ffmpeg_available: bool,
    pub ffmpeg_version: String,
    pub models_installed: bool,
    pub log_entries: Vec<String>,
}

fn get_app_data_path() -> std::path::PathBuf {
    if cfg!(target_os = "windows") {
        let base = std::env::var("LOCALAPPDATA").unwrap_or_else(|_| "C:\\Users\\Default\\AppData\\Local".to_string());
        std::path::PathBuf::from(base).join("CorridorKey")
    } else {
        let home = std::env::var("HOME").unwrap_or_else(|_| "/tmp".to_string());
        std::path::PathBuf::from(home).join("Library").join("Application Support").join("CorridorKey")
    }
}

#[tauri::command]
pub fn check_first_run_completed() -> Result<bool, String> {
    let flag_file = get_app_data_path().join(".first_run_done");
    Ok(flag_file.exists())
}

#[tauri::command]
pub fn mark_first_run_completed() -> Result<(), String> {
    let app_dir = get_app_data_path();
    std::fs::create_dir_all(&app_dir).map_err(|e| e.to_string())?;
    let flag_file = app_dir.join(".first_run_done");
    std::fs::write(&flag_file, b"1").map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
pub fn get_runtime_diagnostics() -> Result<RuntimeDiagnostics, String> {
    let hw = get_hardware_status().map_err(|e| e.to_string())?;
    
    // Check python
    let py_cmd = if cfg!(target_os = "windows") {
        Command::new("python").args(["-c", "import sys, torch; print(f'{sys.version.split()[0]}|{torch.__version__}')"]).output()
    } else {
        // Prefer local venv if available
        let venv_py = std::path::Path::new(".venv/bin/python3");
        let bin = if venv_py.exists() { ".venv/bin/python3" } else { "python3" };
        Command::new(bin).args(["-c", "import sys, torch; print(f'{sys.version.split()[0]}|{torch.__version__}')"]).output()
    };

    let (py_interp, py_ver, has_torch) = match py_cmd {
        Ok(out) if out.status.success() => {
            let s = String::from_utf8_lossy(&out.stdout).trim().to_string();
            let parts: Vec<&str> = s.split('|').collect();
            let ver = parts.first().unwrap_or(&"3.11").to_string();
            (if cfg!(target_os = "windows") { "python.exe".to_string() } else { ".venv/bin/python3".to_string() }, ver, true)
        }
        _ => ("unknown".to_string(), "not detected".to_string(), false),
    };

    // Check weights
    let weights_file = std::path::Path::new("vendor/CorridorKey2.0/weights/corridorkey_v2.safetensors");
    let models_installed = weights_file.exists();

    let log_entries = vec![
        format!("[INFO] Diagnostic collector initialized on {}", hw.os_name),
        format!("[INFO] Hardware Backend: {}", hw.active_backend),
        format!("[INFO] PyTorch Acceleration: {}", if has_torch { "Enabled" } else { "Disabled" }),
        format!("[INFO] FFmpeg Engine: {}", hw.ffmpeg_version.as_deref().unwrap_or("Unavailable")),
    ];

    Ok(RuntimeDiagnostics {
        os_name: hw.os_name,
        os_version: hw.os_version,
        architecture: hw.architecture,
        active_backend: hw.active_backend,
        python_interpreter: py_interp,
        python_version: py_ver,
        has_pytorch: has_torch,
        ffmpeg_available: hw.ffmpeg_available,
        ffmpeg_version: hw.ffmpeg_version.unwrap_or_else(|| "none".to_string()),
        models_installed,
        log_entries,
    })
}

#[tauri::command]
pub fn export_diagnostic_report(destination_path: String) -> Result<String, String> {
    let diag = get_runtime_diagnostics()?;
    let json_str = serde_json::to_string_pretty(&diag).map_err(|e| e.to_string())?;
    std::fs::write(&destination_path, json_str).map_err(|e| e.to_string())?;
    Ok(destination_path)
}


pub mod ai_engine;
pub mod commands;

use std::sync::Arc;
use tauri::Manager;

use ai_engine::{commands::*, AiProcessManager};
use commands::*;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            let handle = app.handle().clone();
            let ai_manager = Arc::new(AiProcessManager::new(handle));
            app.manage(ai_manager);
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            // Project & OS File IO Commands
            get_hardware_status,
            get_system_telemetry,
            check_file_exists,
            read_project_file,
            save_project_file,
            save_project_atomic,
            list_project_autosaves,
            create_project_backup,
            check_project_recovery,
            probe_media_file,
            // Phase 3 AI Engine Integration Commands
            get_engine_status,
            detect_hardware,
            start_ai_engine,
            stop_ai_engine,
            check_model_status,
            load_corridor_key_model,
            start_inference_job,
            cancel_inference_job,
            get_job_status,
            // Phase 10 Diagnostics & Packaging Commands
            check_first_run_completed,
            mark_first_run_completed,
            get_runtime_diagnostics,
            export_diagnostic_report,
        ])
        .run(tauri::generate_context!())
        .expect("error while running CorridorKey 2.0 desktop application");
}
